# business/services/conflict_map_service.py
"""
Servicio para el sistema de visualización de grafo de conflictos.
Maneja la lógica de negocio y transformación de datos a modelos de dominio.
"""

from typing import List, Optional
from app.integration.repositories.conflict_map_repository import ConflictMapRepository
from app.business.models.conflict_schema import (
    GraphFilterType,
    FiltersResponse,
    FilterItem,
    GraphResponse,
    GraphNode,
    GraphEdge,
    GraphSummary,
    NodeMetrics,
    EdgeMetrics,
    NodeDetails,
    NodeStatistics,
    ConflictSummary,
    ConnectedEntity,
    ActorParticipation
)


class ConflictMapService:
    """Servicio para manejar operaciones del grafo de conflictos"""
    
    def __init__(self):
        """Inicializa el servicio con el repositorio"""
        self.repository = ConflictMapRepository()
    
    # OBTENER FILTROS
    async def get_filters(
        self,
        filter_type: GraphFilterType,
        search: Optional[str] = None,
        limit: int = 100
    ) -> FiltersResponse:
        """
        Obtiene lista de países o actores disponibles para filtro.
        
        Args:
            filter_type: Tipo de filtro (country o actor)
            search: Término de búsqueda opcional
            limit: Límite de resultados (default: 100)
        
        Returns:
            FiltersResponse con lista de items disponibles
        """
        # Obtener datos del repositorio
        if filter_type == GraphFilterType.COUNTRY:
            raw_items = self.repository.find_countries_for_filter(search, limit)
        else:  
            raw_items = self.repository.find_actors_for_filter(search, limit)
        
        # Transformar a modelo de dominio
        items = [
            FilterItem(
                value=item["name"],
                label=item["name"],
                conflict_count=item["conflict_count"] or 0,
                total_deaths=item["total_deaths"] or 0
            )
            for item in raw_items
        ]
        
        # Construir respuesta
        return FiltersResponse(
            type=filter_type,
            count=len(items),
            items=items
        )
    
    # OBTENER GRAFO PARA PAÍS
    
    async def get_graph_for_country(
        self,
        country_name: str,
        depth: int = 1
    ) -> GraphResponse:
        """
        Construye grafo de países conectados con el país especificado.
        
        Args:
            country_name: Nombre del país central
            depth: Profundidad del grafo (1 o 2)
        
        Returns:
            GraphResponse con nodos, aristas y resumen
        """
        print(f"🔍 get_graph_for_country()")
        print(f"   Buscando país: '{country_name}'")
        print(f"   Depth: {depth}")
        
        # 1. Verificar si el país existe (búsqueda aproximada)
        similar_countries = self.repository.check_country_exists(country_name)
        
        if similar_countries:
            print(f"   Países similares en DB: {similar_countries}")
        else:
            print(f"   ⚠️ No se encontraron países similares a '{country_name}'")
        
        # 2. Obtener datos del grafo
        graph_data = self.repository.find_country_graph(country_name)
        
        if not graph_data:
            print(f"❌ País '{country_name}' no encontrado en Neo4j")
            if similar_countries:
                raise ValueError(
                    f"Country '{country_name}' not found. "
                    f"Similar countries: {', '.join(similar_countries)}"
                )
            else:
                raise ValueError(f"Country '{country_name}' not found")
        
        print(f"País encontrado: {graph_data['center_name']}")
        print(f"   Región: {graph_data['center_region']}")
        print(f"   Conexiones: {graph_data['center_connections']}")
        print(f"   Vecinos: {len(graph_data['neighbors'])}")
        
        # Construir nodo central
        center_node = GraphNode(
            id=graph_data["center_name"],
            label=graph_data["center_name"],
            type="country",
            region=graph_data["center_region"],
            metrics=NodeMetrics(
                total_conflicts=graph_data["center_connections"] or 0,
                total_deaths=graph_data["center_deaths"] or 0,
                connections=graph_data["center_connections"] or 0
            )
        )
        
        # 4. Construir nodos vecinos (filtrar self-loops)
        nodes = []
        for neighbor_data in graph_data["neighbors"]:
            # SKIP self-loops
            if neighbor_data["name"] == graph_data["center_name"]:
                continue
            
            node = GraphNode(
                id=neighbor_data["name"],
                label=neighbor_data["name"],
                type="country",
                region=neighbor_data["region"],
                metrics=NodeMetrics(
                    total_conflicts=neighbor_data["connections"] or 0,
                    total_deaths=neighbor_data["total_deaths"] or 0,
                    connections=neighbor_data["connections"] or 0
                )
            )
            nodes.append(node)
        
        # 5. Construir aristas (filtrar self-loops)
        edges = []
        total_deaths_sum = 0
        total_conflicts_set = set()
        
        for rel_data in graph_data["relationships"]:
            if rel_data['source'] == rel_data['target']:
                print(f"   ⚠️ Skipping self-loop: {rel_data['source']} → {rel_data['target']}")
                continue
            
            edge_id = f"{rel_data['source']}-{rel_data['target']}"
            weight = rel_data["total_deaths"] or 0
            total_deaths_sum += weight
            
            conflict_names = rel_data.get("conflict_names", []) or []
            total_conflicts_set.update(conflict_names)
            
            edge = GraphEdge(
                id=edge_id,
                source=rel_data["source"],
                target=rel_data["target"],
                weight=weight,
                metrics=EdgeMetrics(
                    event_count=rel_data.get("event_count", 0),
                    conflict_names=conflict_names,
                    actors_involved=rel_data.get("actors_involved", [])
                )
            )
            edges.append(edge)
        
        print(f"   Edges creados: {len(edges)}")
        print(f"   Total deaths: {total_deaths_sum}")
        
        # 6. Construir resumen
        summary = GraphSummary(
            total_nodes=len(nodes) + 1,
            total_edges=len(edges),
            total_deaths=total_deaths_sum,
            total_conflicts=len(total_conflicts_set),
            depth=depth
        )
        
        return GraphResponse(
            center_node=center_node,
            nodes=nodes,
            edges=edges,
            summary=summary
        )
    
    # OBTENER GRAFO PARA ACTOR
    
    async def get_graph_for_actor(
        self,
        actor_name: str,
        depth: int = 1
    ) -> GraphResponse:
        """
        Construye grafo de actores conectados con el actor especificado.
        
        Args:
            actor_name: Nombre del actor central
            depth: Profundidad del grafo (1 o 2)
        
        Returns:
            GraphResponse con nodos, aristas y resumen
        """
        print(f"🔍 get_graph_for_actor()")
        print(f"   Buscando actor: '{actor_name}'")
        print(f"   Depth: {depth}")
        
        # 1. Obtener datos del grafo
        graph_data = self.repository.find_actor_graph(actor_name)
        
        if not graph_data:
            print(f"❌ Actor '{actor_name}' no encontrado en Neo4j")
            raise ValueError(f"Actor '{actor_name}' not found")
        
        print(f"✅ Actor encontrado: {graph_data['center_name']}")
        print(f"   Conexiones: {graph_data['center_connections']}")
        print(f"   Vecinos: {len(graph_data['neighbors'])}")
        
        # 2. Construir nodo central
        center_node = GraphNode(
            id=graph_data["center_name"],
            label=graph_data["center_name"],
            type="actor",
            region=None,
            metrics=NodeMetrics(
                total_conflicts=graph_data["center_connections"] or 0,
                total_deaths=graph_data["center_deaths"] or 0,
                connections=graph_data["center_connections"] or 0,
                encounter_count=graph_data["center_encounters"] or 0
            )
        )
        
        # 3. Construir nodos vecinos (filtrar self-loops)
        nodes = []
        for neighbor_data in graph_data["neighbors"]:
            if neighbor_data["name"] == graph_data["center_name"]:
                continue
            
            node = GraphNode(
                id=neighbor_data["name"],
                label=neighbor_data["name"],
                type="actor",
                region=None,
                metrics=NodeMetrics(
                    total_conflicts=neighbor_data["connections"] or 0,
                    total_deaths=neighbor_data["total_deaths"] or 0,
                    connections=neighbor_data["connections"] or 0,
                    encounter_count=neighbor_data.get("encounter_count", 0)
                )
            )
            nodes.append(node)
        
        # 4. Construir aristas (filtrar self-loops)
        edges = []
        total_deaths_sum = 0
        total_encounters = 0
        
        for rel_data in graph_data["relationships"]:
            if rel_data['source'] == rel_data['target']:
                print(f"   ⚠️ Skipping self-loop: {rel_data['source']} → {rel_data['target']}")
                continue
            
            edge_id = f"{rel_data['source']}-{rel_data['target']}"
            weight = rel_data["total_deaths"] or 0
            encounter_count = rel_data.get("encounter_count", 0)
            
            total_deaths_sum += weight
            total_encounters += encounter_count
            
            edge = GraphEdge(
                id=edge_id,
                source=rel_data["source"],
                target=rel_data["target"],
                weight=weight,
                metrics=EdgeMetrics(
                    encounter_count=encounter_count,
                    via_conflict=rel_data.get("via_conflict"),
                    total_length=rel_data.get("total_length", 0)
                )
            )
            edges.append(edge)
        
        print(f"   Edges creados: {len(edges)}")
        print(f"   Total deaths: {total_deaths_sum}")
        
        # 5. Construir resumen
        summary = GraphSummary(
            total_nodes=len(nodes) + 1,
            total_edges=len(edges),
            total_deaths=total_deaths_sum,
            total_conflicts=total_encounters, 
            depth=depth
        )
        
        return GraphResponse(
            center_node=center_node,
            nodes=nodes,
            edges=edges,
            summary=summary
        )
    
    # OBTENER DETALLES DE NODO 
    
    async def get_node_details(
        self,
        node_type: GraphFilterType,
        node_value: str
    ) -> NodeDetails:
        """
        Obtiene detalles de un nodo específico (país o actor).
        
        Args:
            node_type: Tipo de nodo (country o actor)
            node_value: Nombre del país o actor
        
        Returns:
            NodeDetails con información detallada
        """
        print(f"🔍 get_node_details()")
        print(f"   Type: {node_type}")
        print(f"   Value: '{node_value}'")
        
        if node_type == GraphFilterType.COUNTRY:
            return await self._get_country_details(node_value)
        else:
            return await self._get_actor_details(node_value)
    
    # OBTENER DETALLES DE NODO (PAÍS)
    
    async def _get_country_details(self, country_name: str) -> NodeDetails:
        """Obtiene detalles de un país específico"""
        
        # 1. Obtener estadísticas generales
        stats = self.repository.find_country_statistics(country_name)
        
        if not stats:
            raise ValueError(f"Country '{country_name}' not found")
        
        # 2. Obtener top conflictos
        raw_conflicts = self.repository.find_country_top_conflicts(country_name, limit=10)
        top_conflicts = [
            ConflictSummary(
                name=record["name"],
                deaths=record["deaths"] or 0,
                events=record["events"] or 0
            )
            for record in raw_conflicts
        ]
        
        # 3. Obtener países conectados
        raw_connected = self.repository.find_country_connected_entities(country_name, limit=10)
        connected_entities = [
            ConnectedEntity(
                name=record["name"],
                shared_conflicts=record["shared_conflicts"] or 0,
                shared_deaths=record["shared_deaths"] or 0
            )
            for record in raw_connected
        ]
        
        # 4. Obtener actores involucrados
        raw_actors = self.repository.find_country_actors_involved(country_name, limit=10)
        actors_involved = [
            ActorParticipation(
                name=record["name"],
                participation_count=record["participation_count"] or 0,
                deaths_caused=record["deaths_caused"] or 0
            )
            for record in raw_actors
        ]
        
        # 5. Construir respuesta
        return NodeDetails(
            type="country",
            name=stats["name"],
            region=stats["region"],
            statistics=NodeStatistics(
                total_conflicts=stats["total_conflicts"] or 0,
                total_deaths=stats["total_deaths"] or 0,
                total_events=stats["total_events"] or 0,
                connections=stats["connections"] or 0
            ),
            top_conflicts=top_conflicts,
            connected_entities=connected_entities,
            actors_involved=actors_involved
        )
    
    # OBTENER DETALLES DE NODO (ACTOR)
    
    async def _get_actor_details(self, actor_name: str) -> NodeDetails:
        """Obtiene detalles de un actor específico"""
        
        # 1. Obtener estadísticas generales
        stats = self.repository.find_actor_statistics(actor_name)
        
        if not stats:
            raise ValueError(f"Actor '{actor_name}' not found")
        
        # 2. Obtener top conflictos
        raw_conflicts = self.repository.find_actor_top_conflicts(actor_name, limit=10)
        top_conflicts = [
            ConflictSummary(
                name=record["name"],
                deaths=record["deaths"] or 0,
                encounters=record["encounters"] or 0
            )
            for record in raw_conflicts
        ]
        
        # 3. Obtener enemigos (actores enfrentados)
        raw_enemies = self.repository.find_actor_enemies(actor_name, limit=10)
        connected_entities = [
            ConnectedEntity(
                name=record["name"],
                encounters=record["encounters"] or 0,
                deaths=record["deaths"] or 0
            )
            for record in raw_enemies
        ]
        
        # 4. Construir respuesta
        return NodeDetails(
            type="actor",
            name=stats["name"],
            region=None,
            statistics=NodeStatistics(
                total_conflicts=stats["total_conflicts"] or 0,
                total_deaths=stats["total_deaths"] or 0,
                total_encounters=stats["total_encounters"] or 0,
                connections=stats["connections"] or 0,
                countries_active=stats["countries_active"] or 0
            ),
            top_conflicts=top_conflicts,
            connected_entities=connected_entities,
            actors_involved=None
        )