@echo off
title Etherius Professional Suite
cd /d "%~dp0"

echo Starting Etherius as one software...
echo.

for /f %%A in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue | Measure-Object).Count"') do set PORT_OPEN=%%A

if "%PORT_OPEN%"=="0" (
    echo [startup] Backend is not running. Launching backend service...
    start "Etherius Backend" /min cmd /c "cd /d \"%~dp0\" && START_BACKEND.bat"
    timeout /t 5 >nul
) else (
    echo [startup] Backend already running.
)

start "" http://localhost:8000/dashboard
python -m suite.app
pause
