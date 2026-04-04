@echo off
title Etherius Backend
color 0A
cd /d "%~dp0backend"

echo Starting Etherius Backend...
echo API Docs: http://localhost:8000/docs
echo Dashboard: http://localhost:8000/dashboard
echo.

if not exist venv\Scripts\python.exe (
    echo [setup] Creating local virtual environment...
    python -m venv venv
    if errorlevel 1 goto :fail
)

venv\Scripts\python.exe -m ensurepip --upgrade >nul 2>&1

venv\Scripts\python.exe -c "import fastapi, uvicorn, sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo [setup] Installing backend dependencies...
    venv\Scripts\python.exe -m pip install --upgrade pip
    if errorlevel 1 goto :fail
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 goto :fail
)

if not exist ..\dashboard\dist\index.html (
    echo [setup] Dashboard build not found. Building dashboard...
    cd /d "%~dp0dashboard"
    if not exist node_modules (
        call npm.cmd install
        if errorlevel 1 (
            echo [warn] Dashboard dependencies could not be installed. API will still run.
        )
    )
    if exist node_modules (
        call npm.cmd run build
        if errorlevel 1 echo [warn] Dashboard build failed. API will still run.
    )
    cd /d "%~dp0backend"
)

start "" cmd /c "timeout /t 3 >nul && start http://localhost:8000/docs && start http://localhost:8000/dashboard"
venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
goto :end

:fail
echo.
echo Backend setup failed. Check the messages above and verify that Python is installed.

:end
pause
