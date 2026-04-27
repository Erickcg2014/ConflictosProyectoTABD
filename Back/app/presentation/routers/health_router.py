from fastapi import APIRouter
from app.business.services.bigquery_service import BigQueryService
from app.business.services.mongodb_service import MongoDBService
from app.business.services.neo4j_service import Neo4jService

router = APIRouter()


@router.get("", include_in_schema=True)  
@router.get("/", include_in_schema=True)  
async def health_check():
    """
    Health check endpoint - verifica conectividad con todas las bases de datos
    """
    status = {
        "status": "healthy",
        "bigquery": False,
        "mongodb": False,
        "neo4j": False
    }
    
    # Verificar BigQuery
    try:
        bq_service = BigQueryService()
        status["bigquery"] = bq_service.check_connection()
    except Exception as e:
        print(f"❌ BigQuery health check failed: {e}")
        status["bigquery"] = False
    
    # Verificar MongoDB
    try:
        mongo_service = MongoDBService()
        status["mongodb"] = mongo_service.check_connection()
        mongo_service.close()
    except Exception as e:
        print(f"❌ MongoDB health check failed: {e}")
        status["mongodb"] = False
    
    # Verificar Neo4j
    try:
        neo4j_service = Neo4jService()
        status["neo4j"] = neo4j_service.check_connection()
        neo4j_service.close()
    except Exception as e:
        print(f"❌ Neo4j health check failed: {e}")
        status["neo4j"] = False
    
    # Determinar status general
    if not all([status["bigquery"], status["mongodb"], status["neo4j"]]):
        status["status"] = "degraded"
    
    return status


@router.get("/ready", include_in_schema=True)  # Readiness probe
@router.get("/ready/", include_in_schema=True)
async def readiness_check():
    """
    Readiness probe - verificación rápida sin conectar a las bases de datos
    """
    return {"status": "ready"}


@router.get("/live", include_in_schema=True)  # Liveness probe
@router.get("/live/", include_in_schema=True)
async def liveness_check():
    """
    Liveness probe - verificación básica de que el servicio responde
    """
    return {"status": "alive"}