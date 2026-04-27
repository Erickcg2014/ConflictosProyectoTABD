"""
Cliente singleton para conexión a Neo4j específico para ConflictMap.
Maneja la configuración y ciclo de vida del driver.
"""

import os
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, Neo4jError


class ConflictMapClient:
    """Cliente singleton para Neo4j - ConflictMap"""
    _instance = None
    _driver: Driver = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa la conexión a Neo4j solo una vez"""
        if self._driver is None:
            print("🔧 ConflictMap: Inicializando cliente Neo4j...")
            
            self.uri = os.getenv("NEO4J_URI")
            self.user = os.getenv("NEO4J_USER", "neo4j")
            self.password = os.getenv("NEO4J_PASSWORD")
            self.database = os.getenv("NEO4J_DATABASE", "neo4j")
            
            if not self.uri or not self.password:
                raise ValueError("Neo4j credentials not configured in .env")
            
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                keep_alive=True
            )
            
            print(f"✅ ConflictMap: Cliente Neo4j inicializado")
            print(f"   URI: {self.uri}")
            print(f"   Database: {self.database}")
    
    @property
    def driver(self) -> Driver:
        """Obtener instancia del driver"""
        return self._driver
    
    @property
    def database_name(self) -> str:
        """Obtener nombre de la base de datos"""
        return self.database
    
    def close(self):
        """Cerrar conexión explícitamente"""
        if self._driver:
            print("🔌 ConflictMap: Cerrando conexión Neo4j...")
            self._driver.close()
            self._driver = None
    
    def __del__(self):
        """Cerrar conexión al destruir el cliente"""
        self.close()