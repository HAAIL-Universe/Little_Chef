# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-04T12:33:00+00:00
- Branch: main
- BASE_HEAD: c4215b81b1a50e2f91c94b50ce7c6addb27d95d5
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Added optional -KillPortListeners to stop any process holding the target port before startup (opt-in).
- Kept shape-safe port guard with richer diagnostics; LC_DEBUG_AUTH still enabled by default.
- Tests re-run to ensure no regressions; script-only change.

## Files Changed (staged)
- scripts/run_local.ps1
- evidence/test_runs.md
- evidence/test_runs_latest.md

## git status -sb
    ## main...origin/main
     M evidence/test_runs.md
     M evidence/test_runs_latest.md
     M scripts/run_local.ps1

## Minimal Diff Hunks
    diff --git a/scripts/run_local.ps1 b/scripts/run_local.ps1
    --- a/scripts/run_local.ps1
    +++ b/scripts/run_local.ps1
    @@
      [switch]$NoVenv,
      [switch]$NoOpen,
      [switch]$DebugAuth,
      [switch]$KillPortListeners
    )
    @@
    function Kill-PortListeners($port) {
      try {
        $listeners = @((Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)) | Where-Object { $_ }
      } catch { $listeners = @() }
      if ($listeners.Count -eq 0) { return }
      $pids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
      foreach ($pidVal in $pids) {
        try {
          Warn ("Killing PID {0} holding port {1}" -f $pidVal, $port)
          Stop-Process -Id $pidVal -Force -ErrorAction Stop
        } catch {
          Warn ("Failed to kill PID {0}: {1}" -f $pidVal, $_.Exception.Message)
        }
      }
    }
    @@
      $env:LC_DEBUG_AUTH = "1"
      Info "LC_DEBUG_AUTH=$($env:LC_DEBUG_AUTH) (auth debug enabled by default for local runs)"
      Ensure-Uvicorn $py
      if ($KillPortListeners) { Kill-PortListeners $Port }
      Assert-PortFree $Port

## Verification
- Static: python -m compileall app
- Runtime: python -c "import app.main; print('import ok')"
- Behavior: pwsh -NoProfile -Command "./scripts/run_tests.ps1" (PASS)
- Runtime intent: run_local.ps1 -NoOpen -NoReload -Port 8001 starts; busy-port path now prints listener + tasklist + Cim info without errors. LC_DEBUG_AUTH still on by default.
- Contract: No API/schema changes.

## Notes (optional)
- Port guard now resilient to null/single/array listener results; diagnostics include tasklist/CIM for clarity.

## Next Steps
- If port is reported busy, stop the listed PID or use a different port; rerun run_local.ps1 and confirm debug details on /auth/me.

