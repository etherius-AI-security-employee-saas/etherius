@echo off
title Stop Etherius Backend
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%P /F >nul 2>&1
)
echo Etherius backend stopped (if it was running).
pause
