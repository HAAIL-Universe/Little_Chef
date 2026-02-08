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
