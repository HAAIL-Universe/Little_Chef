# Phase 6A-6C Status Audit
- Timestamp: 2026-02-04T12:40:00+00:00
- HEAD: e6e2bb777214688c0ea8c909c22353dd72892254

## Evidence Snapshot
- git rev-parse HEAD: e6e2bb777214688c0ea8c909c22353dd72892254
- git status -sb: clean
- Routes (23): /, /auth/me, /chat, /chat/confirm, /health, /inventory/events, /inventory/low-stock, /inventory/summary, /mealplan/generate, /prefs, /recipes/books, /recipes/books/{book_id}, /recipes/search, /shopping/diff, /static/{path:path}, /docs, /openapi.json, /redoc, /docs/oauth2-redirect
- UI files present: web/index.html, web/src/main.ts, web/tsconfig.json, web/dist/. No .js sources beyond dist.
- Tests: run_tests.ps1 PASS (compileall/import/pytest)

## Phase 6A Status
- 6A.0 Physics UI mount: Routes include / and /static/{path:path}; physics.yaml does not describe these -> mismatch (served but not defined). Status: PARTIAL (UI mounted, contract gap).
- 6A.1 UI surfaces (mobile-first TS-only):
  1) Auth strip (/auth/me): Implemented in web/src/main.ts; depends on pasted JWT. Status: DONE (manual).
  2) Chat + confirm (/chat, /chat/confirm): Implemented basic call/send; proposal UI minimal. Status: PARTIAL.
  3) Prefs GET/PUT: Implemented buttons in main.ts. Status: DONE (manual wiring).
  4) Mealplan generate: Implemented; displays response. Status: DONE.
  5) Shopping diff: Implemented; shows missing-only. Status: DONE.
  - TS-only rule: satisfied (only main.ts; dist main.js generated).

## Phase 6B Status (DB intro, gated)
- DB gate: DATABASE_URL optional; get_database_url uses env + dotenv. Identity mapping: user_id = uuid5(NAMESPACE_URL, 'littlechef:' + sub) in auth_service.py. Evidence: app/services/auth_service.py lines ~7-20.
- Migrations: SQL-only db/migrations/0001_init.sql; migration runner scripts/db_migrate.ps1. Status: baseline present.
- Prefs/inventory persistence: repo factories choose DB when DATABASE_URL set; in tests LC_DISABLE_DOTENV keeps in-memory. Status: PARTIAL (DB path exists, schema missing users table causing 503 if used without migration).

## Phase 6C Status (deploy/JWT config)
- Render/deploy config: not found (no render.yaml/docs). Status: NOT_STARTED.
- Env wiring: run_local sets LC_DEBUG_AUTH=1; JWT verifier uses LC_JWT_ISSUER, LC_JWKS_URL/LC_OIDC_DISCOVERY_URL, LC_JWT_AUDIENCE. Status: PARTIAL (local only, no deploy doc).
- Smoke test script for deployed URL: not present. Status: NOT_STARTED.

## Gaps
- 6A.0: physics.yaml missing UI mount endpoints / and /static/{path} definitions.
- 6A.1: Chat proposal UI minimal; needs confirm/cancel UX per spec.
- 6B: DB schema not applied by default; users table missing causes 503 unless migrations run. Need clearer migration/run_local integration.
- 6C: No Render config or deploy instructions; no smoke script; JWT prod config not documented.

## Next Minimal Steps
1) Update physics.yaml to include / and /static/{path} (UI mount) to close 6A.0 contract gap.
2) Improve web UI chat flow to show pending proposal + confirm/cancel (small TS change).
3) Ensure db_migrate.ps1 (or run_local) applies 0001_init.sql when DATABASE_URL is set, or document that requirement in README/diff log.
4) Add deploy/readme section for Render + env vars; add simple smoke script curling /health and /auth/me with a token.
