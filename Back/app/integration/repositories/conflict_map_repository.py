# integration/repositories/conflict_map_repository.py
"""
Repositorio para acceso a datos del grafo de conflictos en Neo4j.
Contiene todas las queries de Cypher y retorna datos crudos (dicts/listas).
"""

from typing import List, Dict, Any, Optional
from neo4j import Session
from app.integration.clients.conflict_map_client import ConflictMapClient


class ConflictMapRepository:
    """Repositorio para operaciones de consulta del grafo de conflictos"""
    
    def __init__(self):
        """Inicializa el repositorio con el cliente Neo4j"""
        client = ConflictMapClient()
        self.driver = client.driver
        self.database = client.database_name
    
    # ======================================================
    # CONSULTAS PARA FILTROS
    # ======================================================
    
    def find_countries_for_filter(
        self,
        search: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Buscar países disponibles para filtro
        
        Returns:
            Lista de dicts con: name, conflict_count, total_deaths
        """
        query = """
        MATCH (c:Country)-[r:CONFLICT_WITH]-()
        WHERE $search IS NULL OR c.name CONTAINS $search
        WITH c, count(DISTINCT r) as conflict_count, sum(r.total_deaths) as total_deaths
        RETURN c.name as name,
               conflict_count,
               total_deaths
        ORDER BY conflict_count DESC
        LIMIT $limit
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, search=search, limit=limit)
            return [dict(record) for record in result]
    
    def find_actors_for_filter(
        self,
        search: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Buscar actores disponibles para filtro
        
        Returns:
            Lista de dicts con: name, conflict_count, total_deaths
        """
        query = """
        MATCH (a:Actor)-[r:ENGAGED_WITH]-()
        WHERE $search IS NULL OR a.name CONTAINS $search
        WITH a, count(DISTINCT r) as conflict_count, sum(r.total_deaths) as total_deaths
        RETURN a.name as name,
               conflict_count,
               total_deaths
        ORDER BY conflict_count DESC
        LIMIT $limit
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, search=search, limit=limit)
            return [dict(record) for record in result]
    
    # ======================================================
    # CONSULTAS PARA GRAFO DE PAÍSES
    # ======================================================
    
    def check_country_exists(self, country_name: str) -> List[str]:
        """
        Verificar si un país existe (búsqueda aproximada)
        
        Returns:
            Lista de países similares encontrados
        """
        query = """
        MATCH (p:Country)
        WHERE toLower(p.name) CONTAINS toLower($partial_name)
        RETURN p.name as name
        LIMIT 5
        """
        
        partial_name = country_name[:5] if len(country_name) >= 5 else country_name
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, partial_name=partial_name)
            return [record["name"] for record in result]
    
    def find_country_graph(self, country_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtener grafo de relaciones de un país
        
        Returns:
            Dict con: center_name, center_region, center_connections, center_deaths,
                     neighbors (list), relationships (list)
        """
        query = """
        // Buscar país (case-insensitive)
        MATCH (center:Country)
        WHERE toLower(center.name) = toLower($country_name)

        // Obtener vecinos directos
        MATCH (center)-[r:CONFLICT_WITH]-(neighbor:Country)

        // Calcular estadísticas del centro directamente
        WITH center, neighbor, r,
            size([(center)-[rc:CONFLICT_WITH]-() | rc]) as center_connections
        WITH center, neighbor, r, center_connections,
            [(center)-[rc:CONFLICT_WITH]-() | rc.total_deaths] as center_death_list
        WITH center, neighbor, r, center_connections,
            reduce(total = 0, d IN center_death_list | total + COALESCE(d, 0)) as center_deaths

        // Calcular estadísticas de vecinos
        WITH center, neighbor, r, center_connections, center_deaths,
            size([(neighbor)-[rn:CONFLICT_WITH]-() | rn]) as neighbor_connections
        WITH center, neighbor, r, center_connections, center_deaths, neighbor_connections,
            [(neighbor)-[rn:CONFLICT_WITH]-() | rn.total_deaths] as neighbor_death_list
        WITH center, neighbor, r, center_connections, center_deaths, neighbor_connections,
            reduce(total = 0, d IN neighbor_death_list | total + COALESCE(d, 0)) as neighbor_deaths

        RETURN 
            center.name as center_name,
            center.region as center_region,
            center_connections,
            center_deaths,
            
            collect(DISTINCT {
                name: neighbor.name,
                region: neighbor.region,
                connections: neighbor_connections,
                total_deaths: neighbor_deaths
            }) as neighbors,
            
            collect(DISTINCT {
                source: center.name,
                target: neighbor.name,
                total_deaths: r.total_deaths,
                event_count: r.event_count,
                conflict_names: r.conflict_names,
                actors_involved: r.actors_involved
            }) as relationships
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, country_name=country_name)
            record = result.single()
            return dict(record) if record else None
    
    # ======================================================
    # CONSULTAS PARA GRAFO DE ACTORES
    # ======================================================
    
    def find_actor_graph(self, actor_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtener grafo de relaciones de un actor
        
        Returns:
            Dict con: center_name, center_connections, center_deaths, center_encounters,
                     neighbors (list), relationships (list)
        """
        query = """
        // Buscar actor (case-insensitive)
        MATCH (center:Actor)
        WHERE toLower(center.name) = toLower($actor_name)

        // Obtener vecinos directos (actores enfrentados)
        MATCH (center)-[r:ENGAGED_WITH]-(neighbor:Actor)

        // Calcular estadísticas del centro
        WITH center, neighbor, r,
            size([(center)-[rc:ENGAGED_WITH]-() | rc]) as center_connections
        WITH center, neighbor, r, center_connections,
            [(center)-[rc:ENGAGED_WITH]-() | rc.total_deaths] as center_death_list,
            [(center)-[rc:ENGAGED_WITH]-() | rc.encounter_count] as center_encounter_list
        WITH center, neighbor, r, center_connections,
            reduce(total = 0, d IN center_death_list | total + COALESCE(d, 0)) as center_deaths,
            reduce(total = 0, e IN center_encounter_list | total + COALESCE(e, 0)) as center_encounters

        // Calcular estadísticas de vecinos
        WITH center, neighbor, r, center_connections, center_deaths, center_encounters,
            size([(neighbor)-[rn:ENGAGED_WITH]-() | rn]) as neighbor_connections
        WITH center, neighbor, r, center_connections, center_deaths, center_encounters, neighbor_connections,
            [(neighbor)-[rn:ENGAGED_WITH]-() | rn.total_deaths] as neighbor_death_list,
            [(neighbor)-[rn:ENGAGED_WITH]-() | rn.encounter_count] as neighbor_encounter_list
        WITH center, neighbor, r, center_connections, center_deaths, center_encounters, neighbor_connections,
            reduce(total = 0, d IN neighbor_death_list | total + COALESCE(d, 0)) as neighbor_deaths,
            reduce(total = 0, e IN neighbor_encounter_list | total + COALESCE(e, 0)) as neighbor_encounters

        RETURN 
            center.name as center_name,
            center_connections,
            center_deaths,
            center_encounters,
            
            collect(DISTINCT {
                name: neighbor.name,
                connections: neighbor_connections,
                total_deaths: neighbor_deaths,
                encounter_count: neighbor_encounters
            }) as neighbors,
            
            collect(DISTINCT {
                source: center.name,
                target: neighbor.name,
                total_deaths: r.total_deaths,
                encounter_count: r.encounter_count,
                via_conflict: r.via_conflict,
                total_length: r.total_length
            }) as relationships
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, actor_name=actor_name)
            record = result.single()
            return dict(record) if record else None
    
    # ======================================================
    # CONSULTAS PARA DETALLES DE PAÍSES
    # ======================================================
    
    def find_country_statistics(self, country_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtener estadísticas generales de un país
        
        Returns:
            Dict con: name, region, connections, total_deaths, total_events, total_conflicts
        """
        query = """
        MATCH (c:Country)
        WHERE toLower(c.name) = toLower($country_name)
        OPTIONAL MATCH (c)-[r:CONFLICT_WITH]-()
        OPTIONAL MATCH (c)-[:HAS_CONFLICT]->(conf:Conflict)
        
        RETURN 
            c.name as name,
            c.region as region,
            count(DISTINCT r) as connections,
            sum(r.total_deaths) as total_deaths,
            sum(r.event_count) as total_events,
            count(DISTINCT conf) as total_conflicts
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, country_name=country_name)
            record = result.single()
            return dict(record) if record else None
    
    def find_country_top_conflicts(
        self,
        country_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtener top conflictos de un país
        
        Returns:
            Lista de dicts con: name, deaths, events
        """
        query = """
        MATCH (c:Country)
        WHERE toLower(c.name) = toLower($country_name)
        MATCH (c)-[:HAS_CONFLICT]->(conf:Conflict)
        RETURN conf.name as name,
            conf.total_deaths as deaths,
            conf.event_count as events
        ORDER BY deaths DESC
        LIMIT $limit
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, country_name=country_name, limit=limit)
            return [dict(record) for record in result]
    
    def find_country_connected_entities(
        self,
        country_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtener países conectados
        
        Returns:
            Lista de dicts con: name, shared_conflicts, shared_deaths
        """
        query = """
        MATCH (c:Country)
        WHERE toLower(c.name) = toLower($country_name)
        MATCH (c)-[r:CONFLICT_WITH]-(other:Country)
        RETURN other.name as name,
            size(r.conflict_names) as shared_conflicts,
            r.total_deaths as shared_deaths
        ORDER BY shared_deaths DESC
        LIMIT $limit
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, country_name=country_name, limit=limit)
            return [dict(record) for record in result]
    
    def find_country_actors_involved(
        self,
        country_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtener actores involucrados en conflictos del país
        
        Returns:
            Lista de dicts con: name, participation_count, deaths_caused
        """
        query = """
        MATCH (c:Country)
        WHERE toLower(c.name) = toLower($country_name)
        MATCH (c)-[:HAS_CONFLICT]->(conf:Conflict)
        MATCH (a:Actor)-[p:PARTICIPATED_IN]->(conf)
        WITH a, count(p) as participation_count, sum(p.cumulative_deaths) as deaths_caused
        RETURN a.name as name,
            participation_count,
            deaths_caused
        ORDER BY participation_count DESC
        LIMIT $limit
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, country_name=country_name, limit=limit)
            return [dict(record) for record in result]
    
    # ======================================================
    # CONSULTAS PARA DETALLES DE ACTORES
    # ======================================================
    
    def find_actor_statistics(self, actor_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtener estadísticas generales de un actor
        
        Returns:
            Dict con: name, connections, total_deaths, total_encounters, 
                     total_conflicts, countries_active
        """
        query = """
        MATCH (a:Actor)
        WHERE toLower(a.name) = toLower($actor_name)
        OPTIONAL MATCH (a)-[r:ENGAGED_WITH]-()
        OPTIONAL MATCH (a)-[:PARTICIPATED_IN]->(conf:Conflict)
        OPTIONAL MATCH (conf)<-[:HAS_CONFLICT]-(country:Country)
        
        RETURN 
            a.name as name,
            count(DISTINCT r) as connections,
            sum(r.total_deaths) as total_deaths,
            sum(r.encounter_count) as total_encounters,
            count(DISTINCT conf) as total_conflicts,
            count(DISTINCT country) as countries_active
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, actor_name=actor_name)
            record = result.single()
            return dict(record) if record else None
    
    def find_actor_top_conflicts(
        self,
        actor_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtener top conflictos de un actor
        
        Returns:
            Lista de dicts con: name, deaths, encounters
        """
        query = """
        MATCH (a:Actor)
        WHERE toLower(a.name) = toLower($actor_name)
        MATCH (a)-[p:PARTICIPATED_IN]->(conf:Conflict)
        RETURN conf.name as name,
            sum(p.cumulative_deaths) as deaths,
            count(p) as encounters
        ORDER BY deaths DESC
        LIMIT $limit
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, actor_name=actor_name, limit=limit)
            return [dict(record) for record in result]
    
    def find_actor_enemies(
        self,
        actor_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtener enemigos de un actor (actores enfrentados)
        
        Returns:
            Lista de dicts con: name, encounters, deaths
        """
        query = """
        MATCH (a:Actor)
        WHERE toLower(a.name) = toLower($actor_name)
        MATCH (a)-[r:ENGAGED_WITH]-(enemy:Actor)
        RETURN enemy.name as name,
            r.encounter_count as encounters,
            r.total_deaths as deaths
        ORDER BY encounters DESC
        LIMIT $limit
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, actor_name=actor_name, limit=limit)
            return [dict(record) for record in result]