@echo off
REM ============================
REM Build & Push PostgreSQL Script
REM ============================

REM Check if a parameter is provided
if "%1"=="" (
    echo Usage: %0 image_name
    echo Example: %0 wars-postgres
    exit /b 1
)

REM Set the image name from the parameter
set IMAGE_NAME=%1

echo =========================================
echo Construyendo imagen de PostgreSQL: %IMAGE_NAME%
echo =========================================

REM Build the Docker image from ./postgres
docker build -t localhost:5000/%IMAGE_NAME%:latest .

REM Push the Docker image to local registry
docker push localhost:5000/%IMAGE_NAME%:latest

echo =========================================
echo PostgreSQL completado: %IMAGE_NAME%
echo =========================================
pause
