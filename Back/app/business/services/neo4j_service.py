"""
Servicio para consultas del grafo de conflictos en Neo4j.
Maneja la lógica de negocio y transformación de datos a modelos de dominio.
"""

from typing import List, Dict, Optional, Any
from app.integration.repositories.neo4j_repository import Neo4jRepository
from app.business.models.schemas import (
    ActorDetail, ActorRelationship, ConflictNode,
    ActorNode, Relation
)


class Neo4jService:
    """Servicio para manejar operaciones del grafo de conflictos"""
    
    def __init__(self):
        """Inicializa el servicio con el repositorio"""
        self.repository = Neo4jRepository()
    
    # ======================================================
    # VERIFICACIÓN Y ESTADÍSTICAS
    # ======================================================
    
    def check_connection(self) -> bool:
        """Verificar conexión a Neo4j"""
        print(f"🔍 Neo4j: Verificando conexión...")
        is_connected = self.repository.check_connection()
        if is_connected:
            print("✅ Neo4j: Conexión exitosa")
        else:
            print("❌ Neo4j: Error de conexión")
        return is_connected
    
    def get_graph_stats(self) -> Dict[str, int]:
        """
        Obtener estadísticas generales del grafo
        
        Returns:
            Dict con conteos de nodos y relaciones
        """
        stats = self.repository.get_graph_statistics()
        
        if stats:
            return {
                "total_conflicts": stats["total_conflicts"],
                "total_actors": stats["total_actors"],
                "total_participations": stats["total_participations"],
                "total_engagements": stats["total_engagements"]
            }
        
        return {
            "total_conflicts": 0,
            "total_actors": 0,
            "total_participations": 0,
            "total_engagements": 0
        }
    
    # ======================================================
    # OPERACIONES DE ACTORES
    # ======================================================
    
    def get_actor_by_name(self, actor_name: str) -> Optional[ActorDetail]:
        """
        Obtener detalle de un actor con sus relaciones
        
        Args:
            actor_name: Nombre del actor
            
        Returns:
            ActorDetail o None si no existe
        """
        data = self.repository.find_actor_by_name(actor_name)
        
        if not data:
            return None
        
        # Transformar conflicts
        conflicts_data = data.get("conflicts") or []
        conflicts = [
            ActorRelationship(
                conflict=c.get("conflict"),
                role=c.get("role"),
                cumulative_deaths=c.get("cumulative_deaths"),
                event_count=c.get("event_count")
            )
            for c in conflicts_data if c.get("conflict")
        ]
        
        # Filtrar actores 
        engaged_actors = [a for a in data.get("engaged_actors", []) if a]
        
        return ActorDetail(
            name=data["name"],
            conflicts=conflicts,
            engaged_actors=engaged_actors,
            total_conflicts=len(conflicts)
        )
    
    def get_all_actors(self, limit: int = 100) -> List[str]:
        """
        Obtener lista de todos los actores
        
        Args:
            limit: Número máximo de actores
            
        Returns:
            Lista de nombres de actores
        """
        return self.repository.find_all_actors(limit)
    
    def get_top_actors_by_deaths(self, limit: int = 10) -> List[Dict]:
        """
        Obtener actores más letales
        
        Args:
            limit: Número de actores a retornar
            
        Returns:
            Lista de dicts con estadísticas de actores
        """
        return self.repository.find_top_actors_by_deaths(limit)
    
    def get_actor_network(self, actor_name: str, depth: int = 2) -> Dict[str, Any]:
        """
        Obtener red de actores relacionados
        
        Args:
            actor_name: Nombre del actor central
            depth: Profundidad de búsqueda (1-5)
            
        Returns:
            Dict con actor central y actores relacionados
        """
        # Validar depth (1-5)
        depth = max(1, min(depth, 5))
        
        related_actors = self.repository.find_actor_network(actor_name, depth)
        
        return {
            "central_actor": actor_name,
            "related_actors": related_actors,
            "network_size": len(related_actors)
        }
    
    def get_actor_relationships(self, actor1: str, actor2: str) -> List[Dict]:
        """
        Obtener relaciones ENGAGED_WITH entre dos actores
        
        Args:
            actor1: Nombre del primer actor
            actor2: Nombre del segundo actor
            
        Returns:
            Lista de relaciones de enfrentamiento
        """
        return self.repository.find_actor_relationships(actor1, actor2)
    
    # ======================================================
    # OPERACIONES DE CONFLICTOS
    # ======================================================
    
    def get_conflict_by_name(self, conflict_name: str) -> Optional[ConflictNode]:
        """
        Obtener información de un conflicto
        
        Args:
            conflict_name: Nombre del conflicto
            
        Returns:
            ConflictNode o None si no existe
        """
        data = self.repository.find_conflict_by_name(conflict_name)
        
        if not data:
            return None
        
        return ConflictNode(
            name=data["name"],
            type_of_violence=data.get("type_of_violence"),
            country=data.get("country"),
            region=data.get("region"),
            event_count=data.get("event_count"),
            total_deaths=data.get("total_deaths"),
            event_ids=data.get("event_ids", [])
        )
    
    def get_conflict_event_ids(self, conflict_name: str) -> List[str]:
        """
        Obtener event_ids de un conflicto
        Útil para vincular con BigQuery/MongoDB
        
        Args:
            conflict_name: Nombre del conflicto
            
        Returns:
            Lista de event_ids
        """
        return self.repository.find_conflict_event_ids(conflict_name)
    
    def get_conflict_actors(self, conflict_name: str) -> tuple:
        """
        Obtener actores involucrados en un conflicto
        
        Args:
            conflict_name: Nombre del conflicto
            
        Returns:
            Tupla (ConflictNode, List[ActorNode])
        """
        data = self.repository.find_conflict_with_actors(conflict_name)
        
        if not data:
            return None, []
        
        # Construir ConflictNode
        conflict = ConflictNode(
            name=data["conflict_name"],
            type_of_violence=data.get("type_of_violence"),
            country=data.get("country"),
            region=data.get("region"),
            event_count=data.get("event_count"),
            total_deaths=data.get("total_deaths"),
            event_ids=data.get("event_ids", [])
        )
        
        # Construir lista de ActorNode
        actors_data = data.get("actors") or []
        actors = [
            ActorNode(
                name=a.get("name"),
                role=a.get("role"),
                cumulative_deaths=a.get("cumulative_deaths"),
                event_count=a.get("event_count")
            )
            for a in actors_data if a.get("name")
        ]
        
        return conflict, actors
    
    def get_top_conflicts(self, limit: int = 10) -> List[ConflictNode]:
        """
        Obtener top conflictos por muertes totales
        
        Args:
            limit: Número de conflictos a retornar
            
        Returns:
            Lista de ConflictNode
        """
        conflicts_data = self.repository.find_top_conflicts(limit)
        
        return [
            ConflictNode(
                name=c["name"],
                type_of_violence=c.get("type_of_violence"),
                country=c.get("country"),
                region=c.get("region"),
                event_count=c.get("event_count"),
                total_deaths=c.get("total_deaths"),
                event_ids=c.get("event_ids", [])
            )
            for c in conflicts_data
        ]
    
    def search_conflicts(
        self,
        search_term: str,
        limit: int = 20
    ) -> List[ConflictNode]:
        """
        Buscar conflictos por nombre, país o región
        
        Args:
            search_term: Término de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            Lista de ConflictNode
        """
        conflicts_data = self.repository.search_conflicts(search_term, limit)
        
        return [
            ConflictNode(
                name=c["name"],
                type_of_violence=c.get("type_of_violence"),
                country=c.get("country"),
                region=c.get("region"),
                event_count=c.get("event_count"),
                total_deaths=c.get("total_deaths"),
                event_ids=c.get("event_ids", [])
            )
            for c in conflicts_data
        ]