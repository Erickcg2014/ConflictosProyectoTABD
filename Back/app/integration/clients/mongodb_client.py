"""
Cliente singleton para conexión a MongoDB Atlas.
Maneja la configuración y ciclo de vida del cliente.
"""

from pymongo import MongoClient, GEOSPHERE
from pymongo.database import Database
from pymongo.collection import Collection
from app.config import settings


class MongoDBClient:
    """Cliente singleton para MongoDB Atlas"""
    _instance = None
    _client: MongoClient = None
    _database: Database = None
    _collection: Collection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa la conexión a MongoDB solo una vez"""
        if self._client is None:
            print("🔧 MongoDB: Inicializando cliente...")
            print(f"   Database: {settings.mongo_database}")
            print(f"   Collection: {settings.mongo_collection}")
            
            if not settings.mongo_atlas_uri:
                raise ValueError("MONGO_ATLAS_URI no está configurado en .env")
            
            try:
                self._client = MongoClient(settings.mongo_atlas_uri)
                self._database = self._client[settings.mongo_database]
                self._collection = self._database[settings.mongo_collection]
                
                # Crear índice geoespacial
                self._ensure_geospatial_index()
                
                print("✅ MongoDB: Cliente inicializado exitosamente")
            except Exception as e:
                print(f"❌ MongoDB: Error al crear cliente: {e}")
                raise
    
    def _ensure_geospatial_index(self):
        """
        Verificar y crear índice geoespacial si no existe
        Mejora el rendimiento de queries geoespaciales
        """
        try:
            # Verificar índices existentes
            existing_indexes = self._collection.list_indexes()
            has_geo_index = any(
                'location' in idx.get('key', {}) and idx['key']['location'] == '2dsphere'
                for idx in existing_indexes
            )
            
            if not has_geo_index:
                print("📍 MongoDB: Creando índice geoespacial...")
                self._collection.create_index([("location", GEOSPHERE)])
                print("✅ MongoDB: Índice geoespacial creado")
            else:
                print("✅ MongoDB: Índice geoespacial ya existe")
                
        except Exception as e:
            print(f"⚠️ MongoDB: No se pudo crear índice: {e}")
    
    @property
    def client(self) -> MongoClient:
        """Obtener instancia del cliente MongoDB"""
        return self._client
    
    @property
    def database(self) -> Database:
        """Obtener instancia de la base de datos"""
        return self._database
    
    @property
    def collection(self) -> Collection:
        """Obtener instancia de la colección"""
        return self._collection
    
    def close(self):
        """Cerrar conexión explícitamente"""
        if self._client:
            print("🔌 MongoDB: Cerrando conexión...")
            self._client.close()
            self._client = None
            self._database = None
            self._collection = None
    
    def __del__(self):
        """Cerrar conexión al destruir el cliente"""
        self.close()