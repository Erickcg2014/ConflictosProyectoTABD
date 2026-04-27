from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import date


# ======================================================
# Modelos compartidos
# ======================================================

class HealthCheck(BaseModel):
    """Modelo para health check de las bases de datos"""
    status: str
    bigquery: bool
    mongodb: bool
    neo4j: bool
    message: str


# ======================================================
# Modelos BigQuery 
# ======================================================

class ConflictSummary(BaseModel):
    """Resumen de un conflicto desde BigQuery"""
    event_id: str
    conflict_name: str
    type_of_violence: Optional[str]
    side_a: Optional[str]
    side_b: Optional[str]
    country: Optional[str]
    region: Optional[str]
    date_start: Optional[date]
    date_end: Optional[date]
    deaths_a: Optional[int]
    deaths_b: Optional[int]
    deaths_total: Optional[int]
    length_of_conflict: Optional[int]


class CountryStats(BaseModel):
    """Estadísticas por país"""
    country: str
    total_events: int
    total_deaths: int
    conflicts: List[str]


class ConflictListResponse(BaseModel):
    """Respuesta de lista de conflictos"""
    total: int
    conflicts: List[ConflictSummary]


class StatsResponse(BaseModel):
    """Respuesta de estadísticas"""
    top_countries: List[CountryStats]
    total_events: int
    total_deaths: int


# ======================================================
# MongoDB Modelos
# ======================================================

class GeoLocation(BaseModel):
    """Ubicación geográfica en formato GeoJSON"""
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class WarLocation(BaseModel):
    """Ubicación de un conflicto desde MongoDB"""
    event_id: str
    conflict_name: Optional[str]
    country: Optional[str]
    region: Optional[str]
    location: GeoLocation


class GeoSearchRequest(BaseModel):
    """Request para búsqueda geográfica"""
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)
    max_distance_km: Optional[float] = Field(default=100, gt=0)
    limit: Optional[int] = Field(default=10, ge=1, le=100)


class GeoSearchResponse(BaseModel):
    """Respuesta de búsqueda geográfica"""
    results: List[WarLocation]
    count: int
    search_center: Dict[str, float]


class CountrySearchRequest(BaseModel):
    """Request para búsqueda por país"""
    country: str
    limit: Optional[int] = Field(default=100, ge=1, le=500)


# ======================================================
# Neo4j Modelos
# ======================================================

class ActorNode(BaseModel):
    """Actor en el grafo"""
    name: str
    role: Optional[str]


class ConflictNode(BaseModel):
    """Conflicto en el grafo"""
    name: str
    type_of_violence: Optional[str]
    country: Optional[str]
    region: Optional[str]
    event_count: Optional[int]
    total_deaths: Optional[int]
    event_ids: Optional[List[str]]


class Relation(BaseModel):
    """Relación entre nodos"""
    type: str
    properties: Dict[str, Any]


class ActorRelationship(BaseModel):
    """Relación de participación"""
    conflict: str
    role: Optional[str]
    cumulative_deaths: Optional[int]
    event_count: Optional[int]


class ActorDetail(BaseModel):
    """Detalle de un actor con sus relaciones"""
    name: str
    conflicts: List[ActorRelationship]
    engaged_actors: List[str]
    total_conflicts: int


class ConflictRelationsResponse(BaseModel):
    """Respuesta de relaciones de un conflicto"""
    conflict: ConflictNode
    actors: List[ActorNode]
    relationships: List[Relation]


# ======================================================
# Summary Modelos
# ======================================================

class ConflictDetail(BaseModel):
    """Detalle completo de un conflicto (combinado de las 3 BD)"""
    # Desde BigQuery
    event_id: str
    conflict_name: str
    type_of_violence: Optional[str]
    side_a: Optional[str]
    side_b: Optional[str]
    country: Optional[str]
    region: Optional[str]
    date_start: Optional[date]
    date_end: Optional[date]
    deaths_a: Optional[int]
    deaths_b: Optional[int]
    deaths_total: Optional[int]
    length_of_conflict: Optional[int]
    
    # Desde MongoDB
    location: Optional[GeoLocation]
    
    # Desde Neo4j
    related_actors: Optional[List[str]]
    related_conflicts: Optional[List[str]]


class SummaryResponse(BaseModel):
    """Respuesta de resumen"""
    detail: ConflictDetail
    sources: List[str] = ["bigquery", "mongodb", "neo4j"]

class DashboardSummary(BaseModel):
    """Resumen del dashboard de estadísticas"""
    total_events: int
    total_deaths: int
    countries_affected: int
    unique_conflicts: int
    trends: Dict[str, float]

# ======================================================
# Estadísticas Modelos
# ======================================================

from pydantic import BaseModel
from typing import List

# ==========================================
# SCHEMAS PARA FILTROS
# ==========================================

class RegionOption(BaseModel):
    """Opción de región disponible"""
    value: str
    label: str
    count: int  

class RegionsResponse(BaseModel):
    """Respuesta con regiones disponibles"""
    regions: List[RegionOption]

class ViolenceTypeOption(BaseModel):
    """Opción de tipo de violencia disponible"""
    value: str
    label: str
    count: int  

class ViolenceTypesResponse(BaseModel):
    """Respuesta con tipos de violencia disponibles"""
    violence_types: List[ViolenceTypeOption]

class DateRange(BaseModel):
    """Rango de fechas disponibles"""
    min_date: str  
    max_date: str  
    total_years: int

class DateRangeResponse(BaseModel):
    """Respuesta con rango de fechas"""
    date_range: DateRange

class FiltersMetadata(BaseModel):
    """Metadata completa de filtros disponibles"""
    regions: List[RegionOption]
    violence_types: List[ViolenceTypeOption]
    date_range: DateRange

# ========================
# ESQUEMAS  TIMELINE Y TOPCOUNTRIES
# =========================
class TimelineResponse(BaseModel):
    """Respuesta de datos de timeline"""
    labels: List[str]
    events: List[int]
    deaths: List[int]
    granularity: str

class TopCountriesResponse(BaseModel):
    """Respuesta de top países"""
    countries: List[str]
    values: List[int]
    metric: str
    limit: int

# ========================
# ESQUEMAS VIOLENCETYPES
# =========================

class ViolenceTypesDistributionResponse(BaseModel):
    """Respuesta de distribución por tipo de violencia"""
    types: List[str]
    events: Optional[List[int]]
    deaths: Optional[List[int]]
    percentages: List[float]
    metric: str


class ConflictTableEntry(BaseModel):
    """Entrada de la tabla de conflictos"""
    name: str
    countries: str
    actors: str
    events: int
    deaths: int
    period: str
    region: str

class ConflictsTableResponse(BaseModel):
    """Respuesta de tabla de conflictos con paginación"""
    total: int
    conflicts: List[ConflictTableEntry]
    limit: int
    offset: int

class CountryPoint(BaseModel):
    country: str
    lat: float
    lon: float


class ConflictConnection(BaseModel):
    country_a: str
    country_b: str
    lat_a: Optional[float] = None
    lon_a: Optional[float] = None
    lat_b: Optional[float] = None
    lon_b: Optional[float] = None
    events: int
    deaths: int
    conflict_names: List[str] = []
    actors: Optional[List[str]] = []


class ConflictNetworkResponse(BaseModel):
    connections: List[ConflictConnection]
    total_connections: int
