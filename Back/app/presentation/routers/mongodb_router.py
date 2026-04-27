from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.business.services.mongodb_service import MongoDBService
from app.business.models.schemas import (
    WarLocation, GeoSearchRequest, GeoSearchResponse
)

router = APIRouter()


def get_mongo_service():
    """Obtener instancia de MongoDB service"""
    return MongoDBService()


# ======================================================
# GEO NEARBY
# ======================================================

@router.get("/geo/nearby", response_model=GeoSearchResponse)
async def search_nearby_events(
    longitude: float = Query(..., ge=-180, le=180),
    latitude: float = Query(..., ge=-90, le=90),
    max_distance_km: float = Query(default=100, gt=0, le=5000),
    limit: int = Query(default=10, ge=1, le=100)
):
    """
    Buscar eventos de conflictos cercanos a una ubicación geográfica específica.
    """
    try:
        service = get_mongo_service()

        results = service.search_nearby_events(
            longitude=longitude,
            latitude=latitude,
            max_distance_km=max_distance_km,
            limit=limit
        )

        return GeoSearchResponse(
            results=results,
            count=len(results),
            search_center={"longitude": longitude, "latitude": latitude}
        )
    except Exception as e:
        print("❌ ERROR en /geo/nearby:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# GEO SEARCH (POST)
# ======================================================

@router.post("/geo/search", response_model=GeoSearchResponse)
async def geo_search(body: GeoSearchRequest):
    """
    Buscar eventos cercanos usando POST.
    """
    try:
        service = get_mongo_service()

        results = service.search_nearby_events(
            longitude=body.longitude,
            latitude=body.latitude,
            max_distance_km=body.max_distance_km,
            limit=body.limit
        )

        return GeoSearchResponse(
            results=results,
            count=len(results),
            search_center={"longitude": body.longitude, "latitude": body.latitude}
        )
    except Exception as e:
        print("❌ ERROR en /geo/search:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# GEO BOUNDS
# ======================================================

@router.get("/geo/bounds", response_model=list[WarLocation])
async def get_locations_in_bounds(
    min_lon: float = Query(..., ge=-180, le=180),
    min_lat: float = Query(..., ge=-90, le=90),
    max_lon: float = Query(..., ge=-180, le=180),
    max_lat: float = Query(..., ge=-90, le=90),
    limit: int = Query(default=500, ge=1, le=1000)
):
    """
    Obtener eventos dentro de un área rectangular.
    """
    try:
        service = get_mongo_service()

        return service.get_locations_in_bounds(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            limit=limit
        )
    except Exception as e:
        print("❌ ERROR en /geo/bounds:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# GEO CLUSTERS
# ======================================================

@router.get("/geo/clusters")
async def get_map_clusters(
    zoom: int = Query(default=5, ge=1, le=18),
    min_lon: Optional[float] = Query(None, ge=-180, le=180),
    min_lat: Optional[float] = Query(None, ge=-90, le=90),
    max_lon: Optional[float] = Query(None, ge=-180, le=180),
    max_lat: Optional[float] = Query(None, ge=-90, le=90)
):
    """
    Obtener datos agregados para clustering de eventos en el mapa.
    """
    try:
        coords = [min_lon, min_lat, max_lon, max_lat]
        bounds = None

        if all(v is not None for v in coords):
            bounds = {
                "min_lon": min_lon,
                "min_lat": min_lat,
                "max_lon": max_lon,
                "max_lat": max_lat,
            }

        print("📌 [Clusters] Zoom:", zoom)
        print("📌 [Clusters] Bounds:", bounds)

        service = get_mongo_service()
        result = service.get_cluster_data(zoom_level=zoom, bounds=bounds)

        print("📌 [Clusters] Cantidad clusters:", len(result))
        return result

    except Exception as e:
        print("❌ ERROR en /geo/clusters:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# GET BY EVENT ID
# ======================================================

@router.get("/events/{event_id}", response_model=WarLocation)
async def get_location_by_event_id(event_id: str):
    """
    Obtener ubicación y detalles geográficos de un evento por ID.
    """
    try:
        service = get_mongo_service()
        location = service.get_location_by_event_id(event_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        return location
    except Exception as e:
        print("❌ ERROR en /events/{event_id}:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# GET MULTIPLE BY IDS
# ======================================================

@router.post("/events/batch", response_model=list[WarLocation])
async def get_locations_batch(event_ids: list[str]):
    """
    Obtener ubicaciones de múltiples eventos en una sola consulta.
    """
    try:
        service = get_mongo_service()
        return service.get_locations_by_event_ids(event_ids)
    except Exception as e:
        print("❌ ERROR en /events/batch:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# SEARCH BY COUNTRY
# ======================================================

@router.get("/country/{country}", response_model=list[WarLocation])
async def search_by_country(
    country: str,
    limit: int = Query(default=100, ge=1, le=500)
):
    """
    Buscar eventos por país.
    """
    try:
        service = get_mongo_service()
        return service.search_by_country(country=country, limit=limit)
    except Exception as e:
        print("❌ ERROR en /country:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# SEARCH BY REGION
# ======================================================

@router.get("/region/{region}", response_model=list[WarLocation])
async def search_by_region(
    region: str,
    limit: int = Query(default=100, ge=1, le=500)
):
    """
    Buscar eventos por región.
    """
    try:
        service = get_mongo_service()
        return service.search_by_region(region=region, limit=limit)
    except Exception as e:
        print("❌ ERROR en /region:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# ALL COUNTRIES
# ======================================================

@router.get("/countries", response_model=list[str])
async def get_all_countries():
    """
    Obtener lista de todos los países únicos.
    """
    try:
        service = get_mongo_service()
        return service.get_all_countries()
    except Exception as e:
        print("❌ ERROR en /countries:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# ALL REGIONS
# ======================================================

@router.get("/regions", response_model=list[str])
async def get_all_regions():
    """
    Obtener lista de todas las regiones únicas.
    """
    try:
        service = get_mongo_service()
        return service.get_all_regions()
    except Exception as e:
        print("❌ ERROR en /regions:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# COUNT
# ======================================================

@router.get("/stats/count")
async def get_location_count():
    """
    Obtener estadísticas del total de ubicaciones/eventos.
    """
    try:
        service = get_mongo_service()
        count = service.get_location_count()
        return {"total_locations": count}
    except Exception as e:
        print("❌ ERROR en /stats/count:", e)
        raise HTTPException(status_code=500, detail=str(e))
