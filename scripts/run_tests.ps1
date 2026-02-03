param(
  [switch]$NoVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Info($msg) { Write-Host "[run_tests] $msg" -ForegroundColor Cyan }
function Err($msg)  { Write-Host "[run_tests] $msg" -ForegroundColor Red }

function Resolve-Python {
  if (-not $NoVenv) {
    $venvPy = Join-Path $PSScriptRoot "..\\..\\LittleChef\\.venv\\Scripts\\python.exe"
    $localVenv = Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\\Scripts\\python.exe"
    foreach ($path in @($localVenv, $venvPy)) {
      if (Test-Path $path) { return $path }
    }
  }
  return "python"
}

try {
  $root = Resolve-Path (Join-Path $PSScriptRoot "..")
  Set-Location $root
  $py = Resolve-Python
  Info "Python: $py"

  & $py -m compileall app
  if ($LASTEXITCODE -ne 0) { throw "compileall failed" }
  Info "compileall app: ok"

  & $py -c "import app.main; print('import ok')"
  if ($LASTEXITCODE -ne 0) { throw "import app.main failed" }
  Info "import app.main: ok"

  & $py -m pytest -q
  if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
  Info "pytest: ok"
}
catch {
  Err $_.Exception.Message
  exit 1
}
