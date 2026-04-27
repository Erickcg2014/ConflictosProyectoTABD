
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from app.business.services.statistics_service import StatisticsService
from app.business.models.schemas import (
    RegionsResponse,
    ViolenceTypesResponse,
    DateRangeResponse,
    FiltersMetadata,
    RegionOption,
    ViolenceTypeOption,
    DateRange
)

router = APIRouter()

def get_statistics_service() -> StatisticsService:
    """Crear nueva instancia del servicio por request"""
    return StatisticsService()


@router.get("/dashboard")
async def get_dashboard_summary(
    start_date: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    region: str = Query("all", description="Región a filtrar"),
    violence_types: Optional[List[str]] = Query(None, description="Tipos de violencia"),
    service: StatisticsService = Depends(get_statistics_service)  
):
    """Obtiene el resumen completo del dashboard"""
    try:
        result = service.get_dashboard_summary(
            start_date=start_date,
            end_date=end_date,
            region=region,
            violence_types=violence_types or ["all"]
        )
        return result
    except Exception as e:
        import traceback
        print(f"❌ Error en /dashboard:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener dashboard: {str(e)}")


@router.get("/filters/regions", response_model=RegionsResponse)
async def get_available_regions(
    service: StatisticsService = Depends(get_statistics_service)  
):
    """Obtiene el catálogo completo de regiones"""
    try:
        regions = service.get_available_regions()
        return RegionsResponse(
            regions=[RegionOption(**r) for r in regions]
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener regiones: {str(e)}")


@router.get("/filters/violence-types", response_model=ViolenceTypesResponse)
async def get_available_violence_types(
    service: StatisticsService = Depends(get_statistics_service)  
):
    """Obtiene la taxonomía completa de tipos de violencia"""
    try:
        violence_types = service.get_available_violence_types()
        return ViolenceTypesResponse(
            violence_types=[ViolenceTypeOption(**vt) for vt in violence_types]
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener tipos de violencia: {str(e)}")


@router.get("/filters/date-range", response_model=DateRangeResponse)
async def get_date_range(
    service: StatisticsService = Depends(get_statistics_service)  
):
    """Obtiene los límites temporales extremos"""
    try:
        date_range = service.get_date_range()
        return DateRangeResponse(
            date_range=DateRange(**date_range)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener rango de fechas: {str(e)}")


@router.get("/filters/metadata", response_model=FiltersMetadata)
async def get_filters_metadata(
    service: StatisticsService = Depends(get_statistics_service)  
):
    """Obtiene toda la metadata de filtros"""
    try:
        metadata = service.get_filters_metadata()
        return FiltersMetadata(
            regions=[RegionOption(**r) for r in metadata["regions"]],
            violence_types=[ViolenceTypeOption(**vt) for vt in metadata["violence_types"]],
            date_range=DateRange(**metadata["date_range"])
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener metadata de filtros: {str(e)}")


@router.get("/timeline")
async def get_timeline_data(
    start_date: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    region: str = Query("all", description="Región a filtrar"),
    violence_types: Optional[List[str]] = Query(None, description="Tipos de violencia"),
    granularity: str = Query("month", description="Granularidad: 'month' o 'year'"),
    service: StatisticsService = Depends(get_statistics_service)  
):
    """Obtiene datos de evolución temporal"""
    try:
        print(f"🔍 Timeline request:")
        print(f"   region: {region}")
        print(f"   granularity: {granularity}")
        print(f"   start_date: {start_date}")
        print(f"   end_date: {end_date}")
        
        result = service.get_timeline_data(
            start_date=start_date,
            end_date=end_date,
            region=region,
            violence_types=violence_types or ["all"],
            granularity=granularity
        )
        return result
    except Exception as e:
        import traceback
        print(f"❌ Error en /timeline:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener timeline: {str(e)}")


@router.get("/top-countries")
async def get_top_countries(
    start_date: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    region: str = Query("all", description="Región a filtrar"),
    violence_types: Optional[List[str]] = Query(None, description="Tipos de violencia"),
    metric: str = Query("events", description="Métrica: 'events' o 'deaths'"),
    limit: int = Query(10, ge=1, le=50, description="Cantidad de países a retornar"),
    service: StatisticsService = Depends(get_statistics_service)  
):
    """Genera ranking de países"""
    try:
        result = service.get_top_countries(
            start_date=start_date,
            end_date=end_date,
            region=region,
            violence_types=violence_types or ["all"],
            metric=metric,
            limit=limit
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener top countries: {str(e)}")


@router.get("/violence-types")
async def get_violence_types_distribution(
    start_date: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    region: str = Query("all", description="Región a filtrar"),
    metric: str = Query("events", description="Métrica: 'events' o 'deaths'"),
    service: StatisticsService = Depends(get_statistics_service)  
):
    """Obtiene distribución porcentual de conflictos"""
    try:
        result = service.get_violence_types_distribution(
            start_date=start_date,
            end_date=end_date,
            region=region,
            metric=metric
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener distribución de tipos: {str(e)}")


@router.get("/conflicts")
async def get_conflicts_table(
    start_date: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    region: str = Query("all", description="Región a filtrar"),
    violence_types: Optional[List[str]] = Query(None, description="Tipos de violencia"),
    search: Optional[str] = Query(None, description="Búsqueda por nombre/país/actores"),
    sort_by: str = Query("deaths", description="Ordenar por: 'name', 'events', 'deaths', 'period'"),
    sort_order: str = Query("desc", description="Orden: 'asc' o 'desc'"),
    limit: int = Query(20, ge=1, le=100, description="Cantidad de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    service: StatisticsService = Depends(get_statistics_service)  
):
    """Obtiene datos tabulares de conflictos"""
    try:
        clean_violence_types = None
        if violence_types and "all" not in violence_types:
            clean_violence_types = violence_types
        
        result = service.get_conflicts_table(
            start_date=start_date,
            end_date=end_date,
            region=region,
            violence_types=clean_violence_types,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener conflictos: {str(e)}")