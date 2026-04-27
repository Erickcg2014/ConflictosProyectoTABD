from google.cloud import bigquery
from google.oauth2 import service_account
from app.config import settings
import os


class BigQueryClient:
    """Cliente para BigQuery - NO usar singleton en entornos async"""
    
    def __init__(self):
        """Inicializar cliente de BigQuery"""
        print(f"🔧 BigQuery: Inicializando nuevo cliente...")
        
        if not settings.bigquery_project:
            raise ValueError("❌ BIGQUERY_PROJECT no configurado")
        
        if not settings.google_application_credentials:
            raise ValueError("❌ GOOGLE_APPLICATION_CREDENTIALS no configurado")
        
        if not os.path.exists(settings.google_application_credentials):
            raise FileNotFoundError(
                f"❌ Archivo de credenciales no encontrado: {settings.google_application_credentials}"
            )
        
        # CREAR CLIENTE DESDE ARCHIVO DE CREDENCIALES
        try:
            self._client = bigquery.Client.from_service_account_json(
                settings.google_application_credentials,
                project=settings.bigquery_project
            )
            print(f"✅ BigQuery: Cliente inicializado para proyecto {settings.bigquery_project}")
        except Exception as e:
            print(f"❌ Error al inicializar BigQuery client: {e}")
            raise
    
    @property
    def client(self) -> bigquery.Client:
        """Obtener instancia del cliente"""
        return self._client
    
    @property
    def full_table(self) -> str:
        """Obtener nombre completo de la tabla"""
        return f"{settings.bigquery_project}.{settings.bigquery_dataset}.{settings.bigquery_table}"