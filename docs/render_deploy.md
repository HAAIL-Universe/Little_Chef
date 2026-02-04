# Render Deploy Runbook

## Build / Start commands
- Build (Render native for Python): `pip install -r requirements.txt`
- Start command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Required env vars
- DATABASE_URL (Postgres/Neon) e.g. `postgres://user:pass@host:5432/db?sslmode=require`
- LC_JWT_ISSUER
- LC_JWT_AUDIENCE
- One of LC_OIDC_DISCOVERY_URL or LC_JWKS_URL
- Optional: LC_DEBUG_AUTH=0/1 (leave off in prod unless debugging)

## Migrations
- Before first deploy (or after schema changes):
  1) Open a Render shell (or local with prod DATABASE_URL)
  2) Run: `pwsh -File scripts/db_migrate.ps1`
  3) Verify: `psql $env:DATABASE_URL -c "\dt"` includes `users`, `prefs`, `inventory_events`

## Smoke test
- From CI/desktop: `pwsh -File scripts/smoke_render.ps1 -BaseUrl https://your-service.onrender.com -Jwt "<token>"`
  - Checks /health
  - If Jwt provided: checks /auth/me

## Troubleshooting
- 401 invalid authorization header: confirm Bearer format; enable LC_DEBUG_AUTH=1 temporarily and inspect `details`.
- 503 schema missing (users): run migrations with DATABASE_URL set.
- Startup fails: ensure DATABASE_URL and JWT env vars are set; check Render logs for uvicorn start line.
