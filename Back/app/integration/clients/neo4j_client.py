"""
Cliente singleton para conexión a Neo4j.
Maneja la configuración y ciclo de vida del driver.
"""

from neo4j import GraphDatabase, Driver
from app.config import settings


class Neo4jClient:
    """Cliente singleton para Neo4j"""
    _instance = None
    _driver: Driver = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa la conexión a Neo4j solo una vez"""
        if self._driver is None:
            print("🔧 Neo4j: Inicializando cliente...")
            print(f"   URI: {settings.neo4j_uri}")
            print(f"   User: {settings.neo4j_user}")
            
            if not settings.neo4j_uri:
                raise ValueError("NEO4J_URI no está configurado en .env")
            
            if not settings.neo4j_password:
                print("Neo4j: NEO4J_PASSWORD no configurado (puede fallar)")
            
            try:
                self._driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password),
                    max_connection_lifetime=3600,
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=120
                )
                self._driver.verify_connectivity()
                print("✅ Neo4j: Driver creado y verificado exitosamente")
            except Exception as e:
                print(f"❌ Neo4j: Error al crear driver: {e}")
                raise
    
    @property
    def driver(self) -> Driver:
        """Obtener instancia del driver"""
        return self._driver
    
    def verify_connectivity(self) -> bool:
        """Verificar conectividad del driver"""
        try:
            self._driver.verify_connectivity()
            return True
        except Exception as e:
            print(f"❌ Neo4j: Error de conectividad: {e}")
            return False
    
    def close(self):
        """Cerrar conexión explícitamente"""
        if self._driver:
            print("🔌 Neo4j: Cerrando conexión...")
            self._driver.close()
            self._driver = None
    
    def __del__(self):
        """Cerrar conexión al destruir el cliente"""
        self.close()