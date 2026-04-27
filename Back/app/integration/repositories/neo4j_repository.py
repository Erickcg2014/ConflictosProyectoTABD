"""
Repositorio para acceso a datos del grafo de conflictos en Neo4j.
Contiene todas las queries Cypher y retorna datos crudos (dicts/listas).
"""

from typing import List, Dict, Optional, Any
from app.integration.clients.neo4j_client import Neo4jClient


class Neo4jRepository:
    """Repositorio para operaciones de consulta en Neo4j"""
    
    def __init__(self):
        """Inicializa el repositorio con el cliente Neo4j"""
        client = Neo4jClient()
        self.driver = client.driver
    
    # ======================================================
    # CONSULTAS DE VERIFICACIÓN
    # ======================================================
    
    def check_connection(self) -> bool:
        """Verificar conexión a Neo4j"""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            print(f"❌ Neo4j: Error de conexión: {e}")
            return False
    
    def get_graph_statistics(self) -> Optional[Dict[str, int]]:
        """
        Obtener estadísticas generales del grafo
        
        Returns:
            Dict con: total_conflicts, total_actors, total_participations, total_engagements
        """
        query = """
        MATCH (c:Conflict)
        MATCH (a:Actor)
        MATCH ()-[r:PARTICIPATED_IN]->()
        MATCH ()-[e:ENGAGED_WITH]-()
        RETURN 
            count(DISTINCT c) as total_conflicts,
            count(DISTINCT a) as total_actors,
            count(DISTINCT r) as total_participations,
            count(DISTINCT e) as total_engagements
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            
            if record:
                return dict(record)
        
        return None
    
    # ======================================================
    # CONSULTAS DE ACTORES
    # ======================================================
    
    def find_actor_by_name(self, actor_name: str) -> Optional[Dict[str, Any]]:
        """
        Buscar actor por nombre con sus relaciones
        
        Returns:
            Dict con: name, conflicts (list), engaged_actors (list)
        """
        query = """
        MATCH (a:Actor {name: $actor_name})
        OPTIONAL MATCH (a)-[r:PARTICIPATED_IN]->(c:Conflict)
        OPTIONAL MATCH (a)-[e:ENGAGED_WITH]-(other:Actor)
        RETURN 
            a.name as name,
            collect(DISTINCT {
                conflict: r.conflict,
                role: r.role,
                cumulative_deaths: r.cumulative_deaths,
                event_count: r.event_count
            }) as conflicts,
            collect(DISTINCT other.name) as engaged_actors
        """
        
        with self.driver.session() as session:
            result = session.run(query, actor_name=actor_name)
            record = result.single()
            
            if record:
                return dict(record)
        
        return None
    
    def find_all_actors(self, limit: int = 100) -> List[str]:
        """
        Obtener lista de todos los actores
        
        Returns:
            Lista de nombres de actores
        """
        query = """
        MATCH (a:Actor)
        RETURN a.name as name
        ORDER BY a.name
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [record["name"] for record in result]
    
    def find_top_actors_by_deaths(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtener actores más letales
        
        Returns:
            Lista de dicts con: name, total_deaths, conflict_count
        """
        query = """
        MATCH (a:Actor)-[r:PARTICIPATED_IN]->(:Conflict)
        RETURN 
            a.name as name,
            sum(r.cumulative_deaths) as total_deaths,
            count(DISTINCT r.conflict) as conflict_count
        ORDER BY total_deaths DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def find_actor_network(
        self,
        actor_name: str,
        max_depth: int = 2
    ) -> List[str]:
        """
        Obtener red de actores relacionados
        
        Args:
            actor_name: Nombre del actor central
            max_depth: Profundidad máxima de búsqueda (1-5)
            
        Returns:
            Lista de nombres de actores relacionados
        """
        # Validar depth (1-5)
        max_depth = max(1, min(max_depth, 5))
        
        query = """
        MATCH path = (a:Actor {name: $actor_name})-[*1..5]-(related:Actor)
        WHERE a <> related AND length(path) <= $max_depth
        RETURN DISTINCT related.name as actor_name
        LIMIT 100
        """
        
        with self.driver.session() as session:
            result = session.run(query, actor_name=actor_name, max_depth=max_depth)
            return [record["actor_name"] for record in result]
    
    def find_actor_relationships(
        self,
        actor1: str,
        actor2: str
    ) -> List[Dict[str, Any]]:
        """
        Obtener relaciones ENGAGED_WITH entre dos actores
        
        Returns:
            Lista de dicts con: conflict, total_deaths, total_length, encounter_count
        """
        query = """
        MATCH (a1:Actor {name: $actor1})-[e:ENGAGED_WITH]-(a2:Actor {name: $actor2})
        RETURN 
            e.via_conflict as conflict,
            e.total_deaths as total_deaths,
            e.total_length as total_length,
            e.encounter_count as encounter_count
        """
        
        with self.driver.session() as session:
            result = session.run(query, actor1=actor1, actor2=actor2)
            return [dict(record) for record in result]
    
    # ======================================================
    # CONSULTAS DE CONFLICTOS
    # ======================================================
    
    def find_conflict_by_name(self, conflict_name: str) -> Optional[Dict[str, Any]]:
        """
        Buscar conflicto por nombre
        
        Returns:
            Dict con: name, type_of_violence, country, region, event_count, 
                     total_deaths, event_ids
        """
        query = """
        MATCH (c:Conflict {name: $conflict_name})
        RETURN 
            c.name as name,
            c.type_of_violence as type_of_violence,
            c.country as country,
            c.region as region,
            c.event_count as event_count,
            c.total_deaths as total_deaths,
            c.event_ids as event_ids
        """
        
        with self.driver.session() as session:
            result = session.run(query, conflict_name=conflict_name)
            record = result.single()
            
            if record:
                return dict(record)
        
        return None
    
    def find_conflict_event_ids(self, conflict_name: str) -> List[str]:
        """
        Obtener event_ids de un conflicto
        Útil para vincular con BigQuery/MongoDB
        
        Returns:
            Lista de event_ids
        """
        query = """
        MATCH (c:Conflict {name: $conflict_name})
        RETURN c.event_ids as event_ids
        """
        
        with self.driver.session() as session:
            result = session.run(query, conflict_name=conflict_name)
            record = result.single()
            
            if record and record["event_ids"]:
                return record["event_ids"]
        
        return []
    
    def find_conflict_with_actors(
        self,
        conflict_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener conflicto con actores involucrados
        
        Returns:
            Dict con: conflict_data (dict), actors (list of dicts)
        """
        query = """
        MATCH (c:Conflict {name: $conflict_name})
        OPTIONAL MATCH (a:Actor)-[r:PARTICIPATED_IN {conflict: $conflict_name}]->(c)
        RETURN 
            c.name as conflict_name,
            c.type_of_violence as type_of_violence,
            c.country as country,
            c.region as region,
            c.event_ids as event_ids,
            c.event_count as event_count,
            c.total_deaths as total_deaths,
            collect(DISTINCT {
                name: a.name,
                role: r.role,
                cumulative_deaths: r.cumulative_deaths,
                event_count: r.event_count
            }) as actors
        """
        
        with self.driver.session() as session:
            result = session.run(query, conflict_name=conflict_name)
            record = result.single()
            
            if record:
                return dict(record)
        
        return None
    
    def find_top_conflicts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtener top conflictos por muertes totales
        
        Returns:
            Lista de dicts con propiedades del conflicto
        """
        query = """
        MATCH (c:Conflict)
        WHERE c.total_deaths IS NOT NULL
        RETURN 
            c.name as name,
            c.type_of_violence as type_of_violence,
            c.country as country,
            c.region as region,
            c.event_count as event_count,
            c.total_deaths as total_deaths,
            c.event_ids as event_ids
        ORDER BY c.total_deaths DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def search_conflicts(
        self,
        search_term: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Buscar conflictos por nombre, país o región
        
        Returns:
            Lista de dicts con propiedades del conflicto
        """
        query = """
        MATCH (c:Conflict)
        WHERE 
            toLower(c.name) CONTAINS toLower($search_term)
            OR toLower(c.country) CONTAINS toLower($search_term)
            OR toLower(c.region) CONTAINS toLower($search_term)
        RETURN 
            c.name as name,
            c.type_of_violence as type_of_violence,
            c.country as country,
            c.region as region,
            c.event_count as event_count,
            c.total_deaths as total_deaths,
            c.event_ids as event_ids
        ORDER BY c.total_deaths DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, search_term=search_term, limit=limit)
            return [dict(record) for record in result]