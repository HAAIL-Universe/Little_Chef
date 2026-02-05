# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-05T03:21:06+00:00
- Branch: main
- BASE_HEAD: 168075cc51b616d444a37262b6cb5cbf5d486569
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Expanded Phase 7.5 spec (inventory ghost overlay, dev panel hiding legacy blocks, mobile overflow acceptance) while keeping physics-safe (no new endpoints/schemas).
- Recorded canonical test runs for traceability; no code changes.

## Files Changed (staged)
- Contracts/phases_7_plus.md
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md

## git status -sb
    ## main...origin/main
    M  Contracts/phases_7_plus.md
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
    M  evidence/updatedifflog.md
    ?? evidence/orchestration_system_snapshot.md
    ?? web/node_modules/

## Minimal Diff Hunks
    diff --git a/Contracts/phases_7_plus.md b/Contracts/phases_7_plus.md
    index c281622..4435dca 100644
    --- a/Contracts/phases_7_plus.md
    +++ b/Contracts/phases_7_plus.md
    @@ -48,15 +48,83 @@ Each sub-phase follows: Goal; User-visible outcome; Constraints (TS-only, confir
     - Exit: Confirm/deny visible and functional; no silent writes.
     
     ### 7.5 Flow Dashboards (read-first)
    -- Goal: Provide quick read panels when data exists.
    -- Outcome: Inventory summary + low-stock preview; Meal Plan last plan/today card + link to diff; Prefs compact summary. Selecting a flow drops user into chat for that flow.
    -- Evidence: screenshots of each panel populated (can use seed/mock data if backend empty—state clearly).
    -- Verification: TS build; manual navigation.
    -- Exit: Panels render and link back into chat composer per flow.
    -
    -### 7.6 E2E Evidence Closure Pack (Phase 6A/6B/6C support)
    -- Goal: Define repeatable proof bundle to flip UNKNOWN/PARTIAL → PASS.
    -- Outcome: Checklist for future cycles: mobile screenshots, JSON excerpts of key API responses, smoke outputs, and short notes mapping to Blueprint acceptance items.
    +
    +- Goal:
    +  - Provide quick read panels when data exists, while keeping the app **chat-first** (dashboards are the display surface).
    +  - Hide legacy/raw endpoint panels from normal use (mobile-first) by moving them into a collapsed **Dev Panel**.
    +  - Fix mobile layout overflow (no right-side cut-off / no horizontal scroll).
    +
    +- Constraints (must hold for all 7.5 work):
    +  - **Confirm-before-write**: dashboards do not silently mutate user data.
    +  - **Physics-first**: Phase 7.5 must not introduce new routes or schemas; dashboard data must come from existing backend/physics. If backend data is unavailable, dashboards may render seed/mock placeholders, but must label them as such.
    +  - **TS-only** source under `web/src/` (no new JS source).
    +
    +- Outcome:
    +  - General flow:
    +    - No dashboard beyond the duet shell; remains chat-only.
    +
    +  - Inventory flow (read-first dashboard + ghost overlay):
    +    - On selecting **Inventory**:
    +      - If the flow has **no messages yet**, render a centered “ghost overlay” (≈ 80% opacity) that shows a scrollable bullet list of inventory entries.
    +      - This overlay is **not** an assistant message; it is a UI read surface.
    +      - Overlay groups entries by **location**: `Fridge`, `Freezer`, `Pantry`.
    +      - Within each group, sort by **soonest expiry first** when expiry exists; otherwise list after dated items.
    +      - Each bullet row displays: `Item name — quantity+unit — expiry date` (when present).
    +      - Once the user sends the first message in the Inventory flow, the overlay collapses/fades out and chat becomes primary. Provide a small “Summary” affordance to re-open the overlay later.
    +    - Inventory dashboard strip (above composer):
    +      - “At a glance” (counts like: distinct items, expiring soon, low stock) — if backend provides the data; otherwise show placeholder “—”.
    +      - “Low stock” preview list (top N), with tap → drops user into Inventory chat.
    +    - Notes:
    +      - Inventory UX must support expiry-aware display (user standing at fridge reading labels). Exact storage shape (single row vs multiple rows per item) is a backend detail; UI should be able to render multiple rows for an item when backend returns them.
    +      - FUTURE (requires physics update + confirm-before-write wiring): typed/speech parsing like “bacon 250g 24 Sep fridge” → structured proposal → confirm/deny → write.
    +
    +  - Meal Plan flow (read-first dashboard):
    +    - Show “Today / Next” card if plan data exists; show “Last generated plan” card.
    +    - Provide a clear link/button that navigates to Shopping Diff view (missing-only) for the last plan (using existing backend capability only).
    +    - Selecting Meal Plan flow keeps chat scoped to Meal Plan.
    +
    +  - Preferences flow (read-first dashboard):
    +    - Show compact summary of preference state (servings, meals/day, key allergies/dislikes).
    +    - Provide “Change preferences” action that routes the user into chat for that flow (proposal → confirm/deny; no silent writes).
    +
    +  - Dev Panel (hide legacy endpoint surfaces):
    +    - The following legacy blocks must not be visible in normal use (mobile-first):
    +      - Old “Chat” debug block with “Send /chat”
    +      - Prefs debug panel (GET/PUT buttons and raw fields)
    +      - Mealplan debug panel (POST /mealplan/generate button)
    +      - Shopping diff debug panel (POST /shopping/diff button)
    +      - The large legacy “Little Chef” auth/debug section (JWT paste + legacy instructions)
    +    - Move these into a single **Dev Panel** that is:
    +      - collapsed/hidden by default
    +      - accessible only via an explicit “Dev” toggle (small, non-primary)
    +      - clearly labeled as debug/tools
    +    - Long-term: delete Dev Panel blocks once replaced by proper dashboards (one-by-one, minimal diffs).
    +
    +  - Mobile layout/scaling acceptance (fix right-side cut-off):
    +    - No horizontal overflow in mobile viewport: content must not be cut off to the right; no sideways scroll.
    +    - Chat bubbles, overlay, flow chips, and composer must fit within viewport width.
    +    - Evidence screenshots should include at least one small mobile width (e.g., ~360px or ~390px wide).
    +
    +- Evidence to capture (for UI cycles that implement 7.5):
    +  - Inventory flow opened with no messages: ghost overlay visible (grouped by location).
    +  - Inventory after first message: overlay collapsed; chat visible.
    +  - Each flow selected (General / Inventory / Meal Plan / Preferences) with correct dashboard strip behavior.
    +  - Dev Panel closed (default) proving legacy blocks are hidden.
    +  - Dev Panel opened proving legacy blocks are still accessible for debugging.
    +  - Mobile scaling proof screenshot showing no right-side cut-off.
    +
    +- Verification:
    +  - Static: N/A (plan document update only).
    +  - Runtime: N/A (plan document update only).
    +  - Behavior: Confirm Phase 7.5 text reflects chat-first + confirm-before-write + physics-first (no new routes/schemas implied).
    +  - Contract: No new routes/schemas introduced in this plan update; any FUTURE parsing/write behavior explicitly gated by physics update + confirm flow.
    +
    +- Exit:
    +  - Phase 7.5 section updated exactly as above with no changes to other phases.
    +
    +  ### 7.6 E2E Evidence Closure Pack (Phase 6A/6B/6C support)
    +  - Goal: Define repeatable proof bundle to flip UNKNOWN/PARTIAL → PASS.
    +  - Outcome: Checklist for future cycles: mobile screenshots, JSON excerpts of key API responses, smoke outputs, and short notes mapping to Blueprint acceptance items.
     - Evidence: Written checklist added to evidence per cycle; sample pack produced once.
     - Verification: Inclusion of pack in diff log; no code required.
     - Exit: Evidence pack template exists and is used once to demonstrate completeness.
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    index e7b7e39..933658a 100644
    --- a/evidence/test_runs.md
    +++ b/evidence/test_runs.md
    @@ -2747,3 +2747,27 @@ MM web/src/main.ts
      2 files changed, 7 deletions(-)
     ```
     
    +## Test Run 2026-02-05T03:20:48Z
    +- Status: PASS
    +- Start: 2026-02-05T03:20:48Z
    +- End: 2026-02-05T03:20:53Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 168075cc51b616d444a37262b6cb5cbf5d486569
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 35 passed, 1 warning in 1.99s
    +- git status -sb:
    +```
    +## main...origin/main
    +M  Contracts/phases_7_plus.md
    +M  evidence/updatedifflog.md
    +?? evidence/orchestration_system_snapshot.md
    +?? web/node_modules/
    +```
    +- git diff --stat:
    +```
    +
    +```
    +
    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    index 085c7f3..53ba900 100644
    --- a/evidence/test_runs_latest.md
    +++ b/evidence/test_runs_latest.md
    @@ -1,30 +1,23 @@
     Status: PASS
    -Start: 2026-02-05T02:24:01Z
    -End: 2026-02-05T02:24:06Z
    +Start: 2026-02-05T03:20:48Z
    +End: 2026-02-05T03:20:53Z
     Branch: main
    -HEAD: e7b2c60c5d1cc87bd0aa2c91ad1af1ec7098ec52
    +HEAD: 168075cc51b616d444a37262b6cb5cbf5d486569
     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
     compileall exit: 0
     import app.main exit: 0
     pytest exit: 0
    -pytest summary: 35 passed, 1 warning in 1.98s
    +pytest summary: 35 passed, 1 warning in 1.99s
     git status -sb:
     ```
     ## main...origin/main
    -M  Contracts/physics.yaml
    -M  evidence/test_runs.md
    -M  evidence/test_runs_latest.md
    +M  Contracts/phases_7_plus.md
     M  evidence/updatedifflog.md
    -A  tests/test_openapi_chat_contract.py
    -MM web/dist/main.js
    -MM web/src/main.ts
     ?? evidence/orchestration_system_snapshot.md
     ?? web/node_modules/
     ```
     git diff --stat:
     ```
    - web/dist/main.js | 4 ----
    - web/src/main.ts  | 3 ---
    - 2 files changed, 7 deletions(-)
    +
     ```
     
    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    index c794149..493e0c5 100644
    --- a/evidence/updatedifflog.md
    +++ b/evidence/updatedifflog.md
    @@ -1,60 +1,41 @@
     # Diff Log (overwrite each cycle)
     
     ## Cycle Metadata
    -- Timestamp: 2026-02-05T01:49:12+00:00
    +- Timestamp: 2026-02-05T03:16:35+00:00
     - Branch: main
    -- BASE_HEAD: e7b2c60c5d1cc87bd0aa2c91ad1af1ec7098ec52
    +- BASE_HEAD: 168075cc51b616d444a37262b6cb5cbf5d486569
     - Diff basis: staged
     
     ## Cycle Status
     - Status: COMPLETE
     
     ## Summary
    -- Re-applied Phase 7.4A UI wiring: ASK calls backend `/chat` with mode=ask/message/include_user_library, adds thinking placeholder, disables composer in-flight, renders reply/errors; flow label kept in local echo.
    -- Synced physics /chat schemas to backend OpenAPI (removed thread_id from request/response; include_user_library retained; /chat/confirm present).
    -- Added deterministic OpenAPI drift test (`tests/test_openapi_chat_contract.py`) guarding /chat fields and /chat/confirm presence.
    +- Expanded Phase 7.5 plan to specify inventory ghost overlay, dev panel hiding legacy debug blocks, and mobile overflow acceptance while keeping physics-safe (no new routes/schemas).
    +- Clarified read-first dashboards per flow with confirm-before-write and physics-first constraints; marked parsing/write items as FUTURE gated by physics updates.
     
     ## Files Changed (staged)
    -- Contracts/physics.yaml
    -- web/src/main.ts
    -- web/dist/main.js
    -- tests/test_openapi_chat_contract.py
    -- evidence/test_runs.md
    -- evidence/test_runs_latest.md
    +- Contracts/phases_7_plus.md
     - evidence/updatedifflog.md
     
     ## git status -sb
         ## main...origin/main
    -    M  Contracts/physics.yaml
    -    M  evidence/test_runs.md
    -    M  evidence/test_runs_latest.md
    -    M  evidence/updatedifflog.md
    -    M  web/dist/main.js
    -    M  web/src/main.ts
    -    A  tests/test_openapi_chat_contract.py
    +     M Contracts/phases_7_plus.md
         ?? evidence/orchestration_system_snapshot.md
         ?? web/node_modules/
     
     ## Minimal Diff Hunks
    -    web/src/main.ts (ASK wiring):
    -      - sendAsk POST /chat body: { mode: "ask", message, include_user_library: true }; removed thread_id from request/response handling; added in-flight disable + thinking placeholder; flow labels kept in local echo.
    -
    -    Contracts/physics.yaml (/chat):
    -      - ChatRequest properties: mode (ask|fill), message (string, minLength 1), include_user_library (boolean, default true). thread_id removed.
    -      - ChatResponse properties: reply_text, confirmation_required, proposal_id?, proposed_actions[], suggested_next_questions[]. thread_id removed. /chat/confirm retained.
    -
    -    tests/test_openapi_chat_contract.py:
    -      - EXPECT_CHAT_CONFIRM=True; EXPECT_REQ_FIELDS={"mode","message","include_user_library"}; EXPECT_RESP_FIELDS={"reply_text","confirmation_required"}.
    -      - Resolves $ref/allOf from app.openapi(); asserts expected fields subset of actual; asserts /chat/confirm presence.
    +    Contracts/phases_7_plus.md:
    +      - Replaced Phase 7.5 section with detailed UI plan (inventory ghost overlay, dev panel collapse, mobile overflow acceptance) and physics-safe constraints; no endpoint/schema additions.
     
     ## Verification
    -- Static: python -m compileall app (PASS).
    -- Runtime: OpenAPI proof → `python -c "from app.main import app; import json; o=app.openapi(); print('HAS_/chat/confirm', ('/chat/confirm' in o.get('paths',{}))); print(json.dumps(o['paths']['/chat'], indent=2))"` → HAS_/chat/confirm True.
    -- Tests: `pwsh -NoProfile -Command "./scripts/run_tests.ps1"` (PASS); `pwsh -NoProfile -Command "Set-Item Env:PYTHONPATH '.'; pytest -q -p no:cacheprovider"` → 35 passed (new contract test included).
    -- Contract: physics.yaml now matches OpenAPI evidence; /chat/confirm present; node_modules and snapshot remain untracked; UI uses ASK-only.
    +- Static: N/A (documentation-only).
    +- Runtime: N/A (documentation-only).
    +- Behavior: Plan reviewed for chat-first, confirm-before-write, physics-first compliance (no new routes/schemas).
    +- Contract: Physics untouched; plan explicitly gates FUTURE parsing/writes on physics updates + confirm.
     
     ## Notes (optional)
    -- UI stash reapplied; no npm install run. BASE_HEAD == HEAD per helper; accepted.
    +- Snapshot and node_modules remain untracked/out-of-band; no code touched.
     
     ## Next Steps
     - Await authorization to commit/push.
    +

## Verification
- Static: N/A (documentation-only).
- Runtime: N/A (documentation-only).
- Behavior: Plan text reviewed for chat-first + confirm-before-write + physics-first; no new routes/schemas.
- Contract: Physics untouched this cycle; FUTURE parsing/write items explicitly gated.
- Tests: `pwsh -NoProfile -Command "./scripts/run_tests.ps1"` (PASS) — evidence logs updated for audit trace.

## Notes (optional)
- Snapshot and node_modules remain untracked/out-of-band.

## Next Steps
- Await authorization to commit/push.

