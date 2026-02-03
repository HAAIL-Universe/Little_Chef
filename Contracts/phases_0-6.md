# Little Chef v0.1 Phases  
**Mobile-first PWA · Chat-first · Dashboards as the display surface · Physics-first**

## Guardrails (apply to every phase)
- **Physics law is authoritative** (`Contracts/physics.yaml`): endpoints, schemas, and “no write without confirmation” behavior.
- **Two chat modes only:** **ASK** (query) and **FILL** (guided capture/edit).
- **Edits happen via chat**; UI renders **structured dashboards/forms** (not freeform editing).
- **Auth:** API accepts **Bearer JWT** obtained externally (OAuth flow is out-of-scope for the API in v0.1).
- **Persistence:** Neon Postgres for storage.
- **Hosting target:** Render.
- **Evidence discipline:** minimal diffs; directives follow verification order **static → runtime → behavior → contract**; diff log overwrite via `scripts/overwrite_diff_log.ps1` into `evidence/updatedifflog.md`.

---

## Phase 0 — Repo bootstrap + contract wiring
**Objective:** establish a buildable baseline with contracts in-place and a runnable skeleton.

**Deliverables**
- Repo skeleton runs locally (backend + frontend entrypoints).
- Contracts are present and treated as authoritative inputs to the build.
- Evidence workflow is present: `scripts/overwrite_diff_log.ps1` and `evidence/updatedifflog.md`.

**Acceptance**
- “Run local” path exists (e.g., `scripts/run_local.ps1` or equivalent) and produces a running app, even if minimal.

---

## Phase 1 — Auth boundary + health + “who am I”
**Objective:** prove the API boundary and JWT verification flow per physics.

**Deliverables**
- `GET /health` returns `{ status: "ok" }`.
- `GET /auth/me`:
  - returns **401** without valid Bearer token
  - returns `UserMe` with valid token
- Minimal user resolution layer:
  - map external `sub` → internal `user_id` (storage design is implementation-specific, but must be deterministic and persistent).

**Acceptance**
- Runtime: health ok; auth/me behaves exactly per OpenAPI schemas.
- Contract: responses match physics.

---

## Phase 2 — Chat propose/confirm loop + Prefs + first dashboard surface (vertical slice)
**Objective:** deliver the first full “chat edits + dashboard reflects persisted state” slice.

**Deliverables**
- Prefs:
  - `GET /prefs`
  - `PUT /prefs` (idempotent-friendly)
- Chat:
  - `POST /chat` supports **FILL** mode to **propose** `upsert_prefs` actions (no write)
  - `POST /chat/confirm` applies or discards proposals
  - `ChatResponse.confirmation_required` + `proposal_id` behavior implemented
- UI (mobile-first PWA):
  - Chat surface (text input)
  - **Voice input** available in chat (implementation choice left to repo approach, but must be usable on mobile)
  - A **Prefs dashboard panel** using glassmorphism over blurred multicolour gradient background (per `ui_style.md`)
  - Confirm / cancel UX for proposals inside chat

**Acceptance**
- Behavior: “I’m allergic to peanuts; servings 2; meals per day 3” → chat proposes prefs → user confirms → `/prefs` reflects new prefs → UI dashboard reflects stored prefs.
- Contract: payloads match `UserPrefs`, `ChatResponse`, `ConfirmProposalResponse`.

---

## Phase 3 — Inventory event sourcing + derived read models + chat actions
**Objective:** inventory is event-sourced and queryable via ASK mode.

**Deliverables**
- Inventory writes/reads:
  - `GET /inventory/events`
  - `POST /inventory/events`
  - `GET /inventory/summary` derived from events
  - `GET /inventory/low-stock` derived from events (threshold logic must be explicit in code/spec; no hidden magic)
- Chat:
  - **FILL**: propose `create_inventory_event` actions (add/consume/adjust types per schema)
  - **ASK**: answers “what am I low on?” using low-stock endpoint

**Acceptance**
- Behavior: “Add 500g chicken” → proposal → confirm → summary shows chicken.
- Behavior: “I used 200g chicken for dinner” → proposal → confirm → summary decreases.
- Contract: event types/units conform to physics enums; idempotency respected for writes.

---

## Phase 4 — Recipes: built-in baseline + user uploads + retrieval with citations
**Objective:** recipe retrieval works across built-in + user library, with **no invented user-library recipes**.

**Deliverables**
- Recipe books:
  - `GET /recipes/books`
  - `POST /recipes/books` (upload `.pdf`, `.md`, `.txt`)
  - `GET /recipes/books/{book_id}`
  - `DELETE /recipes/books/{book_id}`
  - Processing lifecycle supported (`uploading/processing/ready/failed`)
- Search:
  - `POST /recipes/search` returns results with:
    - `source_type=built_in` + `built_in_recipe_id` when built-in
    - `source_type=user_library` + anchors (`book_id`, `file_id`, `excerpt`) when user-derived
- Chat:
  - ASK recipe queries call recipe search and respond with **source anchors** in the output (so user can see “why this recipe surfaced”).

**Acceptance**
- Upload → appears in list → becomes ready → search returns anchored results.
- Hard rule enforced: **no user-library recipe content is returned without retrieval anchors** (excerpt + identifiers).

---

## Phase 5 — Meal plan generation + shopping diff (missing-only)
**Objective:** generate meal plans that cite sources and compute shopping list diff against inventory.

**Deliverables**
- `POST /mealplan/generate`
  - inventory-first behavior (implementation-specific but must be consistent)
  - each planned meal includes `RecipeSource` with citation anchors
- `POST /shopping/diff`
  - returns **missing-only** items for the generated plan
- UI dashboards:
  - Meal plan view (structured days/meals)
  - Shopping diff view (missing-only list)

**Acceptance**
- Meal plan response contains sources for each meal (built-in id or user-library anchors).
- Shopping diff returns only missing items (not full ingredient list).

---

## Phase 6 — Deployment readiness (Render + PWA)
**Objective:** ship an installable, mobile-first PWA + API that runs in production.

**Deliverables**
- Render deployment configuration (backend + frontend) with environment variables for:
  - DB connection
  - JWT verification settings (issuer/audience/JWKS/OIDC discovery as chosen)
- Neon DB wired in production.
- PWA installability and mobile layout verified.

**Acceptance**
- Prod endpoints conform to physics.
- Mobile UX works end-to-end (chat, dashboards, confirm flows).

---

## Phase boundaries (workflow)
At the end of each phase:
- **Stop & commit checkpoint** (clean commit with minimal diff).
- Overwrite `evidence/updatedifflog.md` via `scripts/overwrite_diff_log.ps1`.
- Verification evidence recorded in the diff log (static → runtime → behavior → contract).
