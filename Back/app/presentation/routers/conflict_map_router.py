"""
Router para el sistema de visualización de grafo de conflictos.
Expone endpoints REST para:
- Obtener filtros de países y actores
- Construir grafos de relaciones
- Obtener detalles de nodos individuales
"""

from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional
import urllib.parse  

from app.business.models.conflict_schema import (
    GraphFilterType,
    FiltersResponse,
    GraphResponse,
    NodeDetails
)
from app.business.services.conflict_map_service import ConflictMapService


# ======================================================
# CONFIGURACIÓN DEL ROUTER
# ======================================================

router = APIRouter(
    prefix="/api/v1/graph",
    tags=["Conflict Graph"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)


# ======================================================
# ENDPOINT 1: OBTENER FILTROS
# ======================================================

@router.get(
    "/filters",
    response_model=FiltersResponse,
    summary="Obtener lista de filtros disponibles",
    description="""
    Obtiene una lista de países o actores disponibles para usar como filtro inicial del grafo.
    
    **Casos de uso:**
    - Llenar dropdown de países para selección inicial
    - Implementar autocompletado de actores
    - Mostrar opciones ordenadas por relevancia (número de conflictos)
    
    **Parámetros:**
    - `type`: Tipo de filtro (country o actor)
    - `search`: Término de búsqueda opcional para filtrar resultados
    
    **Respuesta:**
    - Lista ordenada por número de conflictos (descendente)
    - Incluye métricas: conflict_count y total_deaths
    - Limitado a top 100 resultados
    """,
    responses={
        200: {
            "description": "Lista de filtros obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "type": "country",
                        "count": 150,
                        "items": [
                            {
                                "value": "Afghanistan",
                                "label": "Afghanistan",
                                "conflict_count": 45,
                                "total_deaths": 50000
                            },
                            {
                                "value": "Pakistan",
                                "label": "Pakistan",
                                "conflict_count": 38,
                                "total_deaths": 35000
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Parámetros inválidos"
        }
    }
)
async def get_graph_filters(
    entity_type: GraphFilterType = Query(  
        ...,
        alias="type",  
        description="Tipo de filtro: 'country' para países, 'actor' para actores"
    ),
    search: Optional[str] = Query(
        None,
        description="Término de búsqueda opcional (case-sensitive)",
        min_length=2,
        max_length=100
    )
):
    """
    Obtiene lista de países o actores disponibles para filtro inicial.
    
    Ejemplo de uso:
```
    GET /api/graph/filters?type=country
    GET /api/graph/filters?type=actor&search=Taliban
```
    """
    try:
        service = ConflictMapService()
        return await service.get_filters(entity_type, search)  
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo filtros: {str(e)}"
        )


# ======================================================
# ENDPOINT 2: OBTENER NODOS Y RELACIONES DEL GRAFO
# ======================================================

@router.get(
    "/nodes",
    response_model=GraphResponse,
    summary="Obtener estructura del grafo para una entidad",
    description="""
    Construye y retorna la estructura completa del grafo para una entidad específica (país o actor).
    
    **Funcionalidad:**
    - Identifica el nodo central (país o actor seleccionado)
    - Encuentra todos los nodos conectados directamente
    - Calcula las relaciones (aristas) entre nodos
    - Agrega métricas de cada nodo y arista
    
    **Parámetros:**
    - `type`: Tipo de entidad (country o actor)
    - `value`: Nombre específico de la entidad
    - `depth`: Profundidad del grafo (1 = vecinos directos, 2 = vecinos + vecinos de vecinos)
    
    **Respuesta:**
    - `center_node`: Nodo central del grafo
    - `nodes`: Lista de nodos conectados
    - `edges`: Lista de aristas con pesos (grosor = total_deaths)
    - `summary`: Estadísticas agregadas del grafo
    
    **Casos de uso:**
    - Visualización de red de conflictos entre países
    - Análisis de actores enfrentados en conflictos
    - Exploración de relaciones geopolíticas
    """,
    responses={
        200: {
            "description": "Grafo construido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "center_node": {
                            "id": "Afghanistan",
                            "label": "Afghanistan",
                            "type": "country",
                            "region": "Asia",
                            "metrics": {
                                "total_conflicts": 45,
                                "total_deaths": 50000,
                                "connections": 8
                            }
                        },
                        "nodes": [
                            {
                                "id": "Pakistan",
                                "label": "Pakistan",
                                "type": "country",
                                "region": "Asia",
                                "metrics": {
                                    "total_conflicts": 38,
                                    "total_deaths": 35000,
                                    "connections": 6
                                }
                            }
                        ],
                        "edges": [
                            {
                                "id": "Afghanistan-Pakistan",
                                "source": "Afghanistan",
                                "target": "Pakistan",
                                "weight": 12000,
                                "metrics": {
                                    "event_count": 150,
                                    "conflict_names": ["Taliban insurgency"],
                                    "actors_involved": ["Taliban", "Government"]
                                }
                            }
                        ],
                        "summary": {
                            "total_nodes": 9,
                            "total_edges": 12,
                            "total_deaths": 65000,
                            "total_conflicts": 28,
                            "depth": 1
                        }
                    }
                }
            }
        },
        404: {
            "description": "Entidad no encontrada"
        }
    }
)
async def get_graph_nodes(
    entity_type: GraphFilterType = Query(  
        ...,
        alias="type",  
        description="Tipo de entidad: 'country' para países, 'actor' para actores"
    ),
    value: str = Query(
        ...,
        description="Nombre específico de la entidad (ej: 'Afghanistan', 'Taliban')",
        min_length=2,
        max_length=200
    ),
    depth: int = Query(
        1,
        description="Profundidad del grafo: 1 = vecinos directos, 2 = vecinos + sus vecinos",
        ge=1,
        le=2
    )
):
    """
    Construye y retorna la estructura del grafo para una entidad específica.
    
    **Para países (type=country):**
    - Encuentra países conectados via relaciones CONFLICT_WITH
    - Incluye información de conflictos compartidos
    - Muestra actores involucrados en cada relación
    
    **Para actores (type=actor):**
    - Encuentra actores enfrentados via relaciones ENGAGED_WITH
    - Incluye número de encuentros y muertes
    - Muestra conflictos donde se enfrentaron
    
    Ejemplo de uso:
```
    GET /api/graph/nodes?type=country&value=Afghanistan&depth=1
    GET /api/graph/nodes?type=actor&value=Taliban&depth=1
```
    """
    try:
        value_decoded = urllib.parse.unquote(value)
        
        print(f"🔍 GET /api/graph/nodes")
        print(f"   Type: {entity_type}")  
        print(f"   Value (raw): {value}")
        print(f"   Value (decoded): {value_decoded}")
        print(f"   Depth: {depth}")
        
        service = ConflictMapService()
        
        if entity_type == GraphFilterType.COUNTRY: 
            result = await service.get_graph_for_country(value_decoded, depth)
        else:
            result = await service.get_graph_for_actor(value_decoded, depth)
        
        print(f"✅ Grafo construido exitosamente:")
        print(f"   Nodos: {result.summary.total_nodes}")
        print(f"   Edges: {result.summary.total_edges}")
        print(f"   Total deaths: {result.summary.total_deaths}")
        
        return result
            
    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ Error inesperado: {type(e).__name__}")  
        print(f"   Mensaje: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error construyendo grafo: {str(e)}"
        )

# ======================================================
# ENDPOINT 3: OBTENER DETALLES DE NODO ESPECÍFICO
# ======================================================

@router.get(
    "/node-details",
    response_model=NodeDetails,
    summary="Obtener información detallada de un nodo",
    description="""
    Obtiene información completa y detallada de un nodo específico (país o actor).
    
    **Funcionalidad:**
    - Estadísticas generales del nodo
    - Top 10 conflictos más mortales asociados
    - Entidades conectadas (países o actores)
    - Para países: Lista de actores involucrados
    - Para actores: Países donde ha estado activo
    
    **Casos de uso:**
    - Mostrar panel lateral con detalles al hacer click en un nodo
    - Análisis profundo de un país o actor específico
    - Exploración de relaciones y contexto histórico
    
    **Parámetros:**
    - `type`: Tipo de nodo (country o actor)
    - `value`: Nombre específico del nodo
    
    **Respuesta diferenciada por tipo:**
    
    **Para países:**
    - `statistics`: Total de conflictos, muertes, eventos, conexiones
    - `top_conflicts`: Conflictos más importantes del país
    - `connected_entities`: Países con conflictos compartidos
    - `actors_involved`: Actores que han participado en conflictos del país
    
    **Para actores:**
    - `statistics`: Total de conflictos, muertes, encuentros, países activos
    - `top_conflicts`: Conflictos donde más ha participado
    - `connected_entities`: Otros actores con los que se ha enfrentado
    """,
    responses={
        200: {
            "description": "Detalles del nodo obtenidos exitosamente",
            "content": {
                "application/json": {
                    "examples": {
                        "country": {
                            "summary": "Detalles de un país",
                            "value": {
                                "type": "country",
                                "name": "Afghanistan",
                                "region": "Asia",
                                "statistics": {
                                    "total_conflicts": 45,
                                    "total_deaths": 50000,
                                    "total_events": 1200,
                                    "connections": 8
                                },
                                "top_conflicts": [
                                    {
                                        "name": "Taliban insurgency",
                                        "deaths": 28000,
                                        "events": 450
                                    }
                                ],
                                "connected_entities": [
                                    {
                                        "name": "Pakistan",
                                        "shared_conflicts": 15,
                                        "shared_deaths": 12000
                                    }
                                ],
                                "actors_involved": [
                                    {
                                        "name": "Taliban",
                                        "participation_count": 350,
                                        "deaths_caused": 25000
                                    }
                                ]
                            }
                        },
                        "actor": {
                            "summary": "Detalles de un actor",
                            "value": {
                                "type": "actor",
                                "name": "Taliban",
                                "region": None,
                                "statistics": {
                                    "total_conflicts": 35,
                                    "total_deaths": 45000,
                                    "total_encounters": 250,
                                    "connections": 12,
                                    "countries_active": 3
                                },
                                "top_conflicts": [
                                    {
                                        "name": "Afghanistan War",
                                        "deaths": 30000,
                                        "encounters": 180
                                    }
                                ],
                                "connected_entities": [
                                    {
                                        "name": "Government of Afghanistan",
                                        "encounters": 180,
                                        "deaths": 25000
                                    }
                                ],
                                "actors_involved": None
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Nodo no encontrado"
        }
    }
)
async def get_node_details(
    entity_type: GraphFilterType = Query(  
        ...,
        alias="type",  
        description="Tipo de nodo: 'country' para países, 'actor' para actores"
    ),
    value: str = Query(
        ...,
        description="Nombre específico del nodo (ej: 'Afghanistan', 'Taliban')",
        min_length=2,
        max_length=200
    )
):
    """
    Obtiene información detallada de un nodo específico (país o actor).
    
    Este endpoint es especialmente útil para:
    - Mostrar un panel lateral con detalles cuando el usuario hace click en un nodo del grafo
    - Proporcionar contexto histórico y estadísticas
    - Explorar relaciones y actores asociados
    
    Ejemplo de uso:
```
    GET /api/graph/node-details?type=country&value=Afghanistan
    GET /api/graph/node-details?type=actor&value=Taliban
```
    """
    try:
        value_decoded = urllib.parse.unquote(value)
        
        print(f"🔍 GET /api/graph/node-details")
        print(f"   Type: {entity_type}")  
        print(f"   Value (raw): {value}")
        print(f"   Value (decoded): {value_decoded}")
        
        service = ConflictMapService()
        result = await service.get_node_details(entity_type, value_decoded)  
        
        print(f"✅ Detalles obtenidos para: {result.name}")
        
        return result
        
    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ Error inesperado: {type(e).__name__}")  
        print(f"   Mensaje: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo detalles: {str(e)}"
        )

# ======================================================
# ENDPOINT 4: HEALTH CHECK 
# ======================================================

@router.get(
    "/health",
    summary="Verificar salud del servicio de grafo",
)
async def health_check():
    """
    Health-check del sistema de ConflictMap.
    Valida la conexión a Neo4j de forma correcta usando el ConflictMapClient.
    """
    try:
        from app.integration.clients.conflict_map_client import ConflictMapClient

        client = ConflictMapClient()
        driver = client.driver
        database = client.database_name

        with driver.session(database=database) as session:
            result = session.run("MATCH (n) RETURN count(n) AS node_count LIMIT 1")
            record = result.single()
            node_count = record["node_count"] if record else 0

        return {
            "status": "healthy",
            "neo4j_connected": True,
            "data_available": node_count > 0,
            "message": "Graph service is operational",
        }

    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

async def health_check():
    """
    Verifica el estado del servicio de grafo.
    
    Ejemplo de uso:
```
    GET /api/graph/health
```
    """
    try:
        service = ConflictMapService()
        
        with service.driver.session(database=service.database) as session:
            result = session.run("MATCH (n) RETURN count(n) as node_count LIMIT 1")
            record = result.single()
            node_count = record["node_count"] if record else 0
            
            countries_result = session.run("""
                MATCH (p:Country)
                RETURN p.name as name
                ORDER BY p.name
                LIMIT 10
            """)
            sample_countries = [r["name"] for r in countries_result]
            
            print(f"📊 Health check OK - Países de muestra: {sample_countries[:5]}")
            
            return {
                "status": "healthy",
                "neo4j_connected": True,
                "data_available": node_count > 0,
                "message": "Graph service is operational",
                "sample_countries": sample_countries  
            }
            
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )