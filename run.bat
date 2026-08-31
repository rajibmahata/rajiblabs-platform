@echo off
setlocal enabledelayedexpansion
title RajibLabs Platform - Local Dev

:: ============================================================================
::  RajibLabs Platform - One-Click Local Runner  (Windows)
::  Runs .NET 8 API  +  Vite React PWA  in parallel
::
::  Usage:
::    run.bat              -> start BOTH backend + frontend (recommended)
::    run.bat backend      -> backend only
::    run.bat frontend     -> frontend only
::    run.bat build        -> production build + preview
::    run.bat help         -> show help
::
::  Requirements:
::    - .NET 8 SDK  (dotnet --version)
::    - Node.js 18+ (node --version)  + npm
::
::  Ports:
::    Backend  -> http://localhost:5000  (forced via --urls, matches vite proxy)
::    Frontend -> http://localhost:5173  (Vite)  + Network via --host for PWA mobile
::    Swagger  -> http://localhost:5000/swagger (if enabled)
:: ============================================================================

pushd "%~dp0"
set "ROOT=%~dp0"
:: Trim trailing backslash for display
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "BACKEND_DIR=%ROOT%\backend\RajibLabs.Api"
set "FRONTEND_DIR=%ROOT%\frontend"
set "BACKEND_URL=http://localhost:5000"
set "FRONTEND_URL=http://localhost:5173"

:: Parse arg (case-insensitive)
set "MODE=both"
if /I "%~1"=="backend"  set "MODE=backend"
if /I "%~1"=="api"      set "MODE=backend"
if /I "%~1"=="frontend" set "MODE=frontend"
if /I "%~1"=="client"   set "MODE=frontend"
if /I "%~1"=="ui"       set "MODE=frontend"
if /I "%~1"=="build"    set "MODE=build"
if /I "%~1"=="help"     goto :help
if /I "%~1"=="--help"   goto :help
if /I "%~1"=="-h"       goto :help

color 0B
echo.
echo  ==========================================================================
echo    RajibLabs Platform ^| Senior .NET ^& Azure ^| PWA Ready
echo  ==========================================================================
echo    Root     : %ROOT%
echo    Mode     : %MODE%
echo    Backend  : %BACKEND_URL%  ^(forced to 5000 - matches vite proxy^)
echo    Frontend : %FRONTEND_URL% ^(Vite + --host for mobile PWA testing^)
echo  ==========================================================================
echo.

:: -------------------- Prerequisite Checks -----------------------------------
echo [1/4] Checking prerequisites...

where dotnet >nul 2>nul
if %errorlevel% neq 0 (
  color 0C
  echo   [ERROR] .NET SDK not found. Install .NET 8 SDK from https://dotnet.microsoft.com/download
  echo   Checking: dotnet --version
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('dotnet --version') do set DOTNET_VER=%%v
echo   - dotnet %DOTNET_VER% OK

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

if not exist "%BACKEND_DIR%\RajibLabs.Api.csproj" (
  color 0C
  echo   [ERROR] Backend project not found: "%BACKEND_DIR%\RajibLabs.Api.csproj"
  pause
  exit /b 1
)
if not exist "%FRONTEND_DIR%\package.json" (
  color 0C
  echo   [ERROR] Frontend package.json not found: "%FRONTEND_DIR%\package.json"
  pause
  exit /b 1
)
echo   Prerequisites OK.
echo.

:: -------------------- Build Mode -------------------------------------------
if /I "%MODE%"=="build" goto :build

:: -------------------- Start Backend ----------------------------------------
if /I "%MODE%"=="frontend" goto :start_frontend

:start_backend
echo [2/4] Starting Backend API...
echo   Project : %BACKEND_DIR%
echo   URL     : %BACKEND_URL%  ^(SQLite auto-creates rajiblabs.db^)
echo.

:: Ensure wwwroot exists (fixes StaticFileMiddleware warning)
if not exist "%BACKEND_DIR%\wwwroot" (
  mkdir "%BACKEND_DIR%\wwwroot" >nul 2>nul
  echo   - Created missing wwwroot folder.
)

:: Check and FREE port 5000 if already in use (fixes "address already in use")
set "PORT_BUSY=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING 2^>nul') do (
  set "PORT_BUSY=1"
  echo   ! Found process on :5000 PID %%a - killing...
  taskkill /PID %%a /F >nul 2>nul
  timeout /t 1 /nobreak >nul
)
:: Verify port is now free
netstat -aon | findstr :5000 | findstr LISTENING >nul 2>nul
if %errorlevel%==0 (
  color 0C
  echo   [WARN] Port 5000 still busy after kill. Backend may fail to start.
  echo   Tip: Run CMD as Administrator, then:
  echo        netstat -ano ^| findstr :5000
  echo        taskkill /PID ^<PID^> /F
  echo   Or change backend port: edit backend/RajibLabs.Api/Properties/launchSettings.json
  echo        and frontend/vite.config.ts proxy, or run:
  echo        dotnet run --urls http://localhost:5001
  color 0B
) else (
  if "!PORT_BUSY!"=="1" (
    echo   - Port 5000 freed.
  ) else (
    echo   - Port 5000 is free.
  )
)

:: Start backend in new window - keeps logs visible, auto-restores packages
start "RajibLabs API - %BACKEND_URL%" cmd /k "cd /d ""%BACKEND_DIR%"" && echo [RajibLabs API] Starting... && echo URL: %BACKEND_URL% && echo. && dotnet restore && echo. && dotnet run --urls %BACKEND_URL%"

:: Give backend a moment to bind
timeout /t 4 /nobreak >nul
echo   Backend window launched. Check "RajibLabs API" window for logs.
echo.

if /I "%MODE%"=="backend" goto :open_browser

:: -------------------- Start Frontend ---------------------------------------
:start_frontend
echo [3/4] Starting Frontend PWA...
echo   Project : %FRONTEND_DIR%
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

:: -------------------- Open Browser -----------------------------------------
:open_browser
echo [4/4] Opening browser...
timeout /t 3 /nobreak >nul

if /I "%MODE%"=="backend" (
  echo   Opening %BACKEND_URL%/health and swagger...
  start "" "%BACKEND_URL%/health"
  timeout /t 1 /nobreak >nul
  start "" "%BACKEND_URL%/swagger"
) else (
  echo   Opening %FRONTEND_URL%
  start "" "%FRONTEND_URL%"
  echo   Backend health: %BACKEND_URL%/health
)

echo.
color 0A
echo  ==========================================================================
echo    All services launched!
echo  ==========================================================================
echo    Frontend : %FRONTEND_URL%
echo    Network  : http://^<your-ip^>:5173  (Vite will show actual IP - use for PWA on phone)
echo    Backend  : %BACKEND_URL%
echo    Health   : %BACKEND_URL%/health
echo    Swagger  : %BACKEND_URL%/swagger  (if enabled)
echo    Proxy    : Frontend /api -^> %BACKEND_URL%  (see frontend/vite.config.ts)
echo  --------------------------------------------------------------------------
echo    PWA Test : On phone, open Network URL -^> Install prompt appears after ~3s
echo             : Chrome DevTools -^> Application -^> Manifest / Service Workers
echo             : Lighthouse -^> PWA score should be 100
echo  --------------------------------------------------------------------------
echo    WhatsApp : https://wa.me/919876543210  (update in frontend/src/config/site.ts)
echo    Call     : tel:+919876543210
echo  --------------------------------------------------------------------------
echo    To stop  : Close the two new windows OR press Ctrl+C in each
echo             : Or run:  taskkill /FI "WindowTitle eq RajibLabs API*" /T /F
echo             :          taskkill /FI "WindowTitle eq RajibLabs Frontend*" /T /F
echo  ==========================================================================
echo.
echo  Tip: Keep this window open. Press any key to open BOTH URLs again, or close to exit.
pause >nul
start "" "%FRONTEND_URL%"
if not "%MODE%"=="frontend" start "" "%BACKEND_URL%/health"
echo  Re-opened browser tabs. You can close this window now.
timeout /t 3 >nul
exit /b 0

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
echo  run.bat              Start both backend + frontend (default)
echo  run.bat backend      Start backend only  (%BACKEND_URL%)
echo  run.bat frontend     Start frontend only (%FRONTEND_URL%)
echo  run.bat build        Production build + optional preview
echo  run.bat help         Show this help
echo.
echo  Examples:
echo    run.bat
echo    run.bat frontend
echo    run.bat build
echo.
echo  After start:
echo    - Two new cmd windows appear (API + Frontend) - keep them open
echo    - Browser opens automatically to %FRONTEND_URL%
echo    - For PWA on phone: use the Network URL shown in Frontend window
echo.
pause
exit /b 0
