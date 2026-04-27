@echo off
REM =========================================
REM Crear usuario Admin en Airflow
REM =========================================
echo.
echo =========================================
echo Creando usuario administrador en Airflow...
echo =========================================
kubectl exec -it deployment/airflow -n wars -c airflow -- airflow users create ^
  --username admin ^
  --firstname Admin ^
  --lastname User ^
  --role Admin ^
  --email admin@example.com ^
  --password admin123

echo Usuario administrador creado exitosamente!
