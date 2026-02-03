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

---

## 7) Confirmation & safety rules (MVP)

### Confirm-before-write (v0.1 default)
Writes that change inventory or prefs should follow:
1) propose structured change
2) user confirms
3) execute write

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
- `Contracts/physics.yaml` (canonical API contract; OpenAPI format)
- `Contracts/ui_style.md` (authoritative UI look/feel for v0.1)

Nothing else added until v0.1 is working.

---

## 10) v0.1 acceptance checklist

MVP is “done” when:
- A new user can OAuth login (bearer JWT), complete onboarding, and see prefs reflected in UI.
- User can add inventory via chat (g/ml/count) and see correct totals.
- User can log consumption via chat:
  - cooked
  - used separately
  - thrown away
- “What am I low on?” returns sensible results based on thresholds.
- User can generate a 7-day plan (full-day) and receive:
  - structured plan output
  - shopping list diff (missing only)
- Recipe library upload works end-to-end for at least 1 PDF and retrieval is used.
- No plan includes a “user library” recipe without a citation.
- API layer remains thin (no domain logic / SQL / LLM calls inside routers).

--- End of Blueprint ---
