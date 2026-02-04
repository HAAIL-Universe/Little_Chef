# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-04T12:26:40+00:00
- Branch: main
- BASE_HEAD: 71c1c3da7a4f54f8a0b6d77c8c9dff53fd05cf08
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Made Assert-PortFree fully shape-safe: coercing listener results to array, counting safely, and avoiding $pid naming issues.
- Added clearer diagnostics when port is busy: listener lines plus tasklist and Get-CimInstance info.
- Verified run_local no longer throws Count/Length errors; test suite remains green.

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
    function Assert-PortFree($port) {
      try {
        $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
      } catch {
        $listeners = @()
      }
      $listeners = @($listeners) | Where-Object { $_ }
      $listenerCount = @($listeners).Count
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

## Verification
- Static: python -m compileall app
- Runtime: python -c "import app.main; print('import ok')"
- Behavior: pwsh -NoProfile -Command "./scripts/run_tests.ps1" (PASS)
- Runtime intent: run_local.ps1 -Port 8001 starts (timeout was due to uvicorn running, no Count/Length errors observed); busy-port path now prints listener + tasklist + Cim info.
- Contract: No API/schema changes.

## Notes (optional)
- Port guard now resilient to null/single/array listener results; diagnostics include tasklist/CIM for clarity.

## Next Steps
- If port is reported busy, stop the listed PID or use a different port; rerun run_local.ps1 and confirm debug details on /auth/me.

