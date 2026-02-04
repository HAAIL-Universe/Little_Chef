# run_local.ps1
# Simple local dev runner for Little Chef
# Examples:
#   pwsh -File .\scripts\run_local.ps1
#   pwsh -File .\scripts\run_local.ps1 -ListenHost 0.0.0.0 -Port 8000
#   pwsh -File .\scripts\run_local.ps1 -NoVenv -NoInstall -NoOpen

param(
  [string]$ListenHost = "127.0.0.1",
  [int]$Port = 8000,
  [switch]$NoReload,
  [switch]$NoInstall,
  [switch]$NoVenv,
  [switch]$NoOpen,
  [switch]$DebugAuth
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Info($m) { Write-Host "[run_local] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[run_local] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[run_local] $m" -ForegroundColor Red; exit 1 }

function RepoRoot {
  $base = $PSScriptRoot
  if (-not $base) { $base = Split-Path -Parent $MyInvocation.MyCommand.Path }
  return (Split-Path -Parent $base)
}

function Load-DotEnv($root) {
  $envPath = Join-Path $root ".env"
  if (-not (Test-Path $envPath)) { return }
  Get-Content $envPath | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $parts = $line.Split("=", 2)
    if ($parts.Count -lt 2) { return }
    $key = $parts[0].Trim()
    $val = $parts[1].Trim()
    if ($val.StartsWith('"') -and $val.EndsWith('"')) { $val = $val.Trim('"') }
    elseif ($val.StartsWith("'") -and $val.EndsWith("'")) { $val = $val.Trim("'") }
    if (-not [string]::IsNullOrWhiteSpace($key) -and [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($key))) {
      [Environment]::SetEnvironmentVariable($key, $val, "Process")
    }
  }
}

function Use-Venv($root) {
  if ($NoVenv) { Warn "NoVenv set; using system python"; return "python" }
  $venvPy = Join-Path $root ".venv\\Scripts\\python.exe"
  if (-not (Test-Path $venvPy)) {
    Info "Creating venv at .venv ..."
    python -m venv (Join-Path $root ".venv")
  }
  if (-not (Test-Path $venvPy)) { Fail "venv python not found: $venvPy" }
  return $venvPy
}

function Ensure-Requirements($py, $root) {
  if ($NoInstall) { Warn "NoInstall set; skipping pip install"; return }
  $req = Join-Path $root "requirements.txt"
  if (-not (Test-Path $req)) { Warn "requirements.txt missing; skipping"; return }
  Info "Installing requirements..."
  & $py -m pip install --upgrade pip
  & $py -m pip install -r $req
}

function Ensure-Uvicorn($py) {
  try { & $py -c "import uvicorn" | Out-Null }
  catch { Info "Installing uvicorn..."; & $py -m pip install uvicorn }
}

function Resolve-AppImport($py) {
  foreach ($c in @("app.main:app", "main:app", "app.main:application", "main:application")) {
    $parts = $c.Split(":")
    $mod,$obj = $parts
    try {
      & $py -c "import importlib; m=importlib.import_module('$mod'); getattr(m,'$obj')" 2>$null | Out-Null
      return $c
    } catch { }
  }
  return $null
}

function Open-App($listenHostParam, $port) {
  if ($NoOpen) { return }
  $openHost = if ($listenHostParam -eq "0.0.0.0") { "127.0.0.1" } else { $listenHostParam }
  $url = "http://$openHost`:$port/"
  Info "Opening $url ..."
  Start-Process $url | Out-Null
}

try {
  $root = RepoRoot
  Set-Location $root
  $env:PYTHONPATH = $root
  Info "Repo root: $root"

  $py = Use-Venv $root
  Ensure-Requirements $py $root
  Load-DotEnv $root
  if ($DebugAuth) { $env:LC_DEBUG_AUTH = "1"; Info "LC_DEBUG_AUTH=1 (debug auth headers)" }
  Ensure-Uvicorn $py

  $appImport = Resolve-AppImport $py
  if (-not $appImport) { Fail "Could not resolve ASGI app (expected app.main:app)" }

  $args = @("-m","uvicorn",$appImport,"--host",$ListenHost,"--port",$Port)
  if (-not $NoReload) { $args += "--reload" }

  Info "Starting uvicorn $appImport on http://$ListenHost`:$Port (Reload=$([bool](-not $NoReload)))"
  Open-App $ListenHost $Port
  & $py @args
}
catch {
  Fail $_.Exception.Message
}
