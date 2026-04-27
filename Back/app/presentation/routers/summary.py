from fastapi import APIRouter, HTTPException
from app.business.services.bigquery_service import BigQueryService
from app.business.services.mongodb_service import MongoDBService
from app.business.services.neo4j_service import Neo4jService
from app.business.models.schemas import SummaryResponse, ConflictDetail, GeoLocation

router = APIRouter()


def get_services():
    """Obtener instancias de servicios (lazy initialization)"""
    return {
        'bq': BigQueryService(),
        'mongo': MongoDBService(),
        'neo4j': Neo4jService()
    }


@router.get("/{event_id}", response_model=SummaryResponse)
async def get_conflict_summary(event_id: str):
    """
    Obtener resumen completo de un conflicto combinando las tres bases de datos
    
    Args:
        event_id: ID único del evento
        
    Returns:
        Detalle completo del conflicto con información de BigQuery, MongoDB y Neo4j
    """
    # Obtener servicios
    services = get_services()
    
    # Obtener datos de BigQuery
    conflict = services['bq'].get_conflict_by_id(event_id)
    if not conflict:
        raise HTTPException(status_code=404, detail=f"Conflict with event_id {event_id} not found")
    
    # Obtener ubicación de MongoDB
    location = services['mongo'].get_location_by_event_id(event_id)
    geo_location = None
    if location:
        geo_location = location.location
    
    # Obtener actores relacionados de Neo4j 
    related_actors = []
    related_conflicts = []
    
    if conflict.conflict_name:
        conflict_node = services['neo4j'].get_conflict_by_name(conflict.conflict_name)
        if conflict_node and conflict_node.event_ids:
            related_conflicts = [cid for cid in conflict_node.event_ids if cid != event_id]
        
        # Obtener actores involucrados
        _, actors = services['neo4j'].get_conflict_actors(conflict.conflict_name)
        related_actors = [actor.name for actor in actors]
    
    # Construir respuesta combinada
    detail = ConflictDetail(
        # Datos de BigQuery
        event_id=conflict.event_id,
        conflict_name=conflict.conflict_name,
        type_of_violence=conflict.type_of_violence,
        side_a=conflict.side_a,
        side_b=conflict.side_b,
        country=conflict.country,
        region=conflict.region,
        date_start=conflict.date_start,
        date_end=conflict.date_end,
        deaths_a=conflict.deaths_a,
        deaths_b=conflict.deaths_b,
        deaths_total=conflict.deaths_total,
        length_of_conflict=conflict.length_of_conflict,
        # Datos de MongoDB
        location=geo_location,
        # Datos de Neo4j
        related_actors=related_actors if related_actors else None,
        related_conflicts=related_conflicts if related_conflicts else None
    )
    
    return SummaryResponse(
        detail=detail,
        sources=["bigquery", "mongodb", "neo4j"]
    )
