Param(
    [string]$InstallerPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($InstallerPath)) {
    $InstallerPath = Join-Path $repoRoot "release\installer\Etherius-Setup.exe"
}

$resolved = Resolve-Path $InstallerPath -ErrorAction Stop
$sig = Get-AuthenticodeSignature $resolved

Write-Host "File: $($sig.Path)"
Write-Host "Status: $($sig.Status)"
Write-Host "Message: $($sig.StatusMessage)"

if ($sig.Status -ne "Valid") {
    throw "Release is not properly signed. Do not distribute this installer."
}
