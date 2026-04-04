Param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$agent = Join-Path $root "agent"
$distRoot = Join-Path $root "release\bin"
$pyiWork = Join-Path $root "build\pyinstaller"
$suiteAssets = Join-Path $root "suite\assets"
$agentAssets = Join-Path $root "agent\assets"
$suiteEntry = Join-Path $root "suite\app.py"

Write-Host "[1/4] Preparing backend virtual environment..."
if (-not (Test-Path "$backend\venv\Scripts\python.exe")) {
    python -m venv "$backend\venv"
}

Write-Host "[2/4] Installing build dependencies..."
& "$backend\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$backend\venv\Scripts\python.exe" -m pip install -r "$agent\requirements.txt"
& "$backend\venv\Scripts\python.exe" -m pip install pyinstaller

if (Test-Path "$root\release") { Remove-Item "$root\release" -Recurse -Force }
if (Test-Path $pyiWork) { Remove-Item $pyiWork -Recurse -Force }
New-Item -Path $distRoot -ItemType Directory -Force | Out-Null
New-Item -Path $pyiWork -ItemType Directory -Force | Out-Null

Write-Host "[3/4] Building unified executable..."
Push-Location $root

& "$backend\venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm --clean --onefile --noconsole `
    --specpath "$pyiWork" `
    --workpath "$pyiWork\work" `
    --distpath "$pyiWork\dist" `
    --name EtheriusSuite `
    --icon "$suiteAssets\etherius-suite.ico" `
    --add-data "$suiteAssets;suite\assets" `
    --add-data "$agentAssets;agent\assets" `
    "$suiteEntry"

Copy-Item "$pyiWork\dist\EtheriusSuite.exe" "$distRoot\EtheriusSuite.exe"
Copy-Item "$agent\agent_config.json" "$distRoot\agent_config.json"

Pop-Location

if ($SkipInstaller) {
    Write-Host "[4/4] Skipped installer creation. Unified binary ready in $distRoot"
    exit 0
}

Write-Host "[4/4] Building installer (requires Inno Setup)..."
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    throw "Inno Setup not found. Install Inno Setup 6 and rerun this script."
}
& $iscc "$PSScriptRoot\etherius-installer.iss"

Write-Host "Release complete. Installer available in release\installer"
