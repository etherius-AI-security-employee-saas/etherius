Param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$agent = Join-Path $root "agent"
$suite = Join-Path $root "suite"
$distRoot = Join-Path $root "release\bin"

Write-Host "[1/5] Preparing backend virtual environment..."
if (-not (Test-Path "$backend\venv\Scripts\python.exe")) {
    python -m venv "$backend\venv"
}

Write-Host "[2/5] Installing build dependencies..."
& "$backend\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$backend\venv\Scripts\python.exe" -m pip install -r "$backend\requirements.txt"
& "$backend\venv\Scripts\python.exe" -m pip install -r "$agent\requirements.txt"
& "$backend\venv\Scripts\python.exe" -m pip install pyinstaller

Write-Host "[3/5] Building dashboard static files..."
Push-Location "$root\dashboard"
npm.cmd install
npm.cmd run build
Pop-Location

if (Test-Path "$root\release") { Remove-Item "$root\release" -Recurse -Force }
New-Item -Path $distRoot -ItemType Directory -Force | Out-Null

Write-Host "[4/5] Building executable binaries..."
Push-Location $root

& "$backend\venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm --clean --onefile --noconsole `
    --name EtheriusSuite `
    --add-data "suite\assets;suite\assets" `
    "suite\app.py"

& "$backend\venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm --clean --onefile --noconsole `
    --name EtheriusShield `
    --add-data "agent\assets;agent\assets" `
    "agent\ui\app.py"

& "$backend\venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm --clean --onefile --noconsole `
    --name EtheriusBackendService `
    --add-data "backend\app;app" `
    --add-data "dashboard\dist;dashboard\dist" `
    "backend\run_backend.py"

Copy-Item "$root\dist\EtheriusSuite.exe" "$distRoot\EtheriusSuite.exe"
Copy-Item "$root\dist\EtheriusShield.exe" "$distRoot\EtheriusShield.exe"
Copy-Item "$root\dist\EtheriusBackendService.exe" "$distRoot\EtheriusBackendService.exe"

Pop-Location

if ($SkipInstaller) {
    Write-Host "[5/5] Skipped installer creation. Binaries ready in $distRoot"
    exit 0
}

Write-Host "[5/5] Building installer (requires Inno Setup)..."
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    throw "Inno Setup not found. Install Inno Setup 6 and rerun this script."
}
& $iscc "$PSScriptRoot\etherius-installer.iss"

Write-Host "Release complete. Installer available in release\installer"
