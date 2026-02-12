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
  [switch]$DebugAuth,
  [switch]$KillPortListeners,
  [switch]$Migrate
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

function Assert-PortFree($port) {
  try {
    $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  } catch {
    $listeners = @()
  }
  $listeners = @($listeners) | Where-Object { $_ }
  $listenerCount = ($listeners | Measure-Object).Count
  if ($listenerCount -gt 0) {
    $pids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
    $procInfo = @($pids | ForEach-Object {
      try { (Get-Process -Id $_) } catch { $null }
    })
    Warn "Port $port already in use:"
    foreach ($l in $listeners) {
      Warn ("  Listener {0}:{1} state={2} pid={3}" -f $l.LocalAddress, $l.LocalPort, $l.State, $l.OwningProcess)
    }
    foreach ($p in $procInfo) {
      if ($p) { Warn ("  PID {0} - {1}" -f $p.Id, $p.Path) }
    }
    foreach ($pidVal in $pids) {
      try {
        Warn ("  tasklist for PID {0}:" -f $pidVal)
        tasklist /fi ("PID eq {0}" -f $pidVal) | Out-Host
      } catch { }
      try {
        Warn ("  Get-CimInstance for PID {0}:" -f $pidVal)
        Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $pidVal) | Select-Object ProcessId,ParentProcessId,Name,CommandLine | Format-List | Out-Host
      } catch { }
    }
    Fail "Port $port already in use; stop the process and rerun."
  }
}

function Kill-PortListeners($port) {
  try {
    $listeners = @((Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)) | Where-Object { $_ }
  } catch { $listeners = @() }
  if (($listeners | Measure-Object).Count -eq 0) { return $port }
  $pids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
  foreach ($pidVal in $pids) {
    try {
      Warn ("Killing PID {0} holding port {1}" -f $pidVal, $port)
      Stop-Process -Id $pidVal -Force -ErrorAction Stop
    } catch {
      Warn ("Stop-Process failed for PID {0}: {1}" -f $pidVal, $_.Exception.Message)
    }
    try {
      & taskkill /PID $pidVal /F /T | Out-Null
    } catch { }
  }
  # re-check to confirm clear
  for ($i=0; $i -lt 5; $i++) {
    Start-Sleep -Milliseconds 300
    try {
      $remaining = @((Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)) | Where-Object { $_ }
    } catch { $remaining = @() }
    if (($remaining | Measure-Object).Count -eq 0) { return $port }
  }
  Warn "Port $port still shows a listener after kill attempts (elevation may be required or listener is in another session)."
  return $null
}

function Find-FreePort($start, $span) {
  foreach ($candidate in $start..($start + $span)) {
    try {
      $check = @((Get-NetTCPConnection -LocalPort $candidate -State Listen -ErrorAction SilentlyContinue)) | Where-Object { $_ }
    } catch { $check = @() }
    if (($check | Measure-Object).Count -eq 0) { return $candidate }
  }
  return $null
}

function Run-Migrations($root) {
  $mig = Join-Path $root "scripts/db_migrate.ps1"
  if (-not (Test-Path $mig)) { Warn "Migration script not found at $mig"; return }
  if (-not $env:DATABASE_URL) { Warn "DATABASE_URL not set; skipping migrations"; return }
  Info "Running migrations via $mig"
  & pwsh -NoProfile -File $mig
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
  $env:LC_DEBUG_AUTH = "1"
  Info "LC_DEBUG_AUTH=$($env:LC_DEBUG_AUTH) (auth debug enabled by default for local runs)"
  Ensure-Uvicorn $py
  if ($Migrate) { Run-Migrations $root }
  $desiredPort = $Port
  if ($KillPortListeners) {
    $killResult = Kill-PortListeners $desiredPort
    if ($killResult) { $desiredPort = $killResult }
  }
  # choose a free port — kill stale listeners rather than silently switching
  # (port drift breaks Auth0 callback URLs)
  $freePort = Find-FreePort $desiredPort 0
  if (-not $freePort) {
    Warn "Port $desiredPort busy — killing stale listeners..."
    $killResult = Kill-PortListeners $desiredPort
    $freePort = Find-FreePort $desiredPort 0
    if (-not $freePort) { Fail "Port $desiredPort still busy after kill attempt. Free it manually." }
  }
  $Port = $freePort

  $appImport = Resolve-AppImport $py
  if (-not $appImport) { Fail "Could not resolve ASGI app (expected app.main:app)" }

  $args = @("-m","uvicorn",$appImport,"--host",$ListenHost,"--port",$Port)
  if (-not $NoReload) { $args += "--reload" }

  Info "Starting uvicorn $appImport on http://$ListenHost`:$Port (Reload=$([bool](-not $NoReload)))"
  Info "Expect UI/API at http://127.0.0.1:$Port"
  Open-App $ListenHost $Port
  & $py @args
}
catch {
  Fail $_.Exception.Message
}
