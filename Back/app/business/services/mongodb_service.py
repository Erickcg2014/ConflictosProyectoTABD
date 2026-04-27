"""
Servicio para consultas geoespaciales en MongoDB.
Maneja la lógica de negocio y transformación de datos a modelos de dominio.
"""

from typing import List, Dict, Optional
from app.integration.repositories.mongodb_repository import MongoDBRepository
from app.business.models.schemas import WarLocation, GeoLocation


class MongoDBService:
    """Servicio para manejar operaciones geoespaciales de conflictos"""
    
    def __init__(self):
        """Inicializa el servicio con el repositorio"""
        self.repository = MongoDBRepository()
    
    # ======================================================
    # VERIFICACIÓN Y ESTADÍSTICAS
    # ======================================================
    
    def check_connection(self) -> bool:
        """Verificar conexión a MongoDB"""
        print(f"🔍 MongoDB: Verificando conexión...")
        is_connected = self.repository.check_connection()
        if is_connected:
            print("✅ MongoDB: Conexión exitosa")
        else:
            print("❌ MongoDB: Error de conexión")
        return is_connected
    
    def get_location_count(self) -> int:
        """Obtener total de ubicaciones en la colección"""
        return self.repository.count_documents()
    
    # ======================================================
    # CONSULTAS POR ID
    # ======================================================
    
    def get_location_by_event_id(self, event_id: str) -> Optional[WarLocation]:
        """
        Obtener ubicación de un evento específico
        
        Args:
            event_id: ID del evento
            
        Returns:
            WarLocation o None si no existe
        """
        doc = self.repository.find_by_event_id(event_id)
        if doc:
            return self._doc_to_location(doc)
        return None
    
    def get_locations_by_event_ids(self, event_ids: List[str]) -> List[WarLocation]:
        """
        Obtener ubicaciones de múltiples eventos
        Útil para vincular con BigQuery
        
        Args:
            event_ids: Lista de IDs de eventos
            
        Returns:
            Lista de ubicaciones
        """
        docs = self.repository.find_by_event_ids(event_ids)
        return [self._doc_to_location(doc) for doc in docs]
    
    # ======================================================
    # CONSULTAS GEOESPACIALES
    # ======================================================
    
    def search_nearby_events(
        self,
        longitude: float,
        latitude: float,
        max_distance_km: float = 100,
        limit: int = 10
    ) -> List[WarLocation]:
        """
        Buscar eventos cercanos usando geocercas
        
        Args:
            longitude: Longitud del punto central
            latitude: Latitud del punto central
            max_distance_km: Distancia máxima en kilómetros
            limit: Número máximo de resultados
            
        Returns:
            Lista de ubicaciones ordenadas por proximidad
        """
        # Convertir distancia de km a metros
        max_distance_meters = max_distance_km * 1000
        
        docs = self.repository.find_nearby(
            longitude=longitude,
            latitude=latitude,
            max_distance_meters=max_distance_meters,
            limit=limit
        )
        
        return [self._doc_to_location(doc) for doc in docs]
    
    def get_locations_in_bounds(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        limit: int = 500
    ) -> List[WarLocation]:
        """
        Obtener ubicaciones dentro de un bounding box
        Útil para cargar eventos visibles en el mapa
        
        Args:
            min_lon: Longitud mínima
            min_lat: Latitud mínima
            max_lon: Longitud máxima
            max_lat: Latitud máxima
            limit: Número máximo de resultados
            
        Returns:
            Lista de ubicaciones dentro del área
        """
        docs = self.repository.find_in_bounding_box(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            limit=limit
        )
        
        return [self._doc_to_location(doc) for doc in docs]
    
    # ======================================================
    # CONSULTAS POR ATRIBUTOS
    # ======================================================
    
    def search_by_country(self, country: str, limit: int = 100) -> List[WarLocation]:
        """
        Buscar eventos por país
        
        Args:
            country: Nombre del país
            limit: Número máximo de resultados
            
        Returns:
            Lista de ubicaciones del país
        """
        docs = self.repository.find_by_country(country, limit)
        return [self._doc_to_location(doc) for doc in docs]
    
    def search_by_region(self, region: str, limit: int = 100) -> List[WarLocation]:
        """
        Buscar eventos por región
        
        Args:
            region: Nombre de la región
            limit: Número máximo de resultados
            
        Returns:
            Lista de ubicaciones de la región
        """
        docs = self.repository.find_by_region(region, limit)
        return [self._doc_to_location(doc) for doc in docs]
    
    def search_by_conflict_name(
        self,
        conflict_name: str,
        limit: int = 50
    ) -> List[WarLocation]:
        """
        Buscar ubicaciones por nombre de conflicto
        Útil para mapear conflictos específicos
        
        Args:
            conflict_name: Nombre del conflicto
            limit: Número máximo de resultados
            
        Returns:
            Lista de ubicaciones del conflicto
        """
        docs = self.repository.find_by_conflict_name(conflict_name, limit)
        return [self._doc_to_location(doc) for doc in docs]
    
    
    def get_all_countries(self) -> List[str]:
        """
        Obtener lista de todos los países únicos
        
        Returns:
            Lista ordenada de países
        """
        return self.repository.get_distinct_countries()
    
    def get_all_regions(self) -> List[str]:
        """
        Obtener lista de todas las regiones únicas
        
        Returns:
            Lista ordenada de regiones
        """
        return self.repository.get_distinct_regions()
    
    # CLUSTERING PARA MAPAS
    
    def get_cluster_data(
        self,
        zoom_level: int,
        bounds: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Obtener datos agregados para clustering en el mapa
        Optimiza la visualización en mapas con muchos puntos
        
        Args:
            zoom_level: Nivel de zoom del mapa (1-18)
            bounds: Límites del mapa visible (opcional)
                   {"min_lon": float, "min_lat": float, 
                    "max_lon": float, "max_lat": float}
            
        Returns:
            Lista de clusters con conteo de eventos
        """
        # Determinar precisión de clustering según zoom
        # A menor zoom (más alejado), menor precisión (más agrupamiento)
        precision = max(1, 10 - zoom_level // 2)
        
        return self.repository.aggregate_clusters(
            precision=precision,
            bounds=bounds,
            limit=1000
        )
    
    # ======================================================
    # TRANSFORMACIÓN DE DATOS
    # ======================================================
    
    def _doc_to_location(self, doc: Dict) -> WarLocation:
        """
        Convertir documento de MongoDB a modelo WarLocation
        
        Args:
            doc: Documento de MongoDB
            
        Returns:
            Modelo WarLocation del dominio
        """
        location = doc.get("location", {})
        return WarLocation(
            event_id=doc.get("event_id"),
            conflict_name=doc.get("conflict_name"),
            country=doc.get("country"),
            region=doc.get("region"),
            location=GeoLocation(
                type=location.get("type", "Point"),
                coordinates=location.get("coordinates", [])
            )
        )