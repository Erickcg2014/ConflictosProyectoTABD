@echo off
REM ============================
REM Build & Push Airflow Script
REM ============================

if "%1"=="" (
    echo Usage: %0 image_name
    echo Example: %0 airflow
    exit /b 1
)

set IMAGE_NAME=%1

echo =========================================
echo Construyendo imagen de Airflow: %IMAGE_NAME%
echo =========================================

docker build -t localhost:5000/%IMAGE_NAME%:latest .

docker push localhost:5000/%IMAGE_NAME%:latest

echo =========================================
echo Airflow completado y enviado al registry local: %IMAGE_NAME%
echo =========================================
pause
