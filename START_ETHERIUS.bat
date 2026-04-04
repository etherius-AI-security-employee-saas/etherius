@echo off
title Etherius Professional Suite
cd /d "%~dp0"

echo Starting Etherius as one software...
echo.

if not exist "%~dp0backend\venv\Scripts\python.exe" (
    echo [setup] Backend runtime not found. Please run Python setup once.
    pause
    exit /b 1
)

netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo [startup] Launching backend service...
    start "Etherius Backend" /min cmd /k "cd /d \"%~dp0backend\" && venv\Scripts\python.exe run_backend.py"
    timeout /t 5 >nul
) else (
    echo [startup] Backend already running.
)

netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo [startup] Minimized launch did not bind port 8000. Opening backend window...
    start "Etherius Backend" cmd /k "cd /d \"%~dp0backend\" && venv\Scripts\python.exe run_backend.py"
    timeout /t 5 >nul
)

start "" http://localhost:8000/dashboard

if exist "%~dp0backend\venv\Scripts\python.exe" (
    "%~dp0backend\venv\Scripts\python.exe" -m suite.app
) else (
    if exist "%~dp0release\bin\EtheriusSuite.exe" (
        start "" "%~dp0release\bin\EtheriusSuite.exe"
    ) else (
        python -m suite.app
    )
)
pause
