"""
Schemas para el sistema de visualización de grafo de conflictos.
Define los modelos de datos para:
- Filtros de países y actores
- Nodos y aristas del grafo
- Detalles de nodos individuales
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ======================================================
# ENUMS
# ======================================================

class GraphFilterType(str, Enum):
    """Tipos de filtro disponibles para el grafo"""
    COUNTRY = "country"
    ACTOR = "actor"


# ======================================================
# MODELOS DE FILTROS
# ======================================================

class FilterItem(BaseModel):
    """Item individual en la lista de filtros"""
    value: str = Field(..., description="Valor único del filtro (nombre)")
    label: str = Field(..., description="Etiqueta para mostrar en UI")
    conflict_count: int = Field(..., description="Número de conflictos asociados")
    total_deaths: int = Field(..., description="Total de muertes acumuladas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "value": "Afghanistan",
                "label": "Afghanistan",
                "conflict_count": 45,
                "total_deaths": 50000
            }
        }


class FiltersResponse(BaseModel):
    """Respuesta con lista de filtros disponibles"""
    type: GraphFilterType = Field(..., description="Tipo de filtro")
    count: int = Field(..., description="Total de items disponibles")
    items: List[FilterItem] = Field(..., description="Lista de items del filtro")
    
    class Config:
        json_schema_extra = {
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


# ======================================================
# MODELOS DEL GRAFO
# ======================================================

class NodeMetrics(BaseModel):
    """Métricas de un nodo en el grafo"""
    total_conflicts: int = Field(..., description="Total de conflictos")
    total_deaths: int = Field(..., description="Total de muertes")
    connections: int = Field(..., description="Número de conexiones")
    
    # Campos opcionales según tipo de nodo
    total_events: Optional[int] = Field(None, description="Total de eventos (para países)")
    encounter_count: Optional[int] = Field(None, description="Total de encuentros (para actores)")
    countries_active: Optional[int] = Field(None, description="Países donde está activo (para actores)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_conflicts": 45,
                "total_deaths": 50000,
                "connections": 8,
                "total_events": 1200
            }
        }


class GraphNode(BaseModel):
    """Nodo individual en el grafo"""
    id: str = Field(..., description="ID único del nodo")
    label: str = Field(..., description="Etiqueta para mostrar")
    type: str = Field(..., description="Tipo de nodo: country o actor")
    region: Optional[str] = Field(None, description="Región geográfica (para países)")
    metrics: NodeMetrics = Field(..., description="Métricas del nodo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "Afghanistan",
                "label": "Afghanistan",
                "type": "country",
                "region": "Asia",
                "metrics": {
                    "total_conflicts": 45,
                    "total_deaths": 50000,
                    "connections": 8
                }
            }
        }


class EdgeMetrics(BaseModel):
    """Métricas de una arista en el grafo"""
    event_count: Optional[int] = Field(None, description="Número de eventos (para países)")
    conflict_names: Optional[List[str]] = Field(None, description="Nombres de conflictos (para países)")
    actors_involved: Optional[List[str]] = Field(None, description="Actores involucrados (para países)")
    encounter_count: Optional[int] = Field(None, description="Número de encuentros (para actores)")
    via_conflict: Optional[str] = Field(None, description="Conflicto principal (para actores)")
    total_length: Optional[int] = Field(None, description="Duración total en días (para actores)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_count": 150,
                "conflict_names": ["Taliban insurgency", "Border conflicts"],
                "actors_involved": ["Taliban", "Government of Afghanistan"]
            }
        }


class GraphEdge(BaseModel):
    """Arista individual en el grafo"""
    id: str = Field(..., description="ID único de la arista")
    source: str = Field(..., description="ID del nodo origen")
    target: str = Field(..., description="ID del nodo destino")
    weight: int = Field(..., description="Peso de la arista (total_deaths)")
    metrics: EdgeMetrics = Field(..., description="Métricas de la arista")
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }


class GraphSummary(BaseModel):
    """Resumen del grafo completo"""
    total_nodes: int = Field(..., description="Total de nodos en el grafo")
    total_edges: int = Field(..., description="Total de aristas en el grafo")
    total_deaths: int = Field(..., description="Total de muertes acumuladas")
    total_conflicts: int = Field(..., description="Total de conflictos únicos")
    depth: int = Field(..., description="Profundidad del grafo (1 o 2)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_nodes": 9,
                "total_edges": 12,
                "total_deaths": 65000,
                "total_conflicts": 28,
                "depth": 1
            }
        }


class GraphResponse(BaseModel):
    """Respuesta completa con la estructura del grafo"""
    center_node: GraphNode = Field(..., description="Nodo central del grafo")
    nodes: List[GraphNode] = Field(..., description="Lista de nodos conectados")
    edges: List[GraphEdge] = Field(..., description="Lista de aristas")
    summary: GraphSummary = Field(..., description="Resumen del grafo")
    
    class Config:
        json_schema_extra = {
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
                            "conflict_names": ["Taliban insurgency"]
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


# ======================================================
# MODELOS DE DETALLES DE NODO
# ======================================================

class ConflictSummary(BaseModel):
    """Resumen de un conflicto individual"""
    name: str = Field(..., description="Nombre del conflicto")
    deaths: int = Field(..., description="Muertes totales")
    events: Optional[int] = Field(None, description="Número de eventos")
    encounters: Optional[int] = Field(None, description="Número de encuentros")
    duration_days: Optional[int] = Field(None, description="Duración en días")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Taliban insurgency",
                "deaths": 28000,
                "events": 450,
                "duration_days": 5000
            }
        }


class ConnectedEntity(BaseModel):
    """Entidad conectada (país o actor)"""
    name: str = Field(..., description="Nombre de la entidad")
    shared_conflicts: Optional[int] = Field(None, description="Conflictos compartidos (para países)")
    shared_deaths: Optional[int] = Field(None, description="Muertes compartidas (para países)")
    encounters: Optional[int] = Field(None, description="Encuentros (para actores)")
    deaths: Optional[int] = Field(None, description="Muertes (para actores)")
    conflict_count: Optional[int] = Field(None, description="Número de conflictos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Pakistan",
                "shared_conflicts": 15,
                "shared_deaths": 12000
            }
        }


class ActorParticipation(BaseModel):
    """Participación de un actor en conflictos"""
    name: str = Field(..., description="Nombre del actor")
    participation_count: int = Field(..., description="Número de participaciones")
    deaths_caused: int = Field(..., description="Muertes causadas")
    role: Optional[str] = Field(None, description="Rol principal (A o B)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Taliban",
                "participation_count": 350,
                "deaths_caused": 25000,
                "role": "A"
            }
        }


class NodeStatistics(BaseModel):
    """Estadísticas detalladas de un nodo"""
    total_conflicts: int = Field(..., description="Total de conflictos")
    total_deaths: int = Field(..., description="Total de muertes")
    total_events: Optional[int] = Field(None, description="Total de eventos")
    total_encounters: Optional[int] = Field(None, description="Total de encuentros")
    connections: int = Field(..., description="Número de conexiones")
    countries_active: Optional[int] = Field(None, description="Países activos (para actores)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_conflicts": 45,
                "total_deaths": 50000,
                "total_events": 1200,
                "connections": 8
            }
        }


class NodeDetails(BaseModel):
    """Detalles completos de un nodo específico"""
    type: str = Field(..., description="Tipo de nodo: country o actor")
    name: str = Field(..., description="Nombre de la entidad")
    region: Optional[str] = Field(None, description="Región geográfica")
    statistics: NodeStatistics = Field(..., description="Estadísticas generales")
    top_conflicts: List[ConflictSummary] = Field(..., description="Top conflictos")
    connected_entities: List[ConnectedEntity] = Field(..., description="Entidades conectadas")
    actors_involved: Optional[List[ActorParticipation]] = Field(None, description="Actores involucrados (para países)")
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }