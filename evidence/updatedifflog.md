# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-04T16:55:00+00:00
- Branch: main
- HEAD: f7e3aa6669f64c7a01213f6cfe6f9284717b2cb9
- BASE_HEAD: 3cd30e43fe83561a51de319dc5764689317e8742
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Fixed migration executor to discover `db/migrations/*.sql`, run every statement in `0001_init.sql`, and only mark a version applied after success.
- Added `-VerifySchema` mode to `scripts/db_migrate.ps1` plus post-apply users-table check; logging now shows discovered/applied versions without secrets.
- Added deterministic migration-discovery test; adjusted auth schema-missing test to mock the correct ensure_user path.

## Files Changed (staged)
- app/db/migrate.py
- scripts/db_migrate.ps1
- tests/test_migrate_discovery.py
- tests/test_auth_schema_missing.py
- evidence/updatedifflog.md

## git status -sb
    ## main...origin/main
     M app/db/migrate.py
     M scripts/db_migrate.ps1
     M tests/test_auth_schema_missing.py
    ?? tests/test_migrate_discovery.py
     M evidence/updatedifflog.md

## Minimal Diff Hunks
    app/db/migrate.py
      + Resolve repo root & migrations dir; list *.sql sorted.
      + Split multi-statement SQL; run each inside one transaction; insert version after success.
      + Log discovered/applied versions; error if no migrations found.
    scripts/db_migrate.ps1
      + Added -VerifySchema; prints applied versions and whether users table exists (no secrets).
      + Post-apply users table check; improved quoting; env load retained.
    tests/test_migrate_discovery.py
      + Verifies discovery order/parsing: 0001 before 0002.
    tests/test_auth_schema_missing.py
      + Monkeypatches auth_service.ensure_user so 503 path is deterministic (schema-independent).
    evidence/updatedifflog.md
      + Updated metadata, summary, verification, and migration evidence.

## Verification
- Static: `python -m compileall app` (PASS)
- Runtime: `python -c "import app.main; print('import ok')"` (PASS)
- Behavior: `pwsh -NoProfile -Command "./scripts/run_tests.ps1"` (PASS)
- Behavior (ValidateOnly): `pwsh -NoProfile -Command "./scripts/db_migrate.ps1 -ValidateOnly"` → DATABASE_URL present; migration file exists (PASS)
- Behavior (Apply): `pwsh -NoProfile -Command "./scripts/db_migrate.ps1"` → discovered `0001_init.sql`; applied versions before run: `(none)`/then `0001` OK; users table present: YES (PASS)
- Behavior (VerifySchema): `pwsh -NoProfile -Command "./scripts/db_migrate.ps1 -VerifySchema"` → applied versions: 0001_init,0001; users table present: YES (PASS)
- Contract: `Contracts/physics.yaml` unchanged (PASS)
- /auth/me before this cycle (reported): 503 service_unavailable (missing users table). After migrations now applied; should return 200/401 as normal once app restarted with same DATABASE_URL (not re-tested here). 

## Notes (optional)
- `.env` is untracked and still required; scripts never print env values.
- Migration runner now fails fast if no migrations are found.

## Next Steps
- Restart app with same `.env`, rerun `./scripts/db_migrate.ps1 -VerifySchema`, then call `/auth/me` with a valid Bearer token to confirm the 503 is gone. If a “user missing” error appears, plan minimal auto-provision next cycle.
