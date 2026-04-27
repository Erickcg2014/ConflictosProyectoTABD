"""
Repositorio para acceso a datos geoespaciales en MongoDB.
Contiene todas las queries y retorna datos crudos (dicts/listas).
"""

from typing import List, Dict, Optional
import re
from app.integration.clients.mongodb_client import MongoDBClient


class MongoDBRepository:
    """Repositorio para operaciones de consulta geoespacial en MongoDB"""
    
    def __init__(self):
        """Inicializa el repositorio con el cliente MongoDB"""
        mongo_client = MongoDBClient()
        self.client = mongo_client.client
        self.collection = mongo_client.collection
    
    # ======================================================
    # CONSULTAS DE VERIFICACIÓN
    # ======================================================
    
    def check_connection(self) -> bool:
        """Verificar conexión a MongoDB"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"❌ MongoDB: Error de conexión: {e}")
            return False
    
    def count_documents(self) -> int:
        """Obtener total de documentos en la colección"""
        return self.collection.count_documents({})
    
    # ======================================================
    # CONSULTAS POR ID
    # ======================================================
    
    def find_by_event_id(self, event_id: str) -> Optional[Dict]:
        """
        Buscar ubicación por event_id
        
        Returns:
            Dict con documento completo o None
        """
        return self.collection.find_one({"event_id": event_id})
    
    def find_by_event_ids(self, event_ids: List[str]) -> List[Dict]:
        """
        Buscar ubicaciones de múltiples eventos
        Útil para vincular con BigQuery
        
        Args:
            event_ids: Lista de IDs de eventos
            
        Returns:
            Lista de documentos
        """
        query = {"event_id": {"$in": event_ids}}
        return list(self.collection.find(query))
    
    # ======================================================
    # CONSULTAS GEOESPACIALES
    # ======================================================
    
    def find_nearby(
        self,
        longitude: float,
        latitude: float,
        max_distance_meters: float,
        limit: int = 10
    ) -> List[Dict]:
        """
        Buscar eventos cercanos a un punto usando $near
        
        Args:
            longitude: Longitud del punto central
            latitude: Latitud del punto central
            max_distance_meters: Distancia máxima en metros
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos ordenados por proximidad
        """
        query = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude]
                    },
                    "$maxDistance": max_distance_meters
                }
            }
        }
        
        return list(self.collection.find(query).limit(limit))
    
    def find_in_bounding_box(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        limit: int = 500
    ) -> List[Dict]:
        """
        Buscar ubicaciones dentro de un bounding box
        Útil para cargar eventos visibles en el mapa
        
        Args:
            min_lon: Longitud mínima
            min_lat: Latitud mínima
            max_lon: Longitud máxima
            max_lat: Latitud máxima
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos dentro del área
        """
        query = {
            "location": {
                "$geoWithin": {
                    "$box": [
                        [min_lon, min_lat],
                        [max_lon, max_lat]
                    ]
                }
            }
        }
        
        return list(self.collection.find(query).limit(limit))
    
    # ======================================================
    # CONSULTAS POR ATRIBUTOS
    # ======================================================
    
    def find_by_country(self, country: str, limit: int = 100) -> List[Dict]:
        """
        Buscar eventos por país (case-insensitive)
        
        Args:
            country: Nombre del país
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos
        """
        safe_country = re.escape(country)
        query = {"country": {"$regex": safe_country, "$options": "i"}}
        return list(self.collection.find(query).limit(limit))
    
    def find_by_region(self, region: str, limit: int = 100) -> List[Dict]:
        """
        Buscar eventos por región (case-insensitive)
        
        Args:
            region: Nombre de la región
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos
        """
        safe_region = re.escape(region)
        query = {"region": {"$regex": safe_region, "$options": "i"}}
        return list(self.collection.find(query).limit(limit))
    
    def find_by_conflict_name(
        self,
        conflict_name: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Buscar ubicaciones por nombre de conflicto
        Útil para mapear conflictos específicos
        
        Args:
            conflict_name: Nombre del conflicto
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos
        """
        safe_name = re.escape(conflict_name)
        query = {"conflict_name": {"$regex": safe_name, "$options": "i"}}
        return list(self.collection.find(query).limit(limit))
    
    # ======================================================
    # CONSULTAS DE VALORES ÚNICOS
    # ======================================================
    
    def get_distinct_countries(self) -> List[str]:
        """
        Obtener lista de todos los países únicos
        
        Returns:
            Lista ordenada de países
        """
        countries = self.collection.distinct("country")
        return sorted([c for c in countries if c])
    
    def get_distinct_regions(self) -> List[str]:
        """
        Obtener lista de todas las regiones únicas
        
        Returns:
            Lista ordenada de regiones
        """
        regions = self.collection.distinct("region")
        return sorted([r for r in regions if r])
    
    # ======================================================
    # CONSULTAS AGREGADAS (CLUSTERING)
    # ======================================================
    
    def aggregate_clusters(
        self,
        precision: int,
        bounds: Optional[Dict[str, float]] = None,
        limit: int = 1000
    ) -> List[Dict]:

        # MongoDB precision < 2 en round → lo forzamos
        safe_precision = max(2, min(precision, 16))

        pipeline = []

        # Validar bounds correctamente 
        if bounds and all(v is not None for v in bounds.values()):
            pipeline.append({
                "$match": {
                    "location": {
                        "$geoWithin": {
                            "$box": [
                                [bounds["min_lon"], bounds["min_lat"]],
                                [bounds["max_lon"], bounds["max_lat"]]
                            ]
                        }
                    }
                }
            })

        pipeline.append({
            "$match": {
                "location.type": "Point",
                "location.coordinates": {"$size": 2}
            }
        })

        # PIPELINE PRINCIPAL
        pipeline.extend([
            {
                "$project": {
                    "event_id": 1,
                    "conflict_name": 1,
                    "country": 1,
                    "lon": {"$arrayElemAt": ["$location.coordinates", 0]},
                    "lat": {"$arrayElemAt": ["$location.coordinates", 1]},
                }
            },
            {
                "$group": {
                    "_id": {
                        "lon": {"$round": ["$lon", safe_precision]},
                        "lat": {"$round": ["$lat", safe_precision]},
                    },
                    "count": {"$sum": 1},
                    "event_ids": {"$push": "$event_id"},
                    "conflicts": {"$addToSet": "$conflict_name"},
                    "countries": {"$addToSet": "$country"},
                }
            },
            {
                "$project": {
                    "longitude": "$_id.lon",
                    "latitude": "$_id.lat",
                    "count": 1,
                    "event_ids": {"$slice": ["$event_ids", 10]},
                    "conflicts": {"$slice": ["$conflicts", 5]},
                    "countries": 1,
                }
            },
            {"$limit": limit},
        ])

        return list(self.collection.aggregate(pipeline))
