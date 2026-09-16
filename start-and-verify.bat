@echo off
title RajibLabs - Start & Verify

echo.
echo  ============================================================
echo   RajibLabs MCP + Orchestrator — Start & Verify
echo  ============================================================
echo.

echo [1/3] Starting Docker stack...
docker compose up -d --build
if "%errorlevel%" neq "0" (
  echo   [ERROR] Docker compose failed.
  pause
  exit /b 1
)

echo.
echo [2/3] Waiting for services (30s)...
timeout /t 30 /nobreak >nul

echo.
echo [3/3] Running verification...
echo.
python verify_system.py

echo.
pause
