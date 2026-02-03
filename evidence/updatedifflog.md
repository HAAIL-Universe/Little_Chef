# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-03T12:02:53+00:00
- Branch: main
- HEAD: 5dc7e4300b880cf46032e3a1d89bc419bd64b862
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Tooling: test run history logging
- run_tests.ps1 appends to evidence/test_runs.md each run
- builder_contract updated with test-run logging gate

## Files Changed (staged)
- Contracts/builder_contract.md
- evidence/test_runs.md
- scripts/run_tests.ps1

## git status -sb
    ## main...origin/main [ahead 6]
    M  Contracts/builder_contract.md
    A  evidence/test_runs.md
    M  scripts/run_tests.ps1

## Minimal Diff Hunks
    diff --git a/Contracts/builder_contract.md b/Contracts/builder_contract.md
    index b4758c0..d4968da 100644
    --- a/Contracts/builder_contract.md
    +++ b/Contracts/builder_contract.md
    @@ -163,6 +163,7 @@ When a reliable, maintained component exists (auth, storage, ingestion, UI widge
     - Create/maintain a PowerShell test runner at: `scripts/run_tests.ps1`.
     - The test runner must be updated whenever new tests are added or existing test layout changes.
     - The test runner must run the full deterministic suite used for “bulk” verification.
    +- Each invocation of `scripts/run_tests.ps1` must append a timestamped entry to `evidence/test_runs.md` capturing start/end time (UTC), python path, branch/HEAD (or “git unavailable”), git status/diff stat, and exit codes/summaries for compileall, import sanity, and pytest. The log MUST append (never overwrite) even when a step fails.
     
     Minimum required behavior for `scripts/run_tests.ps1`:
     - Run static sanity for the backend (compile/import)
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    new file mode 100644
    index 0000000..29380ce
    --- /dev/null
    +++ b/evidence/test_runs.md
    @@ -0,0 +1,47 @@
    +## Test Run 2026-02-03T12:02:17Z
    +- Start: 2026-02-03T12:02:17Z
    +- End: 2026-02-03T12:02:20Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 5dc7e4300b880cf46032e3a1d89bc419bd64b862
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 10 passed, 1 warning in 0.19s
    +- git status -sb:
    +```
    +## main...origin/main [ahead 6]
    + M Contracts/builder_contract.md
    + M scripts/run_tests.ps1
    +```
    +- git diff --stat:
    +```
    + Contracts/builder_contract.md |   1 +
    + scripts/run_tests.ps1         | 109 ++++++++++++++++++++++++++++++++++++------
    + 2 files changed, 96 insertions(+), 14 deletions(-)
    +```
    +
    +## Test Run 2026-02-03T12:02:26Z
    +- Start: 2026-02-03T12:02:26Z
    +- End: 2026-02-03T12:02:28Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 5dc7e4300b880cf46032e3a1d89bc419bd64b862
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 10 passed, 1 warning in 0.19s
    +- git status -sb:
    +```
    +## main...origin/main [ahead 6]
    + M Contracts/builder_contract.md
    + M scripts/run_tests.ps1
    +?? evidence/test_runs.md
    +```
    +- git diff --stat:
    +```
    + Contracts/builder_contract.md |   1 +
    + scripts/run_tests.ps1         | 109 ++++++++++++++++++++++++++++++++++++------
    + 2 files changed, 96 insertions(+), 14 deletions(-)
    +```
    +
    diff --git a/scripts/run_tests.ps1 b/scripts/run_tests.ps1
    index fe6c7c3..aceb661 100644
    --- a/scripts/run_tests.ps1
    +++ b/scripts/run_tests.ps1
    @@ -19,25 +19,106 @@ function Resolve-Python {
       return "python"
     }
     
    +function Append-TestRunLog(
    +  [string]$root,
    +  [string]$pythonPath,
    +  [string]$startUtc,
    +  [string]$endUtc,
    +  [int]$compileExit,
    +  [int]$importExit,
    +  [int]$pytestExit,
    +  [string]$pytestSummary,
    +  [string]$gitBranch,
    +  [string]$gitHead,
    +  [string]$gitStatus,
    +  [string]$gitDiffStat
    +) {
    +  $logPath = Join-Path $root "evidence\test_runs.md"
    +  $logDir = Split-Path -Parent $logPath
    +  if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
    +
    +  $lines = @()
    +  $lines += "## Test Run $startUtc"
    +  $lines += "- Start: $startUtc"
    +  $lines += "- End: $endUtc"
    +  $lines += "- Python: $pythonPath"
    +  $lines += "- Branch: $gitBranch"
    +  $lines += "- HEAD: $gitHead"
    +  $lines += "- compileall exit: $compileExit"
    +  $lines += "- import app.main exit: $importExit"
    +  $lines += "- pytest exit: $pytestExit"
    +  $lines += "- pytest summary: $pytestSummary"
    +  $lines += "- git status -sb:"
    +  $lines += '```'
    +  $lines += $gitStatus
    +  $lines += '```'
    +  $lines += "- git diff --stat:"
    +  $lines += '```'
    +  $lines += $gitDiffStat
    +  $lines += '```'
    +  $lines += ""
    +
    +  Add-Content -LiteralPath $logPath -Value $lines -Encoding utf8
    +}
    +
    +$root = Resolve-Path (Join-Path $PSScriptRoot "..")
    +Set-Location $root
    +$py = Resolve-Python
    +Info "Python: $py"
    +
    +$startUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    +$compileExit = -1
    +$importExit = -1
    +$pytestExit = -1
    +$pytestSummary = "(not run)"
    +
    +$gitBranch = "git unavailable"
    +$gitHead = "git unavailable"
    +$gitStatus = "git unavailable"
    +$gitDiffStat = "git unavailable"
    +
     try {
    -  $root = Resolve-Path (Join-Path $PSScriptRoot "..")
    -  Set-Location $root
    -  $py = Resolve-Python
    -  Info "Python: $py"
    +  $gitBranch = (& git rev-parse --abbrev-ref HEAD 2>$null)
    +  if ($LASTEXITCODE -ne 0 -or -not $gitBranch) { $gitBranch = "git unavailable" }
    +  $gitHead = (& git rev-parse HEAD 2>$null)
    +  if ($LASTEXITCODE -ne 0 -or -not $gitHead) { $gitHead = "git unavailable" }
    +  $gitStatus = (& git status -sb 2>$null)
    +  if ($LASTEXITCODE -ne 0 -or -not $gitStatus) { $gitStatus = "git unavailable" }
    +  $gitDiffStat = (& git diff --stat 2>$null)
    +  if ($LASTEXITCODE -ne 0) { $gitDiffStat = "git unavailable" }
    +}
    +catch {
    +  $gitBranch = "git unavailable"
    +  $gitHead = "git unavailable"
    +  $gitStatus = "git unavailable"
    +  $gitDiffStat = "git unavailable"
    +}
     
    +try {
       & $py -m compileall app
    -  if ($LASTEXITCODE -ne 0) { throw "compileall failed" }
    -  Info "compileall app: ok"
    +  $compileExit = $LASTEXITCODE
    +  if ($compileExit -eq 0) { Info "compileall app: ok" } else { Err "compileall failed ($compileExit)" }
     
       & $py -c "import app.main; print('import ok')"
    -  if ($LASTEXITCODE -ne 0) { throw "import app.main failed" }
    -  Info "import app.main: ok"
    +  $importExit = $LASTEXITCODE
    +  if ($importExit -eq 0) { Info "import app.main: ok" } else { Err "import app.main failed ($importExit)" }
     
    -  & $py -m pytest -q
    -  if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
    -  Info "pytest: ok"
    +  $pytestLines = @()
    +  $pytestOutput = & $py -m pytest -q 2>&1 | Tee-Object -Variable pytestLines
    +  $pytestExit = $LASTEXITCODE
    +  $nonEmpty = $pytestLines | Where-Object { $_ -and $_.Trim().Length -gt 0 }
    +  if ($nonEmpty.Count -gt 0) { $pytestSummary = $nonEmpty[-1] }
    +  if ($pytestExit -eq 0) { Info "pytest: ok" } else { Err "pytest failed ($pytestExit)" }
     }
    -catch {
    -  Err $_.Exception.Message
    -  exit 1
    +finally {
    +  $endUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    +  Append-TestRunLog -root $root -pythonPath $py -startUtc $startUtc -endUtc $endUtc `
    +    -compileExit $compileExit -importExit $importExit -pytestExit $pytestExit -pytestSummary $pytestSummary `
    +    -gitBranch $gitBranch -gitHead $gitHead -gitStatus ($gitStatus -join "`n") -gitDiffStat ($gitDiffStat -join "`n")
    +
    +  $overall = 0
    +  foreach ($code in @($compileExit, $importExit, $pytestExit)) {
    +    if ($code -ne 0) { $overall = 1 }
    +  }
    +  if ($overall -ne 0) { exit 1 } else { exit 0 }
     }

## Verification
- run_tests.ps1 first run: pass (compile/import/pytest)
- run_tests.ps1 second run: pass (append-only confirmed)
- contract: builder_contract updated to mandate logging

## Notes (optional)
- TODO: blockers, risks, constraints.

## Next Steps
- Phase 4: recipes upload + retrieval scaffolding with citations

