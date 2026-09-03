@echo off
setlocal enabledelayedexpansion
title RajibLabs Platform - Docker

:: ============================================================================
::  RajibLabs Platform - One-Click Docker Runner  (Windows)
::  Runs the FULL stack in containers via Docker Compose:
::    frontend    React PWA (nginx)       http://localhost:5010
::    ai-api      FastAPI + Mongo (API)   http://localhost:8090
::    mongo       MongoDB 7               localhost:27017
::
::  Usage:
::    run-docker.bat           -> build + start all (detached) + open browser
::    run-docker.bat up        -> same as above
::    run-docker.bat down      -> stop + remove containers (keeps mongo data)
::    run-docker.bat logs      -> follow logs of all services
::    run-docker.bat rebuild   -> force rebuild images (no cache) + start
::    run-docker.bat ps        -> show container status
::    run-docker.bat help      -> show help
::
::  Requirements:
::    - Docker Desktop running (docker --version)
::    - rajiblabs-ai-backend\.env  (auto-created from .env.example on 1st run;
::      fill ADMIN_INITIAL_PASSWORD / SECRET_KEY / JWT_SECRET / tokens!)
::
::  Config: docker-compose.yml  (frontend/nginx.conf routes /api/* per backend)
:: ============================================================================

pushd "%~dp0"
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "ENV_FILE=%ROOT%\rajiblabs-ai-backend\.env"
set "ENV_EXAMPLE=%ROOT%\rajiblabs-ai-backend\.env.example"

set "MODE=up"
if /I "%~1"=="up"      set "MODE=up"
if /I "%~1"=="down"    set "MODE=down"
if /I "%~1"=="stop"    set "MODE=down"
if /I "%~1"=="logs"    set "MODE=logs"
if /I "%~1"=="rebuild" set "MODE=rebuild"
if /I "%~1"=="ps"      set "MODE=ps"
if /I "%~1"=="status"  set "MODE=ps"
if /I "%~1"=="help"    goto :help
if /I "%~1"=="--help"  goto :help
if /I "%~1"=="-h"      goto :help
if not "%~1"=="" if /I not "%MODE%"=="down" if /I not "%MODE%"=="logs" if /I not "%MODE%"=="rebuild" if /I not "%MODE%"=="ps" if /I not "%MODE%"=="up" (
  echo Unknown mode: %~1
  goto :help
)

color 0B
echo.
echo  ==========================================================================
echo    RajibLabs Platform ^| Docker Compose ^| Full Stack
echo  ==========================================================================
echo    Root : %ROOT%
echo    Mode : %MODE%
echo  ==========================================================================
echo.

:: -------------------- Prerequisite Checks -----------------------------------
echo [1/4] Checking prerequisites...

where docker >nul 2>nul
if %errorlevel% neq 0 (
  color 0C
  echo   [ERROR] Docker not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('docker --version') do set DOCKER_VER=%%v
echo   - %DOCKER_VER% OK

docker info >nul 2>nul
if %errorlevel% neq 0 (
  color 0C
  echo   [ERROR] Docker daemon is not running. Start Docker Desktop and wait until it is green, then retry.
  pause
  exit /b 1
)
echo   - Docker daemon running.

docker compose version >nul 2>nul
if %errorlevel% neq 0 (
  color 0C
  echo   [ERROR] 'docker compose' (v2 plugin) not found. Update Docker Desktop.
  pause
  exit /b 1
)
echo   - docker compose OK.

if not exist "%ROOT%\docker-compose.yml" (
  color 0C
  echo   [ERROR] docker-compose.yml not found in %ROOT%
  pause
  exit /b 1
)
echo   Prerequisites OK.
echo.

:: -------------------- Mode dispatch -----------------------------------------
if /I "%MODE%"=="down"    goto :down
if /I "%MODE%"=="logs"    goto :logs
if /I "%MODE%"=="ps"      goto :ps
if /I "%MODE%"=="rebuild" goto :rebuild
goto :up

:: -------------------- Up -----------------------------------------------------
:up
echo [2/4] Preparing environment file...
if not exist "%ENV_FILE%" (
  if not exist "%ENV_EXAMPLE%" (
    color 0C
    echo   [ERROR] Neither .env nor .env.example found in rajiblabs-ai-backend\
    pause
    exit /b 1
  )
  copy "%ENV_EXAMPLE%" "%ENV_FILE%" >nul
  echo   - Created rajiblabs-ai-backend\.env from .env.example
  color 0E
  echo   [IMPORTANT] Fill secrets in rajiblabs-ai-backend\.env now:
  echo     ADMIN_INITIAL_PASSWORD, SECRET_KEY, JWT_SECRET, GITHUB_TOKEN, OPENAI_API_KEY
  echo   The stack will start, but admin login / AI / GitHub sync need those values.
  color 0B
) else (
  echo   - .env exists, using it.
)
echo.

echo [3/4] Building images + starting stack (this takes a few minutes on 1st run)...
docker compose up -d --build
if %errorlevel% neq 0 (
  color 0C
  echo   [ERROR] 'docker compose up' failed. See errors above.
  echo   Tip: run 'run-docker.bat logs' to inspect, or Docker Desktop -^> Containers.
  pause
  exit /b 1
)
echo.
goto :wait_healthy

:: -------------------- Rebuild ------------------------------------------------
:rebuild
echo [2/4] .env check...
if not exist "%ENV_FILE%" (
  copy "%ENV_EXAMPLE%" "%ENV_FILE%" >nul 2>nul
  echo   - Created .env from .env.example (fill secrets!).
)
echo.
echo [3/4] Force rebuilding all images (no cache)...
docker compose build --no-cache
if %errorlevel% neq 0 (
  color 0C
  echo   [ERROR] Rebuild failed.
  pause
  exit /b 1
)
docker compose up -d
if %errorlevel% neq 0 (
  color 0C
  echo   [ERROR] 'docker compose up' failed.
  pause
  exit /b 1
)
echo.
goto :wait_healthy

:: -------------------- Wait + open --------------------------------------------
:wait_healthy
echo [4/4] Waiting for services to become healthy (max ~90s)...
set "READY=0"
for /L %%i in (1,1,18) do (
  curl -s -o nul -w "%%{http_code}" --max-time 3 http://localhost:5010/ > "%TEMP%\rl_health.txt" 2>nul
  set /p CODE=<"%TEMP%\rl_health.txt" 2>nul
  if "!CODE!"=="200" (
    set "READY=1"
    echo   - Frontend is UP after ~%%i x 5s.
    goto :healthy_done
  )
  echo   - waiting... (%%i/18)
  timeout /t 5 /nobreak >nul
)
:healthy_done
if "%READY%"=="0" (
  color 0E
  echo   [WARN] Frontend not responding yet - containers may still be building.
  echo   Run 'run-docker.bat logs' or 'run-docker.bat ps' to inspect.
  color 0B
)
echo.
docker compose ps
echo.
color 0A
echo  ==========================================================================
echo    Stack is running!
echo  ==========================================================================
echo    Frontend   : http://localhost:5010  (PWA + nginx routes /api/*)
echo    API        : http://localhost:8090  (FastAPI: public CMS, admin, AI, chat)
echo    API Docs   : http://localhost:8090/docs  (dev only)
echo    MongoDB    : localhost:27017  (db: rajiblabs)
echo  --------------------------------------------------------------------------
echo    Admin      : http://localhost:5010/admin/login
echo                 (ADMIN_EMAILS + ADMIN_INITIAL_PASSWORD from
echo                  rajiblabs-ai-backend\.env - first run creates the admin)
echo  --------------------------------------------------------------------------
echo    Useful     : run-docker.bat logs     (follow all logs)
echo                 run-docker.bat ps       (container status)
echo                 run-docker.bat down     (stop; mongo data is kept)
echo  ==========================================================================
echo.
echo  Opening browser...
timeout /t 2 /nobreak >nul
start "" "http://localhost:5010"
timeout /t 1 /nobreak >nul
start "" "http://localhost:8090/docs"
echo  Done. Keep containers running with Docker Desktop, or run 'run-docker.bat down'.
pause
exit /b 0

:: -------------------- Down ---------------------------------------------------
:down
echo [2/2] Stopping stack (containers removed, mongo_data volume KEPT)...
docker compose down
if %errorlevel% neq 0 (
  color 0C
  echo   [ERROR] 'docker compose down' failed.
  pause
  exit /b 1
)
color 0A
echo  Stack stopped. Data preserved in 'mongo_data' volume.
echo  To wipe DB too: docker volume rm rajiblabs-platform_mongo_data
pause
exit /b 0

:: -------------------- Logs ---------------------------------------------------
:logs
echo [2/2] Following logs (Ctrl+C to stop)...
docker compose logs -f --tail=200
exit /b 0

:: -------------------- Status -------------------------------------------------
:ps
echo [2/2] Container status...
docker compose ps
echo.
pause
exit /b 0

:: -------------------- Help ---------------------------------------------------
:help
echo.
echo  RajibLabs Platform - run-docker.bat HELP
echo  ----------------------------------------
echo  run-docker.bat          Build + start all (detached) + open browser
echo  run-docker.bat up       Same as above
echo  run-docker.bat rebuild  Force rebuild images (no cache) + start
echo  run-docker.bat logs     Follow logs of all services (Ctrl+C to stop)
echo  run-docker.bat ps       Show container status
echo  run-docker.bat down     Stop + remove containers (mongo data KEPT)
echo  run-docker.bat help     Show this help
echo.
echo  URLs after start:
echo    Frontend  http://localhost:5010   (API :8090, Mongo :27017)
echo.
echo  First run: .env is auto-created from .env.example - fill secrets!
echo.
pause
exit /b 0
