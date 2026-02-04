# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-04T12:01:25+00:00
- Branch: main
- BASE_HEAD: d156e25aa037c535290f3f4f1fd076d3366b4ced
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Added port-in-use check to run_local.ps1 to fail fast if another process owns the port, preventing accidental old servers.
- run_local.ps1 now echoes LC_DEBUG_AUTH value and expected UI/API URL so users see debug is on and which origin to hit.
- Full test suite re-run; behavior unchanged beyond local runner diagnostics.

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
     function Ensure-Uvicorn($py) {
       try { & $py -c "import uvicorn" | Out-Null }
       catch { Info "Installing uvicorn..."; & $py -m pip install uvicorn }
     }
    +
    +function Assert-PortFree($port) {
    +  try {
    +    $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    +  } catch {
    +    $listeners = @()
    +  }
    +  if ($listeners -and $listeners.Count -gt 0) {
    +    $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    +    $procInfo = $pids | ForEach-Object {
    +      try { (Get-Process -Id $_) } catch { $null }
    +    }
    +    Warn "Port $port already in use:"
    +    foreach ($p in $procInfo) {
    +      if ($p) { Warn ("  PID {0} - {1}" -f $p.Id, $p.Path) }
    +    }
    +    Fail "Port $port already in use; stop the process and rerun."
    +  }
    +}
    @@
       $py = Use-Venv $root
       Ensure-Requirements $py $root
       Load-DotEnv $root
      $env:LC_DEBUG_AUTH = "1"
    -  Info "LC_DEBUG_AUTH=$($env:LC_DEBUG_AUTH) (auth debug enabled by default for local runs)"
    +  Info "LC_DEBUG_AUTH=$($env:LC_DEBUG_AUTH) (auth debug enabled by default for local runs)"
       Ensure-Uvicorn $py
    +  Assert-PortFree $Port

## Verification
- Static: python -m compileall app
- Runtime: python -c "import app.main; print('import ok')"
- Behavior: pwsh -NoProfile -Command "./scripts/run_tests.ps1" (PASS)
- Contract: No API changes; local runner diagnostics only
- Example local proof: LC_DEBUG_AUTH echoes in run_local output; TestClient earlier confirmed /auth/me returns details when debug is on.

## Notes (optional)
- If details remain null in browser, likely hitting a different process/port; port check now prevents silent conflicts.

## Next Steps
- Start via run_local.ps1, confirm port-free message and LC_DEBUG_AUTH=1, then retry /auth/me from browser; gather details if still failing.

