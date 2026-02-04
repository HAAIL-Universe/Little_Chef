# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-04T12:08:59+00:00
- Branch: main
- BASE_HEAD: 03afe0aedd7067ed563d3dd2a8896c36eb63de39
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Fixed run_local.ps1 port check to handle single-object listener results without Count errors and continue failing fast when the port is busy.
- run_local still echoes LC_DEBUG_AUTH=1 and expected UI/API URL to make the active debug backend obvious.
- Re-ran full test suite to confirm no regressions; diagnostics only.

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
      if ($listeners.Count -gt 0) {
        $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
        $procInfo = $pids | ForEach-Object {
          try { (Get-Process -Id $_) } catch { $null }
        }
        Warn "Port $port already in use:"
        foreach ($p in $procInfo) {
          if ($p) { Warn ("  PID {0} - {1}" -f $p.Id, $p.Path) }
        }
        Fail "Port $port already in use; stop the process and rerun."
      }
    }

## Verification
- Static: python -m compileall app
- Runtime: python -c "import app.main; print('import ok')"
- Behavior: pwsh -NoProfile -Command "./scripts/run_tests.ps1" (PASS)
- Contract: No API changes; local runner diagnostics only

## Notes (optional)
- Port check now robust for single-object Get-NetTCPConnection results; prevents silent stale servers.

## Next Steps
- Run run_local.ps1, confirm port-free message, then retry /auth/me to view debug details; stop any other listener if reported.

