# Little Chef v0.1 — Phases 6A–6C Extension

This document extends the canonical Phases 0–6 without modifying them.

---

## Phase 6A — UI slice catch-up (minimal, mobile-first)
- **Objective:** Deliver the missing UI surfaces already promised by earlier phases, without changing backend physics.
- **Deliverables (checklist):**
  - [ ] Mobile-first PWA shell (installable basics if assets exist; otherwise minimal web shell)
  - [ ] Chat surface + confirm/cancel UI for proposals
  - [ ] Prefs dashboard panel (per ui_style.md)
  - [ ] Meal plan view (structured days/meals)
  - [ ] Shopping diff view (missing-only list)
- **Acceptance:**
  - UI can call existing endpoints and render dashboards
  - Proposal confirm/cancel UX works end-to-end
  - No physics changes required
- **Evidence / Verification (order):**
  1) Static: lint/build (if UI toolchain exists)
  2) Runtime: local serve loads on mobile viewport
  3) Behavior: UI can POST /chat and /chat/confirm, GET /prefs, POST /mealplan/generate, POST /shopping/diff
  4) Contract: no physics changes
- **Stop & Commit Checkpoint:** end of Phase 6A

## Phase 6B — DB intro (Neon) (gated)
- **Objective:** Replace in-memory repos with persistence, aligned to manifest/blueprint constraints.
- **Stop Gate (mandatory):** Do not implement DB until Director provides Neon connection details and approves schema approach.
- **Deliverables (once approved) (checklist):**
  - [ ] DB connection wiring via env
  - [ ] Minimal schema/migrations for prefs + inventory first
  - [ ] Incremental swap: prefs/inventory -> DB; then recipes/mealplans
- **Acceptance:**
  - Tests pass deterministically with dependency overrides
  - Physics unchanged unless explicitly updated first
- **Evidence / Verification (order):**
  1) Static: compileall/import
  2) Runtime: app boots with DB env vars
  3) Behavior: pytest with DB overrides/fakes
  4) Contract: physics unchanged
- **Stop & Commit Checkpoint:** end of Phase 6B

## Phase 6C — Render deploy readiness + real JWT config
- **Objective:** Production readiness (Render) and real JWT config exercised beyond overrides.
- **Deliverables (checklist):**
  - [ ] Render config + env var wiring (DB + JWT settings)
  - [ ] Production run instructions
  - [ ] Minimal integration check path (non-OAuth, just JWT verification config)
- **Acceptance:**
  - Deployed endpoints still match physics
  - Mobile UX works end-to-end
- **Evidence / Verification (order):**
  1) Static: compileall/import
  2) Runtime: Render deploy boots; /health ok
  3) Behavior: smoke tests against deployed URL (auth header configurable)
  4) Contract: physics unchanged
- **Stop & Commit Checkpoint:** end of Phase 6C
