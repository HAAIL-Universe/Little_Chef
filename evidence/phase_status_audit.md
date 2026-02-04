# Phase 0–6C Audit (repo vs expected)

Snapshot
- Branch/HEAD: main @ d74e4dbc61e52e5d169de7e466bf2e3cfd2f51f9 (working tree clean)
- Evidence source docs read: builder_contract.md, blueprint.md, manifesto.md, ui_style.md, Contracts/physics.yaml, phases_0-6.md, phases_6a_6c_extension.md
- Last cycle: fixed migration runner (.env loader, verify schema). Files changed: app/db/migrate.py, scripts/db_migrate.ps1, tests/test_migrate_discovery.py, tests/test_auth_schema_missing.py, evidence/updatedifflog.md

Physics vs routes (observed → status → anchors)
- `/health` → MATCH → app/api/routers/health.py:1-10
- `/auth/me` → MATCH (auth service, JWT verify, 401/200) → app/api/routers/auth.py:9-65; app/services/auth_service.py
- `/chat` → MATCH → app/api/routers/chat.py:18-38
- `/chat/confirm` → MATCH → app/api/routers/chat.py:37-58
- `/prefs` GET/PUT → MATCH → app/api/routers/prefs.py:8-41
- `/inventory/events` GET/POST → MATCH → app/api/routers/inventory.py:15-46
- `/inventory/summary` → MATCH → app/api/routers/inventory.py:52-60
- `/inventory/low-stock` → MATCH → app/api/routers/inventory.py:62-70
- `/recipes/books` GET/POST → MATCH → app/api/routers/recipes.py:15-44
- `/recipes/books/{book_id}` GET/DELETE → MATCH → app/api/routers/recipes.py:46-74
- `/recipes/search` → MATCH → app/api/routers/recipes.py:79-95
- `/mealplan/generate` → MATCH → app/api/routers/mealplan.py:7-17
- `/shopping/diff` → MATCH → app/api/routers/shopping.py:7-17
- `/` UI entry → MATCH → app/main.py:16-35
- `/static/{path}` → MATCH → app/main.py:37-50
- `/docs`, `/openapi.json` → auto (FastAPI) → app/main.py:16-20

Phase status table
- Phase 0: DONE
- Phase 1: DONE
- Phase 2: PARTIAL (chat confirm UX minimal; proposal bar not prominent)
- Phase 3: DONE
- Phase 4: DONE
- Phase 5: PARTIAL (UI renders mealplan/shopping diff but limited UX depth)
- Phase 6A: PARTIAL (TS-only UI present; chat confirm UX needs polish)
- Phase 6B: PARTIAL (migrations solid; DB optional; prod apply pending confirmation)
- Phase 6C: PARTIAL (smoke script exists; deploy doc removed; render steps rely on scripts)

Per-phase evidence highlights
- Phase 0: Evidence workflow `scripts/overwrite_diff_log.ps1`; run path `scripts/run_local.ps1` (app/main.py entry) — anchors: scripts/run_local.ps1; evidence/updatedifflog.md
- Phase 1: `/health`, `/auth/me` routes in app/api/routers/health.py, auth.py; auth_service maps sub→user_id; JWT verifier envs LC_JWT_ISSUER/LC_JWT_AUDIENCE; tests cover 401/200 shapes.
- Phase 2: `/prefs` GET/PUT (app/api/routers/prefs.py); chat propose/confirm endpoints (chat.py) and UI surfaces in web/src/main.ts, web/index.html; confirm UX minimal → mark PARTIAL.
- Phase 3: inventory endpoints in app/api/routers/inventory.py; event types/units per physics; repos/services present.
- Phase 4: recipe upload/search endpoints in app/api/routers/recipes.py; citation enforcement in services; physics aligned.
- Phase 5: mealplan/shopping endpoints (mealplan.py, shopping.py); UI renders outputs (web/src/main.ts, web/index.html); UX depth limited → PARTIAL.
- Phase 6A: TS-only UI (web/src/main.ts, tsconfig.json); five surfaces present (auth strip, chat, prefs, mealplan, shopping diff); chat confirm UX needs polish → PARTIAL.
- Phase 6B: Migrations now discover/apply 0001_init (app/db/migrate.py; scripts/db_migrate.ps1); DB optional in tests; prod DB apply still pending → PARTIAL.
- Phase 6C: Smoke script `scripts/smoke.ps1`; render doc removed; deploy readiness depends on Render dashboard + scripts — PARTIAL.

Gaps (ordered)
1) Phase 2/6A: chat proposal confirm/cancel UX is minimal; make confirm bar prominent and stateful.
2) Phase 5/6A: UI for mealplan/shopping diff is basic; improve usability (filters/loading states).
3) Phase 6B: Confirm migrations applied on prod/Neon instance (run db_migrate.ps1 -VerifySchema there).
4) Phase 6C: Capture deploy/runbook steps in ops-notes or dashboard (doc removed); ensure smoke run against prod URL.

Recommended next minimal milestone
- Run `./scripts/db_migrate.ps1 -VerifySchema` against the prod/Neon DATABASE_URL, restart the app, and re-test `/auth/me` with a valid JWT to close Phase 6B gap; then iterate on chat confirm UI (6A/2) if still pending.
