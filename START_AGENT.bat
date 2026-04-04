@echo off
title Etherius Agent
color 0E
cd /d "%~dp0agent"

echo Starting Etherius Agent...
echo Make sure agent_config.json or the activation code from the dashboard is configured.
echo.

python -m pip install -r requirements.txt >nul 2>&1
python -m agent.ui.app
pause
