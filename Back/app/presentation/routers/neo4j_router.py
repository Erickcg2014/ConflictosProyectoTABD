from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.business.services.neo4j_service import Neo4jService
from app.business.models.schemas import (
    ActorDetail, ConflictNode, ActorNode
)

router = APIRouter()


def get_neo4j_service():
    """Obtener instancia de Neo4j service"""
    return Neo4jService()


@router.get("/actors/{actor_name}", response_model=ActorDetail)
async def get_actor_by_name(actor_name: str):
    """
    Obtener información detallada de un actor específico y su red de relaciones.
    
    **Parámetros:**
    - **actor_name**: Nombre exacto del actor (grupo armado, fuerza gubernamental, etc.)
    
    **Retorna:** Información completa incluyendo:
    - Metadatos del actor
    - Conflictos en los que ha participado
    - Relaciones con otros actores
    - Estadísticas de participación
    
    **Uso:** Análisis detallado de un actor específico y su historial de conflictos.
    """
    with get_neo4j_service() as service:
        actor = service.get_actor_by_name(actor_name)
        if not actor:
            raise HTTPException(status_code=404, detail="Actor not found")
        return actor


@router.get("/conflicts/{conflict_name}", response_model=ConflictNode)
async def get_conflict_by_name(conflict_name: str):
    """
    Obtener información estructural de un conflicto desde la perspectiva del grafo.
    
    **Parámetros:**
    - **conflict_name**: Nombre del conflicto armado
    
    **Retorna:** Representación del conflicto como nodo en el grafo con:
    - Propiedades del conflicto
    - Conexiones a actores involucrados
    - Metadatos de temporalidad y ubicación
    
    **Uso:** Análisis de la estructura y composición de un conflicto específico.
    """
    with get_neo4j_service() as service:
        conflict = service.get_conflict_by_name(conflict_name)
        if not conflict:
            raise HTTPException(status_code=404, detail="Conflict not found")
        return conflict


# Endpoint para obtener event_ids
@router.get("/conflicts/{conflict_name}/event-ids", response_model=list[str])
async def get_conflict_event_ids(conflict_name: str):
    """
    Obtener identificadores únicos de eventos asociados a un conflicto.
    
    **Parámetros:**
    - **conflict_name**: Nombre del conflicto armado
    
    **Retorna:** Lista de event_ids que pueden ser usados para consultas en BigQuery y MongoDB.
    
    **Uso:** Vincular datos del grafo con información tabular y geográfica de otras fuentes.
    """
    with get_neo4j_service() as service:
        event_ids = service.get_conflict_event_ids(conflict_name)
        if not event_ids:
            raise HTTPException(status_code=404, detail="Conflict not found or has no events")
        return event_ids


@router.get("/conflicts/{conflict_name}/actors")
async def get_conflict_actors(conflict_name: str):
    """
    Obtener el ecosistema completo de actores involucrados en un conflicto.
    
    **Parámetros:**
    - **conflict_name**: Nombre del conflicto armado
    
    **Retorna:** 
    - Información del conflicto
    - Lista completa de actores participantes
    - Conteo total de actores involucrados
    
    **Uso:** Mapear todos los participantes en un conflicto y analizar su composición.
    """
    with get_neo4j_service() as service:
        conflict, actors = service.get_conflict_actors(conflict_name)
        if not conflict:
            raise HTTPException(status_code=404, detail="Conflict not found")
        
        return {
            "conflict": conflict,
            "actors": actors,
            "total_actors": len(actors)
        }


@router.get("/actors/{actor_name}/network")
async def get_actor_network(
    actor_name: str,
    depth: int = Query(default=2, ge=1, le=5, description="Profundidad de búsqueda (1-5)")
):
    """
    Explorar la red de relaciones de un actor hasta una profundidad específica.
    
    **Parámetros:**
    - **actor_name**: Actor central de la red
    - **depth**: Profundidad de exploración (1-5 niveles de conexión)
    
    **Retorna:** Red completa incluyendo:
    - Actor central
    - Actores conectados directa e indirectamente
    - Relaciones entre todos los actores
    - Métricas de la red (tamaño, densidad)
    
    **Uso:** Análisis de redes para entender alianzas, oposiciones y estructura organizacional.
    """
    with get_neo4j_service() as service:
        network = service.get_actor_network(actor_name, depth=depth)
        if not network or network["network_size"] == 0:
            raise HTTPException(status_code=404, detail="Actor not found or has no connections")
        return network


# Endpoint para relaciones entre actores
@router.get("/actors/{actor1}/relationships/{actor2}")
async def get_actor_relationships(actor1: str, actor2: str):
    """
    Analizar relaciones directas de enfrentamiento entre dos actores específicos.
    
    **Parámetros:**
    - **actor1**: Primer actor
    - **actor2**: Segundo actor
    
    **Retorna:** Lista de conflictos donde ambos actores se han enfrentado directamente.
    
    **Uso:** Estudiar historial de enfrentamientos específicos entre dos grupos armados.
    """
    with get_neo4j_service() as service:
        relationships = service.get_actor_relationships(actor1, actor2)
        if not relationships:
            return {
                "actor1": actor1,
                "actor2": actor2,
                "relationships": [],
                "message": "No direct engagements found between these actors"
            }
        
        return {
            "actor1": actor1,
            "actor2": actor2,
            "relationships": relationships,
            "total_engagements": len(relationships)
        }


@router.get("/conflicts/top", response_model=list[ConflictNode])
async def get_top_conflicts(
    limit: int = Query(default=10, ge=1, le=50, description="Número de conflictos")
):
    """
    Obtener los conflictos más significativos por impacto y letalidad.
    
    **Parámetros:**
    - **limit**: Número de conflictos a retornar (1-50)
    
    **Retorna:** Lista ordenada de conflictos más importantes basados en:
    - Número total de fatalidades
    - Cantidad de actores involucrados
    - Duración temporal
    - Complejidad de la red
    
    **Uso:** Identificar conflictos críticos para análisis prioritario.
    """
    try:
        with get_neo4j_service() as service:
            return service.get_top_conflicts(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint para top actores
@router.get("/actors/top/deadliest")
async def get_top_actors_by_deaths(
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Obtener ranking de actores más letales por fatalidades acumuladas.
    
    **Parámetros:**
    - **limit**: Número de actores en el ranking (1-50)
    
    **Retorna:** Lista ordenada de actores con:
    - Total de fatalidades atribuidas
    - Número de conflictos participados
    - Período de actividad
    - Tipología del actor
    
    **Uso:** Análisis comparativo de letalidad entre diferentes grupos armados.
    """
    try:
        with get_neo4j_service() as service:
            return service.get_top_actors_by_deaths(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actors", response_model=list[str])
async def get_all_actors(
    limit: int = Query(default=100, ge=1, le=500)
):
    """
    Obtener catálogo completo de actores registrados en la base de datos.
    
    **Parámetros:**
    - **limit**: Número máximo de actores a listar (1-500)
    
    **Retorna:** Lista alfabética de nombres de actores.
    
    **Uso:** Navegación y descubrimiento de actores para análisis posteriores.
    """
    try:
        with get_neo4j_service() as service:
            return service.get_all_actors(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=list[ConflictNode])
async def search_conflicts(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    Búsqueda flexible de conflictos en el grafo por múltiples criterios.
    
    **Parámetros:**
    - **q**: Término de búsqueda (mínimo 2 caracteres)
    - **limit**: Número máximo de resultados (1-100)
    
    **Campos buscados:**
    - Nombre del conflicto
    - Países involucrados
    - Regiones geográficas
    - Nombres de actores participantes
    
    **Uso:** Descubrimiento de conflictos relevantes basados en criterios textuales.
    """
    try:
        with get_neo4j_service() as service:
            return service.search_conflicts(search_term=q, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint para estadísticas del grafo
@router.get("/stats")
async def get_graph_stats():
    """
    Obtener métricas estructurales y estadísticas generales del grafo completo.
    
    **Retorna:** Información cuantitativa incluyendo:
    - Total de nodos (actores y conflictos)
    - Total de relaciones (participaciones y enfrentamientos)
    - Distribución por tipos de actores
    - Densidad y conectividad de la red
    
    **Uso:** Monitoreo de la base de datos y análisis de la estructura general de conflictos.
    """
    try:
        with get_neo4j_service() as service:
            return service.get_graph_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))