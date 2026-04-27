"""
Servicio para estadísticas complejas que combinan múltiples fuentes de datos.
Maneja la lógica de negocio, transformación y orquestación de datos.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from app.integration.repositories.statistics_repository import StatisticsRepository


class StatisticsService:
    """Servicio para operaciones estadísticas complejas"""
    
    def __init__(self):
        """Inicializa con el repositorio de estadísticas"""
        self.repository = StatisticsRepository()
    
    
    def get_dashboard_summary(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        region: str,
        violence_types: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Obtener resumen del dashboard combinando múltiples fuentes
        
        Returns:
            Dict con métricas agregadas de BigQuery, MongoDB y Neo4j
        """
        # Normalizar filtros
        region = None if region == "all" else region
        violence_types = None if violence_types and "all" in violence_types else violence_types
        
        # BigQuery: eventos y muertes
        bq_metrics = self.repository.get_events_and_deaths_metrics(
            start_date, end_date, region, violence_types
        )
        
        # MongoDB: países únicos
        mongo_metrics = {"countries_count": self.repository.get_countries_count_from_mongo(region)}
        
        # Neo4j: conflictos únicos
        neo4j_metrics = {
            "conflicts_count": self.repository.get_conflicts_count_from_neo4j(region, violence_types)
        }
        
        return {
            "total_events": bq_metrics["total_events"],
            "total_deaths": bq_metrics["total_deaths"],
            "countries_affected": mongo_metrics["countries_count"],
            "unique_conflicts": neo4j_metrics["conflicts_count"],
            "trends": {
                "events_change": 2.3,
                "deaths_change": -15.2,
                "countries_change": 5.1,
                "conflicts_change": -8.7
            }
        }
    
    # ======================================================
    # FILTROS 
    # ======================================================
    
    def get_available_regions(self) -> List[Dict[str, Any]]:
        """
        Obtener todas las regiones disponibles con conteo
        
        Returns:
            Lista de opciones de regiones con formato UI
        """
        raw_regions = self.repository.get_available_regions()
        
        regions = []
        total_events = 0
        
        for item in raw_regions:
            region_value = item["region"].strip().lower().replace(' ', '-')
            region_label = item["region"].strip().title()
            count = item["event_count"]
            
            regions.append({
                "value": region_value,
                "label": region_label,
                "count": count
            })
            
            total_events += count
        
        regions.insert(0, {
            "value": "all",
            "label": "Todas las Regiones",
            "count": total_events
        })
        
        return regions
    
    def get_available_violence_types(self) -> List[Dict[str, Any]]:
        """
        Obtener todos los tipos de violencia disponibles con conteo
        
        Returns:
            Lista de opciones de tipos de violencia con formato UI
        """
        raw_types = self.repository.get_available_violence_types()
        
        violence_types = []
        total_events = 0
        
        for item in raw_types:
            type_value = item["type_of_violence"].strip().lower().replace(' ', '-')
            type_label = item["type_of_violence"].strip()
            count = item["event_count"]
            
            violence_types.append({
                "value": type_value,
                "label": type_label,
                "count": count
            })
            
            total_events += count
        
        violence_types.insert(0, {
            "value": "all",
            "label": "Todos los Tipos",
            "count": total_events
        })
        
        return violence_types
    
    def get_date_range(self) -> Dict[str, Any]:
        """
        Obtener el rango de fechas disponible con años totales
        
        Returns:
            Dict con min_date, max_date, total_years
        """
        date_info = self.repository.get_date_range()
        
        min_date = date_info["min_date"]
        max_date = date_info["max_date"]
        
        # Calcular años totales
        if min_date and max_date:
            min_year = min_date.year if isinstance(min_date, datetime) else int(str(min_date)[:4])
            max_year = max_date.year if isinstance(max_date, datetime) else int(str(max_date)[:4])
            total_years = max_year - min_year + 1
        else:
            total_years = 0
        
        return {
            "min_date": str(min_date) if min_date else None,
            "max_date": str(max_date) if max_date else None,
            "total_years": total_years
        }
    
    def get_filters_metadata(self) -> Dict[str, Any]:
        """
        Obtener toda la metadata de filtros en una sola llamada (optimizado)
        
        Returns:
            Dict con regions, violence_types, date_range
        """
        return {
            "regions": self.get_available_regions(),
            "violence_types": self.get_available_violence_types(),
            "date_range": self.get_date_range()
        }
    
    # ======================================================
    # GRÁFICAS - TIMELINE
    # ======================================================
    
    def get_timeline_data(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        region: str,
        violence_types: Optional[List[str]],
        granularity: str = "month"
    ) -> Dict[str, Any]:
        """
        Obtener datos de evolución temporal
        
        Args:
            granularity: "year" o "month"
            
        Returns:
            Dict con labels, events, deaths
        """
        # Normalizar filtros
        region = None if region == "all" else region
        violence_types = None if violence_types and "all" in violence_types else violence_types
        
        # Determinar formato de fecha según granularidad
        if granularity == "year":
            date_format = "FORMAT_DATE('%Y', date_start)"
        else:  
            date_format = "FORMAT_DATE('%Y-%m', date_start)"
        
        # Obtener datos del repositorio
        raw_data = self.repository.get_timeline_data(
            start_date, end_date, region, violence_types, date_format
        )
        
        labels = []
        events = []
        deaths = []
        
        for row in raw_data:
            labels.append(row["period"])
            events.append(int(row["total_events"]))
            deaths.append(int(row["total_deaths"]))
        
        return {
            "labels": labels,
            "events": events,
            "deaths": deaths,
            "granularity": granularity
        }
    
    # ======================================================
    # GRÁFICAS - TOP PAÍSES
    # ======================================================
    
    def get_top_countries(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        region: str,
        violence_types: Optional[List[str]],
        metric: str = "events",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Obtener top países por eventos o muertes
        
        Args:
            metric: "events" o "deaths"
            
        Returns:
            Dict con countries, values
        """
        # Normalizar filtros
        region = None if region == "all" else region
        violence_types = None if violence_types and "all" in violence_types else violence_types
        
        # Determinar columna según métrica
        if metric == "deaths":
            metric_column = "COALESCE(SUM(deaths_total), 0)"
        else:  # eventos
            metric_column = "COUNT(DISTINCT event_id)"
        
        # Obtener datos del repositorio
        raw_data = self.repository.get_top_countries_data(
            start_date, end_date, region, violence_types, metric_column, limit
        )
        
        # Transformar a formato de respuesta
        countries = []
        values = []
        
        for row in raw_data:
            countries.append(row["country"])
            values.append(int(row["metric_value"]))
        
        return {
            "countries": countries,
            "values": values,
            "metric": metric,
            "limit": limit
        }
    
    # ======================================================
    # GRÁFICAS - TIPOS DE VIOLENCIA
    # ======================================================
    
    def get_violence_types_distribution(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        region: str,
        metric: str = "events"
    ) -> Dict[str, Any]:
        """
        Obtener distribución por tipo de violencia
        
        Args:
            metric: "events" o "deaths"
            
        Returns:
            Dict con types, events/deaths, percentages
        """
        # Normalizar filtros
        region = None if region == "all" else region
        
        # Determinar columna según métrica
        if metric == "deaths":
            metric_column = "COALESCE(SUM(deaths_total), 0)"
        else:  # eventos
            metric_column = "COUNT(DISTINCT event_id)"
        
        # Obtener datos del repositorio
        raw_data = self.repository.get_violence_types_distribution(
            start_date, end_date, region, metric_column
        )
        
        # Calcular totales y porcentajes
        types = []
        values = []
        percentages = []
        total = sum(int(row["metric_value"]) for row in raw_data)
        
        for row in raw_data:
            value = int(row["metric_value"])
            percentage = round((value / total * 100), 1) if total > 0 else 0
            
            types.append(row["type_of_violence"])
            values.append(value)
            percentages.append(percentage)
        
        return {
            "types": types,
            "values": values,
            "percentages": percentages,
            "metric": metric
        }
    
    # ======================================================
    # TABLA DE CONFLICTOS
    # ======================================================
    
    def get_conflicts_table(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        region: str,
        violence_types: Optional[List[str]],
        search: Optional[str],
        sort_by: str,
        sort_order: str,
        limit: int,
        offset: int
    ) -> Dict[str, Any]:
        """
        Obtener conflictos con paginación, búsqueda y ordenamiento
        
        Returns:
            Dict con total, conflicts, limit, offset
        """
        # Normalizar filtros
        region = None if region == "all" else region
        violence_types = None if violence_types and "all" in violence_types else violence_types
        
        # Obtener datos agregados
        raw_conflicts = self.repository.get_conflicts_aggregated(
            start_date, end_date, region, violence_types
        )
        
        # Transformar a formato de tabla
        conflicts_data = []
        
        for row in raw_conflicts:
            conflict_entry = {
                "name": row["conflict_name"],
                "countries": row["countries"] if row["countries"] else "N/A",
                "actors": self._format_actors(row["side_a"], row["side_b"]),
                "events": int(row["events"]),
                "deaths": int(row["deaths"]),
                "period": self._format_period(row["date_start"], row["date_end"]),
                "region": row["region"] if row["region"] else "N/A"
            }
            
            # Filtrar por búsqueda si existe
            if search:
                search_lower = search.lower()
                if (search_lower in conflict_entry["name"].lower() or
                    search_lower in conflict_entry["countries"].lower() or
                    search_lower in conflict_entry["actors"].lower() or
                    search_lower in conflict_entry["region"].lower()):
                    conflicts_data.append(conflict_entry)
            else:
                conflicts_data.append(conflict_entry)
        
        # Ordenar
        conflicts_data = self._sort_conflicts(conflicts_data, sort_by, sort_order)
        
        # Paginar
        total = len(conflicts_data)
        conflicts_page = conflicts_data[offset:offset + limit]
        
        return {
            "total": total,
            "conflicts": conflicts_page,
            "limit": limit,
            "offset": offset
        }
    
    # ======================================================
    # UTILIDADES PRIVADAS
    # ======================================================
    
    def _format_actors(self, side_a, side_b) -> str:
        """Formatear actores para visualización"""
        if side_a and side_b:
            return f"{side_a} vs {side_b}"
        elif side_a:
            return side_a
        elif side_b:
            return side_b
        return "N/A"
    
    def _format_period(self, date_start, date_end) -> str:
        """Formatear periodo para visualización"""
        if date_start and date_end:
            start_year = str(date_start)[:4]
            end_year = str(date_end)[:4]
            
            if start_year == end_year:
                return start_year
            else:
                return f"{start_year}-{end_year}"
        return "N/A"
    
    def _sort_conflicts(
        self,
        conflicts: List[Dict],
        sort_by: str,
        sort_order: str
    ) -> List[Dict]:
        """Ordenar lista de conflictos"""
        reverse = (sort_order == "desc")
        
        if sort_by == "name":
            return sorted(conflicts, key=lambda x: x["name"].lower(), reverse=reverse)
        elif sort_by == "events":
            return sorted(conflicts, key=lambda x: x["events"], reverse=reverse)
        elif sort_by == "deaths":
            return sorted(conflicts, key=lambda x: x["deaths"], reverse=reverse)
        elif sort_by == "period":
            return sorted(conflicts, key=lambda x: x["period"], reverse=reverse)
        
        return conflicts