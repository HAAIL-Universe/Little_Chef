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
- Goal: Provide quick read panels when data exists.
- Outcome: Inventory summary + low-stock preview; Meal Plan last plan/today card + link to diff; Prefs compact summary. Selecting a flow drops user into chat for that flow.
- Evidence: screenshots of each panel populated (can use seed/mock data if backend empty—state clearly).
- Verification: TS build; manual navigation.
- Exit: Panels render and link back into chat composer per flow.

### 7.6 E2E Evidence Closure Pack (Phase 6A/6B/6C support)
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
