-- ==========================================
-- 🧩 Inicialización de base de datos para Apache Airflow
-- ==========================================

-- Crea el usuario que usará Airflow
CREATE USER airflow WITH PASSWORD 'airflowpwd';

-- Crea la base de datos del metastore
CREATE DATABASE airflowdb OWNER airflow;

-- Otorga permisos sobre la base de datos
GRANT ALL PRIVILEGES ON DATABASE airflowdb TO airflow;

-- Conectarse a la base de datos creada
\c airflowdb;

-- Dar permisos sobre el esquema público
GRANT ALL ON SCHEMA public TO airflow;
ALTER ROLE airflow SET search_path TO public;

-- ==========================================
-- ✅ Verificación
-- ==========================================
-- Lista usuarios y bases de datos
-- \du
-- \l
