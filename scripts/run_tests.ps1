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

function Tail-Lines([string[]]$lines, [int]$n) {
  if (-not $lines) { return @() }
  if ($lines.Count -le $n) { return $lines }
  return $lines[($lines.Count - $n)..($lines.Count - 1)]
}

function Append-TestRunLog(
  [string]$root,
  [string]$statusText,
  [string]$pythonPath,
  [string]$startUtc,
  [string]$endUtc,
  [int]$compileExit,
  [int]$importExit,
  [int]$pytestExit,
  [string]$pytestSummary,
  [int]$playwrightTestExit,
  [string]$playwrightTestSummary,
  [string]$gitBranch,
  [string]$gitHead,
  [string]$gitStatus,
  [string]$gitDiffStat,
  [string]$failurePayload = ""
) {
  $logPath = Join-Path $root "evidence\test_runs.md"
  $logDir = Split-Path -Parent $logPath
  if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }

  $lines = @()
  $lines += "## Test Run $startUtc"
  $lines += "- Status: $statusText"
  $lines += "- Start: $startUtc"
  $lines += "- End: $endUtc"
  $lines += "- Python: $pythonPath"
  $lines += "- Branch: $gitBranch"
  $lines += "- HEAD: $gitHead"
  $lines += "- compileall exit: $compileExit"
  $lines += "- import app.main exit: $importExit"
  $lines += "- pytest exit: $pytestExit"
  $lines += "- pytest summary: $pytestSummary"
  $lines += "- playwright test:e2e exit: $playwrightTestExit"
  $lines += "- playwright summary: $playwrightTestSummary"
  $lines += "- git status -sb:"
  $lines += '```'
  $lines += $gitStatus
  $lines += '```'
  $lines += "- git diff --stat:"
  $lines += '```'
  $lines += $gitDiffStat
  $lines += '```'
  if ($statusText -eq "FAIL" -and $failurePayload) {
    $lines += "- Failure payload:"
    $lines += '```'
    $lines += $failurePayload
    $lines += '```'
  }
  $lines += ""

  Add-Content -LiteralPath $logPath -Value $lines -Encoding utf8
}

function Write-TestRunLatest(
  [string]$root,
  [string]$statusText,
  [string]$pythonPath,
  [string]$startUtc,
  [string]$endUtc,
  [int]$compileExit,
  [int]$importExit,
  [int]$pytestExit,
  [string]$pytestSummary,
  [int]$playwrightTestExit,
  [string]$playwrightTestSummary,
  [string]$failingTests,
  [string]$gitBranch,
  [string]$gitHead,
  [string]$gitStatus,
  [string]$gitDiffStat,
  [string]$failurePayload = ""
) {
  $logPath = Join-Path $root "evidence\test_runs_latest.md"
  $logDir = Split-Path -Parent $logPath
  if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }

  $lines = @()
  $lines += "Status: $statusText"
  $lines += "Start: $startUtc"
  $lines += "End: $endUtc"
  $lines += "Branch: $gitBranch"
  $lines += "HEAD: $gitHead"
  $lines += "Python: $pythonPath"
  $lines += "compileall exit: $compileExit"
  $lines += "import app.main exit: $importExit"
  $lines += "pytest exit: $pytestExit"
  $lines += "pytest summary: $pytestSummary"
  $lines += "playwright test:e2e exit: $playwrightTestExit"
  $lines += "playwright summary: $playwrightTestSummary"
  if ($statusText -eq "FAIL") {
    $lines += "Failing tests:"
    if ($failingTests) {
      $lines += $failingTests
    } else {
      $lines += "(see console output)"
    }
    if ($failurePayload) {
      $lines += "Failure payload:"
      $lines += '```'
      $lines += $failurePayload
      $lines += '```'
    }
  }
  $lines += "git status -sb:"
  $lines += '```'
  $lines += $gitStatus
  $lines += '```'
  $lines += "git diff --stat:"
  $lines += '```'
  $lines += $gitDiffStat
  $lines += '```'
  $lines += ""

  Set-Content -LiteralPath $logPath -Value $lines -Encoding utf8
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root
Load-DotEnv
$py = Resolve-Python
Info "Python: $py"

$startUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$compileExit = -1
$importExit = -1
$pytestExit = -1
$pytestSummary = "(not run)"
$statusText = "FAIL"
$failingTests = ""
$failurePayload = ""
$playwrightInstallExit = -1
$playwrightTestExit = -1
$playwrightTestSummary = "(not run)"
$playwrightLines = @()

$gitBranch = "git unavailable"
$gitHead = "git unavailable"
$gitStatus = "git unavailable"
$gitDiffStat = "git unavailable"

try {
  $gitBranch = (& git rev-parse --abbrev-ref HEAD 2>$null)
  if ($LASTEXITCODE -ne 0 -or -not $gitBranch) { $gitBranch = "git unavailable" }
  $gitHead = (& git rev-parse HEAD 2>$null)
  if ($LASTEXITCODE -ne 0 -or -not $gitHead) { $gitHead = "git unavailable" }
  $gitStatus = (& git status -sb 2>$null)
  if ($LASTEXITCODE -ne 0 -or -not $gitStatus) { $gitStatus = "git unavailable" }
  $gitDiffStat = (& git diff --stat 2>$null)
  if ($LASTEXITCODE -ne 0) { $gitDiffStat = "git unavailable" }
}
catch {
  $gitBranch = "git unavailable"
  $gitHead = "git unavailable"
  $gitStatus = "git unavailable"
  $gitDiffStat = "git unavailable"
}

try {
  $compileOutLines = & $py -m compileall app 2>&1
  $compileExit = $LASTEXITCODE
  if ($compileExit -eq 0) { Info "compileall app: ok" } else { Err "compileall failed ($compileExit)" }

  $importOutLines = & $py -c "import app.main; print('import ok')" 2>&1
  $importExit = $LASTEXITCODE
  if ($importExit -eq 0) { Info "import app.main: ok" } else { Err "import app.main failed ($importExit)" }

  $pytestLines = @()
  $pytestOutput = & $py -m pytest -q 2>&1 | Tee-Object -Variable pytestLines
  $pytestExit = $LASTEXITCODE
  $nonEmpty = $pytestLines | Where-Object { $_ -and $_.Trim().Length -gt 0 }
  if ($nonEmpty.Count -gt 0) { $pytestSummary = $nonEmpty[-1] }
  if ($pytestExit -ne 0) {
    $failingTests = ($nonEmpty | Where-Object { $_ -match "FAILED" -or $_ -match "::" }) -join "`n"
  }
  if ($pytestExit -eq 0) { Info "pytest: ok" } else { Err "pytest failed ($pytestExit)" }

  Info "npm --prefix web run build"
  & npm --prefix web run build
  Info "node scripts/ui_proposal_renderer_test.mjs"
  & node "$PSScriptRoot\ui_proposal_renderer_test.mjs"
  Info "npm --prefix web exec playwright install --with-deps"
  & npm --prefix web exec playwright install --with-deps
  $playwrightInstallExit = $LASTEXITCODE
  if ($playwrightInstallExit -ne 0) { Err "playwright install failed ($playwrightInstallExit)" }
  Info "npm --prefix web run test:e2e"
  $playwrightLines = & npm --prefix web run test:e2e 2>&1
  $playwrightTestExit = $LASTEXITCODE
  if ($playwrightLines) { $playwrightLines | ForEach-Object { Write-Host $_ } }
  $nonEmptyPlaywright = $playwrightLines | Where-Object { $_ -and $_.Trim().Length -gt 0 }
  if ($nonEmptyPlaywright.Count -gt 0) { $playwrightTestSummary = $nonEmptyPlaywright[-1] }
  if ($playwrightTestExit -eq 0) {
    Info "playwright test:e2e: ok"
  } else {
    Err "playwright test:e2e failed ($playwrightTestExit)"
  }
}
finally {
  $endUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  $overall = 0
  foreach ($code in @($compileExit, $importExit, $pytestExit, $playwrightTestExit)) {
    if ($code -ne 0) { $overall = 1 }
  }
  if ($overall -eq 0) { $statusText = "PASS" } else { $statusText = "FAIL" }

  if ($statusText -eq "FAIL") {
    $sections = @()
    if ($compileExit -ne 0) {
      $sections += @("=== compileall (exit $compileExit) ===")
      $sections += (Tail-Lines $compileOutLines 200)
    }
    if ($importExit -ne 0) {
      $sections += @("=== import app.main (exit $importExit) ===")
      $sections += (Tail-Lines $importOutLines 200)
    }
    if ($pytestExit -ne 0) {
      $sections += @("=== pytest (exit $pytestExit) ===")
      $sections += (Tail-Lines $pytestLines 200)
    }
    if ($playwrightTestExit -ne 0) {
      $sections += @("=== playwright test:e2e (exit $playwrightTestExit) ===")
      $sections += (Tail-Lines $playwrightLines 200)
    }
    $failurePayload = ($sections -join "`n").Trim()
  }

  Append-TestRunLog -root $root -statusText $statusText -pythonPath $py -startUtc $startUtc -endUtc $endUtc `
    -compileExit $compileExit -importExit $importExit -pytestExit $pytestExit -pytestSummary $pytestSummary `
    -playwrightTestExit $playwrightTestExit -playwrightTestSummary $playwrightTestSummary `
    -gitBranch $gitBranch -gitHead $gitHead -gitStatus ($gitStatus -join "`n") -gitDiffStat ($gitDiffStat -join "`n") `
    -failurePayload $failurePayload

  Write-TestRunLatest -root $root -statusText $statusText -pythonPath $py -startUtc $startUtc -endUtc $endUtc `
    -compileExit $compileExit -importExit $importExit -pytestExit $pytestExit -pytestSummary $pytestSummary `
    -playwrightTestExit $playwrightTestExit -playwrightTestSummary $playwrightTestSummary `
    -failingTests $failingTests -gitBranch $gitBranch -gitHead $gitHead -gitStatus ($gitStatus -join "`n") -gitDiffStat ($gitDiffStat -join "`n") `
    -failurePayload $failurePayload

  if ($overall -ne 0) { exit 1 } else { exit 0 }
}
