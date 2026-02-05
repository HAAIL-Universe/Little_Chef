# Little Chef — Blueprint (v0.1)

Status: Draft (authoritative for v0.1 build)  
Owner: Julius  
Purpose: Define product fundamentals, hard boundaries, and build targets so implementation cannot drift.

---

## 1) Product intent

Little Chef is a chat-first meal planning and inventory assistant.

The app has two conversation modes:

- **ASK mode**: query your data (e.g., “What am I low on?”, “What am I able to cook tonight?”).
- **FILL mode**: guided form filling via chat (prefs, inventory intake, edits).

The UI shows dashboards/forms as a *display surface* of structured data, but **edits happen via chat** (chat is the primary controller).

---

## Core interaction invariants (must hold)
- Confirm-before-write: all mutations are proposals first; apply only on explicit confirm.
- Exactly one active proposal per thread; a new proposal supersedes the previous active proposal.
- Decline is non-destructive within a thread; declined proposals remain recoverable/editable until a new clean thread starts (then prior proposals are not accessible via UI).
- Thread scope uses `thread_id` (per physics); UI may store/pass it when continuing a thread.
- Voice-first via client-side transcription: backend receives text at `/chat`; no audio routes; no secrets in browser.

---

## 2) MVP scope (v0.1)

### Must ship
1) **OAuth login** (public users soon; no “single-user local” MVP).
   - OAuth sign-in is handled by an external provider/UI flow (managed auth preferred in v0.1).
   - After OAuth, API requests use `Authorization: Bearer <JWT>`.
   - Backend verifies JWT (issuer/audience/signature via JWKS/OpenID config) and resolves the user.
   - v0.1 does not implement custom OAuth initiation/callback endpoints inside Little Chef unless explicitly required.
2) **Onboarding capture** via chat (FILL mode):
   - allergies
   - dislikes/preferences
   - servings/household size
   - meals per day (breakfast/lunch/dinner/supper)
3) **Inventory management** (chat-driven):
   - add items
   - consume items (cooked / used separately / thrown away)
   - simple adjustments/corrections
4) **Meal plan generation**:
   - full-day planning supported (meals/day configurable)
   - uses inventory-first when possible
5) **Shopping list diff**:
   - “missing only” items required to execute the plan
6) **Recipe sources**:
   - built-in baseline recipes included
   - user can upload recipe books/notes as `.pdf`, `.md`, `.txt` and Little Chef can retrieve recipes from them

### Explicitly not MVP (v0.1)
- Nutrition/macros optimization
- Notifications / push alerts
- Auto meal re-ordering based on expiry
- External recipe APIs (licensing/dependency/cost deferred)
- Fine-tuning

---

## 3) Hard boundaries (anti-godfile rules)

### Router/API layer
- Routers are HTTP-only: parse → call service → return response.
- No SQL, no domain rules, no LLM prompt construction in routers.
- No “router calls router”.

### Service layer
- Owns domain logic: inventory math, “low on” rules, plan assembly, shopping diff.
- Calls the repository layer for data.
- Calls the LLM wrapper for model work.

### Repository layer
- Owns DB queries and transactions only.
- No prompt logic, no business rules beyond minimal persistence constraints.

### LLM wrapper
- One integration point for OpenAI.
- All model/tool calls go through this wrapper.
- Services never call OpenAI directly.

---

## 4) Core domain model (conceptual)

### User + preferences
- **User**: id, auth_provider_id, created_at  
  - `auth_provider_id` corresponds to the external auth provider subject/identifier (e.g., `sub` claim).
- **UserPrefs**:
  - allergies[] (e.g., peanuts)
  - dislikes[] (e.g., mushrooms)
  - cuisine_likes[] (optional)
  - servings (int)
  - meals_per_day (int)
  - notes (free text)

### Inventory (event-sourced for auditability)
We store inventory as events so we can answer: “Why is my inventory wrong?”

- **InventoryItem** (catalog entry):
  - id, user_id
  - name (normalized)
  - unit_type: `g|ml|count`
  - default_unit (g/ml/count)
  - optional: category (dry/fresh/frozen/etc.)

- **InventoryEvent**:
  - id, user_id, occurred_at
  - item_name (or item_id if known)
  - event_type:
    - `add` (bought/received)
    - `consume_cooked` (used in a meal)
    - `consume_used_separately` (used outside meals)
    - `consume_thrown_away` (discarded/waste)
    - `adjust` (correction)
  - quantity (number)
  - unit (`g|ml|count`)
  - note (optional: “small chicken breasts”, “half bag”)
  - correlation_id + idempotency_key (for duplicate protection)

**Current inventory state** is derived from events:
- adds increase balance
- consume_* decreases balance
- adjust sets or modifies balance depending on rule chosen (to be defined in service contract)

### Consumption sources (explicit)
Inventory consumption must support these user-intent sources:
- “I cooked this meal” → `consume_cooked`
- “I used this separately” → `consume_used_separately`
- “I threw this away” → `consume_thrown_away`

In v0.1, when the intent is ambiguous, Little Chef must propose a structured event and require confirmation (no silent subtraction).

### Low-stock
- Each user can have thresholds (later UI).
- v0.1 can support:
  - default thresholds by unit_type
  - plus optional per-item overrides

---

## 5) Recipe sources and anti-hallucination rule

Little Chef supports two recipe sources:

1) **Built-in recipes** (shipped with the app)
   - deterministic, structured
   - versioned so results remain stable

2) **User recipe library uploads** (`.pdf`, `.md`, `.txt`)
   - ingested into a per-user vector store for retrieval
   - planning/search uses retrieval; no “book pasted into prompts”

### Hard rule: no invented recipes
Little Chef must not “make up” a recipe that appears to be from a user’s uploads.

Any recipe suggested in a plan must have:
- **either** a `built_in_recipe_id`
- **or** a retrieval citation from the user library (file id + excerpt/title anchor)

If retrieval returns nothing relevant:
- ask a clarifying question
- or fall back to built-in recipes (clearly labeled)

---

## 6) LLM responsibilities (strict)

The model may be used for:
- extracting inventory events from user text (“I threw away 200g spinach”)
- extracting/confirming user prefs from chat
- generating meal plan proposals (structured output)
- mapping plan → shopping list diff (structured output)
- interpreting chat edits (“Swap Tuesday dinner for something spicy”)

The model must NOT:
- directly mutate DB (no direct tool to DB)
- bypass confirmation for destructive actions (see confirmations below)

Background work is allowed (parsing/normalizing messages, pre-fill), but it must only produce proposals or read-only derived state; never commit writes without explicit confirmation. Raw user/assistant messages may be stored for context/audit/background parsing; derived updates still flow through proposal → confirm/decline.

---

## 7) Confirmation & safety rules (MVP)

### Confirm-before-write (v0.1 default)
Writes that change inventory or prefs should follow:
1) propose structured change (one active proposal per thread; new proposal supersedes prior active)
2) user confirms or declines
3) execute write only on confirm

Decline is non-destructive within the thread; starting a new clean thread makes prior thread proposals inaccessible via UI (even if retained for audit).

Exception: small obvious adds can be “auto-confirmed” later, but not in v0.1.

### Deletions
- Deleting recipe books / clearing inventory requires explicit confirmation.

---

## 8) Upload UX (MVP)

A Settings tab includes:
- “Upload recipe book” button (mobile-friendly picker)
- shows status:
  - Uploading
  - Processing
  - Ready
  - Failed (with reason)

Allowed types in v0.1:
- `.pdf`, `.md`, `.txt`

---

## 9) Target system shape (implementation guide, not yet code)

Target folders (to keep things findable/auditable):
- `app/main.py` (FastAPI bootstrap only)
- `app/api/routers/` (HTTP-only routers)
- `app/services/` (domain logic)
- `app/repos/` (DB access)
- `app/llm/` (OpenAI wrapper + schemas)
- `app/models/` (Pydantic models / internal DTOs)
- `app/config/` (env/settings)
- `db/` (schema/migrations)
- `web/` (vanilla TS UI)
- TS-only applies to authored source under `web/src/` (no `.js` sources). If the repo tracks `web/dist/*`, those files are generated build outputs and may include `.js/.css/.html` artifacts that can be committed.
- `Contracts/physics.yaml` (canonical API contract; OpenAPI format)
- `Contracts/ui_style.md` (authoritative UI look/feel for v0.1)

Nothing else added until v0.1 is working.

---

## 10) v0.1 acceptance checklist

MVP is “done” when (each item requires PASS evidence: mobile screenshot/GIF + redacted JSON snippet + endpoint list):
- Auth / prefs: OAuth login with bearer JWT; onboarding prefs via chat; prefs reflected in UI. Evidence: `/auth/me`, `/prefs`.
- Inventory: add via chat (g/ml/count) → proposal → confirm → summary updates; consume (cooked/used separately/thrown away); low-stock output. Evidence: `/inventory/events`, `/inventory/summary`, `/inventory/low-stock`.
- Meal plan: generate 7-day plan with citations. Evidence: `/mealplan/generate` JSON + UI plan view.
- Shopping diff: missing-only items from plan with citations/source chips. Evidence: `/shopping/diff` JSON + UI diff view.
- Recipes: upload at least one PDF and retrieve; plan/diff cites user library; no plan item without citation. Evidence: upload response, `/recipes/search`, plan/diff citations.
- Voice-first: mic → text → `/chat`; no audio endpoints in physics; no secrets in browser.
- Chat confirm/decline: `/chat` shows `thread_id` + proposal; `/chat/confirm` returns `applied` + `status`; decline leaves proposal visible within thread; new clean thread hides prior proposals.
- API layer remains thin (no domain logic / SQL / LLM calls in routers). Evidence: router/service anchors.

E2E proof pack (see Contracts/phases_7_plus.md Phase 7.6): store artifacts in `evidence/` and link from `evidence/updatedifflog.md` each cycle.

--- End of Blueprint ---
