@echo off
title Etherius Setup - Windows
color 0A
echo.
echo  ===================================================
echo   ETHERIUS - Windows Setup Script
echo  ===================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

:: Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found

echo.
echo [1/4] Installing backend dependencies...
cd backend
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)
echo [OK] Backend dependencies installed

echo.
echo [2/4] Initializing database...
python init_db.py
if %errorlevel% neq 0 (
    echo [ERROR] Database init failed. Check PostgreSQL is running and .env is correct.
    pause
    exit /b 1
)
echo [OK] Database ready

echo.
echo [3/4] Installing dashboard dependencies...
cd ..\dashboard
call npm install --silent
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed
    pause
    exit /b 1
)
echo [OK] Dashboard dependencies installed

cd ..
echo.
echo  ===================================================
echo   SETUP COMPLETE!
echo  ===================================================
echo.
echo  Now run:  START_ALL.bat
echo.
pause
