# Little Chef v0.1 — Phases 6A–6C Extension

This document extends the canonical Phases 0–6 without modifying them.

## Extension Charter
- Purpose: plan post-Phase-6 work without altering earlier phases.
- Non-negotiables:
  - Physics-first: endpoints/schemas must exist in `Contracts/physics.yaml` before implementation.
  - No UI stack guessing: frontend folder + entrypoint must be explicitly chosen.
  - Frontend source is TypeScript (no JS); compiled output is allowed.
  - Minimal diffs; no refactors unless required by contract.
  - Verification order: static → runtime → behavior → contract.
  - Every cycle ends with diff log overwrite and `scripts/overwrite_diff_log.ps1 -Finalize` passing.

---

## Phase 6A — UI slice catch-up (minimal, mobile-first)

### Phase 6A.0 — Physics-first UI mount
- If UI requires backend serving (e.g., `/` and static assets), update `Contracts/physics.yaml` first to add UI entry route + static asset route(s).
- No implementation may start until physics reflects the UI-serving surface.

### Phase 6A.1 — Smallest viable UI entrypoint (mobile-first)
- Frontend location/entrypoint:
  - `web/index.html`
  - `web/src/main.ts` (TypeScript)
  - `web/tsconfig.json`
  - Build output to `web/dist/` (or repo-standard equivalent if already defined).
- No JS source files; TypeScript only (compiled output permitted).
- UI surfaces (must call existing physics endpoints):
  1) Auth strip: paste/store JWT + call `GET /auth/me`
  2) Chat: `POST /chat` + proposal handling + `POST /chat/confirm` confirm/cancel
  3) Prefs: `GET /prefs`, `PUT /prefs`
  4) Mealplan: `POST /mealplan/generate` render days/meals structure
  5) Shopping diff: `POST /shopping/diff` render missing-only list (show `reason`)
- Apply `ui_style.md` (mobile-first layout rules).

### Acceptance (Phase 6A)
- End-to-end proposal confirm/cancel works.
- Prefs GET/PUT works.
- Mealplan generate + shopping diff render correctly.
- All calls match `physics.yaml` exactly; no extra fields assumed.

### Evidence / Verification (order)
1) Static: TS typecheck/build (if toolchain exists); ensure no JS sources introduced.
2) Runtime: UI loads in mobile viewport; API running locally; network calls succeed.
3) Behavior: exercise the 5 core flows above end-to-end.
4) Contract: verify `physics.yaml` covers any UI-serving surface added in 6A.0.

### Stop & Commit Checkpoint
- End of Phase 6A.

---

## Phase 6B — DB intro (Neon) (gated)
- Objective: replace in-memory repos with persistence.
- Stop Gate (must have before work starts):
  - Neon connection details (env var name + example format).
  - Chosen identity mapping from JWT claim to `user_id` (recommend `sub`, confirm decision).
  - Migration approach chosen: Alembic migrations OR SQL-only migrations (decide once approved).
- First persistence slice: prefs + inventory events only (incremental swap).
- Acceptance:
  - Deterministic tests with dependency overrides (no external DB required in CI).
  - Physics unchanged unless updated first.
- Evidence / Verification (order):
  1) Static: compileall/import
  2) Runtime: app boots with DB env vars
  3) Behavior: pytest with DB overrides/fakes
  4) Contract: physics unchanged (or updated first if needed)
- Stop & Commit Checkpoint: end of Phase 6B.

---

## Phase 6C — Render deploy readiness + real JWT verification config
- Objective: production readiness (Render) with real JWT verification; OAuth remains future.
- Deliverables:
  - Render build/start commands and env var wiring (DB + JWT).
  - Production run instructions.
  - Smoke-check path (script or steps) using configurable auth header.
- Acceptance:
  - Deployed `/health` OK; endpoints match `physics.yaml`.
  - Mobile UX works end-to-end.
- Evidence / Verification (order):
  1) Static: import/compile (and UI build if part of deploy)
  2) Runtime: Render deploy boots; `/health` ok
  3) Behavior: smoke tests against deployed URL (auth header configurable)
  4) Contract: deployed endpoints still match `physics.yaml`
- Stop & Commit Checkpoint: end of Phase 6C.

---

## Decision Log
- Physics-first: update `physics.yaml` before implementing any new surface (including UI mount); physics is not a blocker when updated first.
- Frontend lives in `web/` with TypeScript entrypoint; no JS sources.
- JWT verification is acceptable as an OAuth-forward stepping stone; OAuth flows require physics update before implementation.
