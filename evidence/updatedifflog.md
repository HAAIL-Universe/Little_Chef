# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-04T11:43:27+00:00
- Branch: main
- BASE_HEAD: 9d4e801a9b54259b0e52a4d5c4f3202a3383b0eb
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Defaulted LC_DEBUG_AUTH=1 in scripts/run_local.ps1 so local runs always emit safe auth debug details without a flag.
- Retained optional -DebugAuth switch (now redundant) and added explicit info message.
- Re-ran full test suite to confirm no regressions; evidence logs refreshed.

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
    @@
       $py = Use-Venv $root
       Ensure-Requirements $py $root
       Load-DotEnv $root
    -  if ($DebugAuth) { $env:LC_DEBUG_AUTH = "1"; Info "LC_DEBUG_AUTH=1 (debug auth headers)" }
    +  $env:LC_DEBUG_AUTH = "1"
    +  Info "LC_DEBUG_AUTH=1 (auth debug enabled by default for local runs)"
       Ensure-Uvicorn $py

## Verification
- Static: python -m compileall app
- Runtime: python -c "import app.main; print('import ok')"
- Behavior: pwsh -NoProfile -Command "./scripts/run_tests.ps1" (PASS)
- Contract: API surface unchanged; only local runner env behavior updated

## Notes (optional)
- None.

## Next Steps
- Start via run_local.ps1 and hit /auth/me with malformed header to confirm details populate; proceed with any remaining auth-header root-cause diagnostics.

