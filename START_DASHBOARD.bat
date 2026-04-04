@echo off
title Etherius Dashboard
color 0B
cd /d "%~dp0"

echo Opening Etherius Dashboard...
echo Dashboard: http://localhost:8000/dashboard
echo.

start "" http://localhost:8000/dashboard
echo If page does not load, first run START_BACKEND.bat and keep that window open.
pause
