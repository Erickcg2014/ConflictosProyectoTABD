from fastapi import APIRouter, Path, Query, HTTPException
from typing import Optional
from app.business.services.bigquery_service import BigQueryService
from app.business.models.schemas import (
    ConflictListResponse, ConflictSummary, 
    StatsResponse, CountryStats
)

router = APIRouter()


def get_bq_service():
    """Obtener instancia de BigQuery service (lazy initialization)"""
    return BigQueryService()


@router.get("/conflicts", response_model=ConflictListResponse)
async def get_conflicts(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    country: Optional[str] = None,
    region: Optional[str] = None
):
    """
    Obtener lista paginada de conflictos armados con filtros opcionales.
    
    **Parámetros:**
    - **limit**: Número máximo de resultados por página (1-1000)
    - **offset**: Número de registros a saltar (para paginación)
    - **country**: Filtrar por nombre de país específico
    - **region**: Filtrar por región geográfica
    
    **Retorna:** Lista de conflictos con metadatos de paginación y total de registros.
    
    **Uso:** Listado principal de conflictos con navegación por páginas.
    """
    try:
        service = get_bq_service()
        conflicts, total = service.get_all_conflicts(
            limit=limit,
            offset=offset,
            country=country,
            region=region
        )
        
        return ConflictListResponse(
            total=total,
            conflicts=conflicts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts/{event_id}", response_model=ConflictSummary)
async def get_conflict_by_id(event_id: str):
    """
    Obtener detalles completos de un conflicto específico por su identificador único.
    
    **Parámetros:**
    - **event_id**: Identificador único del evento en la base de datos UCDP
    
    **Retorna:** Información detallada incluyendo actores, víctimas, ubicación y temporalidad.
    
    **Uso:** Vista detallada de un conflicto específico para análisis en profundidad.
    """
    service = get_bq_service()
    conflict = service.get_conflict_by_id(event_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    return conflict


@router.get("/stats", response_model=StatsResponse)
async def get_statistics(top_countries: int = Query(default=10, ge=1, le=50)):
    """
    Obtener estadísticas agregadas globales de conflictos armados.
    
    **Parámetros:**
    - **top_countries**: Número de países a incluir en el ranking (1-50)
    
    **Retorna:** 
    - Estadísticas globales (total eventos, total muertes)
    - Ranking de países más afectados
    - Métricas agregadas por periodos
    
    **Uso:** Dashboard de métricas generales y análisis comparativo entre países.
    """
    try:
        service = get_bq_service()
        top_countries_list = service.get_top_countries(limit=top_countries)
        total_stats = service.get_total_stats()
        
        return StatsResponse(
            top_countries=top_countries_list,
            total_events=total_stats["total_events"],
            total_deaths=total_stats["total_deaths"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/countries/top", response_model=list[CountryStats])
async def get_top_countries(limit: int = Query(default=10, ge=1, le=50)):
    """
    Obtener ranking de países por número de conflictos y fatalidades.
    
    **Parámetros:**
    - **limit**: Número de países en el ranking (1-50)
    
    **Retorna:** Lista ordenada de países con:
    - Total de conflictos
    - Total de fatalidades
    - Periodo de actividad
    - Tendencia temporal
    
    **Uso:** Análisis comparativo de impacto por país y identificación de zonas críticas.
    """
    try:
        service = get_bq_service()
        return service.get_top_countries(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=list[ConflictSummary])
async def search_conflicts(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    Búsqueda textual en todos los campos de conflictos armados.
    
    **Parámetros:**
    - **q**: Término de búsqueda (mínimo 2 caracteres)
    - **limit**: Número máximo de resultados (1-100)
    
    **Campos buscados:**
    - Nombres de conflictos
    - Actores involucrados
    - Países y regiones
    - Descripciones de eventos
    
    **Uso:** Búsqueda flexible para encontrar conflictos específicos por cualquier criterio textual.
    """
    try:
        service = get_bq_service()
        return service.search_conflicts(search_term=q, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ==========================================================
# MÁS ENDPOINTS PARA ESTADÍSTICAS
# =========================================================
    
@router.get("/conflicts/year/{year}", response_model=list[ConflictSummary])
async def get_conflicts_by_year(
    year: int = Path(..., ge=1989, le=2024, description="Año a consultar"),
    limit: int = Query(default=100, ge=1, le=500)
):
    """
    Obtener todos los conflictos ocurridos en un año específico.
    
    **Parámetros:**
    - **year**: Año de interés (1989-2024)
    - **limit**: Número máximo de resultados (1-500)
    
    **Retorna:** Lista de conflictos ordenados por severidad (mayor número de fatalidades primero).
    
    **Uso:** Análisis temporal y estudio de patrones anuales de conflictividad.
    """
    try:
        service = get_bq_service()
        conflicts = service.get_conflicts_by_year(year=year, limit=limit)
        return conflicts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline/{country}")
async def get_country_timeline(
    country: str = Path(..., description="País a consultar"),
    start_year: int = Query(default=1989, ge=1989, le=2024),
    end_year: int = Query(default=2024, ge=1989, le=2024)
):
    """
    Obtener línea de tiempo de conflictos para un país en un rango de años.
    
    **Parámetros:**
    - **country**: País a analizar
    - **start_year**: Año inicial del rango (1989-2024)
    - **end_year**: Año final del rango (1989-2024)
    
    **Retorna:** Datos agregados por año incluyendo:
    - Número de eventos por año
    - Total de fatalidades por año  
    - Principales conflictos de cada año
    
    **Uso:** Gráficos de tendencia y análisis de evolución histórica de conflictos por país.
    """
    try:
        service = get_bq_service()
        timeline = service.get_country_timeline(
            country=country,
            start_year=start_year,
            end_year=end_year
        )
        return {
            "country": country,
            "period": f"{start_year}-{end_year}",
            "timeline": timeline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison")
async def compare_countries(
    countries: str = Query(..., description="Lista de países separados por coma"),
    metric: str = Query(default="fatalities", enum=["fatalities", "events", "duration"])
):
    """
    Comparar métricas de conflictos entre múltiples países.
    
    **Parámetros:**
    - **countries**: Lista de países a comparar (ej: "Colombia,Afghanistan,Syria")
    - **metric**: Métrica para comparación:
        - **fatalities**: Total de muertes
        - **events**: Número total de eventos
        - **duration**: Duración promedio de conflictos
    
    **Retorna:** Datos comparativos normalizados incluyendo:
    - Totales y promedios por país
    - Rango temporal de eventos
    - Severidad máxima registrada
    
    **Uso:** Análisis comparativo entre regiones o países con contextos similares.
    """
    try:
        country_list = [c.strip() for c in countries.split(",") if c.strip()]
        
        if not country_list:
            raise HTTPException(status_code=400, detail="Debe proporcionar al menos un país")
        
        if len(country_list) > 10:
            raise HTTPException(status_code=400, detail="Máximo 10 países permitidos para comparación")
        
        service = get_bq_service()
        comparison_data = service.compare_countries(
            countries=country_list,
            metric=metric
        )
        
        return {
            "comparison_metric": metric,
            "countries_compared": country_list,
            "data": comparison_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
