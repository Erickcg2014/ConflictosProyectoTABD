#!/usr/bin/env python3
"""
Script para verificar que las variables de entorno están correctamente configuradas
"""
import os
from pathlib import Path

# Cargar variables de entorno
from dotenv import load_dotenv

script_dir = Path(__file__).parent
os.chdir(script_dir)

# Cargar .env
env_file = script_dir / ".env"
print(f"📄 Buscando archivo .env en: {env_file}")
print(f"   Archivo existe: {env_file.exists()}\n")

if env_file.exists():
    load_dotenv(env_file)
    print("✅ Archivo .env cargado\n")
else:
    print("❌ Archivo .env NO encontrado\n")

print("="*60)
print("🔍 VARIABLES DE ENTORNO")
print("="*60)

# Verificar BigQuery
print("\n📊 BigQuery:")
print(f"   BIGQUERY_PROJECT: {os.getenv('BIGQUERY_PROJECT', '❌ NO DEFINIDO')}")
print(f"   BIGQUERY_DATASET: {os.getenv('BIGQUERY_DATASET', 'No definido')}")
print(f"   GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '❌ NO DEFINIDO')}")

# Verificar MongoDB
print("\n📦 MongoDB:")
mongo_uri = os.getenv('MONGO_ATLAS_URI', '')
if mongo_uri:
    print(f"   MONGO_ATLAS_URI: {mongo_uri[:60]}...")
else:
    print(f"   MONGO_ATLAS_URI: ❌ NO DEFINIDO")
print(f"   MONGO_DATABASE: {os.getenv('MONGO_DATABASE', 'No definido')}")
print(f"   MONGO_COLLECTION: {os.getenv('MONGO_COLLECTION', 'No definido')}")

# Verificar Neo4j
print("\n🕸️  Neo4j:")
print(f"   NEO4J_URI: {os.getenv('NEO4J_URI', 'No definido')}")
print(f"   NEO4J_USER: {os.getenv('NEO4J_USER', 'No definido')}")
neo4j_pass = os.getenv('NEO4J_PASSWORD', '')
print(f"   NEO4J_PASSWORD: {'✅ Definida' if neo4j_pass else '❌ NO DEFINIDO'}")

print("="*60)
print()

# Verificar si existen los archivos de credenciales
creds_file = Path(os.getenv('GOOGLE_APPLICATION_CREDENTIALS', ''))
if creds_file:
    print(f"📁 Archivo de credenciales de GCP:")
    print(f"   Ruta: {creds_file}")
    print(f"   Absoluta: {creds_file.absolute()}")
    print(f"   Existe: {creds_file.exists()}")
    if creds_file.exists():
        print(f"   Tamaño: {creds_file.stat().st_size} bytes")
else:
    print(f"   ❌ Ruta no configurada")

print("\n✨ Verificación completada\n")
