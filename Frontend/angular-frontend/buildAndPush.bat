@echo off
REM ============================
REM Build & Push Frontend Script
REM ============================

REM Check if a parameter is provided
if "%1"=="" (
    echo Usage: %0 image_name
    echo Example: %0 wars_frontend
    exit /b 1
)

REM Set the image name from the parameter
set IMAGE_NAME=%1

echo =========================================
echo Construyendo imagen del Frontend: %IMAGE_NAME%
echo =========================================

REM Build the Docker image
docker build --no-cache -t localhost:5000/%IMAGE_NAME%:latest .

REM Push the Docker image to local registry
docker push localhost:5000/%IMAGE_NAME%:latest

echo =========================================
echo Frontend completado: %IMAGE_NAME%
echo =========================================
pause
