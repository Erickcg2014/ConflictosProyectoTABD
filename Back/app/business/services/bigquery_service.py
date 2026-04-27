from typing import List, Optional
from app.integration.repositories.bigquery_repository import BigQueryRepository
from app.business.models.schemas import ConflictSummary, CountryStats

class BigQueryService:
    """Servicio de lógica de negocio para conflictos"""
    
    def __init__(self):
        self.repository = BigQueryRepository()
    
    def check_connection(self) -> bool:
        """Verificar conexión a BigQuery"""
        return self.repository.check_connection()
    
    def get_all_conflicts(
        self,
        limit: int = 100,
        offset: int = 0,
        country: Optional[str] = None,
        region: Optional[str] = None
    ) -> tuple[List[ConflictSummary], int]:
        """
        Obtener conflictos con lógica de negocio aplicada
        """
        # datos del repositorio
        raw_conflicts, total = self.repository.find_all(
            limit=limit,
            offset=offset,
            country=country,
            region=region
        )
        
        # Transformar a modelos de dominio
        conflicts = [self._dict_to_conflict(row) for row in raw_conflicts]
        
        return conflicts, total
    
    def get_conflict_by_id(self, event_id: str) -> Optional[ConflictSummary]:
        """Obtener conflicto por ID"""
        raw_conflict = self.repository.find_by_id(event_id)
        
        if raw_conflict:
            return self._dict_to_conflict(raw_conflict)
        return None
    
    def get_top_countries(self, limit: int = 10) -> List[CountryStats]:
        """Top países con transformación a modelo de dominio"""
        raw_stats = self.repository.find_top_countries(limit)
        
        stats = []
        for row in raw_stats:
            stats.append(CountryStats(
                country=row["country"],
                total_events=row["total_events"],
                total_deaths=int(row["total_deaths"] or 0),
                conflicts=list(row["conflicts"]) if row.get("conflicts") else []
            ))
        
        return stats
    
    def get_total_stats(self) -> dict:
        """Estadísticas globales"""
        raw_stats = self.repository.get_global_stats()
        
        return {
            "total_events": raw_stats["total_events"],
            "total_deaths": int(raw_stats["total_deaths"] or 0),
            "total_countries": raw_stats["total_countries"],
            "total_conflicts": raw_stats["total_conflicts"]
        }
    
    def search_conflicts(
        self,
        search_term: str,
        limit: int = 20
    ) -> List[ConflictSummary]:
        """Buscar conflictos"""
        raw_conflicts = self.repository.search(search_term, limit)
        return [self._dict_to_conflict(row) for row in raw_conflicts]
    
    def _dict_to_conflict(self, row: dict) -> ConflictSummary:
        """Transformar dict a modelo de dominio"""
        return ConflictSummary(
            event_id=row["event_id"],
            conflict_name=row["conflict_name"],
            type_of_violence=row["type_of_violence"],
            side_a=row["side_a"],
            side_b=row["side_b"],
            country=row["country"],
            region=row["region"],
            date_start=row["date_start"],
            date_end=row["date_end"],
            deaths_a=row["deaths_a"],
            deaths_b=row["deaths_b"],
            deaths_total=row["deaths_total"],
            length_of_conflict=row["length_of_conflict"],
        )