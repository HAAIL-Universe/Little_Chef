# LittleChef — Chef Agent MVP: 1-Day Meal Plan + General Chat Nudge

> **Status:** READY TO IMPLEMENT
> **Session Date:** 2026-02-10
> **Source:** Full codebase audit of chef_agent, mealplan_service, chat routing, prefs, inventory, recipe sources

---

## Repo Findings

### Chat Endpoints & Routing

| Endpoint | File | Handler | Notes |
|----------|------|---------|-------|
| `POST /chat` | `app/api/routers/chat.py:33` | `ChatService.handle_chat()` | General chat; dispatches to ASK or FILL (prefs wizard). No mealplan routing. |
| `POST /chat/inventory` | `app/api/routers/chat.py:48` | `InventoryAgent.handle_fill()` | Dedicated inventory lane. Requires `mode=fill` + `thread_id`. |
| `POST /chat/mealplan` | `app/api/routers/chat.py:66` | `ChefAgent.handle_fill()` | Dedicated mealplan lane. Requires `mode=fill` + `thread_id`. Already wired. |
| `POST /chat/confirm` | `app/api/routers/chat.py:84` | `ChatService.confirm()` | Dispatch chain: ChefAgent → InventoryAgent → prefs fallback. |

### Confirm Dispatch Order (`chat_service.py:289-302`)
1. `chef_agent.handles_proposal()` — checked first
2. `inventory_agent.handles_proposal()` — checked second
3. Prefs fallback via `proposal_store.peek()` — last resort

### Meal Plan Generator
- **File:** `app/services/mealplan_service.py`
- `MealPlanService.generate(request)` — takes `MealPlanGenerateRequest(days, meals_per_day, include_user_library, notes)`
- Iterates `BUILT_IN_RECIPES` round-robin to fill `meals_per_day` slots per day
- Uses `_INGREDIENTS_BY_RECIPE` dict for ingredient lists
- Returns `MealPlanResponse` with `plan_id`, `days[]`, `created_at`, `notes`
- **No prefs filtering exists** — allergies/dislikes are not checked

### ChefAgent (Current State)
- **File:** `app/services/chef_agent.py`
- `handle_fill()` — parses days/meals from message, falls back to user prefs, generates plan, stores proposal
- `confirm()` — pops proposal, returns `plan_id` as applied event
- **Gaps:** No 1-day cap. No prefs filtering. No allergy enforcement. No inventory awareness. No nudge for multi-day.

### Preferences
- **Service:** `app/services/prefs_service.py` — `get_prefs(user_id)` returns `UserPrefs` (or `DEFAULT_PREFS` with `plan_days=7, meals_per_day=3`)
- **Schema:** `app/schemas.py:29` — `UserPrefs` has `allergies[]`, `dislikes[]`, `cuisine_likes[]`, `servings`, `meals_per_day`, `plan_days`

### Inventory
- **Service:** `app/services/inventory_service.py` — `summary(user_id)` returns `InventorySummaryResponse` with items `[(item_name, quantity, unit, location)]`
- No complex expiry/burn-down; just event-sourced add/consume aggregates

### Recipe Sources
- **Built-ins:** `app/services/recipe_service.py:14` — `BUILT_IN_RECIPES = [{"id": "builtin_1", "title": "Simple Tomato Pasta"}, {"id": "builtin_2", "title": "Garlic Butter Chicken"}, {"id": "builtin_3", "title": "Veggie Stir Fry"}]`
- **Ingredient map:** `app/services/mealplan_service.py:18` — `_INGREDIENTS_BY_RECIPE` maps recipe IDs to `IngredientLine[]`
- **User library:** `RecipeService.search()` does text search across built-ins + user-uploaded books (via `recipe_repo.search_text()`)
- No invented recipes — all `PlannedMeal` objects carry `RecipeSource` with `built_in_recipe_id` and `citations[]`

### Proposal Store
- **File:** `app/services/proposal_store.py`
- In-memory, per-user, TTL 900s
- `save(user_id, proposal_id, action)`, `peek(user_id, proposal_id)`, `pop(user_id, proposal_id)`

### General Chat `_handle_ask()` (`chat_service.py:1000-1044`)
- Keyword-match dispatch: "pref" → show prefs, "low on" → low stock, "inventory" → summary
- Falls through to LLM or generic "Try FILL mode" reply
- **No mealplan keyword detection exists** — needs adding

### Existing Tests for ChefAgent (`tests/test_chef_agent.py`)
7 tests exist: auth guard, thread_id guard, fill-mode guard, propose+confirm, propose+decline, defaults, thread isolation. All currently pass multi-day plans — these need updating for 1-day cap.

---

## MVP Behavior Summary

### 1-Day Plan Only
- `ChefAgent.handle_fill()` always generates a **1-day** meal plan regardless of what the user requests.
- If the user message explicitly mentions more than 1 day (e.g. "plan for 5 days"), the agent:
  - Still generates a 1-day plan
  - Includes a note in `reply_text`: *"MVP supports 1-day plans. Here's your plan for today — multi-day planning is coming soon!"*
- `meals_per_day` is still user-controllable (from message or prefs, default 3).

### Prefs-First Enforcement
- Before generating, ChefAgent loads `prefs_service.get_prefs(user_id)`.
- `allergies[]` and `dislikes[]` are extracted.
- Recipes whose title or ingredients match any allergy/dislike keyword are **excluded** from the plan.
- If no recipes remain after filtering, reply with a helpful message instead of an empty plan.
- `meals_per_day` from prefs used as fallback when not specified in message.

### Inventory Awareness (Simple)
- After generating the plan, load `inventory_service.summary(user_id)`.
- For each `PlannedMeal`, mark ingredients that are already in stock (informational only).
- Include a `notes` field on the plan: *"You already have: X, Y. You'll need: A, B."*
- No complex burn-down or reordering.

### General Chat Nudge
- In `ChatService._handle_ask()`, if the message contains mealplan-related keywords (`"meal plan"`, `"plan my meals"`, `"plan for"`, `"what should i eat"`, `"what should i cook"`), return a nudge:
  - *"To generate a meal plan, use the Meal Plan flow (/chat/mealplan with mode=fill)."*
- Also in `_handle_prefs_flow_threaded()` (fill mode on `/chat`), same detection → same nudge.
- No smart routing, no auto-switch, no buttons.

### Confirm-Before-Write
- The existing pattern is already correct: `handle_fill()` → propose → `confirm()` → apply.
- No changes needed to the confirm dispatch chain.

---

## Checklist of Changes

- [ ] **1. ChefAgent: enforce 1-day cap** — `app/services/chef_agent.py`
- [ ] **2. ChefAgent: prefs-first filtering** — `app/services/chef_agent.py` + `app/services/mealplan_service.py`
- [ ] **3. ChefAgent: inventory notes** — `app/services/chef_agent.py`
- [ ] **4. General chat nudge** — `app/services/chat_service.py`
- [ ] **5. Update tests** — `tests/test_chef_agent.py`
- [ ] **6. Verify** — compileall + pytest

---

## Step-by-Step Implementation Plan

### Step 1: Enforce 1-Day Cap in ChefAgent

**File:** `app/services/chef_agent.py` — `handle_fill()` method (lines 39-99)

**Current behavior:** Parses `days` from message, falls back to prefs `plan_days`, final default 3. Passes to `mealplan_service.generate()`.

**Change:**
- After parsing `days` from message, check if `days > 1`.
- Set `requested_multi = (days is not None and days > 1)`.
- Force `days = 1` always.
- `meals_per_day` logic stays the same (parse from message → prefs fallback → default 3).
- If `requested_multi`, prepend to `reply_text`: *"MVP supports 1-day plans. Here's your plan for today — multi-day planning is coming soon!\n\n"*

**Diff size:** ~10 lines changed in `handle_fill()`.

### Step 2: Prefs-First Filtering

**Files:**
- `app/services/chef_agent.py` — add `_filter_recipes_by_prefs()` helper
- `app/services/mealplan_service.py` — add optional `excluded_recipe_ids` param to `generate()`

**Current behavior:** `MealPlanService.generate()` cycles through `BUILT_IN_RECIPES` round-robin with no filtering.

**Change in `mealplan_service.py`:**
- Add `excluded_recipe_ids: list[str] | None = None` parameter to `MealPlanGenerateRequest` (or pass it as a separate arg to `generate()`).
- Preferred approach: Add `excluded_recipe_ids` as an optional keyword arg to `MealPlanService.generate()` to avoid changing the schema (the schema is physics-bound; this is an internal implementation detail).
- Filter `meals_catalog` to exclude any recipe whose `id` is in `excluded_recipe_ids`.
- If filtered catalog is empty, raise or return an empty plan (let ChefAgent handle the UX).

**Change in `chef_agent.py`:**
- In `handle_fill()`, after loading prefs, extract `allergies + dislikes` as lowercase set.
- Import `BUILT_IN_RECIPES` from `recipe_service` and `_INGREDIENTS_BY_RECIPE` from `mealplan_service`.
- Build `excluded_ids`: for each recipe, check if title or any ingredient name contains an allergy/dislike keyword.
- Pass `excluded_recipe_ids=excluded_ids` to `mealplan_service.generate()`.
- If the generated plan has zero meals (all recipes excluded), return a `ChatResponse` with `confirmation_required=False` and a message like *"All available recipes conflict with your allergies/dislikes. Try adjusting your preferences."*

**Diff size:** ~5 lines in `mealplan_service.py`, ~25 lines in `chef_agent.py`.

### Step 3: Inventory Notes (Informational)

**File:** `app/services/chef_agent.py` — `handle_fill()` method

**Change:**
- After generating the plan, call `self._get_inventory_service().summary(user.user_id)` if an inventory service is available.
- ChefAgent doesn't currently hold an `inventory_service`. Add it as an optional `__init__` param (set from `ChatService._get_mealplan_service()` wiring won't work — wire from `ChatService.__init__()` where `inventory_service` is already available).
- Collect all ingredient `item_name` values from the plan.
- Compare against inventory items (case-insensitive).
- Split into `in_stock` and `need_to_buy` lists.
- Set `plan.notes` to: *"In stock: {in_stock}. Need to buy: {need_to_buy}."* (or skip if inventory is empty).

**Wiring change in `chat_service.py:142`:** Pass `inventory_service=inventory_service` when constructing `ChefAgent`.

**Diff size:** ~20 lines in `chef_agent.py`, ~1 line in `chat_service.py`.

### Step 4: General Chat Nudge

**File:** `app/services/chat_service.py` — `_handle_ask()` (line 1000) and `_handle_prefs_flow_threaded()` (line 886)

**Change in `_handle_ask()`:**
- Add a new keyword check before the final `return None`, after the existing inventory check:
```python
_MEALPLAN_NUDGE_RE = re.compile(
    r"\b(?:meal\s*plan|plan\s+(?:my\s+)?meals?|what\s+should\s+i\s+(?:eat|cook|make))\b",
    re.IGNORECASE,
)
```
- If `_MEALPLAN_NUDGE_RE.search(message)`, return a `ChatResponse` with:
  - `reply_text`: *"To generate a meal plan, use the Meal Plan flow (send a message to /chat/mealplan with mode=fill and a thread_id)."*
  - `confirmation_required: False`

**Change in `_handle_prefs_flow_threaded()`:**
- Add the same check at the top (after inventory misroute detection, before wizard logic):
- If message matches `_MEALPLAN_NUDGE_RE`, return the nudge response.

**Diff size:** ~20 lines total (regex + two insertion points).

### Step 5: Update Tests

**File:** `tests/test_chef_agent.py`

**Tests to update:**
| Test | Current | Change |
|------|---------|--------|
| `test_chef_agent_propose_and_confirm` | Requests 5 days, asserts 5 days | Change to assert 1 day (MVP cap). Verify reply mentions "MVP supports 1-day". |
| `test_chef_agent_propose_and_decline` | Requests 2 days, asserts 2 days plan exists | Verify plan has 1 day. |
| `test_chef_agent_defaults_when_no_params` | Asserts 7 days (from prefs default) | Change to assert 1 day. |
| `test_chef_agent_thread_isolation` | Requests 2 and 4 days | Both should produce 1-day plans. |

**New tests to add:**
| Test | Purpose |
|------|---------|
| `test_chef_agent_mvp_one_day_cap` | Explicitly request "5 days", verify 1 day returned + MVP note in reply_text. |
| `test_chef_agent_prefs_allergy_filter` | Set prefs with allergy (e.g. "chicken"), verify no chicken recipes in plan. |
| `test_chef_agent_all_recipes_excluded` | Set prefs that exclude all 3 built-in recipes, verify graceful "no recipes" response. |
| `test_chef_agent_inventory_notes` | Add inventory items, generate plan, verify `notes` mentions in-stock items. |
| `test_general_chat_mealplan_nudge_ask` | Send "make me a meal plan" to `/chat` in ASK mode, verify nudge response. |
| `test_general_chat_mealplan_nudge_fill` | Send "plan my meals" to `/chat` in FILL mode, verify nudge response. |

**Setting prefs in tests:** Use `authed_client.put("/prefs", json={"prefs": {...}})` before the mealplan call.
**Setting inventory in tests:** Use `authed_client.post("/inventory/events", json={...})` before the mealplan call.

**Diff size:** ~80-100 lines of test code changes.

### Step 6: Verify

1. `python -m compileall app` — no syntax errors
2. `python -m pytest tests/ -x -q --tb=short` — all tests pass
3. Manual check: confirm-before-write still holds, no cross-agent confirm bleed

---

## Files Touched (Scoped List)

| File | Action | Reason |
|------|--------|--------|
| `app/services/chef_agent.py` | MODIFY | 1-day cap, prefs filtering, inventory notes |
| `app/services/mealplan_service.py` | MODIFY | Add `excluded_recipe_ids` param to `generate()` |
| `app/services/chat_service.py` | MODIFY | Mealplan nudge in `_handle_ask()` + `_handle_prefs_flow_threaded()`, pass `inventory_service` to ChefAgent |
| `tests/test_chef_agent.py` | MODIFY | Update existing tests for 1-day cap, add new tests |

**Not touched:** `app/schemas.py`, `app/api/routers/chat.py`, `Contracts/physics.yaml`, `web/` — no changes needed.

---

## Acceptance Criteria

1. **1-day cap:** `POST /chat/mealplan` with any `days` value always produces a plan with exactly 1 day.
2. **Multi-day note:** If user requests >1 day, `reply_text` contains "MVP supports 1-day".
3. **Prefs loaded:** Allergies and dislikes filter out recipes; `meals_per_day` from prefs used as fallback.
4. **All-excluded graceful:** If all recipes match allergy/dislike, response says so without crashing.
5. **Inventory notes:** Plan `notes` field mentions in-stock vs need-to-buy (or omitted if no inventory).
6. **General chat nudge:** Sending mealplan-related text to `/chat` (ASK or FILL mode) returns nudge text, not a plan.
7. **Confirm-before-write:** Proposal → confirm → apply pattern still works; no silent writes.
8. **Thread isolation:** ChefAgent proposals are scoped to `(user_id, thread_id)`; cross-thread confirm fails.
9. **All tests pass:** `pytest tests/` green, including updated + new tests.

---

## Verification Plan

### 1. Static Correctness
```powershell
.\.venv\Scripts\python.exe -m compileall app -q
```
Expected: no output (clean).

### 2. Runtime Sanity
```powershell
.\.venv\Scripts\python.exe -c "from app.services.chef_agent import ChefAgent; print('OK')"
.\.venv\Scripts\python.exe -c "from app.services.mealplan_service import MealPlanService; print('OK')"
.\.venv\Scripts\python.exe -c "from app.services.chat_service import ChatService; print('OK')"
```

### 3. Behavioral Tests
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_chef_agent.py -x -q --tb=short
```

### 4. Full Suite
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -x -q --tb=short
```
Expected: all ~183+ tests pass.

### 5. Contract Compliance
- Confirm-before-write: verified by `test_chef_agent_propose_and_confirm`
- No cross-agent bleed: verified by `test_chef_agent_thread_isolation`
- Physics match: `/chat/mealplan` endpoint already in `physics.yaml`; no new endpoints added
- File boundaries: ChefAgent is service-layer only; router is HTTP-only

---

## Environment Notes

- **Windows** — use `.venv\Scripts\python.exe`
- **Python environment:** `.venv` in project root
- **SDK:** `openai==1.86.0` — do NOT downgrade
- **Tests run with in-memory repos** (`DATABASE_URL=""`)
- **`authed_client` test fixture** creates user with `user_id="test-user"`
- **`BUILT_IN_RECIPES`:** 3 recipes — Simple Tomato Pasta, Garlic Butter Chicken, Veggie Stir Fry
