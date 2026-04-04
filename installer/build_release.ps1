Param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$agent = Join-Path $root "agent"
$distRoot = Join-Path $root "release\bin"
$installerOut = Join-Path $root "release\installer\Etherius-Setup.exe"
$pyiWork = Join-Path $root "build\pyinstaller"
$suiteAssets = Join-Path $root "suite\assets"
$agentAssets = Join-Path $root "agent\assets"
$suiteEntry = Join-Path $root "suite\app.py"

$signThumbprint = ""
if ($env:ETHERIUS_SIGN_CERT_SHA1) { $signThumbprint = $env:ETHERIUS_SIGN_CERT_SHA1.Trim() }

$signPfxPath = ""
if ($env:ETHERIUS_SIGN_PFX_PATH) { $signPfxPath = $env:ETHERIUS_SIGN_PFX_PATH.Trim() }
$signPfxPassword = $env:ETHERIUS_SIGN_PFX_PASSWORD
$timestampUrl = "http://timestamp.digicert.com"
if ($env:ETHERIUS_SIGN_TIMESTAMP_URL) { $timestampUrl = $env:ETHERIUS_SIGN_TIMESTAMP_URL.Trim() }

function Find-SignTool {
    $explicit = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
    if ($explicit) { return $explicit.Source }

    $paths = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin",
        "${env:ProgramFiles}\Windows Kits\10\bin"
    ) | Where-Object { $_ -and (Test-Path $_) }

    foreach ($base in $paths) {
        $match = Get-ChildItem -Path $base -Recurse -Filter "signtool.exe" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match "\\x64\\signtool.exe$" } |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($match) { return $match.FullName }
    }
    return $null
}

function Get-SigningMode {
    if ($signPfxPath) {
        if (-not (Test-Path $signPfxPath)) {
            throw "Signing PFX file not found: $signPfxPath"
        }
        return "pfx"
    }
    if ($signThumbprint) {
        return "thumbprint"
    }
    return "none"
}

function Sign-Binary {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath
    )

    $mode = Get-SigningMode
    if ($mode -eq "none") {
        Write-Host "[SIGN] Skipped signing for $FilePath (no signing certificate configured)."
        return
    }

    $signtool = Find-SignTool
    if (-not $signtool) {
        throw "signtool.exe not found. Install Windows SDK and retry signing."
    }

    if (-not (Test-Path $FilePath)) {
        throw "Cannot sign missing file: $FilePath"
    }

    Write-Host "[SIGN] Signing $FilePath"
    if ($mode -eq "pfx") {
        if ([string]::IsNullOrEmpty($signPfxPassword)) {
            & $signtool sign /fd SHA256 /tr $timestampUrl /td SHA256 /f $signPfxPath $FilePath
        } else {
            & $signtool sign /fd SHA256 /tr $timestampUrl /td SHA256 /f $signPfxPath /p $signPfxPassword $FilePath
        }
    } else {
        & $signtool sign /fd SHA256 /tr $timestampUrl /td SHA256 /sha1 $signThumbprint $FilePath
    }

    $sig = Get-AuthenticodeSignature $FilePath
    if ($sig.Status -ne "Valid") {
        throw "Signature verification failed for $FilePath. Status: $($sig.Status)"
    }
    Write-Host "[SIGN] Signature valid for $FilePath"
}

Write-Host "[1/5] Preparing backend virtual environment..."
if (-not (Test-Path "$backend\venv\Scripts\python.exe")) {
    python -m venv "$backend\venv"
}

Write-Host "[2/5] Installing build dependencies..."
& "$backend\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$backend\venv\Scripts\python.exe" -m pip install -r "$agent\requirements.txt"
& "$backend\venv\Scripts\python.exe" -m pip install pyinstaller

if (Test-Path "$root\release") { Remove-Item "$root\release" -Recurse -Force }
if (Test-Path $pyiWork) { Remove-Item $pyiWork -Recurse -Force }
New-Item -Path $distRoot -ItemType Directory -Force | Out-Null
New-Item -Path $pyiWork -ItemType Directory -Force | Out-Null

Write-Host "[3/5] Building unified executable..."
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

Write-Host "[4/5] Applying code signing (if configured)..."
Sign-Binary "$distRoot\EtheriusSuite.exe"

if ($SkipInstaller) {
    Write-Host "[5/5] Skipped installer creation. Unified binary ready in $distRoot"
    exit 0
}

Write-Host "[5/5] Building installer (requires Inno Setup)..."
$isccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
)
$iscc = $null
foreach ($candidate in $isccCandidates) {
    if (Test-Path $candidate) {
        $iscc = $candidate
        break
    }
}
if (-not $iscc) {
    $isccCmd = Get-Command "iscc.exe" -ErrorAction SilentlyContinue
    if ($isccCmd) {
        $iscc = $isccCmd.Source
    }
}
if (-not $iscc) {
    throw "Inno Setup not found. Install Inno Setup 6 and rerun this script."
}
& $iscc "$PSScriptRoot\etherius-installer.iss"

Sign-Binary $installerOut

$signature = Get-AuthenticodeSignature $installerOut
Write-Host "Release complete. Installer available in release\installer"
Write-Host "Installer signature status: $($signature.Status)"
if ($signature.Status -ne "Valid") {
    Write-Warning "Unsigned or invalidly signed installers trigger SmartScreen warnings. Configure OV/EV signing certificate."
}
