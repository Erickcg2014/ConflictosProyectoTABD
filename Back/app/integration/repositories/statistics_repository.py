"""
Repositorio para consultas estadísticas complejas.
Contiene queries que agregan datos de múltiples fuentes.
"""

from typing import Optional, List, Dict, Any
from google.cloud import bigquery
from app.integration.repositories.bigquery_repository import BigQueryRepository
from app.integration.repositories.mongodb_repository import MongoDBRepository
from app.integration.repositories.neo4j_repository import Neo4jRepository
from app.config import settings

class StatisticsRepository:
    """Repositorio para operaciones estadísticas complejas"""
    
    def __init__(self):
        """Inicializa con los repositorios base"""
        self.bq_repo = BigQueryRepository()
        self.mongo_repo = MongoDBRepository()
        self.neo4j_repo = Neo4jRepository()
    
    # ======================================================
    # MÉTRICAS DE BIGQUERY
    # ======================================================
    
    def get_events_and_deaths_metrics(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        region: Optional[str],
        violence_types: Optional[List[str]]
    ) -> Dict[str, int]:
        """
        Obtener métricas de eventos y muertes desde BigQuery
        
        Returns:
            Dict con: total_events, total_deaths
        """
        query = f"""
        SELECT 
            COUNT(DISTINCT event_id) as total_events,
            COALESCE(SUM(deaths_total), 0) as total_deaths
        FROM `{settings.bigquery_project}.{settings.bigquery_dataset}.{settings.bigquery_table}`
        WHERE 1=1
        """
        
        query_params = []
        
        #Filtro por fecha inicial
        if start_date:
            query += " AND date_start >= @start_date"
            query_params.append(
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date)
            )
        # Filtro por fecha final
        if end_date:
            query += " AND date_end <= @end_date"
            query_params.append(
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date)
            )
        
        # Filtro por región
        if region:
            query += " AND LOWER(region) = LOWER(@region)"
            query_params.append(
                bigquery.ScalarQueryParameter("region", "STRING", region)
            )
        
        # Filtro por tipos de violencia
        if violence_types:
            query += " AND type_of_violence IN UNNEST(@violence_types)"
            query_params.append(
                bigquery.ArrayQueryParameter("violence_types", "STRING", violence_types)
            )
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        results = self.bq_repo.client.query(query, job_config=job_config).result()
        
        for row in results:
            return {
                "total_events": int(row.total_events) if row.total_events else 0,
                "total_deaths": int(row.total_deaths) if row.total_deaths else 0
            }
        
        return {"total_events": 0, "total_deaths": 0}
    
    def get_available_regions(self) -> List[Dict[str, Any]]:
        """
        Obtener todas las regiones disponibles con conteo de eventos
        
        Returns:
            Lista de dicts con: value, label, count
        """
        query = f"""
        SELECT 
            region,
            COUNT(DISTINCT event_id) as event_count
        FROM `{settings.bigquery_project}.{settings.bigquery_dataset}.{settings.bigquery_table}`
        WHERE region IS NOT NULL 
            AND TRIM(region) != ''
        GROUP BY region
        ORDER BY event_count DESC
        """
        
        results = self.bq_repo.client.query(query).result()
        
        regions = []
        for row in results:
            regions.append({
                "region": row.region,
                "event_count": int(row.event_count)
            })
        
        return regions
    
    def get_available_violence_types(self) -> List[Dict[str, Any]]:
        """
        Obtener todos los tipos de violencia con conteo de eventos
        
        Returns:
            Lista de dicts con: type_of_violence, event_count
        """
        query = f"""
        SELECT 
            type_of_violence,
            COUNT(DISTINCT event_id) as event_count
        FROM `{settings.bigquery_project}.{settings.bigquery_dataset}.{settings.bigquery_table}`
        WHERE type_of_violence IS NOT NULL 
            AND TRIM(type_of_violence) != ''
        GROUP BY type_of_violence
        ORDER BY event_count DESC
        """
        
        results = self.bq_repo.client.query(query).result()
        
        violence_types = []
        for row in results:
            violence_types.append({
                "type_of_violence": row.type_of_violence,
                "event_count": int(row.event_count)
            })
        
        return violence_types
    
    def get_date_range(self) -> Dict[str, Any]:
        """
        Obtener el rango de fechas disponible (min y max)
        
        Returns:
            Dict con: min_date, max_date
        """
        query = f"""
        SELECT 
            MIN(date_start) as min_date,
            MAX(date_end) as max_date
        FROM `{settings.bigquery_project}.{settings.bigquery_dataset}.{settings.bigquery_table}`
        WHERE date_start IS NOT NULL 
            AND date_end IS NOT NULL
        """
        
        results = self.bq_repo.client.query(query).result()
        
        for row in results:
            return {
                "min_date": row.min_date,
                "max_date": row.max_date
            }
        
        return {
            "min_date": None,
            "max_date": None
        }
    
    def get_timeline_data(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        region: Optional[str],
        violence_types: Optional[List[str]],
        date_format: str
    ) -> List[Dict[str, Any]]:
        """
        Obtener datos de evolución temporal
        
        Args:
            date_format: Formato SQL de fecha (ej: "FORMAT_DATE('%Y-%m', date_start)")
            
        Returns:
            Lista de dicts con: period, total_events, total_deaths
        """
        query = f"""
        SELECT 
            {date_format} as period,
            COUNT(DISTINCT event_id) as total_events,
            COALESCE(SUM(deaths_total), 0) as total_deaths
        FROM `{settings.bigquery_project}.{settings.bigquery_dataset}.{settings.bigquery_table}`
        WHERE date_start IS NOT NULL
        """
        
        query_params = []
        
        if start_date:
            query += " AND date_start >= @start_date"
            query_params.append(
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date)
            )
        
        if end_date:
            query += " AND date_end <= @end_date"
            query_params.append(
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date)
            )
        
        if region:
            query += " AND LOWER(region) = LOWER(@region)"
            query_params.append(
                bigquery.ScalarQueryParameter("region", "STRING", region)
            )
        
        if violence_types:
            query += " AND type_of_violence IN UNNEST(@violence_types)"
            query_params.append(
                bigquery.ArrayQueryParameter("violence_types", "STRING", violence_types)
            )
        
        query += """
        GROUP BY period
        ORDER BY period ASC
        """
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        results = self.bq_repo.client.query(query, job_config=job_config).result()
        
        return [dict(row) for row in results]
    
    def get_top_countries_data(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        region: Optional[str],
        violence_types: Optional[List[str]],
        metric_column: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Obtener top países por métrica especificada
        
        Args:
            metric_column: Expresión SQL para la métrica (ej: "COUNT(DISTINCT event_id)")
            
        Returns:
            Lista de dicts con: country, metric_value
        """
        query = f"""
        SELECT 
            country,
            {metric_column} as metric_value
        FROM `{settings.bigquery_project}.{settings.bigquery_dataset}.{settings.bigquery_table}`
        WHERE country IS NOT NULL 
            AND TRIM(country) != ''
        """
        
        query_params = []
        
        if start_date:
            query += " AND date_start >= @start_date"
            query_params.append(
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date)
            )
        
        if end_date:
            query += " AND date_end <= @end_date"
            query_params.append(
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date)
            )
        
        if region:
            query += " AND LOWER(region) = LOWER(@region)"
            query_params.append(
                bigquery.ScalarQueryParameter("region", "STRING", region)
            )
        
        if violence_types:
            query += " AND type_of_violence IN UNNEST(@violence_types)"
            query_params.append(
                bigquery.ArrayQueryParameter("violence_types", "STRING", violence_types)
            )
        
        query += f"""
        GROUP BY country
        ORDER BY metric_value DESC
        LIMIT @limit
        """
        
        query_params.append(
            bigquery.ScalarQueryParameter("limit", "INT64", limit)
        )
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        results = self.bq_repo.client.query(query, job_config=job_config).result()
        
        return [dict(row) for row in results]
    
    def get_violence_types_distribution(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        region: Optional[str],
        metric_column: str
    ) -> List[Dict[str, Any]]:
        """
        Obtener distribución por tipo de violencia
        
        Args:
            metric_column: Expresión SQL para la métrica
            
        Returns:
            Lista de dicts con: type_of_violence, metric_value
        """
        query = f"""
        SELECT 
            type_of_violence,
            {metric_column} as metric_value
        FROM `{settings.bigquery_project}.{settings.bigquery_dataset}.{settings.bigquery_table}`
        WHERE type_of_violence IS NOT NULL 
            AND TRIM(type_of_violence) != ''
        """
        
        query_params = []
        
        if start_date:
            query += " AND date_start >= @start_date"
            query_params.append(
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date)
            )
        
        if end_date:
            query += " AND date_end <= @end_date"
            query_params.append(
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date)
            )
        
        if region:
            query += " AND LOWER(region) = LOWER(@region)"
            query_params.append(
                bigquery.ScalarQueryParameter("region", "STRING", region)
            )
        
        query += """
        GROUP BY type_of_violence
        ORDER BY metric_value DESC
        """
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        results = self.bq_repo.client.query(query, job_config=job_config).result()
        
        return [dict(row) for row in results]
    
    def get_conflicts_aggregated(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        region: Optional[str],
        violence_types: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Obtener conflictos agregados con todos sus detalles
        
        Returns:
            Lista de dicts con: conflict_name, countries, side_a, side_b, region,
                               events, deaths, date_start, date_end
        """
        query = f"""
        SELECT 
            conflict_name,
            STRING_AGG(DISTINCT country, ', ' ORDER BY country) as countries,
            ANY_VALUE(side_a) as side_a,
            ANY_VALUE(side_b) as side_b,
            ANY_VALUE(region) as region,
            COUNT(DISTINCT event_id) as events,
            COALESCE(SUM(deaths_total), 0) as deaths,
            MIN(date_start) as date_start,
            MAX(date_end) as date_end
        FROM `{settings.bigquery_project}.{settings.bigquery_dataset}.{settings.bigquery_table}`
        WHERE conflict_name IS NOT NULL 
            AND TRIM(conflict_name) != ''
        """
        
        query_params = []
        
        if start_date:
            query += " AND date_start >= @start_date"
            query_params.append(
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date)
            )
        
        if end_date:
            query += " AND date_end <= @end_date"
            query_params.append(
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date)
            )
        
        if region:
            query += " AND LOWER(region) = LOWER(@region)"
            query_params.append(
                bigquery.ScalarQueryParameter("region", "STRING", region)
            )
        
        if violence_types:
            query += " AND type_of_violence IN UNNEST(@violence_types)"
            query_params.append(
                bigquery.ArrayQueryParameter("violence_types", "STRING", violence_types)
            )
        
        query += """
        GROUP BY conflict_name
        """
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        results = self.bq_repo.client.query(query, job_config=job_config).result()
        
        return [dict(row) for row in results]
    
    # ======================================================
    # MÉTRICAS DE MONGODB
    # ======================================================
    
    def get_countries_count_from_mongo(self, region: Optional[str]) -> int:
        """
        Obtener conteo de países únicos desde MongoDB
        
        Returns:
            Número de países únicos
        """
        match_stage = {}
        
        if region:
            match_stage["region"] = {"$regex": f"^{region}$", "$options": "i"}
        
        pipeline = []
        if match_stage:
            pipeline.append({"$match": match_stage})
        
        pipeline.append({
            "$group": {
                "_id": None,
                "countries": {"$addToSet": "$country"}
            }
        })
        
        results = list(self.mongo_repo.collection.aggregate(pipeline))
        
        if results:
            return len(results[0].get("countries", []))
        
        return 0
    
    # ======================================================
    # MÉTRICAS DE NEO4J
    # ======================================================
    
    def get_conflicts_count_from_neo4j(
        self,
        region: Optional[str],
        violence_types: Optional[List[str]]
    ) -> int:
        """
        Obtener conteo de conflictos únicos desde Neo4j
        
        Returns:
            Número de conflictos únicos
        """
        query = "MATCH (c:Conflict) WHERE 1=1"
        params = {}
        
        if region:
            query += " AND toLower(c.region) = toLower($region)"
            params["region"] = region
        
        if violence_types:
            query += " AND c.type_of_violence IN $violence_types"
            params["violence_types"] = violence_types
        
        query += " RETURN COUNT(DISTINCT c.name) as conflicts_count"
        
        with self.neo4j_repo.driver.session() as session:
            result = session.run(query, params)
            record = result.single()
            if record:
                return record["conflicts_count"]
        
        return 0