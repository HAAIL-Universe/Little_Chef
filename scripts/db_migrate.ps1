param(
  [switch]$NoVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Load-DotEnv {
  param([string]$Path = ".env")
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
  Load-DotEnv
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
