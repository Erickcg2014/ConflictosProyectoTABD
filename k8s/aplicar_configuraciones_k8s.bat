@echo off
echo =========================================
echo Aplicando configuraciones de Kubernetes para proyecto TABD
echo =========================================

REM =========================================
REM Persistent Volume Claims
REM =========================================
echo Aplicando PersistentVolumeClaims...
kubectl apply -f postgres-airflow-pvc.yaml -n wars

REM =========================================
REM Secrets y ConfigMaps 
REM =========================================
echo Creando Secrets...
REM Cargar variables desde archivo externo
for /f "tokens=1,2 delims==" %%a in (secrets.env) do set %%a=%%b

kubectl create secret generic airflow-s3-secret ^
  --from-literal=AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY_ID% ^
  --from-literal=AWS_SECRET_ACCESS_KEY=%AWS_SECRET_ACCESS_KEY% ^
  -n wars --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic gcp-credentials-secret ^
  --from-file=gcp-key.json=../.secrets/proyectotabd-d3510e72e652.json ^
  -n wars --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic gcp-credentials ^
  --from-file=gcp-key.json=../.secrets/proyectotabd-d3510e72e652.json ^
  -n wars
  
kubectl apply -f mongodb-secret.yaml -n wars

kubectl apply -f neo4j-secret.yaml -n wars


echo Creando ConfigMaps...
kubectl create configmap postgres-airflow-init ^
  --from-file=init.sql=../postgres_airflow/init.sql ^
  -n wars --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap airflow-dags ^
  --from-file=..\airflow\dags\ ^
  -n wars ^
  --dry-run=client -o yaml | kubectl apply -f -


echo.
echo =========================================
echo Desplegando PostgreSQL para Airflow...
echo =========================================
kubectl apply -f airflow_postgres_deployment.yaml -n wars

echo Esperando a que PostgreSQL este corriendo...
set /a POSTGRES_RETRY=0
:wait_postgres_running
kubectl get pod -l app=airflow-postgres -n wars 2>nul | findstr "Running" >nul
if errorlevel 1 (
  set /a POSTGRES_RETRY+=1
  if %POSTGRES_RETRY% GEQ 60 (
    echo ERROR: PostgreSQL no inicio despues de 5 minutos
    echo Mostrando estado:
    kubectl get pods -l app=airflow-postgres -n wars
    kubectl describe pod -l app=airflow-postgres -n wars
    kubectl logs -l app=airflow-postgres -n wars --tail=30
    pause
    exit /b 1
  )
  echo Intento %POSTGRES_RETRY%/60...
  timeout /t 5 /nobreak >nul
  goto wait_postgres_running
)

echo PostgreSQL esta running, esperando que acepte conexiones...
timeout /t 15 /nobreak >nul

echo Verificando conexion a PostgreSQL...
kubectl exec deployment/airflow-postgres -n wars -- pg_isready -U airflow 2>nul
if errorlevel 1 (
  echo PostgreSQL aun no acepta conexiones, esperando 10s mas...
  timeout /t 10 /nobreak >nul
)

REM =========================================
REM Neo4j
REM =========================================



echo.
echo =========================================
echo Desplegando Apache Airflow...
echo =========================================
kubectl apply -f airflow_deployment.yaml -n wars

echo Esperando a que el pod de Airflow se cree...
timeout /t 10 /nobreak >nul

echo Esperando a que Airflow este running...
set /a AIRFLOW_RETRY=0
:wait_airflow_running
kubectl get pod -l app=airflow -n wars 2>nul | findstr "Running" >nul
if errorlevel 1 (
  set /a AIRFLOW_RETRY+=1
  if %AIRFLOW_RETRY% GEQ 60 (
    echo ERROR: Airflow no inicio despues de 5 minutos
    echo Mostrando estado:
    kubectl get pods -l app=airflow -n wars
    kubectl describe pod -l app=airflow -n wars
    kubectl logs -l app=airflow -n wars -c airflow --tail=50
    pause
    exit /b 1
  )
  echo Intento %AIRFLOW_RETRY%/60...
  timeout /t 5 /nobreak >nul
  goto wait_airflow_running
)

echo Airflow pod esta running, esperando servicios internos...
timeout /t 20 /nobreak >nul

REM =========================================
REM Inicializar base de datos de Airflow
REM =========================================
echo.
echo =========================================
echo Inicializando base de datos de Airflow...
echo =========================================

REM Reintentar varias veces
set /a DB_INIT_RETRY=0
:retry_db_init
kubectl exec deployment/airflow -n wars -c airflow -- airflow db init 2>nul
if errorlevel 1 (
  set /a DB_INIT_RETRY+=1
  if %DB_INIT_RETRY% GEQ 5 (
    echo ERROR: No se pudo inicializar la BD de Airflow
    kubectl logs -l app=airflow -n wars -c airflow --tail=50
    pause
    exit /b 1
  )
  echo Reintentando inicializacion de BD... intento %DB_INIT_RETRY%/5
  timeout /t 10 /nobreak >nul
  goto retry_db_init
)

echo Airflow DB inicializada exitosamente!

REM =========================================
REM Crear usuario Admin en Airflow
REM =========================================
echo.
echo =========================================
echo Creando usuario administrador en Airflow...
echo =========================================
kubectl exec deployment/airflow -n wars -c airflow -- airflow users create ^
  --username admin ^
  --firstname Admin ^
  --lastname User ^
  --role Admin ^
  --email admin@example.com ^
  --password admin123 2>nul

if errorlevel 1 (
  echo Usuario admin probablemente ya existe, continuando...
)

REM =========================================
REM Aplicaciones principales
REM =========================================
echo.
echo =========================================
echo Desplegando Backend y Frontend...
echo =========================================
kubectl apply -f backend_deployment.yaml -n wars
kubectl apply -f frontend_deployment.yaml -n wars

REM =========================================
REM Configuracion de Ingress
REM =========================================
echo Configurando Ingress...
kubectl apply -f ingress.yaml -n wars

echo.
echo =========================================
echo Configuracion completada exitosamente!
echo =========================================
echo.
echo Estado de los pods:
kubectl get pods -n wars
echo.
echo Servicios disponibles:
kubectl get svc -n wars
echo.
pause