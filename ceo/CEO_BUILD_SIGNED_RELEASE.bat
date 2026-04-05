@echo off
setlocal
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File "%~dp0BUILD_SIGNED_RELEASE.ps1"
if errorlevel 1 (
  echo.
  echo Signed release build failed.
  pause
  exit /b 1
)
echo.
echo Signed release build completed successfully.
pause
