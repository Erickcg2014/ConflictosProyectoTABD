# =============================
# Imagen base oficial de Apache Airflow
# =============================
FROM apache/airflow:2.9.0-python3.10

# =============================
# Etapa 1: Instalación de dependencias
# =============================
USER airflow
RUN pip install pymongo

# Copiar e instalar requerimientos adicionales
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# =============================
# Etapa 2: Copia de DAGs y credenciales
# =============================
USER root

# Copiar DAGs al contenedor
COPY dags /opt/airflow/dags

RUN mkdir -p /opt/airflow/credentials
COPY airflow-bigquery-key.json /opt/airflow/credentials/gcp-key-Erick.json

# Ajustar permisos de carpetas
RUN chown -R airflow: /opt/airflow/dags /opt/airflow/credentials

# =============================
# Etapa 3: Script de inicio 
# =============================
USER root

COPY start_airflow.sh /start-airflow.sh
RUN chmod +x /start-airflow.sh

# Exponer el puerto del Webserver
EXPOSE 8080

# =============================
# Inicialización automática mejorada
# =============================
CMD ["/start-airflow.sh"]