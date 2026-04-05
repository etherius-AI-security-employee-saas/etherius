Param(
    [switch]$SkipInstaller,
    [string]$PfxPath = "",
    [string]$PfxPassword = "",
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Etherius Signed Release Builder"
Write-Host "--------------------------------"

if ([string]::IsNullOrWhiteSpace($PfxPath)) {
    $PfxPath = Read-Host "Enter full path to your code-signing .pfx file"
}

if (-not (Test-Path $PfxPath)) {
    throw "PFX file not found: $PfxPath"
}

if ([string]::IsNullOrWhiteSpace($PfxPassword)) {
    $securePassword = Read-Host "Enter PFX password (input hidden)" -AsSecureString
    $marshal = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    try {
        $PfxPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($marshal)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($marshal)
    }
}

$env:ETHERIUS_SIGN_PFX_PATH = $PfxPath
$env:ETHERIUS_SIGN_PFX_PASSWORD = $PfxPassword
$env:ETHERIUS_SIGN_TIMESTAMP_URL = $TimestampUrl

Write-Host ""
Write-Host "Building signed release..."
if ($SkipInstaller) {
    & powershell -ExecutionPolicy Bypass -File (Join-Path $repoRoot "installer\build_release.ps1") -SkipInstaller
} else {
    & powershell -ExecutionPolicy Bypass -File (Join-Path $repoRoot "installer\build_release.ps1")
}

if (-not $SkipInstaller) {
    Write-Host ""
    Write-Host "Verifying installer signature..."
    & powershell -ExecutionPolicy Bypass -File (Join-Path $repoRoot "ceo\VERIFY_RELEASE_SIGNATURE.ps1")
}

Write-Host ""
Write-Host "Done. Signed release process completed."
