# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.presentation.routers import (
    bigquery_router, 
    health_router, 
    mongodb_router, 
    neo4j_router,
    summary,
    statistics_router,
    conflict_map_router
)
from app.config import settings
import os

app = FastAPI(
    title="TABD - Data Explorer API",
    description="API REST para consultar conflictos armados mundiales desde BigQuery, MongoDB y Neo4j",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_version="3.1.0",      
    redoc_url="/api/v1/redoc",   
    redirect_slashes=False,
    openapi_url="/api/v1/openapi.json",      
)

# ============================================
# CORS Configuration
# ============================================
origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "http://localhost:4200",
        "http://frontend-service"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Mostrar Configuración
# ============================================
@app.on_event("startup")
async def startup_event():
    """Mostrar configuración al iniciar el servidor"""
    print("\n" + "="*60)
    print("🔧 CONFIGURACIÓN CARGADA")
    print("="*60)
    print(f"📊 BigQuery:")
    print(f"   Project: {settings.bigquery_project}")
    print(f"   Dataset: {settings.bigquery_dataset}")
    print(f"   Credentials: {settings.google_application_credentials}")
    
    print(f"\n📦 MongoDB:")
    mongo_uri = settings.mongo_atlas_uri or "No configurada"
    print(f"   URI: {mongo_uri[:50]}...")
    print(f"   Database: {settings.mongo_database}")
    print(f"   Collection: {settings.mongo_collection}")
    
    print(f"\n🕸️  Neo4j:")
    print(f"   URI: {settings.neo4j_uri}")
    print(f"   User: {settings.neo4j_user}")
    print(f"   Password: {'✅ Configurada' if settings.neo4j_password else '❌ No configurada'}")
    print("="*60)
    
    print("\n🔍 RUTAS REGISTRADAS:")
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods = ", ".join(route.methods)
            print(f"   [{methods}] {route.path}")
    print("="*60 + "\n")

# ============================================
# Registrar Routers
# ============================================

# Health checks
app.include_router(
    health_router.router, 
    prefix="/api/v1/health", 
    tags=["Health"]
)

# BigQuery
app.include_router(
    bigquery_router.router, 
    prefix="/api/v1/bigquery", 
    tags=["BigQuery"]
)

# MongoDB
app.include_router(
    mongodb_router.router, 
    prefix="/api/v1/mongodb", 
    tags=["MongoDB"]
)

# Neo4j
app.include_router(
    neo4j_router.router, 
    prefix="/api/v1/neo4j", 
    tags=["Neo4j"]
)

# Summary
app.include_router(
    summary.router, 
    prefix="/api/v1/summary", 
    tags=["Summary"]
)

# Statistics
app.include_router(
    statistics_router.router, 
    prefix="/api/v1/statistics", 
    tags=["Statistics"]
)

app.include_router(
    conflict_map_router.router, 
    tags=["Conflict Map"]
)

# ============================================
# Root Endpoints
# ============================================
@app.get("/")
async def root():
    """
    Endpoint raíz de la API
    Retorna información básica y enlaces útiles
    """
    return {
        "message": "UCDP Data Explorer API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/api/v1/docs",
            "redoc": "/api/v1/redoc",
            "health": "/api/v1/health",
            "health_ready": "/api/v1/health/ready",
            "health_live": "/api/v1/health/live"
        },
        "services": {
            "bigquery": "/api/v1/bigquery",
            "mongodb": "/api/v1/mongodb",
            "neo4j": "/api/v1/neo4j",
            "summary": "/api/v1/summary",
            "statistics": "/api/v1/statistics",
            "conflict_map": "/api/graph"  
        }
    }

@app.get("/health")
async def root_health():
    """
    Health check simple en la raíz
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "wars-backend",
            "version": "1.0.0"
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al apagar el servidor"""
    print("\n🛑 Servidor apagándose...")
    print("✅ Recursos liberados correctamente\n")

# ============================================
# Main Execution
# ============================================
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000")) 
    reload = os.getenv("RELOAD", "false").lower() == "true"
    workers = int(os.getenv("WORKERS", "1"))
    
    print(f"\n🚀 Iniciando servidor...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {reload}")
    print(f"   Workers: {workers}")
    print(f"\n📖 Documentación disponible en: http://{host}:{port}/api/v1/docs\n")
    
    uvicorn.run(
        "app.main:app",              
        host=host,
        port=port,
        reload=reload,               
        workers=workers,             
        log_level="info",
        access_log=True,
        proxy_headers=True,          
        forwarded_allow_ips="*"     
    )