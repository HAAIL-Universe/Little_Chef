# phases_10+.md

## How to use this phases document
This document defines **Phases 10+** for Little Chef. Treat it as the "north star" plan from the current project state onward.

Operating rules:
- Work **one phase at a time**. Do not mix phase deliverables unless explicitly instructed.
- At the start of each phase, run an **evidence-first audit**:
  1) Read the current code paths for the relevant flow(s)
  2) Compare current behavior to the phase requirements
  3) Produce a minimal-diff implementation plan scoped to the smallest set of files
  4) Run verification (static → runtime → behavior → tests → contract)
- If any phase assumption is not supported by current code, stop and flag it before implementing.

---

## Current baseline (pre–Phase 10 reality)
As of the most recent audit:
- ChefAgent exists and serves **POST `/chat/mealplan`** using **propose → confirm → apply**.
- Meal plan generation is **deterministic** (regex parsing + round-robin) and uses only **3 built-in recipes**.
- Installed Hugging Face recipe packs are stored in `recipe_books` but are **not used** by meal planning.
- No plan persistence; confirm returns a `plan_id` but does not write to DB.
- Shopping diff exists as **POST `/shopping/diff`** but is **not wired** into the ChefAgent flow.
- No decision engine ("what can I make now?"), no "can I cook X?", no scoring, no expiry awareness, no consume-event logging.

---

## System capability anchors (locked truths)
These are verified capabilities that Phases 10+ may rely on without guesswork:

### Inventory: numeric quantity tracking (event-sourced)
- Inventory is fully **event-sourced** via `inventory_events`.
- Three consume event types exist and **numerically decrement float quantities**:
  - `consume_cooked`
  - `consume_used_separately`
  - `consume_thrown_away`
- Inventory summary is derived by replay keyed by `(item_name, unit, location)`.
- Low-stock detection exists with unit-based thresholds.

**Implication for Phase 11+:**
"Cooked/Consumed" can be implemented as real consume events (not just name-only flags), but only once the plan→ingredient mapping is reliable.

### Preferences: time constraints exist; budget does not
- Preferences include:
  - `cook_time_weekday_mins`
  - `cook_time_weekend_mins`
- No budget/cost fields exist anywhere today.

**Implication for Phase 10+:**
Time-based filtering/ranking is feasible; budget mode is out-of-scope until a schema addition.

### Recipe books: pack recipes are structured markdown; uploads are freeform
- `recipe_books.text_content` stores markdown as a single TEXT blob.
- Built-in pack books are consistently sectioned with `## Ingredients` and other headers (parseable).
- User uploads are freeform and not reliably parseable.
- No ingredient parsing exists today; current meal planner uses hardcoded ingredients for 3 recipes.

**Implication for Phase 10 MVP:**
Phase 10 should treat built-in pack recipes as the primary scalable corpus and parse only the pack-style `## Ingredients` section for structured ingredient lists. User uploads can remain searchable/displayable, but not guaranteed for planning precision until later.

---

## Phase 10 — Chef Agent MVP v1
### Goal
Turn the Chef Agent into a genuinely useful "kitchen brain" while keeping scope tight:
- **Decision engine** for "what can I make right now?"
- **1-day meal plan** generation that uses the real recipe corpus (installed packs) and shows usable steps
- **Inventory-aware ranking** with missing ingredients surfaced
- Use prefs constraints in priority order:
  1) allergies (hard filter)
  2) dislikes (hard filter)
  3) likes (soft boost)
  4) cook time (soft filter/boost if present)

### Endpoint routing (current reality)
Today, chat routing is by **endpoint path**, not by in-message mode detection:
- **`POST /chat/mealplan`** → `ChefAgent.handle_fill()` — always generates a meal plan proposal (`confirmation_required=True`).
- **`POST /chat`** (ask mode) → `ChatService.handle_chat()` — returns informational replies (no proposal).
- **`POST /chat/confirm`** → `ChatService.confirm()` → delegates to whichever agent owns the proposal.
- `ChatRequest.mode` is `Literal["ask", "fill"]`. No "plan"/"match"/"check" sub-modes exist yet.

Phase 10 routing plan:
- **PLAN** stays on `POST /chat/mealplan` with propose→confirm→apply (existing flow).
- **MATCH** and **CHECK** are informational queries. They should be served via `POST /chat` in ask mode (or by extending ChefAgent to handle ask-mode dispatch from `/chat/mealplan`). They do **not** create proposals — they return immediate `ChatResponse` results.
- No new endpoints are required; extend existing routing.

### Phase 10 constraints (non-negotiable)
- **No multi-day planning** (keep 1-day MVP clean; multi-day comes in Phase 11).
- **No expiry-aware suggestions** (requires storing expiry in a queryable form; comes later unless explicitly pulled forward).
- **No automatic inventory deduction** (consume events come later, when recipe→ingredient mapping is trustworthy).
- **No budget constraints** (none exist in prefs schema today).
- **Minimal-diff bias**: extend existing services instead of introducing new architecture.

### Phase 10 deliverables

#### 10.1 Recipe corpus integration (installed packs first, built-ins as fallback)
**Outcome:** meal planning and decision mode must draw from more than 3 static recipes.

Requirements:
- ChefAgent must be able to source recipes from:
  - installed pack recipe books in `recipe_books` (source=`built_in_pack`, pack_id set)
  - built-in recipes as fallback
- Recipe selection must not be locked to round-robin ordering.

Acceptance criteria:
- When at least one pack is installed, meal plan selection can include pack recipes.
- When no packs are installed, the existing built-in fallback remains functional.

Notes:
- In Phase 10, prioritize the pack corpus because it is structurally consistent and parseable.
- User-uploaded recipes may remain in the library but are not guaranteed to be usable for planning in Phase 10.

#### 10.2 Instructions / step-by-step display (pack-backed)
**Outcome:** every planned meal should have usable instructions.

Requirements:
- Planned meals must include non-empty instructions.
- For pack recipes:
  - it is acceptable to include the entire markdown `text_content` as a single instruction block, OR
  - extract "Procedure/Steps" sections if present (best-effort).
- For built-ins:
  - provide short instructions (even minimal) so instructions are not always empty.

Acceptance criteria:
- At least pack-backed planned meals render non-empty instructions in API response.

#### 10.3 Ingredient extraction for pack recipes (MVP parser)
**Outcome:** enable inventory matching and missing ingredients using real recipes.

Requirements:
- For built-in pack recipes:
  - parse ingredients from the `## Ingredients` section (line-based)
  - store as structured ingredient lines where possible
- For user uploads:
  - do not promise ingredient extraction; treat them as "display/search only" in Phase 10.

Acceptance criteria:
- For pack recipes with `## Ingredients`, ChefAgent can produce a structured ingredient list sufficient for:
  - completion scoring
  - missing items list
  - shopping diff integration

Notes:
- Parsing can be "best effort" (e.g., quantity/unit parsing may be partial at first), but names must be extracted consistently.

#### 10.4 Decision mode (MATCH): "What can I make right now?"
**Outcome:** user asks for ideas, gets ranked suggestions.

Requirements:
- Support a decision mode that returns:
  - top meal suggestions
  - completion % (ingredient overlap)
  - missing ingredients per suggestion
  - optional quick "cook time fit" note if weekday/weekend time pref exists
- This output does **not** need propose/confirm (informational — returns an immediate `ChatResponse`).
- MATCH queries are routed through `POST /chat` (ask mode) or `POST /chat/mealplan` (with sub-mode detection added to `ChefAgent`). No new endpoint required.

Acceptance criteria:
- Query like "What can I make?" returns ranked suggestions with completion % and missing items.

#### 10.5 Feasibility check (CHECK): "Can I cook X?"
**Outcome:** user asks about a specific recipe, gets feasibility answer.

Requirements:
- Search the recipe corpus by name (best-effort substring match is acceptable for MVP).
- Respond with:
  - feasible / almost / not feasible
  - missing items list
  - optionally suggest 1–3 alternatives from the corpus
- This is informational — returns an immediate `ChatResponse`, no proposal.
- CHECK queries use the same routing as MATCH (see 10.4).

Acceptance criteria:
- "Can I cook [recipe name]?" responds deterministically using inventory and parsed ingredients.

#### 10.6 Inventory-aware scoring and ranking (name-based in Phase 10)
**Outcome:** suggestions/plans prefer meals that match inventory.

Requirements:
- Implement a simple scoring model:
  - `completion_pct = have_ingredients_count / total_ingredients_count`
  - matching is **name-only** (normalized string match against `InventorySummaryItem.item_name`)
- Use scoring to:
  - rank decision suggestions (MATCH)
  - influence plan selection (PLAN) to avoid static ordering

Acceptance criteria:
- With inventory containing key ingredients for a recipe, that recipe ranks above others.
- Ranking remains deterministic (no random suggestions unless explicitly introduced later).

Notes:
- The existing `_annotate_inventory_notes()` already does name-only set intersection (`{item.item_name.lower()}`). Phase 10 scoring extends this pattern to compute a percentage.
- **Quantity-aware scoring** (checking sufficient quantity per unit) is deferred to Phase 11+. The inventory system supports it (`InventorySummaryItem` has `quantity: float` and `unit: Unit`), but combining it with best-effort ingredient quantity parsing adds complexity that should not gate Phase 10 delivery.

#### 10.7 Wire shopping diff into Chef outputs
**Outcome:** missing items are accurate and reusable.

Requirements:
- Reuse `ShoppingService.diff(user_id, plan)` (`app/services/shopping_service.py`) — this function already takes a `MealPlanResponse` and returns `ShoppingDiffResponse` with quantity-aware missing items. Do not duplicate this logic; call it directly from ChefAgent.
- The existing `_annotate_inventory_notes()` in ChefAgent does name-only "In stock" / "Need to buy" annotations. Replace or augment it with `ShoppingService.diff()` for consistency.
- Output must clearly distinguish:
  - "you have"
  - "you need"

Acceptance criteria:
- Meal plan result includes missing items consistent with `ShoppingService.diff()` output semantics.
- `POST /shopping/diff` and ChefAgent's missing-items output use the same underlying function.

#### 10.8 Time constraints (weekday/weekend) as a soft constraint
**Outcome:** make plans more realistic without adding new prefs fields.

Requirements:
- If `cook_time_weekday_mins` / `cook_time_weekend_mins` is present:
  - use it as a ranking/boost signal
  - optionally filter out obviously long recipes if duration metadata exists; if not, do not fabricate durations
- If no time constraints are set, behavior is unchanged.

Acceptance criteria:
- ChefAgent mentions or reflects time preferences only when present in prefs.

#### 10.9 Maintain propose → confirm → apply semantics for plans
**Outcome:** UX stays consistent.

Requirements:
- Meal plan generation remains proposal-based.
- Confirm remains safe and deterministic:
  - returns plan_id
  - preserves thread isolation
- Plan persistence remains out-of-scope unless explicitly pulled forward.

Acceptance criteria:
- Existing proposal confirm flow continues working.

### Phase 10 "done" definition
Phase 10 is complete when:
- Mealplan flow uses installed pack recipe books when present.
- Pack recipes provide parseable ingredients (from `## Ingredients`) and non-empty instructions.
- Decision mode exists and returns ranked suggestions with completion %, missing items.
- "Can I cook X?" works using the same corpus and ingredient extraction.
- Shopping diff is wired into Chef outputs (missing items are consistent).
- No new test failures are introduced; tests remain deterministic.

---

## Phase 11 — Planning MVP v2 (1–7 day planning + consumption event integration)
### Goal
Evolve Chef into a planning agent:
- plan across multiple days
- produce an aggregated shopping list
- introduce "cooked/consumed" confirmation that can write real consume events (supported by inventory system)

### Deliverables

#### 11.1 Multi-day planning (configurable X days)
Requirements:
- Support 1–7 days in plan generation.
- Respect user prefs:
  - allergies (hard filter)
  - dislikes (hard filter)
  - likes (soft boost)
  - cook time (soft boost)
- Preserve freemium strategy via UI gating if desired.

Acceptance criteria:
- Requesting X days returns X days worth of meals in the plan structure.

#### 11.2 Aggregated shopping list from plan (quantity-aware when possible)
Requirements:
- Compute shopping list across the whole plan.
- Deduct items already in inventory:
  - name-only minimum
  - quantity-aware where ingredient parsing supports it
- Mark items:
  - "already have"
  - "need to buy"
  - "auto-added" (reserved for Phase 12 staples)

Acceptance criteria:
- Shopping list reflects inventory availability and remains explainable.

#### 11.3 "Cooked / Consumed" confirmation → real inventory consume events
Requirements:
- Add a consumption confirmation flow:
  - user confirms a cooked meal (or multiple meals)
  - system writes `consume_cooked` events for mapped ingredients
- Ensure decrement semantics align with existing event-sourced inventory model.

Acceptance criteria:
- Consumption creates deterministic inventory events and changes `/inventory/summary` as expected.

Notes:
- This depends on Phase 10 ingredient extraction being sufficiently structured.

---

## Phase 12 — Restock + staples intelligence
### Goal
Close the loop between cooking and restocking:
- staples
- auto-add items when low/empty
- better shopping list behavior

### Deliverables

#### 12.1 Always-keep-stocked toggle per item
Requirements:
- User can mark an item as a staple.
- When item is low/empty, it can be auto-added to shopping list (marked "auto-added").

Acceptance criteria:
- Staples logic triggers predictably and is visible in shopping list output/UI.

#### 12.2 Low/empty detection improvements (explainable)
Requirements:
- Continue using existing low-stock thresholds, then optionally expand to per-item rules.
- Keep it explainable ("why was this added?").

Acceptance criteria:
- Low-stock signals are consistent and test-covered.

#### 12.3 Shopping list refinement
Requirements:
- Distinguish:
  - needed for plan
  - added as staple
- Support quick confirm/remove toggles (UI-level).

---

## Phase 13 — Voice layer hardening
### Goal
Make voice interaction a first-class interface for the kitchen loop.

### Deliverables

#### 13.1 In-app voice flows stabilized
Requirements:
- Dictation for Chef queries works reliably:
  - MATCH queries
  - CHECK queries
  - PLAN requests
  - "we cooked X" consumption confirmations
- Ensure dictation paths trigger the same UX cues and parsing logic as typing paths.

Acceptance criteria:
- Voice works across primary Chef workflows without missing states.

#### 13.2 Alexa integration (optional but targeted)
Requirements:
- Minimal command set:
  - "What can I make?"
  - "Can I cook X?"
  - "Add X to shopping list"
  - "We cooked X"
- Keep responses concise and reliable.

Acceptance criteria:
- Demo-ready integration for the above commands.

#### 13.3 Household sync concept (optional extension)
Requirements:
- Consumption/shopping events can optionally notify other household members.

---

## Phase 14+ — Recipe ingestion + advanced constraints
### Goal
Unlock user-specific recipe sources and richer optimization without breaking MVP simplicity.

### Deliverables

#### 14.1 Recipe ingestion
- PDF upload ingestion
- Text paste ingestion
- Photo capture ingestion (OCR/parsing)

Acceptance criteria:
- User can add recipes and Chef can plan from them.

#### 14.2 Serving scaling + ingredient math
Requirements:
- Scale recipe quantities based on servings.
- Handle units best-effort (start simple, expand later).

Acceptance criteria:
- Scaling produces sensible quantities and is test-covered.

#### 14.3 Utensil-aware and constraint-aware suggestions
Requirements:
- Filter/boost recipes based on available utensils (air fryer, slow cooker, etc.)
- Incorporate time constraints more strongly (already present in prefs).
- Budget constraints remain out-of-scope until prefs schema adds them.

Acceptance criteria:
- Constraints visibly affect ranking and remain explainable.

---

## Open questions to verify before implementing certain sub-features
These are not blockers for the Phase 10+ plan, but must be verified before implementation where relevant:
1) Whether pack recipes include consistent "Procedure/Steps" sections across most categories (beyond `## Ingredients`).
2) Whether quantity/unit extraction from ingredient lines should be strict or best-effort in Phase 10.
3) Whether any existing UI expects plan persistence semantics (since confirm currently writes nothing).

--- EOF ---
