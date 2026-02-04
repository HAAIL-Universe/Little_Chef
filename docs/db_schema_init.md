# DB Schema Initialization

## Prereqs
- Set `DATABASE_URL` (e.g., postgres://user:pass@host:port/db?sslmode=require)
- Ensure migration runner exists: `scripts/db_migrate.ps1`
- Migration SQL: `db/migrations/0001_init.sql`

## Local steps
1) `pwsh -NoProfile -File .\scripts\db_migrate.ps1`
2) Verify tables:
   - `psql $env:DATABASE_URL -c "\dt"` should list `users`, `prefs`, `inventory_events`, `schema_migrations`.
3) Smoke: start app (`scripts/run_local.ps1 -Migrate` or run migrations first), then call `/auth/me` with a valid Bearer token; it should not fail with missing table.

## Render/Neon notes
- Set `DATABASE_URL` in Render env vars.
- Run `scripts/db_migrate.ps1` (from a one-off shell) after setting the URL before first deploy or when migrations change.
- Re-verify with `psql` or `/auth/me` smoke.

## Safety
- Migrations are opt-in; run_local.ps1 only runs them when `-Migrate` is passed.
- No migrations run during tests; tests stay in-memory when `DATABASE_URL` is absent.
