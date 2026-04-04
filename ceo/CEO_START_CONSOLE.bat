@echo off
title Etherius CEO Control Console
cd /d "%~dp0\.."

if exist "backend\venv\Scripts\python.exe" (
  backend\venv\Scripts\python.exe -m ceo.ceo_console
) else (
  python -m ceo.ceo_console
)
