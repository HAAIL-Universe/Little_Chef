# run_local.ps1
# Usage:
#   Drag this file into a PowerShell terminal and press Enter.
#   Or run: .\run_local.ps1
#
# Optional:
#   .\run_local.ps1 -Port 8000 -Host "127.0.0.1" -Reload
#
param(
  [string]$Host = "127.0.0.1",
  [int]$Port = 8000,
  [switch]$Reload = $true,
  [switch]$NoInstall,
  [switch]$NoVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host "[run_local] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[run_local] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[run_local] $msg" -ForegroundColor Red }

function Get-RepoRoot {
  # Repo root assumed to be the directory containing this script.
  return (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

function Use-Venv($root) {
  if ($NoVenv) {
    Write-Warn "NoVenv set; using system Python."
    return $null
  }

  $venvDir = Join-Path $root ".venv"
  $venvPy  = Join-Path $venvDir "Scripts\python.exe"
  if (-not (Test-Path $venvPy)) {
    Write-Info "Creating venv at .venv ..."
    python -m venv $venvDir
  }

  if (-not (Test-Path $venvPy)) {
    throw "Failed to create/find venv python at: $venvPy"
  }

  Write-Info "Using venv python: $venvPy"
  return $venvPy
}

function Install-Requirements($py, $root) {
  if ($NoInstall) {
    Write-Warn "NoInstall set; skipping dependency install."
    return
  }

  $req = Join-Path $root "requirements.txt"
  if (Test-Path $req) {
    Write-Info "Installing/upgrading pip + requirements.txt ..."
    & $py -m pip install --upgrade pip
    & $py -m pip install -r $req
  } else {
    Write-Warn "No requirements.txt found; skipping install."
  }
}

function Load-DotEnv($root) {
  # Optional convenience: load KEY=VALUE lines from .env into process env
  $envPath = Join-Path $root ".env"
  if (-not (Test-Path $envPath)) {
    Write-Warn "No .env found (ok)."
    return
  }

  Write-Info "Loading .env into process environment ..."
  Get-Content $envPath | ForEach-Object {
    $line = $_.Trim()
    if (-not $line) { return }
    if ($line.StartsWith("#")) { return }
    # Split on first '='
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { return }
    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim()

    # Strip surrounding quotes if present
    if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
      $val = $val.Substring(1, $val.Length - 2)
    }

    if ($key) {
      [System.Environment]::SetEnvironmentVariable($key, $val, "Process")
    }
  }
}

function Resolve-AppImport {
  # Preferred module path per blueprint
  $candidates = @(
    "app.main:app",
    "main:app",
    "app.main:application",
    "main:application"
  )

  foreach ($c in $candidates) {
    $parts = $c.Split(":")
    $mod = $parts[0]
    $obj = $parts[1]
    try {
      python -c "import importlib; m=importlib.import_module('$mod'); getattr(m,'$obj')" 2>$null | Out-Null
      return $c
    } catch {
      # ignore
    }
  }

  return $null
}

try {
  $root = Get-RepoRoot
  Set-Location $root
  Write-Info "Repo root: $root"

  $py = Use-Venv $root
  if ($null -eq $py) {
    # fallback to system python
    $py = "python"
  }

  Install-Requirements $py $root
  Load-DotEnv $root

  # Ensure uvicorn exists
  try {
    & $py -c "import uvicorn" | Out-Null
  } catch {
    Write-Info "uvicorn not found; installing uvicorn ..."
    & $py -m pip install uvicorn
  }

  $appImport = Resolve-AppImport
  if (-not $appImport) {
    throw "Could not resolve ASGI app import. Expected app.main:app (preferred). Check your app entrypoint."
  }

  $reloadFlag = ""
  if ($Reload) { $reloadFlag = "--reload" }

  Write-Info "Starting FastAPI via uvicorn: $appImport"
  Write-Info "Host=$Host Port=$Port Reload=$Reload"
  & $py -m uvicorn $appImport --host $Host --port $Port $reloadFlag

} catch {
  Write-Err $_.Exception.Message
  exit 1
}
