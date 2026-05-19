@echo off
REM Clone GoogleCloudPlatform/microservices-demo into this folder
REM Usage: run from repository root or double-click this file

SETLOCAL ENABLEDELAYEDEXPANSION
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Git is required but not found in PATH. Install Git and retry.
  exit /b 1
)

REM target dir
set TARGET_DIR=%~dp0microservices-demo

if exist "%TARGET_DIR%" (
  echo Target folder %TARGET_DIR% already exists. Pulling latest changes...
  pushd "%TARGET_DIR%"
  git pull
  popd
) else (
  echo Cloning microservices-demo into %TARGET_DIR%...
  git clone https://github.com/GoogleCloudPlatform/microservices-demo "%TARGET_DIR%"
)

echo Done. Inspect %TARGET_DIR% and then run the demo services (Docker or Kubernetes) as described in their README.
echo To use this repo as input for acv, copy or generate OpenAPI specs into demo\test_demo\openapi and then run acv validate.

pause
