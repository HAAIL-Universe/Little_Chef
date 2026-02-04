param(
  [switch]$NoVenv,
  [switch]$ValidateOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Load-EnvFile {
  param([string]$Path)
  if (-not (Test-Path $Path)) { return }
  Get-Content -Path $Path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line) { return }
    if ($line.StartsWith("#")) { return }
    $parts = $line.Split("=", 2)
    if ($parts.Count -lt 2) { return }
    $key = $parts[0].Trim()
    $val = $parts[1].Trim()
    if ($val.StartsWith('"') -and $val.EndsWith('"')) { $val = $val.Trim('"') }
    elseif ($val.StartsWith("'") -and $val.EndsWith("'")) { $val = $val.Trim("'") }
    if (-not $key) { return }
    if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($key))) {
      [Environment]::SetEnvironmentVariable($key, $val)
    }
  }
}

function Info($m) { Write-Host "[db_migrate] $m" -ForegroundColor Cyan }
function Err ($m) { Write-Host "[db_migrate] $m" -ForegroundColor Red }

function Resolve-Python {
  if (-not $NoVenv) {
    $localVenv = Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\\Scripts\\python.exe"
    if (Test-Path $localVenv) { return $localVenv }
  }
  return "python"
}

try {
  $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
  $envPath = Join-Path $repoRoot ".env"
  Load-EnvFile -Path $envPath

  if (-not $env:DATABASE_URL) {
    Err "DATABASE_URL not set; set it in .env or the environment before running migrations."
    exit 1
  } else {
    Info "DATABASE_URL present (value not printed)."
  }

  if ($ValidateOnly) {
    $sqlPath = Join-Path $repoRoot "db/migrations/0001_init.sql"
    if (-not (Test-Path $sqlPath)) {
      Err "Migration file not found at $sqlPath"
      exit 1
    }
    Info ".env load check complete; migration file exists. ValidateOnly exiting."
    exit 0
  }

  $py = Resolve-Python
  Info "Python: $py"
  Push-Location $repoRoot
  try {
    & $py -m app.db.migrate
    if ($LASTEXITCODE -ne 0) { throw "Migration failed ($LASTEXITCODE)" }
  }
  finally {
    Pop-Location
  }
}
catch {
  Err $_.Exception.Message
  exit 1
}

exit 0
