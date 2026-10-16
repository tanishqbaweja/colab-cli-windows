param(
    [switch]$SkipUvBootstrap
)

$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "This installer is for native Windows only."
}

function Find-Uv {
    $command = Get-Command uv -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        (Join-Path $HOME ".local\bin\uv.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\uv\uv.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    return $null
}

$uv = Find-Uv
if (-not $uv -and -not $SkipUvBootstrap) {
    Write-Host "[colab-windows] uv was not found; installing it for the current user..."
    $installer = Invoke-RestMethod https://astral.sh/uv/install.ps1
    Invoke-Expression $installer
    $uv = Find-Uv
}

if (-not $uv) {
    throw "uv is required. Install it, reopen PowerShell, and run this installer again."
}

$requiredOpenSsh = @("ssh", "scp", "ssh-keygen")
$missingOpenSsh = @()
foreach ($command in $requiredOpenSsh) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        $missingOpenSsh += $command
    }
}

if ($missingOpenSsh.Count -gt 0) {
    throw "Windows OpenSSH Client is required. Missing: $($missingOpenSsh -join ', '). Install the Windows optional feature 'OpenSSH Client' and rerun this installer."
}

Push-Location $PSScriptRoot
try {
    Write-Host "[colab-windows] Ensuring Python 3.12 is available..."
    & $uv python install 3.12
    if ($LASTEXITCODE -ne 0) {
        throw "uv could not provision Python 3.12."
    }

    $packageDir = Join-Path $PSScriptRoot "package"
    $bundledWheel = Get-ChildItem $packageDir -Filter "google_colab_cli-*.whl" -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($bundledWheel) {
        $persistentPackageDir = Join-Path $env:LOCALAPPDATA "ColabCLIWindows\packages"
        New-Item -ItemType Directory -Force -Path $persistentPackageDir | Out-Null
        $installTarget = Join-Path $persistentPackageDir $bundledWheel.Name
        Copy-Item $bundledWheel.FullName $installTarget -Force
        Write-Host "[colab-windows] Installing bundled Windows package..."
    }
    else {
        $installTarget = $PSScriptRoot
        Write-Host "[colab-windows] No bundled wheel found; installing from this Git checkout..."
    }

    & $uv tool install --force $installTarget
    if ($LASTEXITCODE -ne 0) {
        throw "uv could not install the Colab CLI."
    }

    $toolBin = (& $uv --color never tool dir --bin).Trim()
    if (-not $toolBin) {
        throw "uv did not report its tool executable directory."
    }

    $colabExe = Join-Path $toolBin "colab.exe"
    if (-not (Test-Path $colabExe)) {
        throw "Installation completed but colab.exe was not found in '$toolBin'."
    }

    Write-Host "[colab-windows] Installed: $colabExe"
    & $colabExe --help *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "The installed colab command failed its smoke test."
    }

    if (-not (Get-Command colab -ErrorAction SilentlyContinue)) {
        Write-Host "[colab-windows] Note: '$toolBin' is not visible in this PowerShell session's PATH yet."
        Write-Host "[colab-windows] Open a new terminal before running 'colab'."
    }

    Write-Host "[colab-windows] Native Windows installation is ready. No WSL is used."
}
finally {
    Pop-Location
}
