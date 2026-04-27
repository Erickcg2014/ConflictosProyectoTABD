"""
ETL para Datos Históricos de Conflictos desde S3
=================================================
Lee wars_historico_data.csv desde S3 y carga a BigQuery, MongoDB y Neo4j

Diferencias con ETL original:
- Tabla BigQuery separada: war_events_historical (con source_article, outcome, etc.)
- Genera event_id desde conflict_id
- Mapea type_of_conflict → type_of_violence
- Valida calidad de datos antes de insertar
- Idempotencia garantizada en las 3 bases de datos
"""

import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from typing import Dict, Any
import os, hashlib, boto3
import pandas as pd
from io import StringIO


S3_BUCKET = os.getenv("S3_BUCKET", "wars-datasets")
S3_KEY = os.getenv("S3_KEY_HISTORICAL", "CSV_DATA/wars_historico_data.csv")

# MAPEO DE TIPOS
TYPE_OF_CONFLICT_MAPPING = {
    "intrastate": "State-based violence",
    "interstate": "Interstate conflict",
    "extrastate": "Extrastate conflict",
    "non-state": "Non-state conflict",
    "one-sided": "One-sided violence",
}

# 🔑 GENERACIÓN DE EVENT_ID
def _mk_event_id_historical(row: dict) -> str:
    """
    Genera event_id determinístico para datos históricos.
    Prioriza conflict_id si existe, sino usa método original.
    """
    if row.get('conflict_id') and pd.notna(row.get('conflict_id')):
        return hashlib.md5(str(row['conflict_id']).encode("utf-8")).hexdigest()[:16]
    else:
        base = f"{row.get('conflict_name','')}|{row.get('date_start','')}|{row.get('latitude','')}|{row.get('longitude','')}"
        return hashlib.md5(base.encode("utf-8")).hexdigest()[:16]


def validate_row(row: dict) -> tuple[bool, str]:
    """
    Valida un registro antes de insertarlo.
    Retorna (es_valido, mensaje_error)
    """
    # Validar coordenadas
    try:
        lat = float(row.get('latitude', 0))
        lon = float(row.get('longitude', 0))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return False, "Coordenadas fuera de rango"
    except (ValueError, TypeError):
        return False, "Coordenadas inválidas"
    
    # Validar fechas
    try:
        start = pd.to_datetime(row.get('date_start'))
        end = pd.to_datetime(row.get('date_end'))
        if start > end:
            return False, "date_start > date_end"
    except:
        return False, "Fechas inválidas"
    
    # Validar estadísticas de muertes
    try:
        deaths_a = int(row.get('deaths_a', 0))
        deaths_b = int(row.get('deaths_b', 0))
        deaths_civ = int(row.get('deaths_civilians', 0))
        deaths_total = int(row.get('deaths_total', 0))
        
        calculated = deaths_a + deaths_b + deaths_civ
        if deaths_total < calculated:
            return False, f"deaths_total ({deaths_total}) < suma componentes ({calculated})"
    except (ValueError, TypeError):
        return False, "Estadísticas de muertes inválidas"
    
    return True, ""

# EXTRACT + TRANSFORM

def extract_and_transform_historical(**kwargs) -> Dict[str, Any]:
    """
    Extrae wars_historico_data.csv desde S3 y transforma para cada base de datos.
    
    Transformaciones:
    1. Genera event_id desde conflict_id
    2. Mapea type_of_conflict → type_of_violence
    3. Valida calidad de datos
    4. Prepara datasets específicos para cada destino
    """
    ti = kwargs["ti"]

    # --- Descargar CSV desde S3 ---
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )

    print(f"📥 Descargando CSV histórico desde s3://{S3_BUCKET}/{S3_KEY} ...")
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        csv_data = obj["Body"].read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"❌ Error al descargar CSV desde S3: {e}")

    # --- Leer CSV ---
    df = pd.read_csv(
        StringIO(csv_data),
        parse_dates=["date_start", "date_end"],
        dtype={
            "conflict_id": "string",
            "conflict_name": "string",
            "type_of_conflict": "string",
            "side_a": "string",
            "side_b": "string",
            "iso_a": "string",
            "iso_b": "string",
            "country": "string",
            "region": "string",
            "outcome": "string",
            "source_article": "string",
        },
    )

    print(f"✅ CSV histórico cargado: {len(df)} filas")

    # --- columnas esperadas ---
    cols = [
        "conflict_id", "conflict_name", "type_of_conflict",
        "side_a", "side_b", "iso_a", "iso_b",
        "latitude", "longitude", "country", "region",
        "date_start", "date_end",
        "deaths_a", "deaths_b", "deaths_civilians", "deaths_unknown", 
        "deaths_total", "best", "high", "low",
        "length_of_conflict", "outcome", "source_article",
    ]
    
    missing_cols = [col for col in cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"❌ Columnas faltantes en CSV: {missing_cols}")
    
    df = df[cols].copy()

    # --- Conversión de tipos numéricos ---
    for c in ["latitude", "longitude"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    
    numeric_int_cols = [
        "deaths_a", "deaths_b", "deaths_civilians", "deaths_unknown",
        "deaths_total", "best", "high", "low", "length_of_conflict"
    ]
    for c in numeric_int_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype("Int64")

    df["iso_a"] = df["iso_a"].str.upper().str.strip()
    df["iso_b"] = df["iso_b"].str.upper().str.strip()

    # --- Generar event_id desde conflict_id ---
    print("🔑 Generando event_id desde conflict_id...")
    df["event_id"] = df.apply(lambda row: _mk_event_id_historical(row.to_dict()), axis=1)

    print("🔄 Mapeando type_of_conflict → type_of_violence...")
    df["type_of_violence"] = df["type_of_conflict"].map(TYPE_OF_CONFLICT_MAPPING)
    df["type_of_violence"] = df["type_of_violence"].fillna("State-based violence")

    print("\n Validando calidad de datos...")
    initial_count = len(df)
    
    validation_results = df.apply(lambda row: validate_row(row.to_dict()), axis=1)
    df["is_valid"] = validation_results.apply(lambda x: x[0])
    df["validation_error"] = validation_results.apply(lambda x: x[1])
    
    invalid_df = df[~df["is_valid"]]
    if len(invalid_df) > 0:
        print(f"\n⚠️ Registros inválidos encontrados: {len(invalid_df)}")
        error_counts = invalid_df["validation_error"].value_counts()
        for error, count in error_counts.items():
            print(f"  • {error}: {count}")
    
    df_valid = df[df["is_valid"]].drop(columns=["is_valid", "validation_error"]).copy()
    
    print(f"\n📊 RESUMEN DE VALIDACIÓN:")
    print(f"  • Total inicial: {initial_count}")
    print(f"  • Registros válidos: {len(df_valid)}")
    print(f"  • Registros inválidos: {initial_count - len(df_valid)}")
    print(f"  • Tasa de calidad: {len(df_valid)/initial_count*100:.1f}%\n")

    # --- Preparar datasets por destino ---
    
    # BIGQUERY
    df_bigquery = df_valid[[
        "event_id", "conflict_id", "conflict_name", "type_of_violence",
        "side_a", "side_b", "iso_a", "iso_b", "country", "region",
        "date_start", "date_end",
        "deaths_a", "deaths_b", "deaths_civilians", "deaths_unknown", 
        "deaths_total", "best", "high", "low",
        "length_of_conflict", "outcome", "source_article"
    ]].copy()

    # MONGODB
    df_mongo = df_valid[[
        "event_id", "conflict_id", "conflict_name", 
        "latitude", "longitude", "country", "region"
    ]].copy()
    df_mongo = df_mongo.dropna(subset=["latitude", "longitude"])

    # NEO4J
    df_neo4j = df_valid[[
        "event_id", "conflict_id", "conflict_name", "type_of_violence",
        "side_a", "side_b", "iso_a", "iso_b", "country", "region",
        "date_start", "date_end",
        "deaths_a", "deaths_b", "deaths_civilians", "deaths_total",
        "length_of_conflict", "outcome"
    ]].copy()

    # --- Enviar a XCom ---
    ti.xcom_push("bigquery_data", df_bigquery.to_json(orient="records", date_format="iso"))
    ti.xcom_push("mongodb_data", df_mongo.to_json(orient="records", date_format="iso"))
    ti.xcom_push("neo4j_data", df_neo4j.to_json(orient="records", date_format="iso"))

    print(f"✅ Datos preparados:")
    print(f"  📊 BigQuery: {len(df_bigquery)} eventos completos")
    print(f"  🗺️ MongoDB: {len(df_mongo)} ubicaciones geográficas")
    print(f"  🕸️ Neo4j: {len(df_neo4j)} relaciones de conflicto")

    return {
        "rows_bq": len(df_bigquery), 
        "rows_mongo": len(df_mongo), 
        "rows_n4j": len(df_neo4j),
        "quality_rate": len(df_valid)/initial_count*100
    }

# ======================================================
# 📊 LOAD TO BIGQUERY 
# ======================================================
def load_historical_to_bigquery(**kwargs):
    """
    Carga datos históricos a BigQuery en tabla separada: war_events_historical
    
    Tabla incluye campos adicionales:
    - conflict_id, iso_a, iso_b, deaths_civilians, deaths_unknown
    - best, high, low (estimaciones)
    - outcome, source_article
    
    Idempotencia: Verifica event_ids existentes antes de insertar
    """
    try:
        import pandas as pd
        from google.cloud import bigquery
        from google.cloud.exceptions import NotFound
        from io import StringIO
        
        ti = kwargs["ti"]
        
        # Leer JSON desde XCom
        json_data = ti.xcom_pull(task_ids="extract_and_transform_historical", key="bigquery_data")
        df = pd.read_json(StringIO(json_data), orient="records")
        
        df["date_start"] = pd.to_datetime(df["date_start"], errors="coerce").dt.date
        df["date_end"] = pd.to_datetime(df["date_end"], errors="coerce").dt.date
        
        # Convertir integers
        int_cols = [
            "deaths_a", "deaths_b", "deaths_civilians", "deaths_unknown",
            "deaths_total", "best", "high", "low", "length_of_conflict"
        ]
        for col in int_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        print(f"📊 Tipos de datos en DataFrame:")
        print(df.dtypes)

        project_id = os.getenv("BIGQUERY_PROJECT", "proyectotabd")
        dataset_id = os.getenv("BIGQUERY_DATASET", "wars_dataset")
        table_id = "war_events_historical"  
        full_table_id = f"{project_id}.{dataset_id}.{table_id}"
        
        if not project_id:
            print("❌ BigQuery: sin BIGQUERY_PROJECT -> se omite carga.")
            return

        gcp_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not gcp_key:
            print("❌ BigQuery: sin GOOGLE_APPLICATION_CREDENTIALS -> se omite carga.")
            return
            
        client = bigquery.Client.from_service_account_json(gcp_key, project=project_id)
        
        # Crear dataset si no existe
        dataset_ref = bigquery.Dataset(f"{project_id}.{dataset_id}")
        try:
            client.create_dataset(dataset_ref, exists_ok=True)
            print(f"✅ Dataset {dataset_id} verificado/creado")
        except Exception as e:
            print(f"⚠️ Dataset ya existe o error: {e}")

        existing_ids = set()
        try:
            query = f"SELECT DISTINCT event_id FROM `{full_table_id}`"
            result = client.query(query).result()
            existing_ids = {row.event_id for row in result}
            print(f"📋 Encontrados {len(existing_ids)} event_ids existentes en {table_id}")
        except NotFound:
            print(f"🆕 Tabla {table_id} no existe. Se creará e insertarán todos los datos.")
        
        df_new = df[~df["event_id"].isin(existing_ids)].copy()
        
        if len(df_new) == 0:
            print(f"⏭️ BigQuery: Todos los {len(df)} registros ya existen. SKIP inserción.")
            return
        
        print(f"📝 BigQuery: Insertando {len(df_new)} nuevos registros de {len(df)} totales")

        schema = [
            bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("conflict_id", "STRING"),
            bigquery.SchemaField("conflict_name", "STRING"),
            bigquery.SchemaField("type_of_violence", "STRING"),
            bigquery.SchemaField("side_a", "STRING"),
            bigquery.SchemaField("side_b", "STRING"),
            bigquery.SchemaField("iso_a", "STRING"),            
            bigquery.SchemaField("iso_b", "STRING"),           
            bigquery.SchemaField("country", "STRING"),
            bigquery.SchemaField("region", "STRING"),
            bigquery.SchemaField("date_start", "DATE"),
            bigquery.SchemaField("date_end", "DATE"),
            bigquery.SchemaField("deaths_a", "INTEGER"),
            bigquery.SchemaField("deaths_b", "INTEGER"),
            bigquery.SchemaField("deaths_civilians", "INTEGER"), 
            bigquery.SchemaField("deaths_unknown", "INTEGER"),  
            bigquery.SchemaField("deaths_total", "INTEGER"),
            bigquery.SchemaField("best", "INTEGER"),             
            bigquery.SchemaField("high", "INTEGER"),             
            bigquery.SchemaField("low", "INTEGER"),             
            bigquery.SchemaField("length_of_conflict", "INTEGER"),
            bigquery.SchemaField("outcome", "STRING"),           
            bigquery.SchemaField("source_article", "STRING"),    
        ]

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition="WRITE_APPEND",
        )

        job = client.load_table_from_dataframe(df_new, full_table_id, job_config=job_config)
        job.result()
        
        print(f"✅ BigQuery OK: {len(df_new)} eventos históricos cargados")
        print(f"🔑 Total en tabla {table_id}: {len(existing_ids) + len(df_new)} registros")
        print(f"📍 Nota: Coordenadas están en MongoDB. Usar event_id para vincular.")
        
    except Exception as e:
        print(f"❌ BigQuery error: {e}")
        import traceback
        traceback.print_exc()
        raise

# ======================================================
# 🗺️ LOAD TO MONGODB 
# ======================================================
def load_historical_to_mongodb(**kwargs):
    """
    Carga ubicaciones históricas a MongoDB con GeoJSON.
    Usa misma colección war_locations pero con tag data_source='historical'.
    
    Idempotencia: Upsert por event_id
    """
    try:
        import pandas as pd
        from pymongo import MongoClient, GEOSPHERE, UpdateOne
        from datetime import datetime

        ti = kwargs["ti"]
        df = pd.read_json(
            ti.xcom_pull(task_ids="extract_and_transform_historical", key="mongodb_data"),
            orient="records"
        )

        mongo_uri = os.getenv("MONGO_ATLAS_URI")
        if not mongo_uri or "USUARIO" in mongo_uri:
            raise ValueError("❌ MONGO_ATLAS_URI no configurado correctamente")

        client = MongoClient(mongo_uri)
        db = client.get_database()
        collection = db["war_locations"]

        # Crear índice geoespacial
        try:
            collection.create_index([("location", GEOSPHERE)])
            print("✅ Índice geoespacial creado/verificado")
        except Exception as e:
            print(f"Índice geoespacial ya existe: {e}")

        # Transformar a documentos MongoDB con GeoJSON 
        documents = []
        for _, row in df.iterrows():
            doc = {
                "event_id": row.get("event_id"),
                "conflict_id": row.get("conflict_id"),      
                "conflict_name": row.get("conflict_name"),
                "country": row.get("country"),
                "region": row.get("region"),
                "location": {
                    "type": "Point",
                    "coordinates": [
                        float(row.get("longitude")),  # GeoJSON: [lon, lat]
                        float(row.get("latitude"))
                    ]
                },
                "data_source": "historical",                 
                "indexed_at": datetime.utcnow()
            }
            documents.append(doc)

        # Upsert por event_id 
        operations = [
            UpdateOne(
                {"event_id": doc["event_id"]},
                {"$set": doc},
                upsert=True
            )
            for doc in documents
        ]
        
        result = collection.bulk_write(operations)
        client.close()

        print(f"✅ MongoDB OK: {result.upserted_count} insertados, {result.modified_count} actualizados")
        print(f"🏷️ Tagged como 'historical' para diferenciación")
        print(f"🔑 Usa event_id para vincular con BigQuery")
        print(f"📍 Query ejemplo: db.war_locations.find({{data_source: 'historical'}})")

    except Exception as e:
        print(f"❌ MongoDB error: {e}")
        import traceback
        traceback.print_exc()
        raise

# ======================================================
# 🕸️ LOAD TO NEO4J 
# ======================================================
def load_historical_to_neo4j(**kwargs):
    """
    Carga relaciones históricas a Neo4j de forma idempotente.
    
    Mejoras vs ETL original:
    - Usa nodos HistoricalEvent para tracking de procesamiento
    - No acumula estadísticas infinitamente
    - Agrega outcome e ISOs
    - ON CREATE vs ON MATCH para evitar duplicación
    """
    try:
        import pandas as pd
        from neo4j import GraphDatabase

        ti = kwargs["ti"]
        df = pd.read_json(
            ti.xcom_pull(task_ids="extract_and_transform_historical", key="neo4j_data"), 
            orient="records"
        )

        uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "test12345")

        driver = GraphDatabase.driver(uri, auth=(user, password))
        rows = df.to_dict(orient="records")

        cypher = """
        UNWIND $rows AS r
        WITH r
        WHERE r.side_a IS NOT NULL AND r.side_b IS NOT NULL AND r.conflict_name IS NOT NULL
        
        OPTIONAL MATCH (existing:HistoricalEvent {event_id: r.event_id})
        WITH r, existing
        WHERE existing IS NULL  // Solo procesar si NO existe
        
        // Crear nodo de tracking para prevenir reprocesamiento
        CREATE (e:HistoricalEvent {
            event_id: r.event_id,
            conflict_id: r.conflict_id,
            processed_at: datetime()
        })
        
        // Crear/actualizar Conflicto
        MERGE (c:Conflict {name: r.conflict_name})
          ON CREATE SET 
            c.type_of_violence = r.type_of_violence,
            c.country = r.country,
            c.region = r.region,
            c.is_historical = true,
            c.outcome = r.outcome,
            c.event_ids = [r.event_id],
            c.total_deaths = r.deaths_total,
            c.total_civilians = r.deaths_civilians,
            c.event_count = 1
          ON MATCH SET
            c.event_ids = CASE 
                WHEN NOT r.event_id IN c.event_ids THEN c.event_ids + [r.event_id]
                ELSE c.event_ids
            END,
            c.total_deaths = c.total_deaths + r.deaths_total,
            c.total_civilians = COALESCE(c.total_civilians, 0) + r.deaths_civilians,
            c.event_count = size(c.event_ids)
        
        // Vincular evento con conflicto
        WITH c, r, e
        CREATE (e)-[:BELONGS_TO]->(c)
        
        // Crear Actores con ISOs
        MERGE (a:Actor {name: r.side_a})
          ON CREATE SET a.iso = r.iso_a
        MERGE (b:Actor {name: r.side_b})
          ON CREATE SET b.iso = r.iso_b

        // Relación Actor A -> Conflicto
        MERGE (a)-[ra:PARTICIPATED_IN {conflict: r.conflict_name}]->(c)
          ON CREATE SET 
            ra.role = 'A',
            ra.cumulative_deaths = r.deaths_a,
            ra.event_count = 1,
            ra.is_historical = true
          ON MATCH SET
            ra.cumulative_deaths = ra.cumulative_deaths + r.deaths_a,
            ra.event_count = ra.event_count + 1

        // Relación Actor B -> Conflicto
        MERGE (b)-[rb:PARTICIPATED_IN {conflict: r.conflict_name}]->(c)
          ON CREATE SET 
            rb.role = 'B',
            rb.cumulative_deaths = r.deaths_b,
            rb.event_count = 1,
            rb.is_historical = true
          ON MATCH SET
            rb.cumulative_deaths = rb.cumulative_deaths + r.deaths_b,
            rb.event_count = rb.event_count + 1

        // Relación Actor A <-> Actor B (enfrentamiento)
        MERGE (a)-[eng:ENGAGED_WITH {via_conflict: r.conflict_name}]-(b)
          ON CREATE SET
            eng.total_deaths = r.deaths_total,
            eng.total_civilians = r.deaths_civilians,
            eng.encounter_count = 1,
            eng.is_historical = true
          ON MATCH SET
            eng.total_deaths = eng.total_deaths + r.deaths_total,
            eng.total_civilians = eng.total_civilians + r.deaths_civilians,
            eng.encounter_count = eng.encounter_count + 1
        """
        
        with driver.session() as session:
            session.execute_write(lambda tx: tx.run(cypher, rows=rows))
        
        driver.close()
        
        print(f"✅ Neo4j OK: {len(rows)} eventos históricos procesados")
        print(f"🏷️ Nodos HistoricalEvent creados para tracking")
        print(f"🔑 Conflicts contienen outcome e ISOs de actores")
        print(f"📊 Query ejemplo: MATCH (e:HistoricalEvent)-[:BELONGS_TO]->(c) RETURN c.name, c.outcome")
        
    except Exception as e:
        print(f"❌ Neo4j error: {e}")
        import traceback
        traceback.print_exc()
        raise

# DAG
with DAG(
    dag_id="etl_wars_historical_s3",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    schedule_interval="@once",  
    catchup=False,
    is_paused_upon_creation=False,
    tags=["wars", "historical", "etl", "s3", "validated"],
    default_args={
        "owner": "airflow",
        "retries": 2,
        "retry_delay": pendulum.duration(minutes=5),
    },
    description="ETL para datos históricos desde S3 con validación y deduplicación",
) as dag:

    # ===== Extract & Transform con validación =====
    t_extract = PythonOperator(
        task_id="extract_and_transform_historical",
        python_callable=extract_and_transform_historical,
        do_xcom_push=True,
    )

    # ===== Loads idempotentes =====
    t_bq = PythonOperator(
        task_id="load_historical_to_bigquery",
        python_callable=load_historical_to_bigquery
    )

    t_mongo = PythonOperator(
        task_id="load_historical_to_mongodb",
        python_callable=load_historical_to_mongodb
    )

    t_n4j = PythonOperator(
        task_id="load_historical_to_neo4j",
        python_callable=load_historical_to_neo4j
    )

    # Dependencias del flujo
    t_extract >> [t_bq, t_mongo, t_n4j]