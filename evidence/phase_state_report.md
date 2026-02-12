# Phase State Report — 2026-02-08T19:56Z

## 0) Documents reviewed
- `Contracts/builder_contract.md`, `Contracts/blueprint.md`, `Contracts/manifesto.md`, `Contracts/ui_style.md`, `Contracts/physics.yaml`
- Phase docs discovered via `git ls-files | findstr /i "phase"`:
  - `Contracts/phases_0-6.md` (Phases 0–6 baseline)
  - `Contracts/phases_6a_6c_extension.md`
  - `Contracts/phases_7_plus.md`
  - `Contracts/phases_8.md`
  - Evidence artifacts referencing phase status: `evidence/phase_status_audit.md`, `evidence/phase6_status_audit.md`, `evidence/phases_7.6.md`
- Canonical evidence logs read: `evidence/updatedifflog.md`, `evidence/test_runs.md`, `evidence/test_runs_latest.md`
- `Contracts/directive.md` is **NOT PRESENT (allowed)**.

## 1) Evidence snapshot

### A) API endpoints vs `Contracts/physics.yaml`
| Path | Status | Anchor |
|---|---|---|
| `/health` | ✅ implemented | `app/api/routers/health.py:8` |
| `/auth/me` | ✅ implemented | `app/api/routers/auth.py:45–48` |
| `/prefs` GET/PUT | ✅ | `app/api/routers/prefs.py:11–27` |
| `/inventory/events`, `/summary`, `/low-stock` | ✅ | `app/api/routers/inventory.py:18–63` |
| `/recipes/books` & `/recipes/books/{book_id}` | ✅ | `app/api/routers/recipes.py:18–74` |
| `/recipes/search` | ✅ | `app/api/routers/recipes.py:79–95` |
| `/mealplan/generate` | ✅ | `app/api/routers/mealplan.py:10–17` |
| `/shopping/diff` | ✅ | `app/api/routers/shopping.py:10–17` |
| `/chat`, `/chat/inventory`, `/chat/confirm` | ✅ | `app/api/routers/chat.py:30–64` |
| `/` + `/static/{path}` | ✅ (UI served via FastAPI) | `app/main.py:18–56` |

Contract drift: none; all physics routes have matching router anchors. `/chat/inventory` is the dedicated inventory-agent entrypoint mandated by Phase 8 (§Contracts/phases_8.md:3.7).

### B) UI reality
- Duet shell + flows defined in `web/src/main.ts`:
  - Flow options and placeholders: `web/src/main.ts:80–110`
  - `sendAsk` decides between `/chat` vs `/chat/inventory`, increments the history badge, and keeps the bubble state in sync (`web/src/main.ts:1206–1254`).
  - History badge + overlay logic lives at `web/src/main.ts:750–806`; styling is defined in `web/src/style.css:467–506`.
  - Proposal summaries + confirm logic are rendered by `web/src/proposalRenderer.ts:30–195`.
  - Flow selector chips, history drawer, and onboarding copy are also defined in `web/src/main.ts:557–635` and later drag/long-press handlers (`web/src/main.ts:656–710`, `1796–1890`).
- Frontend build artifacts (`web/dist/main.js`, `web/dist/style.css`) mirror the TS sources.
- Evidence of confirm/deny/responses: `web/src/proposalRenderer.ts:148–195`.

### C) Tests & evidence
- Deterministic tests exercise inventory parsing and ensures the new guard list (`tests/test_inventory_agent.py:1–232`).
- Evidence log entries describe the most recent verification cycle (`evidence/test_runs.md` entry dated 2026-02-08T19:50:39Z; `evidence/test_runs_latest.md` mirrors this status).
- Governance script `scripts/overwrite_diff_log.ps1` enforces the diff log rewrite workflow before each change.
- Verification commands run for this cycle: `python -m compileall .` and `python -m pytest -q` (both passed, see `evidence/test_runs.md` addition).

## 2) Phase doc reconciliation

| Doc | Covers | Notes |
|---|---|---|
| `Contracts/phases_0-6.md` | Phases 0–6 baseline (API + core workflows) | Canonical “pre-7” roadmap. |
| `Contracts/phases_6a_6c_extension.md` | Phases 6A–6C (UI mount + DB + deploy) | Extension to the baseline; no overlaps with other docs. |
| `Contracts/phases_7_plus.md` | Phases 7.1–7.8 plus 8–10 (UI/evidence closure) | UI-heavy plan; it also contains a Phase 8 entry describing meal plan/shopping diff evidence. |
| `Contracts/phases_8.md` | Phase 8 inventory agent split (backend isolation) | Backend-focused; overlaps/conflicts with Phase 8 entry inside `phases_7_plus`. |
| Evidence docs (`evidence/phase_status_audit.md`, `evidence/phase6_status_audit.md`, `evidence/phases_7.6.md`) | Status snapshots for phases 0–6 and 7.6 | Provide audit context for statuses.

**Conflict resolution proposal**
- Treat `Contracts/phases_8.md` as the **canonical inventory-agent Phase 8** because it prescribes backend routing (dedicated `/chat/inventory`, action allowlist) and no UI changes; the `Phase 8` section inside `phases_7_plus` should be interpreted as **Phase 8 UI evidence (meal plan/shopping diff)**. Recommendation:
  - Rename `Contracts/phases_7_plus.md`’s Phase 8 subsection to “Phase 8 Evidence Pack: Meal Plan + Shopping Diff” to avoid confusion.
  - Keep `Contracts/phases_8.md` as the authoritative isolation contract for Inventory Agent.
- Add a short note to `Contracts/phases_7_plus.md` referencing this split so future readers know the dual definitions intentionally share the number.

## Phase doc mapping table
| Phase ID | Source doc | Scope label | Acceptance criteria |
|---|---|---|---|
| 0–6 | `Contracts/phases_0-6.md` | Core backend + chat/prefs/inventory/mealplan/shopping/recipes | Health/auth, chat propose/confirm, prefs UI, inventory event sourcing/read models, recipe uploads/search, meal plans, and shopping diff per Blueprint/physics. |
| 6A–6C | `Contracts/phases_6a_6c_extension.md` | Frontend mount + Neon persistence + deploy readiness | TS-only UI entry (auth strip, chat, prefs, plan, diff), DB migrations/scripts, and Render smoke/runbook. |
| 7.1–7.8 & 9–10 | `Contracts/phases_7_plus.md` | UI/evidence closure (Duet shell, onboarding/flow polish, plan/diff proofs, recipes/auth screenshots) | Flow dashboards, ghost overlays, confirm/deny prominence, evidence pack (plan/diff + recipe uploads + auth status) following the phase sub-sections. |
| 8 (Inventory Agent) | `Contracts/phases_8.md` | Inventory `/fill` isolation with dedicated agent + allowlist | `/chat/inventory` never emits non-inventory actions, proposals confined to thread_id, confirm-only writes to `inventory_events`, deny/edit behavior scoped per doc. |

## 3) Phase-by-phase status (Phases 0–10, including 6A–6C)

| Phase | Status | Evidence anchors | Missing | Contract drift |
|---|---|---|---|---|
| 0 | **DONE** | `scripts/run_local.ps1`, `evidence/updatedifflog.md` (Cycle metadata) | — | None |
| 1 | **DONE** | `app/api/routers/health.py:8`, `app/api/routers/auth.py:45–65` | — | None |
| 2 | **PARTIAL** | `/prefs` router + UI confirm (chat + confirm/deny in `web/src/main.ts:1206–1255`; `web/src/proposalRenderer.ts:148–195`) | Confirm bar UI needs prominence / clearer state transitions (crowded `sendAsk` path) | UI confirm/deny minimal vs. blueprint expectation |
| 3 | **DONE** | Inventory routers `app/api/routers/inventory.py:18–63`; tests verifying event schema | — | None |
| 4 | **DONE** | Recipe routers `app/api/routers/recipes.py:18–95`; services enforce citations | None (per blueprint) |
| 5 | **PARTIAL** | Meal plan + shopping routers `app/api/routers/mealplan.py:10–17`, `app/api/routers/shopping.py:10–17`; UI renders plan/diff (`web/src/style.css`, `web/src/main.ts` minimal view) | Improve mobile UX per Phase 5/7.5 (filters, context chips). | UI depth limited vs. Phase 5 acceptance. |
| 6A | **PARTIAL** | UI mount + chat flows (TS entry `web/src/main.ts:80–1255`); `scripts/run_tests.ps1` ensures compile/test | Proposal confirm UI needs polish; long-press history/resizable flows still evolving (Phases 7.1/7.5). | Some confirm UI still minimal vs. 6A deliverable. |
| 6B | **PARTIAL** | Migrations + scripts (docs refereed earlier, e.g., `scripts/db_migrate.ps1`) | Need to run migrations against prod Neon; ensure DB envs documented fully (`scripts/db_migrate.ps1` + `docs/db_schema_init.md`). | DB hook in code without formal prod run. |
| 6C | **NOT STARTED** | Smoke/runbook missing (`scripts/smoke.ps1` only scaf) | Provide Render deploy doc + smoke checks verifying `/health` with env vars. | No Render deployment guidance anchored. |
| 7.1–7.4 | **PARTIAL** | Flow shell in `web/src/main.ts`, history drag/w selection, confirm summary (`proposalRenderer.ts`). | UX still needs flow dashboards/confirm polish; mobile history evidence capture pending. | Confirm UX needs more visibility. |
| 7.5 | **PARTIAL** | Inventory overlay + dashboards touched (`web/src/main.ts:557–710`), but ghost overlay/diff evidence still coarse. | Implement group-by-location overlay + dev panel hide per doc. | UI not yet matching Phase 7.5 read panels. |
| 7.6 | **IN PROGRESS** | New inventory parser logic + tests `app/services/inventory_agent.py` and `tests/test_inventory_agent.py`; ensures container-only proposals blocked. | Concern: need manual location UI + confirm/test coverage for warns; location not yet surfaced. | Warnings/confirm flows align but UI integration still pending. |
| 7.7 / 7.7.5 | **PARTIAL** | Onboarding copy + long-press flow baked in `web/src/main.ts:557–710`; user bubble uses “Sent”. | Need final persistence tests, preference table migration (Phase 7.7.5) and confirm UI. | Onboarding copy partly implemented but specialized intake/backing still evolving. |
| 8 (inventory agent) | **IN PROGRESS** | Dedicated `/chat/inventory` endpoint (`app/api/routers/chat.py:42–49`); new parser ensures only `create_inventory_event` actions (`tests/test_inventory_agent.py`). | Need confirm that `/chat/inventory` responses never include prefs actions (additional validation). | Overlap with `Contracts/phases_7_plus.md` 8 entry; canonical doc in `Contracts/phases_8.md`. |
| 8 (mealplan evidence) | **PLANNED** | `Contracts/phases_7_plus.md` Phase 8 section describes plan/diff evidence; UI already shows plan/diff but needs "why this" chips per doc. | Capture mobile screenshots + JSON evidence per Phase 8 spec. | None beyond doc instructions. |
| 9 | **NOT STARTED** | Phase 9 doc awaits recipe upload evidence; backend routes exist but no formal capture. | Provide upload/search/citation snapshots. | None beyond missing evidence. |
| 10 | **NOT STARTED** | Auth UI exists (`web/src/main.ts` stores token) but documented UX proof missing. | Add JWT entry/status indicator + `/auth/me` round-trip screenshot referencing Phase 10 doc. | None beyond evidence.

## 4) Coverage matrix (capabilities ↔ phases)

| Capability | Phase(s) | State | Evidence |
|---|---|---|---|
| OAuth/JWT boundary | 1,6A | Implemented | `app/api/routers/auth.py:45–65`, UI uses `Tokens` (per `web/src/main.ts:20–75`). |
| Chat propose/confirm loop | 2,6A,7.4 | Implemented (partial UX) | `app/api/routers/chat.py:30–64`; `web/src/main.ts:1206–1326`; `web/src/proposalRenderer.ts:148–195`. |
| Preferences GET/PUT + summary panel | 2,6A | Implemented (read panel minimal) | `app/api/routers/prefs.py:11–27`; UI summary in `web/src/main.ts:552–575`. |
| Inventory event sourcing/performance | 3 | Implemented | `app/api/routers/inventory.py:18–63`; aggregator services (app/services/inventory_agent). |
| Inventory fill agent isolation | 8 | Implemented (endpoint + allowlist) | `/chat/inventory` route `app/api/routers/chat.py:42–49`; tests ensure only `create_inventory_event` actions (`tests/test_inventory_agent.py:1–232`). |
| Recipes upload/search with citations | 4 | Implemented | `app/api/routers/recipes.py:18–95`; services enforce citations (app/services/recipe). |
| Meal plan + shopping diff | 5 | Partial | `app/api/routers/mealplan.py:10–17`, `shopping.py:10–17`; UI glimpsed in `web/src/main.ts` but evidence still limited. |
| Deployment ops readiness | 6C | Missing | No current Render docs; `scripts/smoke.ps1` alone insufficient. |
| Inventory conversational parsing | 7.6 | In progress | New parser & tests `app/services/inventory_agent.py` and `tests/...` provide normalization/warnings. |
| Onboarding long-press + history | 7.1/7.2/7.7 | Partial | `web/src/main.ts` lines 557–710 + `history` functions `web/src/main.ts:557–806`. |
| Evidence logging discipline | All phases | Implemented | `scripts/overwrite_diff_log.ps1` + repeated log pattern in `evidence/updatedifflog.md`. |

## 5) Risks & contradictions (top 5)
1. **Duplicate Phase 8 definitions**: `Contracts/phases_7_plus.md` includes a UI-focused Phase 8 while `Contracts/phases_8.md` claims the same number for the backend inventory agent. This duplication risks inconsistent scope. Proposed fix: treat `phases_8.md` as canonical for Inventory Agent and rename the other section to “Phase 8 Evidence Pack (Meal Plan + Shopping Diff)”.
2. **Phase 6C (deploy/runbook) missing**: No Render deployment guide or smoke script verifying `/health` with prod envs. Without it, Phase 6C cannot be closed.
3. **Confirm UX still minimal**: Phase 2/6A/7.4 demand a prominent confirm/cancel bar; the current UI hides these states inside `sendAsk` with minimal visibility, increasing regression risk.
4. **Inventory flow warnings not surfaced in UI yet**: Phase 7.6 normalization now emits warnings (UNIT_ASSUMED, DATE_PARSED, LOCATION_SUSPICIOUS) but there is no frontend display or tests verifying the warning bubble, so ambiguous items may be auto-confirmed.
5. **Phase 7.5 read dashboards not fully realized**: Inventory flow lacks the grouped ghost overlay and summary cards described in Phase 7.5, leaving the scoreboard incomplete and increasing the burden on chat-only flows.

## 6) Recommended next phase slice
Prioritize **Phase 7.5 (Flow Dashboards + Dev Panel cleanup)** as the next deliverable. The UI already has the shell, history, and confirm framework (`web/src/main.ts:557–1326`); closing 7.5 by building the ghost overlay (grouped by location), the low-stock preview, and the Dev Panel toggle will unblock both Phase 5 (meal plan UX) and Phase 7 evidence closure. Document the evidence (mobile screenshot + JSON) in `evidence/updatedifflog.md` and `evidence/phase_state_report.md`.

## 7) Phase sign-off ledger

### Phase 0 — Repo bootstrap + contract wiring (Contracts/phases_0-6.md:15-45)
- **Status:** SIGNED_OFF
- **Sign-off date:** 2026-02-08T21:00:00Z
- **Acceptance criteria (per doc):**
  - Repo skeleton runs locally and produces the basic UI/API entry points (`scripts/run_local.ps1` + FastAPI `app/main.py`). 
  - Evidence workflow (diff log + report) sits on top of the contracts (per Phase 0 description).
- **Evidence anchors:**
  - `scripts/run_local.ps1:1-214` (local runner + venv/install logic).
  - `app/main.py:18-56` (FastAPI serving `/`, `/static`, router wiring).
- **Tests/evidence logs:**
  - `evidence/updatedifflog.md:1-34` (diff-log discipline proof).
  - `evidence/test_runs_latest.md:1-8` (recent compileall/pytest run showing green suite).
- **Notes:** None.

### Phase 1 — Auth boundary + health + “who am I” (Contracts/phases_0-6.md:28-41)
- **Status:** SIGNED_OFF
- **Sign-off date:** 2026-02-08T21:00:00Z
- **Acceptance criteria (per doc):**
  - `/health` returns `HealthResponse` and `/auth/me` validates JWT returning `UserMe` or 401 as specified.
- **Evidence anchors:**
  - `app/api/routers/health.py:1-10` (Health router).
  - `app/api/routers/auth.py:45-67` (JWT extraction and `/auth/me` response with prefs/inventory markers).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-8`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** These routes satisfy the phase 1 acceptance for health/auth per the blueprint.

### Phase 2 — Chat propose/confirm loop + Prefs + first dashboard surface (Contracts/phases_0-6.md:45-66)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Prefs GET/PUT exist and FILL-mode chat proposals use `upsert_prefs` with `ChatResponse.confirmation_required`.
  - Mobile-first UI exposes chat surface, voice affordance, prefs summary, and confirm/cancel controls.
- **Evidence anchors:**
  - `app/api/routers/prefs.py:11-41`.
  - `web/src/main.ts:1206-1326` (sendAsk + `/chat`/`/chat/inventory` wiring + proposal handling).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-8`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** Confirm/cancel UI remains minimal, so Phase 2 is still partial.

### Phase 3 — Inventory event sourcing + derived read models + chat actions (Contracts/phases_0-6.md:68-81)
- **Status:** SIGNED_OFF
- **Sign-off date:** 2026-02-08T21:05:00Z
- **Acceptance criteria (per doc):**
  - Inventory events, summary, and low-stock endpoints exist and reflect the event-sourced model.
  - Chat proposals create inventory events and ASK answers low-stock questions.
- **Evidence anchors:**
  - `app/api/routers/inventory.py:18-68`.
  - `tests/test_inventory_agent.py:1-260`.
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** Confirm/deny gating keeps proposals tied to inventory events.

### Phase 4 — Recipes: built-in baseline + user uploads + retrieval with citations (Contracts/phases_0-6.md:88-105)
- **Status:** SIGNED_OFF
- **Sign-off date:** 2026-02-08T21:05:00Z
- **Acceptance criteria (per doc):**
  - Recipe book CRUD/search exist and responses include built-in/user-library citations.
- **Evidence anchors:**
  - `app/api/routers/recipes.py:18-95`.
  - `app/services/recipe_service.py:1-88`.
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** Citations are enforced for both built-in and user-library results.

### Phase 5 — Meal plan generation + shopping diff (Contracts/phases_0-6.md:111-126)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - POST `/mealplan/generate` returns inventory-first plans with citations for each meal source.
  - POST `/shopping/diff` returns the missing-only shopping list derived from the latest plan.
  - UI surfaces allow the user to generate a plan and refresh the diff results on mobile-friendly panels.
- **Evidence anchors:**
  - `app/api/routers/mealplan.py:10-17` (plan generation endpoint).
  - `app/api/routers/shopping.py:10-17` (shopping diff endpoint).
  - `web/src/main.ts:1344-1386` (buttons that call the routes and store plan/diff responses).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** The plan/diff UI still lacks the mobile cards, low-stock preview, and "why this" chips that Phase 5 describes, so the experience remains partial.

### Phase 6A — UI slice catch-up (Contracts/phases_6a_6c_extension.md:17-53)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Frontend entry (`web/index.html` + TS sources) renders auth strip, chat composer (text + mic), prefs controls, meal plan buttons, and shopping diff hooks.
  - UI is TypeScript-only, mobile-first, and wired to the physics routes without introducing new endpoints.
- **Evidence anchors:**
  - `web/src/main.ts:80-1420` (flow chips, history, composer, plan/diff hooks, overlays, onboarding behaviors).
  - `scripts/run_tests.ps1:1-120` (governs the deterministic static → runtime → behavior loop per the test gate).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** Confirm/cancel UI and announcement copy still read as “shell stubs”; Phase 6A will not be marked complete until that UX is more prominent.

### Phase 6B — DB intro (Neon) (Contracts/phases_6a_6c_extension.md:55-73)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Run Neon-backed migrations for prefs and inventory using the provided scripts; the DB design is documented.
  - Tests remain deterministic with dependency overrides; production deployment can apply the migrations.
- **Evidence anchors:**
  - `scripts/db_migrate.ps1:1-200` (migration runner with schema checks).
  - `db/migrations/0001_init.sql:1-200` (initial schema definition referenced in the doc).
  - `docs/db_schema_init.md:1-60` (migration guidance and schema snapshot).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** The migrations exist, but they have not been executed against the production Neon URL yet; Phase 6B remains partial until that run is confirmed.

### Phase 6C — Render deploy readiness + JWT config (Contracts/phases_6a_6c_extension.md:74-90)
- **Status:** NOT_STARTED
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Render builds and smoke scripts run with DB/JWT env var wiring (DATABASE_URL, LC_JWT_ISSUER/AUDIENCE, JWKS/OIDC settings).
  - Smoke check hits `/health` and verifies token-based auth.
- **Evidence anchors:**
  - `scripts/smoke.ps1` (available script but not yet expanded into a documented runbook).
- **Tests/evidence logs:**
  - `evidence/updatedifflog.md:1-34` (notes the missing deploy doc).
- **Notes:** No Render deployment document or smoke run exists in repo yet, so the Phase 6C gate is not satisfied.

### Phase 7.1 — Duet Chat Shell (Contracts/phases_7_plus.md:22-27)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Assistant bubble pinned top-left, user bubble bottom-right, composer handles text/mic, and history drawer gesture exists.
- **Evidence anchors:**
  - `web/src/main.ts:557-710` (bubble updates, history drawer wiring, thread label, history toggles).
  - `web/src/main.ts:1799-1869` (onboarding long-press, menu activation, Start action wiring).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** The shell exists, but some history UX and onboarding menu polish still reflect Phase 7.4/7.5 work in progress.

### Phase 7.2 — History Drawer “Lock to Scroll” & inverted chronology (Contracts/phases_7_plus.md:29-34)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Dragging the user bubble toward the top third locks into history, with inverted chronology in the drawer.
- **Evidence anchors:**
  - `web/src/main.ts:513-660` (syncHistoryUi, applyDrawerProgress, wireDuetDrag, setDrawerOpen).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** The drawer exists, but visual confirmation (screenshots/GIF) and inverted chronology evidence remains to be logged before claiming full completion.

### Phase 7.3 — Flow Selector Bubbles (Contracts/phases_7_plus.md:36-41)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Flow selector chips for General, Inventory, Meal Plan, Preferences, with active state and contextual copy.
- **Evidence anchors:**
  - `web/src/main.ts:80-110` (flow options definition and currentFlowKey state) and the wiring around 420-520 for the chips.
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** Chips are present, but the evidence pack about state persistence per log is still partial.

### Phase 7.4 — Confirm-before-write UX Polish (Contracts/phases_7_plus.md:43-48)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Proposed actions render confirm/deny controls alongside assistant bubble, invoking `/chat/confirm` without silent writes.
- **Evidence anchors:**
  - `web/src/proposalRenderer.ts:30-195` (proposal summary rendering, confirm/deny detection and formatting).
  - `web/src/main.ts:1226-1340` (proposal submission, state management for confirm/deny, status updates).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** The confirm/deny controls exist, but they currently show shell-only messages in the UI and need more visible UX per Phase 7.4 evidence requirements.

### Phase 7.5 — Flow Dashboards (Contracts/phases_7_plus.md:50-124)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Inventory ghost overlay grouped by location, dev panel hiding legacy blocks, low-stock preview, and mobile layout with no overflow.
  - Meal Plan and Preferences flows show read-only dashboards while chat remains primary.
- **Evidence anchors:**
  - `web/src/main.ts:557-710` (inventory overlays and flow dashboard scaffolding).
  - `web/src/main.ts:924-980` (`setupInventoryGhostOverlay` with overlay content and low stock list) and `web/src/main.ts:219-259` (`setupDevPanel` moving legacy debug blocks into a hidden panel).
  - `web/src/main.ts:1344-1386` (plan/shopping flow hooks demonstrating read-only behavior for plan/diff buttons).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** The overlay and Dev Panel exist in scaffolding form, but Phase 7.5 still requests grouped-by-location content, mobile screenshots, and mobile layout proof before it can be marked complete.

### Phase 7.6 — Inventory conversational parsing & normalization (Contracts/phases_7_plus.md:125-145)
- **Status:** IN_PROGRESS
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Parse free-flow text into draft items, normalize units/dates/locations, surface warnings, and restrict writes to confirmed actions.
- **Evidence anchors:**
  - `app/services/inventory_agent.py:512-920` (parsing, cleanup, disallowed item filtering, note extraction).
  - `tests/test_inventory_agent.py:150-260` (container-word rejection, date removal, quantity/unit normalization tests).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** Normalizer logic is in place, but warnings and manual location UI described in Phase 7.6 have not yet surfaced to the frontend, so the phase remains in progress.

### Phase 7.7 — Preferences-first Onboarding Entry (Contracts/phases_7_plus.md:147-167)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Assistant + user bubble fallback copy promotes onboarding, long-press on the user bubble surfaces the Start action, and selecting Start enters Preferences flow with new copy.
- **Evidence anchors:**
  - `web/src/main.ts:558-570` (assistant/user bubble copy, ellipsis-to-Sent switch, fallback placeholders).
  - `web/src/main.ts:1799-1869` (bindOnboardingLongPress showing/handling the onboard menu and Start action).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** The long-press menu is functional, but the onboarding copy resets and the start flow still triggers placeholder shell responses; this needs more polish before being signed off.

### Phase 7.7.5 — Preferences Persistence (Contracts/phases_7_plus.md:169-187)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Preferences table/migration exists, API reads/writes prefs, and the UI flow captures preferences via proposal/confirm before persisting to the dashboard.
- **Evidence anchors:**
  - `db/migrations/0001_init.sql:1-200` (schema includes prefs tables referenced by the doc).
  - `app/api/routers/prefs.py:11-41` (prefs read/write endpoints tied to the service layer).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** Preferences persistence still relies on shell stubs in the UI (Phase 7.7.5 acceptance requires end-to-end confirm/summary that remains to be implemented).

### Phase 7.8 — E2E Evidence Closure Pack (Contracts/phases_7_plus.md:189-195)
- **Status:** PARTIAL
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - A written checklist of mobile screenshots + JSON responses + smoke outputs captured once per cycle and linked in the evidence log.
- **Evidence anchors:**
  - `evidence/updatedifflog.md:1-34` (reports mention mobile evidence but do not yet include the full pack).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
- **Notes:** The checklist concept exists, but the evidence artifacts required by Phase 7.8 have not appeared in the log yet, so this phase remains partial.

### Phase 8A — Inventory Agent Isolation (Contracts/phases_8.md:20-156)
- **Status:** IN_PROGRESS
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - `/chat/inventory` is the dedicated entry for fill-only inventory updates, proposals only include `create_inventory_event`, and confirm semantics produce inventory_events scoped to `thread_id`.
- **Evidence anchors:**
  - `app/api/routers/chat.py:30-64` (inventory mode routing with the new endpoint).
  - `tests/test_inventory_agent.py:150-260` (ensures container names/dates are stripped and only permissible actions remain).
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
  - `evidence/updatedifflog.md:1-34`.
- **Notes:** Additional proof (e.g., test assertions or API contract checks) is needed to guarantee `/chat/inventory` never emits pref actions; until then, the phase stays in progress.

### Phase 8B — Meal plan + shopping diff evidence pack (Contracts/phases_7_plus.md:196-201)
- **Status:** PLANNED
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Mobile screenshots of plan/diff views + saved JSON responses showing "why this" chips for citations.
- **Evidence anchors:**
  - `web/src/main.ts:1344-1386` (plan/diff hooks) though the requested evidence is not yet captured.
- **Tests/evidence logs:**
  - `evidence/test_runs_latest.md:1-20`.
- **Notes:** Screenshots, JSON snippets, and citations per Phase 8 instructions have not yet appeared in the evidence log; this is a planning placeholder.

### Phase 9 — Recipe Library E2E + citations (Contracts/phases_7_plus.md:202-207)
- **Status:** NOT_STARTED
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Upload a recipe PDF, verify retrieval with anchors, and show plan/shopping diff referencing user-library recipes.
- **Evidence anchors:** None yet; backend routes exist but usage in the UI is not proven.
- **Tests/evidence logs:**
  - `evidence/updatedifflog.md:1-34` (no new evidence for Phase 9 yet).
- **Notes:** Implementation and evidence capture remain undone.

### Phase 10 — Onboarding/Auth UX proof (Contracts/phases_7_plus.md:209-213)
- **Status:** NOT_STARTED
- **Sign-off date:** —
- **Acceptance criteria (per doc):**
  - Minimal JWT entry/status indicator in the UI plus `/auth/me` round-trip screenshot showing success.
- **Evidence anchors:** None; the UI currently lacks the JWT status indicator/screenshots requested by Phase 10.
- **Tests/evidence logs:** `evidence/updatedifflog.md:1-34`.
- **Notes:** Phase 10 is waiting on the planned JWT indicator feature.

## What remains
- **Phase 2:** Confirm/cancel UX is still hidden in the composer. Next step: make the proposal bar persistent and highlight confirm/cancel buttons when `state.proposalId` exists.
- **Phase 5:** Mobile-friendly plan/diff cards, "why this" chips, and saved JSON evidence have not been recorded. Next step: capture at least one mobile screenshot and JSON snippet for plan and diff and note it in `evidence/updatedifflog.md`.
- **Phase 6A:** Confirm/deny responses still show shell-only text. Next step: wire actual `/chat/confirm` calls and show a persistent confirmation bar tied to `state.proposalId`.
- **Phase 6B:** Migrations are untested on Neon/production. Next step: run `scripts/db_migrate.ps1 -VerifySchema` against the production DATABASE_URL and log the success.
- **Phase 6C:** Render deploy/runbook is absent. Next step: author a Render deployment plus smoke-check guide (including `/health` and `/auth/me` checks) and link it from evidence.
- **Phases 7.1–7.4:** Drawer, confirm polish, and flow dashboards still lack mobile evidence. Next step: collect annotated mobile screenshots (drawer, confirm bar, flow chips) and reference them in `evidence/updatedifflog.md`.
- **Phase 7.5:** Grouped inventory overlay, low-stock strip, and Dev Panel proof are scaffolded but not yet compliant. Next step: finish the overlay grouping by location plus low-stock list, then capture evidence of the Dev Panel hidden/default states.
- **Phase 7.6:** Warnings and manual location UI are not surfaced. Next step: show warning badges in the UI and note the manual location control state for one pending proposal.
- **Phase 7.7/7.7.5:** Onboarding persistence is stubbed. Next step: ensure the Starter flow writes prefs via the real `/chat` endpoint and that the Prefs read panel reflects the persisted values.
- **Phase 7.8:** Evidence pack checklist is missing. Next step: draft the checklist entries (mobile screenshot, plan JSON, smoke output) and store them in the diff log.
- **Phase 8A:** Need a formal proof that `/chat/inventory` only emits inventory actions. Next step: add an integration test asserting the response contains no `upsert_prefs` actions.
- **Phase 8B:** Screenshot/JSON evidence is outstanding. Next step: capture plan/shopping diff screens with citations and note them in the log.
- **Phase 9:** Upload/retrieval evidence absent. Next step: perform a PDF recipe upload, capture the API response plus UI evidence showing citations, and log it.
- **Phase 10:** JWT entry/status indicator is missing. Next step: add the UI indicator and document a successful `/auth/me` round-trip screenshot with token redacted.

## Delta vs prior report
- Added the Phase Sign-Off Ledger with evidence-linked statuses for Phases 0–10 (including the split Phase 8 entries) so future agents can skip already signed-off phases with certainty.
- Introduced the "What remains" reconciliation list with one concrete next step per incomplete phase plus an explicit Delta vs prior report section summarizing the change.

## Next recommended slice
- Phase 7.5 (Flow Dashboards + Dev Panel cleanup) remains the single highest-leverage slice: complete the inventory ghost overlay grouping, low-stock preview, and Dev Panel proof to unblock Phase 5/7 evidence closure, then capture the required mobile screenshots and JSON snippets in `evidence/updatedifflog.md`.
---

## Phase 13–14 Addendum (added post-build)

### Phase 13 — Voice Layer Hardening
**Commit:** `a21129f` | **Tests:** 61 new (24 + 18 + 19) | **Total:** 378

| Slice | Status | Tests | Key Deliverables |
|-------|--------|-------|-----------------|
| 13.1 Voice flow stabilization | ✅ Complete | 24 | stt_normalize.py, voice_input/voice_hint schema fields |
| 13.2 Alexa integration | ✅ Complete | 18 | AlexaService, POST /alexa/webhook, 4 intents |
| 13.3 Household sync concept | ✅ Complete | 19 | HouseholdService, 5 REST endpoints, multi-user tests |

### Phase 14 — Recipe Ingestion + Advanced Constraints
**Commit:** `5f00521` | **Tests:** 26 new | **Total:** 404

| Slice | Status | Tests | Key Deliverables |
|-------|--------|-------|-----------------|
| 14.1 Recipe ingestion | ✅ Complete | 8 | POST /recipes/paste, POST /recipes/photo, PDF extraction |
| 14.2 Serving scaling | ✅ Complete | 7 | scale_ingredients(), target_servings in mealplan generate |
| 14.3 Constraint-aware | ✅ Complete | 11 | equipment prefs field, detect_equipment(), MATCH/CHECK scoring |

**STOPPED BEFORE PHASE 15.**