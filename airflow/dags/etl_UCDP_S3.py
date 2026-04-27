import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from typing import Dict, Any
import os, hashlib, boto3
import pandas as pd
from io import StringIO

# Configuración de S3

S3_BUCKET = os.getenv("S3_BUCKET", "wars-datasets")
S3_KEY = os.getenv("S3_KEY", "CSV_DATA/WarsConflicts.csv")

# Directorio temporal
TEMP_DIR = "/tmp/airflow_data"

# Utilidad: generar event_id para todos los registros del CSV
def _mk_event_id(row: dict) -> str:
    """Genera un ID único por evento basado en conflicto + fecha + ubicación"""
    base = f"{row.get('conflict_name','')}|{row.get('date_start','')}|{row.get('latitude','')}|{row.get('longitude','')}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()[:16]

# EXTRACT + TRANSFORM (lee desde S3)
def extract_and_transform_data(**kwargs) -> Dict[str, Any]:
    """
     CAMBIO: Ahora incluye país_a y país_b para MongoDB
    """
    ti = kwargs["ti"]

    # Crear directorio temporal
    os.makedirs(TEMP_DIR, exist_ok=True)
    print(f"📁 Directorio temporal: {TEMP_DIR}")

    # --- Descargar CSV desde S3 ---
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )

    print(f"📥 Descargando CSV desde s3://{S3_BUCKET}/{S3_KEY} ...")
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        csv_data = obj["Body"].read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"❌ Error al descargar CSV desde S3: {e}")

    # Leer CSV desde memoria
    df = pd.read_csv(
        StringIO(csv_data),
        parse_dates=["date_start", "date_end"],
        dtype={
            "type_of_violence": "string",
            "conflict_name": "string",
            "side_a": "string",
            "side_b": "string",
            "country": "string",
            "region": "string",
            "país_a": "string",  
            "país_b": "string",  
        },
    )

    # Imprimir información detallada sobre las columnas
    print(f" CSV cargado correctamente ({len(df)} filas, {len(df.columns)} columnas)")
    print(f"📋 COLUMNAS EXISTENTES EN EL ARCHIVO S3:")
    for i, col in enumerate(df.columns.tolist(), 1):
        print(f"   {i:2d}. {col}")
    print(f"📊 Tipos de datos del DataFrame original:")
    print(df.dtypes)

    cols = [
        "type_of_violence","conflict_name","side_a","side_b",
        "latitude","longitude","country","region",
        "país_a","país_b",  
        "date_start","date_end",
        "deaths_a","deaths_b","deaths_total","length_of_conflict",
    ]
    
    missing_cols = [col for col in cols if col not in df.columns]
    if missing_cols:
        print(f"⚠️  ADVERTENCIA: Columnas faltantes en el CSV: {missing_cols}")
    
    df = df[cols].copy()

    # Numéricos seguros
    for c in ["latitude","longitude"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["deaths_a","deaths_b","deaths_total","length_of_conflict"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype("Int64")

    # Generar event_id para todos los registros
    df["event_id"] = df.apply(lambda row: _mk_event_id(row.to_dict()), axis=1)
    
    # --- Datasets por destino ---
    # BIG QUERY 
    df_bigquery = df.copy()

    # MongoDB 
    df_mongo = df[["event_id", "conflict_name", "latitude", "longitude", "country", "region", "país_a", "país_b"]].copy()
    df_mongo = df_mongo.dropna(subset=["latitude","longitude"])

    df_neo4j = df[[
        "event_id", 
        "conflict_name", 
        "type_of_violence", 
        "side_a", 
        "side_b", 
        "country", 
        "region",
        "país_a",          
        "país_b",        
        "date_start", 
        "date_end",
        "deaths_a", 
        "deaths_b", 
        "deaths_total", 
        "length_of_conflict",
    ]].copy()

    print(f"📊 Columnas en df_neo4j: {df_neo4j.columns.tolist()}")

    # Guardar en archivos temporales en formato Parquet
    bigquery_path = os.path.join(TEMP_DIR, "bigquery_data.parquet")
    mongo_path = os.path.join(TEMP_DIR, "mongo_data.parquet")
    neo4j_path = os.path.join(TEMP_DIR, "neo4j_data.parquet")
    
    df_bigquery.to_parquet(bigquery_path, index=False)
    df_mongo.to_parquet(mongo_path, index=False)
    df_neo4j.to_parquet(neo4j_path, index=False)
    
    print(f"💾 Datos guardados en archivos temporales:")
    print(f"   BigQuery: {bigquery_path} ({os.path.getsize(bigquery_path) / 1024 / 1024:.2f} MB)")
    print(f"   MongoDB:  {mongo_path} ({os.path.getsize(mongo_path) / 1024 / 1024:.2f} MB)")
    print(f"   Neo4j:    {neo4j_path} ({os.path.getsize(neo4j_path) / 1024 / 1024:.2f} MB)")

    ti.xcom_push("bigquery_path", bigquery_path)
    ti.xcom_push("mongo_path", mongo_path)
    ti.xcom_push("neo4j_path", neo4j_path)

    print(f"📊 BigQuery: {len(df_bigquery)} eventos completos")
    print(f"🗺️ MongoDB: {len(df_mongo)} ubicaciones geográficas con país_a y país_b")
    print(f"🕸️ Neo4j: {len(df_neo4j)} relaciones de conflicto")
    print(f"\n🔍 DEBUG - Columnas en neo4j_data.parquet:")
    print(f"   Columnas: {df_neo4j.columns.tolist()}")
    print(f"   'país_a' presente: {'país_a' in df_neo4j.columns}")
    print(f"   'país_b' presente: {'país_b' in df_neo4j.columns}")

    if 'país_a' in df_neo4j.columns and 'país_b' in df_neo4j.columns:
        print(f"   Registros con ambos países: {df_neo4j[df_neo4j['país_a'].notna() & df_neo4j['país_b'].notna()].shape[0]:,}")

    return {"rows_bq": len(df_bigquery), "rows_mongo": len(df_mongo), "rows_n4j": len(df_neo4j)}
   
# ======================================================
# CARGAR A BIG QUERY BIGQUERY 
# ======================================================
def load_to_bigquery(**kwargs):
    """
     MEJORA: Ahora crea dataset y tabla si no existen
    """
    try:
        import pandas as pd
        from google.cloud import bigquery
        from google.cloud.exceptions import NotFound
        
        ti = kwargs["ti"]
        
        bigquery_path = ti.xcom_pull(task_ids="extract_and_transform", key="bigquery_path")
        print(f"📂 Leyendo datos desde: {bigquery_path}")
        
        df = pd.read_parquet(bigquery_path)
        print(f"📊 Datos cargados: {len(df)} filas desde archivo temporal")

        # Eliminar columnas geográficas - eso es responsabilidad de MongoDB
        df = df.drop(columns=["latitude", "longitude", "país_a", "país_b"], errors="ignore")
        
        # CRÍTICO: Convertir fechas correctamente
        df["date_start"] = pd.to_datetime(df["date_start"], errors="coerce").dt.date
        df["date_end"] = pd.to_datetime(df["date_end"], errors="coerce").dt.date
        
        # Convertir integers que pueden venir como object/string
        for col in ["deaths_a", "deaths_b", "deaths_total", "length_of_conflict"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        print(f"📊 Tipos de datos en DataFrame:")
        print(df.dtypes)

        project_id = os.getenv("BIGQUERY_PROJECT", "proyectotabd")
        dataset_id = os.getenv("BIGQUERY_DATASET", "wars_dataset")
        table_id = "war_events"
        full_table_id = f"{project_id}.{dataset_id}.{table_id}"
        
        if not project_id:
            print("❌ BigQuery: sin BIGQUERY_PROJECT -> se omite carga.")
            return

        gcp_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not gcp_key:
            print("❌ BigQuery: sin GOOGLE_APPLICATION_CREDENTIALS -> se omite carga.")
            return
            
        client = bigquery.Client.from_service_account_json(gcp_key, project=project_id)
        
        # CREAR DATASET SI NO EXISTE
        dataset_ref = bigquery.Dataset(f"{project_id}.{dataset_id}")
        dataset_ref.location = "US"  
        try:
            client.create_dataset(dataset_ref, exists_ok=True)
            print(f" Dataset {dataset_id} creado/verificado")
        except Exception as e:
            print(f" Error con dataset: {e}")

        # Verificar si la tabla existe y tiene datos
        table_exists = False
        try:
            table = client.get_table(full_table_id)
            row_count = table.num_rows
            table_exists = True
            
            if row_count > 0:
                print(f"⏭️ BigQuery: Tabla {table_id} ya existe con {row_count} registros. SKIP inserción.")
                return
            else:
                print(f"📝 BigQuery: Tabla {table_id} existe pero está vacía. Insertando datos...")
                
        except NotFound:
            print(f"🆕 BigQuery: Tabla {table_id} no existe. Creando...")
            table_exists = False

        schema = [
            bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("conflict_name", "STRING"),
            bigquery.SchemaField("type_of_violence", "STRING"),
            bigquery.SchemaField("side_a", "STRING"),
            bigquery.SchemaField("side_b", "STRING"),
            bigquery.SchemaField("country", "STRING"),
            bigquery.SchemaField("region", "STRING"),
            bigquery.SchemaField("date_start", "DATE"),
            bigquery.SchemaField("date_end", "DATE"),
            bigquery.SchemaField("deaths_a", "INTEGER"),
            bigquery.SchemaField("deaths_b", "INTEGER"),
            bigquery.SchemaField("deaths_total", "INTEGER"),
            bigquery.SchemaField("length_of_conflict", "INTEGER"),
        ]

        # SI LA TABLA NO EXISTE, CREARLA
        if not table_exists:
            table_ref = bigquery.Table(full_table_id, schema=schema)
            client.create_table(table_ref)
            print(f" Tabla {table_id} creada exitosamente")

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition="WRITE_APPEND",
        )

        job = client.load_table_from_dataframe(df, full_table_id, job_config=job_config)
        job.result()
        
        print(f" BigQuery OK: {len(df)} eventos cargados a {full_table_id}")
        print(f"🔑 Clave primaria: event_id (para vincular con MongoDB para obtener coordenadas)")
        
    except Exception as e:
        print(f"❌ BigQuery error: {e}")
        import traceback
        traceback.print_exc()
        raise

# ======================================================
# CARGAR A MONGO DB DATOS GEOGRÁFICOS
# ======================================================
def load_to_mongodb(**kwargs):
    """
     Base de datos: wars_db
     Colección: war_locations
    """
    import pandas as pd
    from pymongo import MongoClient, GEOSPHERE
    from datetime import datetime

    ti = kwargs["ti"]
    
    mongo_path = ti.xcom_pull(task_ids="extract_and_transform", key="mongo_path")
    print(f"📂 Leyendo datos desde: {mongo_path}")
    
    df = pd.read_parquet(mongo_path)
    print(f"📊 Datos cargados: {len(df)} filas desde archivo temporal")

    # Configuración Mongo
    mongo_uri = os.getenv("MONGO_ATLAS_URI")
    mongo_db_name = "wars_db"  
    mongo_collection_name = "war_locations" 
    
    if not mongo_uri:
        raise ValueError("❌ MONGO_ATLAS_URI no está configurado")
    if "USUARIO" in mongo_uri or "PASSWORD" in mongo_uri:
        raise ValueError("❌ MONGO_ATLAS_URI contiene placeholders. Configura las credenciales correctas.")
    
    print(f"🔗 Conectando a MongoDB Atlas...")
    print(f"   Database: {mongo_db_name}")
    print(f"   Collection: {mongo_collection_name}")

    try:
        client = MongoClient(mongo_uri)
        
        # Especificar base de datos
        db = client[mongo_db_name]
        
        # Verificar conexión
        client.server_info()
        print(f" Conexión exitosa a MongoDB Atlas")
        
    except Exception as e:
        raise ConnectionError(f"❌ Error al conectar a MongoDB Atlas: {e}")
    
    #  Acceder a la colección war_locations
    collection = db[mongo_collection_name]
    print(f" Trabajando en: {mongo_db_name}.{mongo_collection_name}")

    #  Crear índices
    try:
        collection.create_index([("location", GEOSPHERE)])
        print(" Índice geoespacial creado/verificado en 'location'")
    except Exception as e:
        print(f" Índice geoespacial: {e}")

    try:
        collection.create_index([("event_id", 1)], unique=True)
        print(" Índice único creado/verificado en 'event_id'")
    except Exception as e:
        print(f" Índice event_id: {e}")

    # Transformar a documentos MongoDB con GeoJSON
    print(f" Transformando {len(df):,} registros a formato GeoJSON...")
    documents = []
    
    for _, row in df.iterrows():
        doc = {
            "event_id": row.get("event_id"),
            "conflict_name": row.get("conflict_name"),
            "country": row.get("country"),
            "region": row.get("region"),
            
            # Países involucrados
            "país_a": row.get("país_a"),
            "país_b": row.get("país_b"),
            
            # GeoJSON Point
            "location": {
                "type": "Point",
                "coordinates": [
                    float(row.get("longitude")),  # [lon, lat]
                    float(row.get("latitude"))
                ]
            },
            
            "indexed_at": datetime.utcnow()
        }
        documents.append(doc)

    # Upsert por event_id
    from pymongo import UpdateOne
    
    print(f"📤 Preparando {len(documents):,} operaciones de upsert...")
    
    operations = [
        UpdateOne(
            {"event_id": doc["event_id"]},
            {"$set": doc},
            upsert=True
        )
        for doc in documents
    ]
    
    print(f"💾 Ejecutando bulk write en wars_db.war_locations...")
    result = collection.bulk_write(operations, ordered=False)
    
    # Obtener estadísticas finales
    total_docs = collection.count_documents({})
    
    print(f"\n✅ MongoDB OK:")
    print(f"   📊 Insertados: {result.upserted_count:,}")
    print(f"    Actualizados: {result.modified_count:,}")
    print(f"   📚 Total en colección: {total_docs:,}")
    print(f"   🗄️ Base de datos: {mongo_db_name}")
    print(f"   📁 Colección: {mongo_collection_name}")
    print(f"   🔑 Campos incluidos: event_id, conflict_name, country, region, país_a, país_b, location")
    
    client.close()
    print(f"🔌 Conexión cerrada")
    
# ======================================================
# CARGAR A NEO4J - AURA DB
# ======================================================
def load_to_neo4j(**kwargs):
    """
     CARGA EN DOS FASES CON NORMALIZACIÓN DE COLUMNAS
    """
    import pandas as pd
    from neo4j import GraphDatabase
    import time
    import os
    from neo4j.exceptions import ServiceUnavailable, TransientError

    ti = kwargs["ti"]
    
    neo4j_path = ti.xcom_pull(task_ids="extract_and_transform", key="neo4j_path")
    print(f"📂 Leyendo datos desde: {neo4j_path}")
    
    df = pd.read_parquet(neo4j_path)
    total_rows = len(df)
    
    if 'país_a' in df.columns:
        df = df.rename(columns={'país_a': 'pais_a', 'país_b': 'pais_b'})
        print(f" Columnas renombradas: país_a → pais_a, país_b → pais_b")
    
    print(f"📊 Datos cargados: {total_rows:,} filas")

    print(f"\n🔍 Verificando columnas de países:")
    if 'pais_a' in df.columns:
        print(f"    Columna 'pais_a' existe")
        print(f"   📊 Registros con pais_a: {df['pais_a'].notna().sum():,}")
    else:
        print(f"   ❌ Columna 'pais_a' NO existe")
    
    if 'pais_b' in df.columns:
        print(f"    Columna 'pais_b' existe")
        print(f"   📊 Registros con pais_b: {df['pais_b'].notna().sum():,}")
    else:
        print(f"   ❌ Columna 'pais_b' NO existe")
    
    if 'pais_a' in df.columns and 'pais_b' in df.columns:
        with_both_countries = df[df['pais_a'].notna() & df['pais_b'].notna()].shape[0]
        print(f"   📊 Registros con AMBOS países: {with_both_countries:,}")

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    BATCH_SIZE = 500
    
    print(f"\n🔗 Conectando a Neo4j Aura...")
    
    try:
        driver = GraphDatabase.driver(
            uri, 
            auth=(user, password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=120,
            connection_timeout=60,
            keep_alive=True
        )
        driver.verify_connectivity()
        print(" Conexión exitosa")
    except Exception as e:
        raise ConnectionError(f"❌ Error al conectar: {e}")

    def create_constraints_and_indexes():
        with driver.session(database=database) as session:
            commands = [
                "CREATE CONSTRAINT actor_name_unique IF NOT EXISTS FOR (a:Actor) REQUIRE a.name IS UNIQUE",
                "CREATE CONSTRAINT conflict_name_unique IF NOT EXISTS FOR (c:Conflict) REQUIRE c.name IS UNIQUE",
                "CREATE CONSTRAINT country_name_unique IF NOT EXISTS FOR (p:Country) REQUIRE p.name IS UNIQUE",
                "CREATE INDEX conflict_country_idx IF NOT EXISTS FOR (c:Conflict) ON (c.country)",
                "CREATE INDEX conflict_region_idx IF NOT EXISTS FOR (c:Conflict) ON (c.region)",
                "CREATE INDEX country_region_idx IF NOT EXISTS FOR (p:Country) ON (p.region)",
                "CREATE INDEX actor_name_idx IF NOT EXISTS FOR (a:Actor) ON (a.name)",
            ]
            
            print("\n🔧 Creando constraints e índices...")
            for cmd in commands:
                try:
                    session.run(cmd)
                except Exception:
                    pass

    try:
        create_constraints_and_indexes()
        
        print(f"\n🚀 INICIANDO CARGA DIRECTA - Sin verificación de datos existentes")
        print(f"   📊 Registros a procesar: {total_rows:,}")
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        driver.close()
        raise

    rows = df.to_dict(orient="records")
    print(f"\n📤 FASE 1: Cargando conflictos y actores ({total_rows:,} registros)...")

    # ========================================
    # QUERY 1: CONFLICTOS Y ACTORES
    # ========================================
    cypher_main = """
    UNWIND $batch AS r
    WITH r
    WHERE r.side_a IS NOT NULL AND r.side_b IS NOT NULL AND r.conflict_name IS NOT NULL

    MERGE (c:Conflict {name: r.conflict_name})
    ON CREATE SET 
        c.type_of_violence = r.type_of_violence,
        c.country = r.country,
        c.region = r.region,
        c.event_ids = [r.event_id],
        c.total_deaths = COALESCE(r.deaths_total, 0),
        c.event_count = 1
    ON MATCH SET
        c.event_ids = 
            CASE WHEN NOT r.event_id IN c.event_ids 
            THEN c.event_ids + [r.event_id]
            ELSE c.event_ids END,
        c.total_deaths = c.total_deaths + COALESCE(r.deaths_total, 0),
        c.event_count = c.event_count + 1

    WITH r, c
    MERGE (a:Actor {name: r.side_a})
    MERGE (b:Actor {name: r.side_b})

    WITH r, c, a, b
    MERGE (a)-[ra:PARTICIPATED_IN {conflict: r.conflict_name}]->(c)
    ON CREATE SET 
        ra.role = 'A',
        ra.cumulative_deaths = COALESCE(r.deaths_a, 0),
        ra.event_count = 1
    ON MATCH SET
        ra.cumulative_deaths = ra.cumulative_deaths + COALESCE(r.deaths_a, 0),
        ra.event_count = ra.event_count + 1

    MERGE (b)-[rb:PARTICIPATED_IN {conflict: r.conflict_name}]->(c)
    ON CREATE SET 
        rb.role = 'B',
        rb.cumulative_deaths = COALESCE(r.deaths_b, 0),
        rb.event_count = 1
    ON MATCH SET
        rb.cumulative_deaths = rb.cumulative_deaths + COALESCE(r.deaths_b, 0),
        rb.event_count = rb.event_count + 1

    WITH r, a, b
    MERGE (a)-[e:ENGAGED_WITH]-(b)
    ON CREATE SET
        e.via_conflict = r.conflict_name,
        e.total_deaths = COALESCE(r.deaths_total, 0),
        e.total_length = COALESCE(r.length_of_conflict, 0),
        e.encounter_count = 1
    ON MATCH SET
        e.total_deaths = e.total_deaths + COALESCE(r.deaths_total, 0),
        e.total_length = e.total_length + COALESCE(r.length_of_conflict, 0),
        e.encounter_count = e.encounter_count + 1

    RETURN count(*) as processed
    """
    
    # ========================================
    # QUERY 2: PAÍSES 
    # ========================================
    cypher_countries = """
    UNWIND $batch AS r
    WITH r
    WHERE r.pais_a IS NOT NULL AND r.pais_b IS NOT NULL AND r.conflict_name IS NOT NULL

    MERGE (pa:Country {name: r.pais_a})
    ON CREATE SET pa.region = r.region
    
    MERGE (pb:Country {name: r.pais_b})
    ON CREATE SET pb.region = r.region
    
    MERGE (pa)-[rel_pais:CONFLICT_WITH]-(pb)
    ON CREATE SET
        rel_pais.conflict_names = [r.conflict_name],
        rel_pais.total_deaths = COALESCE(r.deaths_total, 0),
        rel_pais.event_count = 1,
        rel_pais.actors_involved = [r.side_a, r.side_b]
    ON MATCH SET
        rel_pais.conflict_names = 
            CASE WHEN NOT r.conflict_name IN rel_pais.conflict_names 
            THEN rel_pais.conflict_names + [r.conflict_name]
            ELSE rel_pais.conflict_names END,
        rel_pais.total_deaths = rel_pais.total_deaths + COALESCE(r.deaths_total, 0),
        rel_pais.event_count = rel_pais.event_count + 1

    WITH r, pa, pb
    MATCH (c:Conflict {name: r.conflict_name})
    
    MERGE (pa)-[rpa:HAS_CONFLICT]->(c)
    ON CREATE SET rpa.event_count = 1
    ON MATCH SET rpa.event_count = rpa.event_count + 1
    
    MERGE (pb)-[rpb:HAS_CONFLICT]->(c)
    ON CREATE SET rpb.event_count = 1
    ON MATCH SET rpb.event_count = rpb.event_count + 1

    RETURN count(*) as processed
    """
    
    def execute_batch_with_retry(session, cypher, batch, batch_num, phase, max_retries=3):
        def run_batch_transaction(tx):
            result = tx.run(cypher, batch=batch)
            return result.consume()
        
        for attempt in range(max_retries):
            try:
                return session.execute_write(run_batch_transaction)
            except (ServiceUnavailable, TransientError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"    {phase} Batch {batch_num}: Retry {attempt + 1} en {wait_time}s")
                    time.sleep(wait_time)
                else:
                    print(f"   ❌ {phase} Batch {batch_num}: Falló tras {max_retries} intentos")
                    return None
            except Exception as e:
                print(f"   ❌ {phase} Batch {batch_num}: {str(e)[:200]}")
                return None
    
    # ========================================
    # FASE 1: CONFLICTOS Y ACTORES
    # ========================================
    total_processed = 0
    total_nodes_created = 0
    total_relationships_created = 0
    failed_batches = 0
    start_time = time.time()
    
    try:
        with driver.session(database=database) as session:
            total_batches = (total_rows + BATCH_SIZE - 1) // BATCH_SIZE
            
            for i in range(0, total_rows, BATCH_SIZE):
                batch = rows[i:i + BATCH_SIZE]
                batch_num = (i // BATCH_SIZE) + 1
                
                summary = execute_batch_with_retry(session, cypher_main, batch, batch_num, "FASE 1")
                
                if summary:
                    total_nodes_created += summary.counters.nodes_created
                    total_relationships_created += summary.counters.relationships_created
                    total_processed += len(batch)
                else:
                    failed_batches += 1
                
                if batch_num % 20 == 0 or batch_num == total_batches:
                    elapsed = time.time() - start_time
                    progress = (batch_num / total_batches) * 100
                    eta = (elapsed / batch_num) * (total_batches - batch_num) / 60
                    
                    print(f"   [{batch_num}/{total_batches}] {progress:.1f}% | ETA: {eta:.1f}min | Rels: {total_relationships_created:,}")
        
        phase1_time = time.time() - start_time
        print(f"\n✅ FASE 1 completada en {phase1_time/60:.2f} min")
        print(f"   📊 Procesados: {total_processed:,}")
        print(f"   🆕 Nodos: {total_nodes_created:,}")
        print(f"   🔗 Relaciones: {total_relationships_created:,}")
        
        # ========================================
        # FASE 2: PAÍSES 
        # ========================================
        if 'pais_a' in df.columns and 'pais_b' in df.columns:
            df_countries = df[df['pais_a'].notna() & df['pais_b'].notna()].copy()
            
            if len(df_countries) > 0:
                print(f"\n📤 FASE 2: Cargando países ({len(df_countries):,} registros)...")
                
                rows_countries = df_countries.to_dict(orient="records")
                total_batches_countries = (len(df_countries) + BATCH_SIZE - 1) // BATCH_SIZE
                
                countries_processed = 0
                countries_nodes = 0
                countries_rels = 0
                phase2_start = time.time()
                
                with driver.session(database=database) as session:
                    for i in range(0, len(df_countries), BATCH_SIZE):
                        batch = rows_countries[i:i + BATCH_SIZE]
                        batch_num = (i // BATCH_SIZE) + 1
                        
                        summary = execute_batch_with_retry(session, cypher_countries, batch, batch_num, "FASE 2")
                        
                        if summary:
                            countries_nodes += summary.counters.nodes_created
                            countries_rels += summary.counters.relationships_created
                            countries_processed += len(batch)
                        
                        if batch_num % 20 == 0 or batch_num == total_batches_countries:
                            elapsed = time.time() - phase2_start
                            progress = (batch_num / total_batches_countries) * 100
                            eta = (elapsed / batch_num) * (total_batches_countries - batch_num) / 60
                            
                            print(f"   [{batch_num}/{total_batches_countries}] {progress:.1f}% | ETA: {eta:.1f}min | Países: {countries_nodes:,} | Rels: {countries_rels:,}")
                
                phase2_time = time.time() - phase2_start
                print(f"\n✅ FASE 2 completada en {phase2_time/60:.2f} min")
                print(f"   📊 Procesados: {countries_processed:,}")
                print(f"   🆕 Nodos (países): {countries_nodes:,}")
                print(f"   🔗 Relaciones: {countries_rels:,}")
                
                total_nodes_created += countries_nodes
                total_relationships_created += countries_rels
            else:
                print(f"\n⚠️ FASE 2: No hay registros con ambos países - SALTANDO")
        else:
            print(f"\n⚠️ FASE 2: Columnas de países no encontradas - SALTANDO")
        
        # RESUMEN FINAL

        total_time = time.time() - start_time
        
        print(f"\n🎉 CARGA COMPLETA en {total_time/60:.2f} min")
        print(f"   📊 Total procesados: {total_processed:,}")
        print(f"   🆕 Total nodos: {total_nodes_created:,}")
        print(f"   🔗 Total relaciones: {total_relationships_created:,}")
        print(f"   ❌ Fallos: {failed_batches}")
        
        print(f"\n📊 Verificando datos cargados...")
        with driver.session(database=database) as session:
            def check_final_data():
                result = session.run("MATCH (c:Conflict) RETURN count(c) as count")
                conflict_count = result.single()["count"]
                
                result = session.run("MATCH (a:Actor) RETURN count(a) as count")
                actor_count = result.single()["count"]
                
                result = session.run("MATCH (p:Country) RETURN count(p) as count")
                country_count = result.single()["count"]
                
                return conflict_count, actor_count, country_count
            
            conflict_count, actor_count, country_count = check_final_data()
            
            result = session.run("MATCH ()-[r:CONFLICT_WITH]-() RETURN count(r) as count")
            rel_country = result.single()["count"]
            
            result = session.run("MATCH ()-[r:PARTICIPATED_IN]-() RETURN count(r) as count")
            rel_participated = result.single()["count"]
            
            result = session.run("MATCH ()-[r:ENGAGED_WITH]-() RETURN count(r) as count")
            rel_engaged = result.single()["count"]
            
            result = session.run("MATCH ()-[r:HAS_CONFLICT]-() RETURN count(r) as count")
            rel_has_conflict = result.single()["count"]
            
            print(f"\n✅ VERIFICACIÓN FINAL:")
            print(f"   🏛️ Conflicts: {conflict_count:,}")
            print(f"   👥 Actors: {actor_count:,}")
            print(f"   🌍 Countries: {country_count:,}")
            print(f"\n   🔗 Tipos de relaciones:")
            print(f"      • CONFLICT_WITH (país↔país): {rel_country:,}")
            print(f"      • PARTICIPATED_IN (actor→conflicto): {rel_participated:,}")
            print(f"      • ENGAGED_WITH (actor↔actor): {rel_engaged:,}")
            print(f"      • HAS_CONFLICT (país→conflicto): {rel_has_conflict:,}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        driver.close()
        print("\n🔌 Conexión cerrada")

# ======================================================
# DAG
# ======================================================
with DAG(
    dag_id="etl_ucdp_s3",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    schedule_interval="@once",
    catchup=False,
    is_paused_upon_creation=False,
    tags=["wars", "etl", "bigdata", "mongodb", "neo4j", "geojson", "optimized"],
    default_args={"owner": "airflow"},
) as dag:

    # ===== Extract & Transform =====
    t_extract = PythonOperator(
        task_id="extract_and_transform",
        python_callable=extract_and_transform_data,
        do_xcom_push=True,
    )

    # ===== Loads =====
    t_bq = PythonOperator(
        task_id="load_to_bigquery",
        python_callable=load_to_bigquery
    )

    t_mongo = PythonOperator(
        task_id="load_to_mongodb",
        python_callable=load_to_mongodb
    )

    t_n4j = PythonOperator(
        task_id="load_to_neo4j_aura",
        python_callable=load_to_neo4j
    )

    # Dependencias del flujo
    t_extract >> [t_bq, t_mongo, t_n4j]