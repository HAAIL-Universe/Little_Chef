# Little Chef — Phases 7+ (UI/TS Evidence Closure Plan)

## 1) Purpose & Scope
- Phase 7+ assumes backend/routes already exist and focuses on UI polish + end-to-end evidence to close remaining Blueprint/Manifesto gaps.
- Hard constraints:
  - Mobile-first UI (per Contracts/ui_style.md).
  - TypeScript source only (no new .js sources).
  - Confirm-before-write is core: propose → confirm/deny (no silent writes).
  - Physics-first: no new routes without updating Contracts/physics.yaml first (not in scope here).
  - Minimal diff per cycle.
  - Evidence discipline: every cycle overwrites evidence/updatedifflog.md with verification (static → runtime → behavior → contract).

## 2) Current Known Gaps (from evidence/blueprint_manifesto_status_audit.md)
- Onboarding/prefs UX needs user-facing proof/polish.
- Inventory add/consume + low-stock needs end-to-end proof.
- Meal plan + shopping diff usability + evidence is thin.
- Recipe upload/retrieval + citations enforcement needs end-to-end proof.

## 3) Phase 7 — TypeScript UI Foundation (Duet Chat + Flows)
Each sub-phase follows: Goal; User-visible outcome; Constraints (TS-only, confirm-before-write, physics-first, mobile-first); Evidence to capture; Verification (static → runtime → behavior → contract); Exit criteria.

### 7.1 Duet Chat Shell (mobile-first)
- Goal: Establish “duet” chat frame with pinned assistant/user bubbles.
- Outcome: Assistant bubble pinned top-left; user bubble pinned bottom-right; composer supports text + mic (mic → transcription into text; send when text exists); history drawer gesture begins to exist (drag user bubble).
- Evidence: screenshots mobile viewport; short clip optional.
- Verification: TS build passes; app boots; smoke basic chat render.
- Exit: Shell renders on mobile, mic affordance visible, drag gesture recognized (even if history empty).

### 7.2 History Drawer “Lock to Scroll” + Inverted Chronology
- Goal: Usable history view.
- Outcome: Most recent messages at top; dragging user bubble to top-third locks into scrollable history; pull-down collapses.
- Evidence: screenshots/GIF showing top-third threshold and collapse; note any fallback on desktop.
- Verification: TS build; manual UI exercise recorded.
- Exit: History drawer behaves as described in mobile viewport.

### 7.3 Flow Selector Bubbles (Inventory / Meal Plan / Prefs)
- Goal: Scope assistant prompts/responses by flow.
- Outcome: Three selector bubbles; active flow visibly highlighted; no-selection shows neutral assist.
- Evidence: screenshots showing each flow active; note state persistence rules.
- Verification: TS build; manual toggle.
- Exit: Flow state reflected in UI and assistant copy switches contextually (static copy acceptable).

### 7.4 Confirm-before-write UX Polish
- Goal: Make confirmations explicit and aligned with assistant bubble.
- Outcome: Proposals render confirm/deny controls within/adjacent to assistant bubble; confirm triggers existing /chat/confirm behavior (no new routes).
- Evidence: screenshot of proposal with controls; API log or console showing confirm call.
- Verification: TS build; manual confirm/deny flow against existing backend or mocked responses.
- Exit: Confirm/deny visible and functional; no silent writes.

### 7.5 Flow Dashboards (read-first)

- Goal:
  - Provide quick read panels when data exists, while keeping the app **chat-first** (dashboards are the display surface).
  - Hide legacy/raw endpoint panels from normal use (mobile-first) by moving them into a collapsed **Dev Panel**.
  - Fix mobile layout overflow (no right-side cut-off / no horizontal scroll).

- Constraints (must hold for all 7.5 work):
  - **Confirm-before-write**: dashboards do not silently mutate user data.
  - **Physics-first**: Phase 7.5 must not introduce new routes or schemas; dashboard data must come from existing backend/physics. If backend data is unavailable, dashboards may render seed/mock placeholders, but must label them as such.
  - **TS-only** source under `web/src/` (no new JS source).

- Outcome:
  - General flow:
    - No dashboard beyond the duet shell; remains chat-only.

  - Inventory flow (read-first dashboard + ghost overlay):
    - On selecting **Inventory**:
      - If the flow has **no messages yet**, render a centered “ghost overlay” (≈ 80% opacity) that shows a scrollable bullet list of inventory entries.
      - This overlay is **not** an assistant message; it is a UI read surface.
      - Overlay groups entries by **location**: `Fridge`, `Freezer`, `Pantry`.
      - Within each group, sort by **soonest expiry first** when expiry exists; otherwise list after dated items.
      - Each bullet row displays: `Item name — quantity+unit — expiry date` (when present).
      - Once the user sends the first message in the Inventory flow, the overlay collapses/fades out and chat becomes primary. Provide a small “Summary” affordance to re-open the overlay later.
    - Inventory dashboard strip (above composer):
      - “At a glance” (counts like: distinct items, expiring soon, low stock) — if backend provides the data; otherwise show placeholder “—”.
      - “Low stock” preview list (top N), with tap → drops user into Inventory chat.
    - Notes:
      - Inventory UX must support expiry-aware display (user standing at fridge reading labels). Exact storage shape (single row vs multiple rows per item) is a backend detail; UI should be able to render multiple rows for an item when backend returns them.
      - FUTURE (requires physics update + confirm-before-write wiring): typed/speech parsing like “bacon 250g 24 Sep fridge” → structured proposal → confirm/deny → write.

  - Meal Plan flow (read-first dashboard):
    - Show “Today / Next” card if plan data exists; show “Last generated plan” card.
    - Provide a clear link/button that navigates to Shopping Diff view (missing-only) for the last plan (using existing backend capability only).
    - Selecting Meal Plan flow keeps chat scoped to Meal Plan.

  - Preferences flow (read-first dashboard):
    - Show compact summary of preference state (servings, meals/day, key allergies/dislikes).
    - Provide “Change preferences” action that routes the user into chat for that flow (proposal → confirm/deny; no silent writes).

  - Dev Panel (hide legacy endpoint surfaces):
    - The following legacy blocks must not be visible in normal use (mobile-first):
      - Old “Chat” debug block with “Send /chat”
      - Prefs debug panel (GET/PUT buttons and raw fields)
      - Mealplan debug panel (POST /mealplan/generate button)
      - Shopping diff debug panel (POST /shopping/diff button)
      - The large legacy “Little Chef” auth/debug section (JWT paste + legacy instructions)
    - Move these into a single **Dev Panel** that is:
      - collapsed/hidden by default
      - accessible only via an explicit “Dev” toggle (small, non-primary)
      - clearly labeled as debug/tools
    - Long-term: delete Dev Panel blocks once replaced by proper dashboards (one-by-one, minimal diffs).

  - Mobile layout/scaling acceptance (fix right-side cut-off):
    - No horizontal overflow in mobile viewport: content must not be cut off to the right; no sideways scroll.
    - Chat bubbles, overlay, flow chips, and composer must fit within viewport width.
    - Evidence screenshots should include at least one small mobile width (e.g., ~360px or ~390px wide).

- Evidence to capture (for UI cycles that implement 7.5):
  - Inventory flow opened with no messages: ghost overlay visible (grouped by location).
  - Inventory after first message: overlay collapsed; chat visible.
  - Each flow selected (General / Inventory / Meal Plan / Preferences) with correct dashboard strip behavior.
  - Dev Panel closed (default) proving legacy blocks are hidden.
  - Dev Panel opened proving legacy blocks are still accessible for debugging.
  - Mobile scaling proof screenshot showing no right-side cut-off.

- Verification:
  - Static: N/A (plan document update only).
  - Runtime: N/A (plan document update only).
  - Behavior: Confirm Phase 7.5 text reflects chat-first + confirm-before-write + physics-first (no new routes/schemas implied).
  - Contract: No new routes/schemas introduced in this plan update; any FUTURE parsing/write behavior explicitly gated by physics update + confirm flow.

- Exit:
  - Phase 7.5 section updated exactly as above with no changes to other phases.

### 7.6 — Inventory conversational parsing & normalization (draft → confirm → write events)
- Goal: Capture free-flow “cupboard scan” speech/text into draft items, normalize deterministically, surface warnings, and only write inventory events after confirm/edit/deny.
- Scope:
  - Parse user message into draft items (LLM extraction contract).
  - Normalize fields (name/variant/item_key, quantity+unit, GB dates, manual location).
  - Warning flags (unit assumed, date parse, location suspicious, expiry unknown, etc.).
  - One event per item (inventory_events payload shape).
  - Bulk confirm/edit/deny flow; no DB writes until confirm.
  - Link to detailed spec: evidence/phases_7.6.md.
- Non-goals:
  - No recall/retrieval.
  - No auto-location; manual toggle only.
  - No batch/lot tracking (totals model only).
  - No onboarding/region switching yet.
- Acceptance (summary):
  - Draft extraction JSON-only, no writes.
  - Normalization enforces g/ml/count with kg/l → g/ml conversions; GB date (DD/MM) to ISO; item_key base|variant.
  - Manual location stored; suspicious location flagged but not blocked.
  - Warnings list present in payload.
  - Confirm writes exactly one event per item; deny writes none; edit updates draft before write.
  - Totals model remains compatible (aggregates by item_key + location).

### 7.7 Preferences-first Onboarding Entry (UI-only scaffolding)
- Goal: Fix first-load bland greeting and provide a deterministic onboarding entry that does not depend on auth/backend.
- Outcome:
  - Default duet assistant fallback copy is onboarding-directed: “Welcome — I’m Little Chef. To start onboarding, fill out your preferences (allergies, likes/dislikes, servings, days).”
  - Default duet user bubble fallback/placeholder is onboarding-directed: “Press and hold to start onboarding and fill out your preferences.”
  - Long-press on the YOU duet bubble opens the existing mini menu at press location with a single **Start** action.
  - Selecting **Start** routes to the **Preferences** flow using the same routing as Options → Preferences (no new routing logic).
  - When onboarding starts, assistant bubble updates to: “Welcome — I’m Little Chef. To get started, let’s set your preferences…”
  - When onboarding starts, user bubble placeholder updates to: “Answer in one message…” (or similar concise prompt).
- Evidence:
  - Screenshot: first load showing new assistant fallback copy.
  - Screenshot: first load showing new user fallback placeholder.
  - Screenshot: long-press menu at press location with Start action.
  - Screenshot: after Start, Preferences flow active and onboarding copy visible.
- Verification:
  - TS/UI build step used by repo (or noted N/A if not required).
  - Manual nav: refresh → new copy; long-press → menu; Start → Preferences flow.
  - Test Gate: run repo test script and record in updatedifflog.
- Exit:
  - First-load copy is on-brand and guides to preferences.
  - Long-press Start deterministically opens Preferences flow; no backend calls required.

### 7.7.5 Preferences Persistence (DB-backed intake + confirm-before-write)
- Goal: Implement Preferences flow end-to-end with persistence for allergies, dislikes, likes, meals/day, servings/people, days/week, cooking style, equipment.
- Outcome:
  - Add preferences table + minimal API to read/write user prefs.
  - One-message intake template captures all fields; produces a proposal; confirm-before-write persists.
  - Preferences dashboard/summary (Phase 7.5 read panel) reflects saved prefs after confirm.
- Evidence:
  - Schema/migration snippet for preferences table.
  - API request/response excerpts (read/write).
  - UI screens: intake → proposal → confirm → persisted summary.
  - Tests proving read/write behavior.
- Verification:
  - Static/type checks as required by repo.
  - Runtime sanity/import checks.
  - Behavior: repo test script + new pref persistence tests.
  - Contract: update physics/openapi only if endpoints require it.
- Exit:
  - Preferences can be captured, confirmed, persisted, and shown in Prefs read panel; refresh shows retained prefs.
  - Note: Silent greet post-auth is parked; onboarding starts via Preferences entry above.

### 7.8 E2E Evidence Closure Pack (Phase 6A/6B/6C support)
  - Goal: Define repeatable proof bundle to flip UNKNOWN/PARTIAL → PASS.
  - Outcome: Checklist for future cycles: mobile screenshots, JSON excerpts of key API responses, smoke outputs, and short notes mapping to Blueprint acceptance items.
- Evidence: Written checklist added to evidence per cycle; sample pack produced once.
- Verification: Inclusion of pack in diff log; no code required.
- Exit: Evidence pack template exists and is used once to demonstrate completeness.

## 4) Phase 8 — Meal Plan + Shopping Diff UX (Usability + Evidence)
- Focus: Make plan/diff usable on mobile using existing routes.
- Evidence required: mobile screenshots of plan/diff views; saved JSON response snippets; “why this” source chips (Built-in vs User Library) with tap-to-open minimal drawer.
- Verification: TS build; manual UI run; contract unchanged.
- Exit: Plan/diff screens usable on mobile with visible citations chips and captured evidence.

## 5) Phase 9 — Recipe Library E2E + Citations Enforcement Proof
- Focus: Upload a recipe PDF, verify search/retrieval, and show meal plan + shopping diff citing user library.
- PASS evidence: upload success (UI + API snippet), search results showing anchors, meal plan citing user library (chips + sources drawer), shopping diff citing user library similarly.
- Note: Any new citation fields/behaviors require physics update first (not in this plan).
- Verification: TS build; manual E2E exercise; contract unchanged unless updated first.
- Exit: All above evidence captured in `evidence/` and linked in diff log.

## 6) Phase 10 — Onboarding/Auth UX Proof
- Focus: Minimal JWT entry + status indicator in UI; prove `/auth/me` works in-app with valid token (Swagger auth limitation acknowledged).
- Evidence: screenshot of JWT entry/status, `/auth/me` success within app UI (token redacted).
- Verification: TS build; manual auth check; contract unchanged.
- Exit: Auth status visible; `/auth/me` round-trip proven in UI.

## 7) Operational Guidance (future cycles)
- Per-cycle evidence checklist:
  - Mobile viewport screenshot(s).
  - Saved key JSON responses (plan, diff, search) in evidence/ or pasted in updatedifflog.
  - Command outputs for verification steps.
  - Smoke run as needed (no secrets printed).
- Always overwrite `evidence/updatedifflog.md` each cycle with verification order: static → runtime → behavior → contract. No appends.
