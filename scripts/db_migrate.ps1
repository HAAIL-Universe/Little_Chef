param(
  [switch]$NoVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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
  $py = Resolve-Python
  Info "Python: $py"
  & $py -m app.db.migrate
  if ($LASTEXITCODE -ne 0) { throw "Migration failed ($LASTEXITCODE)" }
}
catch {
  Err $_.Exception.Message
  exit 1
}

exit 0
