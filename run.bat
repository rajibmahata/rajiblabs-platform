@echo off
setlocal enabledelayedexpansion
title RajibLabs Platform - Local Dev

:: ============================================================================
::  RajibLabs Platform - One-Click Local Runner  (Windows)
::  Runs the Vite React PWA natively; full stack (API + MongoDB) via Docker.
::
::  Usage:
::    run.bat              -> start frontend only (recommended for UI work)
::    run.bat frontend     -> frontend only
::    run.bat docker       -> full stack via run-docker.bat (frontend :5010,
::                            FastAPI :8090, Mongo :27017)
::    run.bat build        -> production build + preview
::    run.bat help         -> show help
::
::  Requirements:
::    - Node.js 18+ (node --version)  + npm
::    - Docker Desktop only needed for "docker" mode (API + DB)
::
::  Ports:
::    Frontend (native) -> http://localhost:5173  (Vite) + Network via --host
::    API (Docker)      -> http://localhost:8090  (FastAPI, proxied as /api)
:: ============================================================================

pushd "%~dp0"
set "ROOT=%~dp0"
:: Trim trailing backslash for display
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "FRONTEND_DIR=%ROOT%\frontend"
set "FRONTEND_URL=http://localhost:5173"
set "API_URL=http://localhost:8090"

:: Parse arg (case-insensitive)
set "MODE=frontend"
if /I "%~1"=="frontend" set "MODE=frontend"
if /I "%~1"=="client"   set "MODE=frontend"
if /I "%~1"=="ui"       set "MODE=frontend"
if /I "%~1"=="docker"   set "MODE=docker"
if /I "%~1"=="compose"  set "MODE=docker"
if /I "%~1"=="build"    set "MODE=build"
if /I "%~1"=="backend"  goto :no_backend
if /I "%~1"=="api"      goto :no_backend
if /I "%~1"=="help"     goto :help
if /I "%~1"=="--help"   goto :help
if /I "%~1"=="-h"       goto :help

color 0B
echo.
echo  ==========================================================================
echo    RajibLabs Platform ^| FastAPI + Mongo ^| PWA Ready
echo  ==========================================================================
echo    Root     : %ROOT%
echo    Mode     : %MODE%
echo    Frontend : %FRONTEND_URL% ^(Vite + --host for mobile PWA testing^)
echo    API      : %API_URL% ^(FastAPI via Docker - see run-docker.bat^)
echo  ==========================================================================
echo.

:: -------------------- Prerequisite Checks -----------------------------------
echo [1/3] Checking prerequisites...

where node >nul 2>nul
if %errorlevel% neq 0 (
  color 0C
  echo   [ERROR] Node.js not found. Install Node 18+ from https://nodejs.org
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('node --version') do set NODE_VER=%%v
echo   - node %NODE_VER% OK

where npm >nul 2>nul
if %errorlevel% neq 0 (
  color 0C
  echo   [ERROR] npm not found. Reinstall Node.js.
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('npm --version') do set NPM_VER=%%v
echo   - npm %NPM_VER% OK

if not exist "%FRONTEND_DIR%\package.json" (
  color 0C
  echo   [ERROR] Frontend package.json not found: "%FRONTEND_DIR%\package.json"
  pause
  exit /b 1
)
echo   Prerequisites OK.
echo.

:: -------------------- Build / Docker Modes ----------------------------------
if /I "%MODE%"=="build" goto :build
if /I "%MODE%"=="docker" goto :docker

:: -------------------- Start Frontend ----------------------------------------
:start_frontend
echo [2/3] Starting Frontend PWA...
echo   Project : %FRONTEND_DIR%
echo   Note    : /api calls proxy to %API_URL% (see frontend/vite.config.ts).
echo             Start the API with:  run-docker.bat   (or run.bat docker)
echo.

:: Install deps if node_modules missing
if not exist "%FRONTEND_DIR%\node_modules" (
  echo   - node_modules not found, running npm install (this may take 1-3 minutes on first run)...
  pushd "%FRONTEND_DIR%"
  call npm install --legacy-peer-deps
  if %errorlevel% neq 0 (
    color 0C
    echo   [ERROR] npm install failed. Check errors above.
    popd
    pause
    exit /b 1
  )
  popd
  echo   - npm install complete.
) else (
  echo   - node_modules exists, skipping install.
)

:: Free frontend port 5173 if busy
set "FRONTEND_BUSY=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING 2^>nul') do (
  set "FRONTEND_BUSY=1"
  echo   ! Found process on :5173 PID %%a - killing...
  taskkill /PID %%a /F >nul 2>nul
  timeout /t 1 /nobreak >nul
)
netstat -aon | findstr :5173 | findstr LISTENING >nul 2>nul
if %errorlevel%==0 (
  color 0C
  echo   [WARN] Port 5173 still busy. Frontend may fail. Try: taskkill /F /IM node.exe
  color 0B
) else (
  if "!FRONTEND_BUSY!"=="1" echo   - Port 5173 freed.
)

:: Start frontend in new window with --host for PWA mobile testing (Network URL)
start "RajibLabs Frontend - %FRONTEND_URL%" cmd /k "cd /d ""%FRONTEND_DIR%"" && echo [RajibLabs Frontend] Starting Vite... && echo URL: %FRONTEND_URL% && echo Network: use --host to test PWA on phone && echo. && call npm run dev -- --host"

timeout /t 4 /nobreak >nul
echo   Frontend window launched. Check "RajibLabs Frontend" window for logs.
echo.

:: -------------------- Open Browser ------------------------------------------
:open_browser
echo [3/3] Opening browser...
timeout /t 3 /nobreak >nul

echo   Opening %FRONTEND_URL%
start "" "%FRONTEND_URL%"
echo   API health (needs Docker stack): %API_URL%/health

echo.
color 0A
echo  ==========================================================================
echo    Frontend launched!
echo  ==========================================================================
echo    Frontend : %FRONTEND_URL%
echo    Network  : http://^<your-ip^>:5173  (Vite will show actual IP - use for PWA on phone)
echo    API      : %API_URL%  (run 'run-docker.bat' if /api calls fail)
echo    Proxy    : Frontend /api -^> %API_URL%  (see frontend/vite.config.ts)
echo  --------------------------------------------------------------------------
echo    PWA Test : On phone, open Network URL -^> Install prompt appears after ~3s
echo             : Chrome DevTools -^> Application -^> Manifest / Service Workers
echo             : Lighthouse -^> PWA score should be 100
echo  --------------------------------------------------------------------------
echo    WhatsApp : https://wa.me/918420249020  (update in frontend/src/config/site.ts)
echo    Call     : tel:+918420249020
echo  --------------------------------------------------------------------------
echo    To stop  : Close the new window OR press Ctrl+C in it
echo  ==========================================================================
echo.
pause
exit /b 0

:: -------------------- Docker Mode --------------------------------------------
:docker
echo.
echo  Delegating to run-docker.bat (full stack: frontend :5010, API :8090)...
echo.
call "%ROOT%\run-docker.bat" %~2
exit /b %errorlevel%

:: -------------------- Removed backend mode -----------------------------------
:no_backend
color 0E
echo.
echo  The legacy .NET API was removed. The API is now FastAPI + MongoDB.
echo  Use one of:
echo    run.bat docker     - full stack via Docker (recommended)
echo    run-docker.bat     - same, with up/down/logs/rebuild modes
echo.
pause
exit /b 2

:: -------------------- Build Mode -------------------------------------------
:build
echo [BUILD] Production build...
echo   Frontend: npm run build  (tsc + vite)
echo.
pushd "%FRONTEND_DIR%"
call npm run build
if %errorlevel% neq 0 (
  color 0C
  echo [ERROR] Build failed.
  popd
  pause
  exit /b 1
)
popd
echo.
echo  Build complete: %FRONTEND_DIR%\dist
echo  Preview with:  npm run preview  (in frontend)
echo.
set /p PREVIEW="Start preview now on http://localhost:4173 ? (y/n): "
if /I "%PREVIEW%"=="y" (
  pushd "%FRONTEND_DIR%"
  start "RajibLabs Preview" cmd /k "npm run preview -- --host --port 4173"
  timeout /t 2 >nul
  start "" "http://localhost:4173"
  popd
)
pause
exit /b 0

:help
echo.
echo  RajibLabs Platform - run.bat HELP
echo  ---------------------------------
echo  run.bat              Start frontend only (default)
echo  run.bat frontend     Start frontend only (%FRONTEND_URL%)
echo  run.bat docker       Full stack via Docker (frontend :5010, API :8090)
echo  run.bat build        Production build + optional preview
echo  run.bat help         Show this help
echo.
echo  API removed? The legacy .NET API was replaced by FastAPI + MongoDB.
echo  Run 'run-docker.bat' for the API + database.
echo.
echo  Examples:
echo    run.bat
echo    run.bat docker
echo    run.bat build
echo.
echo  After start:
echo    - A new cmd window appears (Frontend) - keep it open
echo    - Browser opens automatically to %FRONTEND_URL%
echo    - For PWA on phone: use the Network URL shown in Frontend window
echo.
pause
exit /b 0
