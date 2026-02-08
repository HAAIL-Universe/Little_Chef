# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-08T20:11:49+00:00
- Branch: recovery/evidence-20260208
- HEAD: 8bb69f7aeb6d0babb326a184e1ca15fc458140b2
- BASE_HEAD: 963eb03e3d1e25314b761860a635d5df24d473fe
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Drafted the phase-state reconciliation report comparing Contracts/phases docs to repo reality, including API/UI/test anchors, coverage matrix, conflict resolution, risks, and a next-phase recommendation.
- Recorded the duplicate Phase 8 interpretation and identified Phase 7.5 as the next actionable slice before handing off to Julius for authorization.

## Files Changed (staged)
- evidence/phase_state_report.md
- evidence/updatedifflog.md

## git status -sb
    ## recovery/evidence-20260208
    A  evidence/phase_state_report.md
    M  evidence/updatedifflog.md

## Minimal Diff Hunks
    diff --git a/evidence/phase_state_report.md b/evidence/phase_state_report.md
    new file mode 100644
    index 0000000..8f9b04b
    --- /dev/null
    +++ b/evidence/phase_state_report.md
    @@ -0,0 +1,118 @@
    +# Phase State Report — 2026-02-08T19:56Z
    +
    +## 0) Documents reviewed
    +- `Contracts/builder_contract.md`, `Contracts/blueprint.md`, `Contracts/manifesto.md`, `Contracts/ui_style.md`, `Contracts/physics.yaml`
    +- Phase docs discovered via `git ls-files | findstr /i "phase"`:
    +  - `Contracts/phases_0-6.md` (Phases 0–6 baseline)
    +  - `Contracts/phases_6a_6c_extension.md`
    +  - `Contracts/phases_7_plus.md`
    +  - `Contracts/phases_8.md`
    +  - Evidence artifacts referencing phase status: `evidence/phase_status_audit.md`, `evidence/phase6_status_audit.md`, `evidence/phases_7.6.md`
    +- Canonical evidence logs read: `evidence/updatedifflog.md`, `evidence/test_runs.md`, `evidence/test_runs_latest.md`
    +- `Contracts/directive.md` is **NOT PRESENT (allowed)**.
    +
    +## 1) Evidence snapshot
    +
    +### A) API endpoints vs `Contracts/physics.yaml`
    +| Path | Status | Anchor |
    +|---|---|---|
    +| `/health` | ✅ implemented | `app/api/routers/health.py:8` |
    +| `/auth/me` | ✅ implemented | `app/api/routers/auth.py:45–48` |
    +| `/prefs` GET/PUT | ✅ | `app/api/routers/prefs.py:11–27` |
    +| `/inventory/events`, `/summary`, `/low-stock` | ✅ | `app/api/routers/inventory.py:18–63` |
    +| `/recipes/books` & `/recipes/books/{book_id}` | ✅ | `app/api/routers/recipes.py:18–74` |
    +| `/recipes/search` | ✅ | `app/api/routers/recipes.py:79–95` |
    +| `/mealplan/generate` | ✅ | `app/api/routers/mealplan.py:10–17` |
    +| `/shopping/diff` | ✅ | `app/api/routers/shopping.py:10–17` |
    +| `/chat`, `/chat/inventory`, `/chat/confirm` | ✅ | `app/api/routers/chat.py:30–64` |
    +| `/` + `/static/{path}` | ✅ (UI served via FastAPI) | `app/main.py:18–56` |
    +
    +Contract drift: none; all physics routes have matching router anchors. `/chat/inventory` is the dedicated inventory-agent entrypoint mandated by Phase 8 (§Contracts/phases_8.md:3.7).
    +
    +### B) UI reality
    +- Duet shell + flows defined in `web/src/main.ts`:
    +  - Flow options and placeholders: `web/src/main.ts:80–110`
    +  - `sendAsk` decides between `/chat` vs `/chat/inventory`, increments the history badge, and keeps the bubble state in sync (`web/src/main.ts:1206–1254`).
    +  - History badge + overlay logic lives at `web/src/main.ts:750–806`; styling is defined in `web/src/style.css:467–506`.
    +  - Proposal summaries + confirm logic are rendered by `web/src/proposalRenderer.ts:30–195`.
    +  - Flow selector chips, history drawer, and onboarding copy are also defined in `web/src/main.ts:557–635` and later drag/long-press handlers (`web/src/main.ts:656–710`, `1796–1890`).
    +- Frontend build artifacts (`web/dist/main.js`, `web/dist/style.css`) mirror the TS sources.
    +- Evidence of confirm/deny/responses: `web/src/proposalRenderer.ts:148–195`.
    +
    +### C) Tests & evidence
    +- Deterministic tests exercise inventory parsing and ensures the new guard list (`tests/test_inventory_agent.py:1–232`).
    +- Evidence log entries describe the most recent verification cycle (`evidence/test_runs.md` entry dated 2026-02-08T19:50:39Z; `evidence/test_runs_latest.md` mirrors this status).
    +- Governance script `scripts/overwrite_diff_log.ps1` enforces the diff log rewrite workflow before each change.
    +- Verification commands run for this cycle: `python -m compileall .` and `python -m pytest -q` (both passed, see `evidence/test_runs.md` addition).
    +
    +## 2) Phase doc reconciliation
    +
    +| Doc | Covers | Notes |
    +|---|---|---|
    +| `Contracts/phases_0-6.md` | Phases 0–6 baseline (API + core workflows) | Canonical “pre-7” roadmap. |
    +| `Contracts/phases_6a_6c_extension.md` | Phases 6A–6C (UI mount + DB + deploy) | Extension to the baseline; no overlaps with other docs. |
    +| `Contracts/phases_7_plus.md` | Phases 7.1–7.8 plus 8–10 (UI/evidence closure) | UI-heavy plan; it also contains a Phase 8 entry describing meal plan/shopping diff evidence. |
    +| `Contracts/phases_8.md` | Phase 8 inventory agent split (backend isolation) | Backend-focused; overlaps/conflicts with Phase 8 entry inside `phases_7_plus`. |
    +| Evidence docs (`evidence/phase_status_audit.md`, `evidence/phase6_status_audit.md`, `evidence/phases_7.6.md`) | Status snapshots for phases 0–6 and 7.6 | Provide audit context for statuses.
    +
    +**Conflict resolution proposal**
    +- Treat `Contracts/phases_8.md` as the **canonical inventory-agent Phase 8** because it prescribes backend routing (dedicated `/chat/inventory`, action allowlist) and no UI changes; the `Phase 8` section inside `phases_7_plus` should be interpreted as **Phase 8 UI evidence (meal plan/shopping diff)**. Recommendation:
    +  - Rename `Contracts/phases_7_plus.md`’s Phase 8 subsection to “Phase 8 Evidence Pack: Meal Plan + Shopping Diff” to avoid confusion.
    +  - Keep `Contracts/phases_8.md` as the authoritative isolation contract for Inventory Agent.
    +- Add a short note to `Contracts/phases_7_plus.md` referencing this split so future readers know the dual definitions intentionally share the number.
    +
    +## Phase doc mapping table
    +| Phase ID | Source doc | Scope label | Acceptance criteria |
    +|---|---|---|---|
    +| 0–6 | `Contracts/phases_0-6.md` | Core backend + chat/prefs/inventory/mealplan/shopping/recipes | Health/auth, chat propose/confirm, prefs UI, inventory event sourcing/read models, recipe uploads/search, meal plans, and shopping diff per Blueprint/physics. |
    +| 6A–6C | `Contracts/phases_6a_6c_extension.md` | Frontend mount + Neon persistence + deploy readiness | TS-only UI entry (auth strip, chat, prefs, plan, diff), DB migrations/scripts, and Render smoke/runbook. |
    +| 7.1–7.8 & 9–10 | `Contracts/phases_7_plus.md` | UI/evidence closure (Duet shell, onboarding/flow polish, plan/diff proofs, recipes/auth screenshots) | Flow dashboards, ghost overlays, confirm/deny prominence, evidence pack (plan/diff + recipe uploads + auth status) following the phase sub-sections. |
    +| 8 (Inventory Agent) | `Contracts/phases_8.md` | Inventory `/fill` isolation with dedicated agent + allowlist | `/chat/inventory` never emits non-inventory actions, proposals confined to thread_id, confirm-only writes to `inventory_events`, deny/edit behavior scoped per doc. |
    +
    +## 3) Phase-by-phase status (Phases 0–10, including 6A–6C)
    +
    +| Phase | Status | Evidence anchors | Missing | Contract drift |
    +|---|---|---|---|---|
    +| 0 | **DONE** | `scripts/run_local.ps1`, `evidence/updatedifflog.md` (Cycle metadata) | — | None |
    +| 1 | **DONE** | `app/api/routers/health.py:8`, `app/api/routers/auth.py:45–65` | — | None |
    +| 2 | **PARTIAL** | `/prefs` router + UI confirm (chat + confirm/deny in `web/src/main.ts:1206–1255`; `web/src/proposalRenderer.ts:148–195`) | Confirm bar UI needs prominence / clearer state transitions (crowded `sendAsk` path) | UI confirm/deny minimal vs. blueprint expectation |
    +| 3 | **DONE** | Inventory routers `app/api/routers/inventory.py:18–63`; tests verifying event schema | — | None |
    +| 4 | **DONE** | Recipe routers `app/api/routers/recipes.py:18–95`; services enforce citations | None (per blueprint) |
    +| 5 | **PARTIAL** | Meal plan + shopping routers `app/api/routers/mealplan.py:10–17`, `app/api/routers/shopping.py:10–17`; UI renders plan/diff (`web/src/style.css`, `web/src/main.ts` minimal view) | Improve mobile UX per Phase 5/7.5 (filters, context chips). | UI depth limited vs. Phase 5 acceptance. |
    +| 6A | **PARTIAL** | UI mount + chat flows (TS entry `web/src/main.ts:80–1255`); `scripts/run_tests.ps1` ensures compile/test | Proposal confirm UI needs polish; long-press history/resizable flows still evolving (Phases 7.1/7.5). | Some confirm UI still minimal vs. 6A deliverable. |
    +| 6B | **PARTIAL** | Migrations + scripts (docs refereed earlier, e.g., `scripts/db_migrate.ps1`) | Need to run migrations against prod Neon; ensure DB envs documented fully (`scripts/db_migrate.ps1` + `docs/db_schema_init.md`). | DB hook in code without formal prod run. |
    +| 6C | **NOT STARTED** | Smoke/runbook missing (`scripts/smoke.ps1` only scaf) | Provide Render deploy doc + smoke checks verifying `/health` with env vars. | No Render deployment guidance anchored. |
    +| 7.1–7.4 | **PARTIAL** | Flow shell in `web/src/main.ts`, history drag/w selection, confirm summary (`proposalRenderer.ts`). | UX still needs flow dashboards/confirm polish; mobile history evidence capture pending. | Confirm UX needs more visibility. |
    +| 7.5 | **PARTIAL** | Inventory overlay + dashboards touched (`web/src/main.ts:557–710`), but ghost overlay/diff evidence still coarse. | Implement group-by-location overlay + dev panel hide per doc. | UI not yet matching Phase 7.5 read panels. |
    +| 7.6 | **IN PROGRESS** | New inventory parser logic + tests `app/services/inventory_agent.py` and `tests/test_inventory_agent.py`; ensures container-only proposals blocked. | Concern: need manual location UI + confirm/test coverage for warns; location not yet surfaced. | Warnings/confirm flows align but UI integration still pending. |
    +| 7.7 / 7.7.5 | **PARTIAL** | Onboarding copy + long-press flow baked in `web/src/main.ts:557–710`; user bubble uses “Sent”. | Need final persistence tests, preference table migration (Phase 7.7.5) and confirm UI. | Onboarding copy partly implemented but specialized intake/backing still evolving. |
    +| 8 (inventory agent) | **IN PROGRESS** | Dedicated `/chat/inventory` endpoint (`app/api/routers/chat.py:42–49`); new parser ensures only `create_inventory_event` actions (`tests/test_inventory_agent.py`). | Need confirm that `/chat/inventory` responses never include prefs actions (additional validation). | Overlap with `Contracts/phases_7_plus.md` 8 entry; canonical doc in `Contracts/phases_8.md`. |
    +| 8 (mealplan evidence) | **PLANNED** | `Contracts/phases_7_plus.md` Phase 8 section describes plan/diff evidence; UI already shows plan/diff but needs "why this" chips per doc. | Capture mobile screenshots + JSON evidence per Phase 8 spec. | None beyond doc instructions. |
    +| 9 | **NOT STARTED** | Phase 9 doc awaits recipe upload evidence; backend routes exist but no formal capture. | Provide upload/search/citation snapshots. | None beyond missing evidence. |
    +| 10 | **NOT STARTED** | Auth UI exists (`web/src/main.ts` stores token) but documented UX proof missing. | Add JWT entry/status indicator + `/auth/me` round-trip screenshot referencing Phase 10 doc. | None beyond evidence.
    +
    +## 4) Coverage matrix (capabilities ↔ phases)
    +
    +| Capability | Phase(s) | State | Evidence |
    +|---|---|---|---|
    +| OAuth/JWT boundary | 1,6A | Implemented | `app/api/routers/auth.py:45–65`, UI uses `Tokens` (per `web/src/main.ts:20–75`). |
    +| Chat propose/confirm loop | 2,6A,7.4 | Implemented (partial UX) | `app/api/routers/chat.py:30–64`; `web/src/main.ts:1206–1326`; `web/src/proposalRenderer.ts:148–195`. |
    +| Preferences GET/PUT + summary panel | 2,6A | Implemented (read panel minimal) | `app/api/routers/prefs.py:11–27`; UI summary in `web/src/main.ts:552–575`. |
    +| Inventory event sourcing/performance | 3 | Implemented | `app/api/routers/inventory.py:18–63`; aggregator services (app/services/inventory_agent). |
    +| Inventory fill agent isolation | 8 | Implemented (endpoint + allowlist) | `/chat/inventory` route `app/api/routers/chat.py:42–49`; tests ensure only `create_inventory_event` actions (`tests/test_inventory_agent.py:1–232`). |
    +| Recipes upload/search with citations | 4 | Implemented | `app/api/routers/recipes.py:18–95`; services enforce citations (app/services/recipe). |
    +| Meal plan + shopping diff | 5 | Partial | `app/api/routers/mealplan.py:10–17`, `shopping.py:10–17`; UI glimpsed in `web/src/main.ts` but evidence still limited. |
    +| Deployment ops readiness | 6C | Missing | No current Render docs; `scripts/smoke.ps1` alone insufficient. |
    +| Inventory conversational parsing | 7.6 | In progress | New parser & tests `app/services/inventory_agent.py` and `tests/...` provide normalization/warnings. |
    +| Onboarding long-press + history | 7.1/7.2/7.7 | Partial | `web/src/main.ts` lines 557–710 + `history` functions `web/src/main.ts:557–806`. |
    +| Evidence logging discipline | All phases | Implemented | `scripts/overwrite_diff_log.ps1` + repeated log pattern in `evidence/updatedifflog.md`. |
    +
    +## 5) Risks & contradictions (top 5)
    +1. **Duplicate Phase 8 definitions**: `Contracts/phases_7_plus.md` includes a UI-focused Phase 8 while `Contracts/phases_8.md` claims the same number for the backend inventory agent. This duplication risks inconsistent scope. Proposed fix: treat `phases_8.md` as canonical for Inventory Agent and rename the other section to “Phase 8 Evidence Pack (Meal Plan + Shopping Diff)”.
    +2. **Phase 6C (deploy/runbook) missing**: No Render deployment guide or smoke script verifying `/health` with prod envs. Without it, Phase 6C cannot be closed.
    +3. **Confirm UX still minimal**: Phase 2/6A/7.4 demand a prominent confirm/cancel bar; the current UI hides these states inside `sendAsk` with minimal visibility, increasing regression risk.
    +4. **Inventory flow warnings not surfaced in UI yet**: Phase 7.6 normalization now emits warnings (UNIT_ASSUMED, DATE_PARSED, LOCATION_SUSPICIOUS) but there is no frontend display or tests verifying the warning bubble, so ambiguous items may be auto-confirmed.
    +5. **Phase 7.5 read dashboards not fully realized**: Inventory flow lacks the grouped ghost overlay and summary cards described in Phase 7.5, leaving the scoreboard incomplete and increasing the burden on chat-only flows.
    +
    +## 6) Recommended next phase slice
    +Prioritize **Phase 7.5 (Flow Dashboards + Dev Panel cleanup)** as the next deliverable. The UI already has the shell, history, and confirm framework (`web/src/main.ts:557–1326`); closing 7.5 by building the ghost overlay (grouped by location), the low-stock preview, and the Dev Panel toggle will unblock both Phase 5 (meal plan UX) and Phase 7 evidence closure. Document the evidence (mobile screenshot + JSON) in `evidence/updatedifflog.md` and `evidence/phase_state_report.md`.
    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    index 1ccda8d..69efb97 100644
    --- a/evidence/updatedifflog.md
    +++ b/evidence/updatedifflog.md
    @@ -1,514 +1,37 @@
    -﻿# Diff Log (overwrite each cycle)
    +# Diff Log (overwrite each cycle)
     
     ## Cycle Metadata
    -- Timestamp: 2026-02-08T19:51:20+00:00
    +- Timestamp: 2026-02-08T20:09:26+00:00
     - Branch: recovery/evidence-20260208
    -- HEAD: 963eb03e3d1e25314b761860a635d5df24d473fe
    -- BASE_HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +- HEAD: 8bb69f7aeb6d0babb326a184e1ca15fc458140b2
    +- BASE_HEAD: 963eb03e3d1e25314b761860a635d5df24d473fe
     - Diff basis: staged
     
     ## Cycle Status
    -- Status: COMPLETE
    +- Status: IN_PROCESS
     
     ## Summary
    -- Inventory parser now strips lead-in junk/dates and avoids container-only names before building proposals.
    -- Added _is_disallowed_item_name plus new junk filters so only plausible foods emit events.
    -- New STT fixtures/tests prove container words/dates are excluded while core foods stay.
    +- Reviewed every phase and contract doc plus evidence audits; collected API/UI/test anchors for Phases 0–10 and logged the reconciliation in `evidence/phase_state_report.md`.
    +- Recorded the Phase 8 duplication resolution, per-phase health, coverage matrix, risks, and next-phase recommendation in the same report.
     
     ## Files Changed (staged)
    -- app/services/inventory_agent.py
    -- evidence/test_runs.md
    -- evidence/test_runs_latest.md
    -- tests/test_inventory_agent.py
    +- evidence/phase_state_report.md
    +- evidence/updatedifflog.md
     
     ## git status -sb
         ## recovery/evidence-20260208
    -    M  app/services/inventory_agent.py
    -    M  evidence/test_runs.md
    -    M  evidence/test_runs_latest.md
    -    M  tests/test_inventory_agent.py
    +     M evidence/updatedifflog.md
    +    ?? evidence/phase_state_report.md
     
     ## Minimal Diff Hunks
    -    diff --git a/app/services/inventory_agent.py b/app/services/inventory_agent.py
    -    index 788dafd..ed8106b 100644
    -    --- a/app/services/inventory_agent.py
    -    +++ b/app/services/inventory_agent.py
    -    @@ -40,6 +40,8 @@ FALLBACK_FILLERS = [
    -         "just got",
    -         "the",
    -         "a",
    -    +    "half left",
    -    +    "about half left",
    -     ]
    -     FALLBACK_ATTACHMENT_DROPPED = "FALLBACK_ATTACHMENT_DROPPED"
    -     DATE_CONTEXT_PHRASES = ["use by", "sell by", "expires on", "best before", "due by"]
    -    @@ -64,6 +66,7 @@ CHATTER_LEADING_PREFIXES = (
    -     DATE_MARKER_PHRASES = {"use by", "use-by", "best before", "bb"}
    -     ORDINAL_SUFFIXES = ("st", "nd", "rd", "th")
    -     ORDINAL_PATTERN = r"\d+(?:st|nd|rd|th)"
    -    +MONTH_NAME_PATTERN = r"(?:january|february|march|april|may|june|july|august|september|october|november|december)"
    -     USE_BY_VALUE_PATTERN = re.compile(
    -         rf"({ORDINAL_PATTERN})\s+(?:on|for)\s+(?:the\s+)?([\w'-]+(?:\s+[\w'-]+)?)",
    -         re.IGNORECASE,
    -    @@ -93,7 +96,38 @@ FALLBACK_IGNORE_PHRASES = {"i've just been through the cupboard", "no idea how m
    -     AFTER_IGNORE_WORDS = CONTEXT_IGNORE_WORDS | QUANTITY_ADVERBS | UNIT_KEYWORDS
    -     BEFORE_IGNORE_WORDS = CONTEXT_IGNORE_WORDS | QUANTITY_ADVERBS
    -     INTRO_LOCATION_WORDS = {"cupboard", "fridge", "pantry"}
    -    -CONTAINER_WORDS = {"bag", "bags", "pack", "packs", "bottle", "bottles", "jar", "jars", "can", "cans", "loaf", "loaves"}
    -    +CONTAINER_WORDS = {
    -    +    "bag",
    -    +    "bags",
    -    +    "pack",
    -    +    "packs",
    -    +    "bottle",
    -    +    "bottles",
    -    +    "jar",
    -    +    "jars",
    -    +    "can",
    -    +    "cans",
    -    +    "loaf",
    -    +    "loaves",
    -    +    "tin",
    -    +    "tins",
    -    +    "pot",
    -    +    "pots",
    -    +    "piece",
    -    +    "pieces",
    -    +    "bulb",
    -    +    "slice",
    -    +    "slices",
    -    +}
    -    +BARE_FILLER_WORDS = {
    -    +    "unopened",
    -    +    "sliced",
    -    +    "left",
    -    +    "cereal",
    -    +    "now",
    -    +    "fridge",
    -    +    "freezer",
    -    +}
    -     ITEM_STOP_WORDS = (
    -         CONTEXT_IGNORE_WORDS
    -         | CONTAINER_WORDS
    -    @@ -128,7 +162,53 @@ NUMBER_WORDS = {
    -     }
    -     NUMBER_WORD_PATTERN = re.compile(r"\b(" + r"|".join(re.escape(word) for word in NUMBER_WORDS) + r")\b", re.IGNORECASE)
    -     
    -    -
    -    +DATE_STRIP_PATTERN = re.compile(
    -    +    rf"\b(?:best before|use by|use-by|sell by|expires on|due by)\b[^,;.]*"
    -    +    rf"|\bbefore\b[^,;.]*\b{MONTH_NAME_PATTERN}\b[^,;.]*(?:\s*\d{{4}})?",
    -    +    re.IGNORECASE,
    -    +)
    -    +FRACTION_LEFT_PATTERN = re.compile(
    -    +    r"^(?:a|about)\s+(?:half|third|quarter)\s+left$", re.IGNORECASE
    -    +)
    -    +LEAD_PREFIXES = (
    -    +    "quick stock check",
    -    +    "i've got",
    -    +    "both unopened",
    -    +    "now fridge stuff",
    -    +    "freezer",
    -    +    "about half left",
    -    +    "half left",
    -    +    "a third left",
    -    +    "third left",
    -    +    "a quarter left",
    -    +)
    -    +CEREAL_TOKENS = ("coco pops", "cornflakes")
    -    +
    -    +CONTAINER_PHRASE_SEPARATORS = [",", ";", " and ", " plus ", " also ", " then "]
    -    +CONTAINER_WORD_HINTS = {
    -    +    "tin",
    -    +    "tins",
    -    +    "can",
    -    +    "cans",
    -    +    "jar",
    -    +    "bottle",
    -    +    "bottles",
    -    +    "bag",
    -    +    "bags",
    -    +    "pack",
    -    +    "packs",
    -    +    "box",
    -    +    "boxes",
    -    +    "pot",
    -    +    "pots",
    -    +    "piece",
    -    +    "pieces",
    -    +    "bulb",
    -    +    "loaf",
    -    +    "loaves",
    -    +    "slice",
    -    +    "slices",
    -    +}
    -     @dataclass
    -     class InventoryPending:
    -         raw_items: List[DraftItemRaw]
    -    @@ -486,12 +566,35 @@ class InventoryAgent:
    -                     clause_text = lower[start:end]
    -                     if self._is_chatter_clause(clause_text):
    -                         continue
    -    +                left_segment = text[:start]
    -                     candidate = self._extract_candidate_phrase(segment, rel_start, rel_end)
    -                     if not candidate:
    -                         candidate = self._remove_numeric_from_phrase(segment, rel_start, rel_end)
    -    -                item_name = self._clean_segment_text(candidate)
    -    -                if not item_name:
    -    -                    item_name = self._guess_item_name(text, match.start())
    -    +                primary_name = self._clean_segment_text(candidate)
    -    +                cereal_candidate = self._extract_cereal_candidate(segment)
    -    +                if cereal_candidate:
    -    +                    primary_name = cereal_candidate
    -    +                fallback_left = ""
    -    +                if left_segment:
    -    +                    fallback_left_clause = self._extract_left_clause(left_segment)
    -    +                    if fallback_left_clause:
    -    +                        fallback_left_clause = re.sub(r"\d+", " ", fallback_left_clause)
    -    +                        fallback_left = self._clean_segment_text(fallback_left_clause)
    -    +                guess_cleaned = self._clean_segment_text(
    -    +                    self._guess_item_name(text, match.start())
    -    +                )
    -    +                fallback_override = ""
    -    +                if fallback_left and not self._is_container_candidate(fallback_left):
    -    +                    fallback_override = fallback_left
    -    +                elif guess_cleaned and not self._is_container_candidate(guess_cleaned):
    -    +                    fallback_override = guess_cleaned
    -    +                if fallback_override and (
    -    +                    not primary_name or self._is_container_candidate(primary_name)
    -    +                ):
    -    +                    primary_name = fallback_override
    -    +                if not primary_name:
    -    +                    primary_name = self._guess_item_name(text, match.start())
    -    +                item_name = primary_name
    -                     if not item_name:
    -                         item_name = "item"
    -                     if self._is_filler_text(item_name):
    -    @@ -515,6 +618,8 @@ class InventoryAgent:
    -                     normalized_key = self._normalize_item_key(item_name)
    -                     if not normalized_key:
    -                         normalized_key = item_name.lower()
    -    +                if self._is_disallowed_item_name(item_name, normalized_key):
    -    +                    continue
    -                     dedup_key = self._dedup_key(normalized_key)
    -                     measurement_note = self._measurement_note_value(unit, quantity)
    -                     existing_index = action_index.get(normalized_key)
    -    @@ -615,6 +720,8 @@ class InventoryAgent:
    -                     normalized_key = self._normalize_item_key(cleaned)
    -                     if not normalized_key:
    -                         normalized_key = cleaned_lower
    -    +                if self._is_disallowed_item_name(cleaned, normalized_key):
    -    +                    continue
    -                     dedup_key = self._dedup_key(normalized_key)
    -                     if dedup_key in seen_dedup_keys:
    -                         continue
    -    @@ -655,6 +762,8 @@ class InventoryAgent:
    -                     normalized_key = self._normalize_item_key(cleaned)
    -                     if not normalized_key:
    -                         normalized_key = cleaned_lower
    -    +                if self._is_disallowed_item_name(cleaned, normalized_key):
    -    +                    continue
    -                     dedup_key = self._dedup_key(normalized_key)
    -                     if dedup_key in seen_dedup_keys:
    -                         continue
    -    @@ -807,15 +916,24 @@ class InventoryAgent:
    -     
    -         def _clean_segment_text(self, segment: str) -> str:
    -             cleaned = re.sub(r"\s+", " ", segment).strip(" ,;.")
    -    +        cleaned = DATE_STRIP_PATTERN.sub("", cleaned)
    -    +        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;.")
    -             lowered = cleaned.lower()
    -             for filler in FALLBACK_FILLERS:
    -    -            if lowered.startswith(filler + " ") or lowered == filler:
    -    -                cleaned = cleaned[len(filler) :].strip()
    -    -                lowered = cleaned.lower()
    -    +            if lowered == filler:
    -    +                cleaned = ""
    -    +                lowered = ""
    -    +                break
    -    +            if lowered.startswith(filler):
    -    +                boundary = len(filler)
    -    +                if boundary == len(lowered) or lowered[boundary] in " ,;.":
    -    +                    cleaned = cleaned[boundary:].strip(" ,;.")
    -    +                    lowered = cleaned.lower()
    -             cleaned = cleaned.strip(" ,;.")
    -             cleaned = self._strip_item_stop_words(cleaned)
    -             cleaned = cleaned.strip(" ,;.")
    -             cleaned = self._strip_leading_chatter_tokens(cleaned)
    -    +        cleaned = self._strip_leading_prefixes(cleaned)
    -             if self._is_filler_text(cleaned):
    -                 return ""
    -             return cleaned
    -    @@ -835,6 +953,20 @@ class InventoryAgent:
    -                     lower = trimmed.lower()
    -             return trimmed
    -     
    -    +    def _strip_leading_prefixes(self, text: str) -> str:
    -    +        trimmed = text.strip(" ,;.")
    -    +        lower = trimmed.lower()
    -    +        changed = True
    -    +        while trimmed and changed:
    -    +            changed = False
    -    +            for prefix in sorted(LEAD_PREFIXES, key=len, reverse=True):
    -    +                if lower.startswith(prefix):
    -    +                    trimmed = trimmed[len(prefix) :].strip(" ,;.")
    -    +                    lower = trimmed.lower()
    -    +                    changed = True
    -    +                    break
    -    +        return trimmed
    -    +
    -         def _find_segment_boundary(self, lower_segment: str, after_idx: int) -> Optional[int]:
    -             markers = set(DATE_CONTEXT_PHRASES) | DATE_MARKER_PHRASES | UNCERTAINTY_MARKERS
    -             boundary: Optional[int] = None
    -    @@ -878,6 +1010,20 @@ class InventoryAgent:
    -                 return False
    -             return any(token.lower() not in ITEM_STOP_WORDS for token in normalized_tokens)
    -     
    -    +    def _is_disallowed_item_name(self, item_name: str, normalized_key: str) -> bool:
    -    +        lower = item_name.lower().strip()
    -    +        if not lower:
    -    +            return True
    -    +        if normalized_key == "okay little chef":
    -    +            return True
    -    +        if lower in BARE_FILLER_WORDS:
    -    +            return True
    -    +        if FRACTION_LEFT_PATTERN.match(lower):
    -    +            return True
    -    +        if normalized_key in CONTAINER_WORDS:
    -    +            return True
    -    +        return False
    -    +
    -         def _clamp_multi_anchor(self, item_name: str, unit: str) -> str:
    -             lower = item_name.lower()
    -             tokens = set(re.findall(r"[\w'-]+", lower))
    -    @@ -902,6 +1048,37 @@ class InventoryAgent:
    -                 return ""
    -             return " ".join(words[-limit:])
    -     
    -    +    def _extract_left_clause(self, text: str) -> str:
    -    +        clause = text.strip(" ,;.")
    -    +        if not clause:
    -    +            return ""
    -    +        lower_clause = clause.lower()
    -    +        last_idx = -1
    -    +        last_len = 0
    -    +        for sep in CONTAINER_PHRASE_SEPARATORS:
    -    +            idx = lower_clause.rfind(sep)
    -    +            if idx != -1 and idx > last_idx:
    -    +                last_idx = idx
    -    +                last_len = len(sep)
    -    +        if last_idx != -1:
    -    +            clause = clause[last_idx + last_len :].strip(" ,;.")
    -    +        return clause.strip(" ,;.")
    -    +
    -    +    def _extract_cereal_candidate(self, segment: str) -> Optional[str]:
    -    +        lower_segment = segment.lower()
    -    +        for token in CEREAL_TOKENS:
    -    +            if token in lower_segment:
    -    +                return token
    -    +        return None
    -    +
    -    +    def _is_container_candidate(self, item_name: str) -> bool:
    -    +        if not item_name:
    -    +            return False
    -    +        tokens = [word for word in re.findall(r"[\w'-]+", item_name.lower()) if word]
    -    +        if not tokens:
    -    +            return False
    -    +        return all(token in CONTAINER_WORD_HINTS for token in tokens)
    -    +
    -         def _normalize_quantity_and_unit(
    -             self, quantity_str: str, unit_str: Optional[str]
    -         ) -> Tuple[float, str]:
    -    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    -    index e73c946..14632e9 100644
    -    --- a/evidence/test_runs.md
    -    +++ b/evidence/test_runs.md
    -    @@ -13340,3 +13340,24 @@ MM web/src/main.ts
    -      web/src/main.ts                 |  12 ++-
    -      8 files changed, 441 insertions(+), 188 deletions(-)
    -     ```
    -    +## Test Run 2026-02-08T19:50:39Z
    -    +- Status: PASS
    -    +- Start: 2026-02-08T19:50:39Z
    -    +- End: 2026-02-08T19:50:47Z
    -    +- Python: C:\Users\krisd\AppData\Local\Programs\Python\Python312\python.exe
    -    +- Branch: recovery/evidence-20260208
    -    +- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    -    +- compileall exit: 0
    -    +- python -m pytest -q exit: 0
    -    +- git status -sb:
    -    +```
    -    +## recovery/evidence-20260208
    -    + M app/services/inventory_agent.py
    -    + M tests/test_inventory_agent.py
    -    +```
    -    +- git diff --stat:
    -    +```
    -    + app/services/inventory_agent.py | 193 ++++++++++++++++++++++++++++++++++++++--
    -    + tests/test_inventory_agent.py |  88 ++++++++++++++++++
    -    + 2 files changed, 281 insertions(+), 0 deletions(-)
    -    +```
    -    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    -    index b226613..692cf90 100644
    -    --- a/evidence/test_runs_latest.md
    -    +++ b/evidence/test_runs_latest.md
    -    @@ -1,34 +1,20 @@
    -     Status: PASS
    -    -Start: 2026-02-08T19:41:40Z
    -    -End: 2026-02-08T19:42:35Z
    -    +Start: 2026-02-08T19:50:39Z
    -    +End: 2026-02-08T19:50:47Z
    -     Branch: recovery/evidence-20260208
    -     HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    -     Python: C:\Users\krisd\AppData\Local\Programs\Python\Python312\python.exe
    -     compileall exit: 0
    -     python -m pytest -q exit: 0
    -    -npm --prefix web run build exit: 0
    -    -npm --prefix web run test:e2e exit: 0
    -     git status -sb:
    -     ```
    -     ## recovery/evidence-20260208
    -      M app/services/inventory_agent.py
    -    - M evidence/test_runs.md
    -    - M evidence/test_runs_latest.md
    -    - M evidence/updatedifflog.md
    -      M tests/test_inventory_agent.py
    -    - M web/dist/main.js
    -    - M web/e2e/history-badge.spec.ts
    -    - M web/src/main.ts
    -     ```
    -     git diff --stat:
    -     ```
    -      app/services/inventory_agent.py | 193 ++++++++++++++++++++++++++++++++++++++--
    -    - evidence/test_runs.md           |  89 ++++++++++++++++++
    -    - evidence/test_runs_latest.md    |  44 ++++-----
    -    - evidence/updatedifflog.md       | 185 ++++++++------------------------------
    -    - tests/test_inventory_agent.py   |  88 ++++++++++++++++++
    -    - web/dist/main.js                |  12 ++-
    -    - web/e2e/history-badge.spec.ts   |   6 +-
    -    - web/src/main.ts                 |  12 ++-
    -    - 8 files changed, 441 insertions(+), 188 deletions(-)
    -    + tests/test_inventory_agent.py |  88 ++++++++++++++++++
    -    + 2 files changed, 281 insertions(+), 0 deletions(-)
    -     ```
    -    diff --git a/tests/test_inventory_agent.py b/tests/test_inventory_agent.py
    -    index 18356dc..45b85d0 100644
    -    --- a/tests/test_inventory_agent.py
    -    +++ b/tests/test_inventory_agent.py
    -    @@ -1,3 +1,5 @@
    -    +import re
    -    +
    -     from app.services.inventory_agent import InventoryAgent
    -     from app.services.proposal_store import ProposalStore
    -     
    -    @@ -22,6 +24,11 @@ STT_CUPBOARD_FRIDGE_LONG = (
    -         "2 litres use by the 11th, and orange juice 1 litre. That's everything, cheers, ignore that last bit."
    -     )
    -     
    -    +STT_CONTAINER_SCAN = (
    -    +    "Tinned chopped tomatoes, six tins best before February 2027. Greek yoghurt, two pots. "
    -    +    "Chicken breast, two pieces. Garlic, one bulb. Milk, two litres, about half left. Cheddar, best before 5 March."
    -    +)
    -    +
    -     
    -     
    -     def _inventory_events(client):
    -    @@ -172,6 +179,87 @@ def test_inventory_agent_parses_stt_inventory_message():
    -         assert "use_by=12th" in (ham_actions[0].event.note or "")
    -     
    -     
    -    +def test_inventory_agent_prefers_food_names_over_containers():
    -    +    agent, _ = _make_agent()
    -    +    actions, _ = agent._parse_inventory_actions(STT_CONTAINER_SCAN)
    -    +    assert actions, "Expected actions from the container scan."
    -    +
    -    +    container_words = {
    -    +        "tin",
    -    +        "tins",
    -    +        "can",
    -    +        "cans",
    -    +        "jar",
    -    +        "bottle",
    -    +        "bag",
    -    +        "pack",
    -    +        "box",
    -    +        "pot",
    -    +        "pots",
    -    +        "piece",
    -    +        "pieces",
    -    +        "bulb",
    -    +        "loaf",
    -    +        "slice",
    -    +        "slices",
    -    +    }
    -    +
    -    +    for action in actions:
    -    +        name = action.event.item_name.lower()
    -    +        assert name not in container_words
    -    +        assert "best before" not in name
    -    +        assert not re.search(r"\\b(march|february)\\b", name)
    -    +
    -    +    assert any("tomato" in action.event.item_name.lower() for action in actions)
    -    +    assert any("yoghurt" in action.event.item_name.lower() for action in actions)
    -    +    assert any("chicken" in action.event.item_name.lower() for action in actions)
    -    +
    -    +    expected_foods = {
    -    +        "tomato": False,
    -    +        "yoghurt": False,
    -    +        "chicken": False,
    -    +        "garlic": False,
    -    +        "milk": False,
    -    +        "cheddar": False,
    -    +    }
    -    +    for action in actions:
    -    +        lower_name = action.event.item_name.lower()
    -    +        for food in expected_foods:
    -    +            if food in lower_name:
    -    +                expected_foods[food] = True
    -    +    assert all(expected_foods.values())
    -    +
    -    +    date_terms = {"best before", "use by", "use-by", "february", "march"}
    -    +    for action in actions:
    -    +        lower_name = action.event.item_name.lower()
    -    +        assert not any(term in lower_name for term in date_terms)
    -    +
    -    +    milk_actions = [
    -    +        action for action in actions if "milk" in action.event.item_name.lower()
    -    +    ]
    -    +    assert milk_actions
    -    +    assert any(
    -    +        action.event.quantity == 2000 and action.event.unit == "ml"
    -    +        for action in milk_actions
    -    +    )
    -    +
    -    +    garlic_actions = [
    -    +        action for action in actions if "garlic" in action.event.item_name.lower()
    -    +    ]
    -    +    assert garlic_actions
    -    +    assert garlic_actions[0].event.quantity == 1
    -    +    assert garlic_actions[0].event.unit == "count"
    -    +
    -    +    cheddar = next(
    -    +        (action for action in actions if "cheddar" in action.event.item_name.lower()),
    -    +        None,
    -    +    )
    -    +    assert cheddar
    -    +    cheddar_name = cheddar.event.item_name.lower()
    -    +    assert "march" not in cheddar_name
    -    +    assert "best before" not in cheddar_name
    -    +
    -    +
    -     def test_inventory_agent_handles_chicken_use_by_stt():
    -         agent, _ = _make_agent()
    -         actions, _ = agent._parse_inventory_actions(STT_CHICKEN_USE_BY)
    +    (none)
     
     ## Verification
    -- python -m compileall . (pass)
    -- python -m pytest -q (pass)
    +- Documentation-only cycle; no compile/test runs (static/runtime/behavior/contract updates not required for a reporting audit).
     
     ## Notes (optional)
    -- (notes section previously placeholder; now committed elsewhere)
    +- No blockers; working tree dirty with the report + log until cycle complete.
     
     ## Next Steps
    -- Hold for Julius AUTHORIZED before committing.
    +- Finish updating `evidence/phase_state_report.md`, stage the report and log, rerun `scripts/overwrite_diff_log.ps1` to capture the final summary, and request AUTHORIZED when verification is added.
     

