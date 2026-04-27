from google.cloud import bigquery
from typing import List, Dict, Any, Optional
from app.integration.clients.bigquery_client import BigQueryClient

class BigQueryRepository:
    """Repositorio para acceso a datos de BigQuery"""
    
    def __init__(self):
        bq_client = BigQueryClient()
        self.client = bq_client.client
        self.full_table = bq_client.full_table
    
    def check_connection(self) -> bool:
        """Verificar conexión"""
        try:
            query = f"SELECT COUNT(*) as count FROM `{self.full_table}` LIMIT 1"
            self.client.query(query).result()
            return True
        except Exception as e:
            print(f"❌ BigQuery: Error de conexión: {e}")
            return False
    
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        country: Optional[str] = None,
        region: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Buscar conflictos con paginación y filtros
        
        Returns:
            Tupla con (lista de filas como dicts, total de registros)
        """

        where_clauses = []
        query_params = []
        
        if country:
            where_clauses.append("country = @country")
            query_params.append(
                bigquery.ScalarQueryParameter("country", "STRING", country)
            )
        
        if region:
            where_clauses.append("region = @region")
            query_params.append(
                bigquery.ScalarQueryParameter("region", "STRING", region)
            )
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Query para contar total
        count_query = f"""
        SELECT COUNT(*) as total 
        FROM `{self.full_table}`
        {where_sql}
        """
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        count_result = list(self.client.query(count_query, job_config=job_config).result())
        total = count_result[0].total if count_result else 0
        
        # Query para obtener datos
        data_query = f"""
        SELECT * 
        FROM `{self.full_table}`
        {where_sql}
        ORDER BY date_start DESC
        LIMIT @limit OFFSET @offset
        """
        
        query_params.extend([
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
            bigquery.ScalarQueryParameter("offset", "INT64", offset)
        ])
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        results = self.client.query(data_query, job_config=job_config).result()
        
        # Convertir filas a diccionarios
        conflicts = [dict(row.items()) for row in results]
        
        return conflicts, total
    
    def find_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Buscar conflicto por ID"""
        query = f"""
        SELECT * 
        FROM `{self.full_table}` 
        WHERE event_id = @event_id
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("event_id", "STRING", event_id)
            ]
        )
        
        results = list(self.client.query(query, job_config=job_config).result())
        
        if results:
            return dict(results[0].items())
        return None
    
    def find_top_countries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Top países por eventos y muertes"""
        query = f"""
        SELECT 
            country,
            COUNT(*) as total_events,
            SUM(deaths_total) as total_deaths,
            ARRAY_AGG(DISTINCT conflict_name IGNORE NULLS LIMIT 5) as conflicts
        FROM `{self.full_table}`
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY total_deaths DESC
        LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [dict(row.items()) for row in results]
    
    def get_global_stats(self) -> Dict[str, int]:
        """Estadísticas globales"""
        query = f"""
        SELECT 
            COUNT(*) as total_events,
            SUM(deaths_total) as total_deaths,
            COUNT(DISTINCT country) as total_countries,
            COUNT(DISTINCT conflict_name) as total_conflicts
        FROM `{self.full_table}`
        """
        
        results = list(self.client.query(query).result())
        if results:
            return dict(results[0].items())
        return {
            "total_events": 0,
            "total_deaths": 0,
            "total_countries": 0,
            "total_conflicts": 0
        }
    
    def search(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Buscar conflictos por término"""
        query = f"""
        SELECT * 
        FROM `{self.full_table}`
        WHERE 
            LOWER(conflict_name) LIKE CONCAT('%', LOWER(@search_term), '%')
            OR LOWER(side_a) LIKE CONCAT('%', LOWER(@search_term), '%')
            OR LOWER(side_b) LIKE CONCAT('%', LOWER(@search_term), '%')
            OR LOWER(country) LIKE CONCAT('%', LOWER(@search_term), '%')
        ORDER BY deaths_total DESC
        LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("search_term", "STRING", search_term),
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [dict(row.items()) for row in results]