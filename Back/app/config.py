import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación desde variables de entorno"""
    
    # API Settings
    app_name: str = "UCDP Data Explorer API"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # BigQuery Settings
    bigquery_project: str = ""
    bigquery_dataset: str = "wars_dataset"
    bigquery_table: str = "war_events"
    google_application_credentials: str = ""
    
    # MongoDB Atlas Settings
    mongo_atlas_uri: str = ""
    mongo_database: str = "wars"
    mongo_collection: str = "war_locations"
    
    # Neo4j Settings
    neo4j_uri: str
    neo4j_user: str = "neo4j"  
    neo4j_password: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Retorna la configuración (cached para performance)"""
    settings = Settings()
    
    print("\n" + "="*60)
    print("🔧 CONFIGURACIÓN CARGADA")
    print("="*60)
    print(f"📊 BigQuery:")
    print(f"   Project: {settings.bigquery_project or '❌ NO CONFIGURADO'}")
    print(f"   Dataset: {settings.bigquery_dataset}")
    print(f"   Credentials: {settings.google_application_credentials or '❌ NO CONFIGURADO'}")
    print(f"")
    print(f"📦 MongoDB:")
    print(f"   URI: {settings.mongo_atlas_uri[:60] + '...' if settings.mongo_atlas_uri else '❌ NO CONFIGURADO'}")
    print(f"   Database: {settings.mongo_database}")
    print(f"   Collection: {settings.mongo_collection}")
    print(f"")
    print(f"🕸️  Neo4j:")
    print(f"   URI: {settings.neo4j_uri}")
    print(f"   User: {settings.neo4j_user}")
    print(f"   Password: {'Configurada' if settings.neo4j_password else '❌ NO CONFIGURADO'}")
    print("="*60 + "\n")
    
    return settings


settings = get_settings()
