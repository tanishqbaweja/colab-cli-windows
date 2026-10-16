param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "release")
)

$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "This release builder is intended for Windows."
}

$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCommand) {
    throw "uv is required to build the portable release."
}

$staging = Join-Path $OutputDirectory "google-colab-cli-windows-portable"
$packageDir = Join-Path $staging "package"
$zipPath = Join-Path $OutputDirectory "google-colab-cli-windows-portable.zip"

if (Test-Path $staging) {
    Remove-Item $staging -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $packageDir | Out-Null

Push-Location $PSScriptRoot
try {
    & $uvCommand.Source build --wheel --out-dir $packageDir
    if ($LASTEXITCODE -ne 0) {
        throw "Wheel build failed."
    }

    Copy-Item (Join-Path $PSScriptRoot "install-windows.ps1") $staging
    Copy-Item (Join-Path $PSScriptRoot "install-windows.cmd") $staging
    Copy-Item (Join-Path $PSScriptRoot "WINDOWS.md") $staging
    if (Test-Path (Join-Path $PSScriptRoot "LICENSE")) {
        Copy-Item (Join-Path $PSScriptRoot "LICENSE") $staging
    }

    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Host "[colab-windows] Portable release: $zipPath"
}
finally {
    Pop-Location
}