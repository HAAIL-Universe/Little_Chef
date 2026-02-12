# Phase 10–14 End-to-End Test Blueprint

> **Scope:** Manual / system verification of user-facing flows.
> Not a substitute for the unit suite (404 tests) — this blueprint validates
> observable behavior from a user's perspective against a running server.

## Classification key

| Tag | Meaning |
|-----|---------|
| **(A)** | Runnable locally today (server + curl / browser) |
| **(B)** | Requires external hardware (Alexa Echo device) |
| **(C)** | Requires external service (Alexa Developer Console) |

## Prerequisites (all tests)

| Item | How |
|------|-----|
| Server running | `scripts/run_local.ps1` or `uvicorn app.main:create_app --factory --port 8000` |
| Valid JWT | Obtain from Auth0 (`/auth/me` returns 200). Export as `$TOKEN`. |
| curl alias | `$H = @{ "Authorization" = "Bearer $TOKEN"; "Content-Type" = "application/json" }` |
| Clean state | `DELETE /auth/me` + re-authenticate, or use a fresh test user |

---

## 0. Cross-Phase Happy Path (A)

> A single end-to-end walkthrough covering onboarding through scaled, constraint-aware planning.
> Run this first. Individual phase sections below cover edge cases.

### Steps

| # | Action | Endpoint | Expected | Evidence |
|---|--------|----------|----------|----------|
| 1 | Confirm clean user | `GET /auth/me` | `onboarded: false`, `inventory_onboarded: false` | JSON body |
| 2 | Set prefs | `PUT /prefs` body: `{ "prefs": { "allergies": ["peanuts"], "dislikes": ["liver"], "cuisine_likes": ["italian"], "servings": 4, "meals_per_day": 2, "plan_days": 3, "cook_time_weekday_mins": 30, "equipment": ["oven", "blender"] } }` | 200, returns `UserPrefs` with `equipment: ["oven","blender"]` | Response JSON |
| 3 | Verify onboarded | `GET /auth/me` | `onboarded: true` | `onboarded` field |
| 4 | Browse packs | `GET /recipes/built-in-packs` | ≥ 15 packs listed | Pack IDs |
| 5 | Install a pack | `POST /recipes/built-in-packs/install` body: `{ "pack_id": "pasta" }` | 201, `books_created ≥ 1` | Response JSON |
| 6 | Add inventory | `POST /inventory/events` × 3: tomato (500 g), pasta (1000 g), olive oil (500 ml) | 201 each | Event IDs |
| 7 | Verify onboarded (inv) | `GET /auth/me` | `inventory_onboarded: true` | Field value |
| 8 | MATCH — "What can I make?" | `POST /chat` body: `{ "mode": "ask", "message": "What can I make?" }` | Ranked list with completion %, missing items, time note. Recipes with "peanuts" excluded. `confirmation_required: false` | `reply_text` |
| 9 | CHECK — "Can I cook tomato pasta?" | `POST /chat` body: `{ "mode": "ask", "message": "Can I cook tomato pasta?" }` | Feasibility verdict, missing items, equipment has/needs | `reply_text` |
| 10 | PLAN — 3-day meal plan | `POST /chat/mealplan` body: `{ "mode": "fill", "message": "plan 3 days 2 meals per day", "thread_id": "happy-1" }` | `confirmation_required: true`, `proposal_id` present, plan has 3 days × 2 meals each. Ingredients are 4-serving scaled (not default 2). | Response JSON — check `days` array length and ingredient quantities |
| 11 | Shopping diff | `POST /shopping/diff` with the `mealplan` from step 10 proposal | `missing_items` list, items we added (tomato/pasta/olive oil) NOT in missing list | Response JSON |
| 12 | Confirm plan | `POST /chat/confirm` body: `{ "proposal_id": "<from step 10>", "confirm": true, "thread_id": "happy-1" }` | `applied: true` | Response JSON |
| 13 | Consume — "I cooked tomato pasta" | `POST /chat` body: `{ "mode": "ask", "message": "I cooked tomato pasta" }` | `confirmation_required: true`, proposed actions contain `consume_cooked` events | Proposed actions |
| 14 | Confirm consumption | `POST /chat/confirm` with proposal from step 13 | `applied: true`, `applied_event_ids` non-empty | Response JSON |
| 15 | Verify inventory decremented | `GET /inventory/summary` | Tomato and pasta quantities reduced | Summary quantities |
| 16 | Mark tomato as staple | `POST /inventory/staples` body: `{ "item_name": "tomato", "unit": "g" }` | `is_staple: true` | Response JSON |
| 17 | Low-stock check | `GET /inventory/low-stock` | If tomato is below 100 g threshold: appears with `is_staple: true`, `reason` contains "staple" | Response JSON |
| 18 | Voice MATCH | `POST /chat` body: `{ "mode": "ask", "message": "um like what can I make", "voice_input": true }` | Same quality as step 8, plus `voice_hint` present and ≤ 200 chars | `voice_hint` field |

**Pass criteria:** All 18 steps return expected results with no 4xx/5xx errors.

---

## Phase 10 — Chef Agent MVP v1

### T10.1 Recipe Corpus Integration (A)

**Preconditions:** Fresh user, no packs installed.

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /chat { "mode":"ask", "message":"What can I make?" }` with no packs | Returns suggestions from 3 built-in recipes only (Tomato Pasta, Garlic Butter Chicken, Veggie Stir Fry) |
| 2 | Install `soup` pack | 201 |
| 3 | Repeat MATCH query | Results now include soup-pack recipes alongside built-ins |
| 4 | Uninstall `soup` pack | 200 |
| 5 | Repeat MATCH query | Soup recipes gone, built-ins remain |

**Evidence:** `reply_text` from steps 1, 3, 5 showing recipe source changes.

### T10.2 Instructions Display (A)

**Preconditions:** At least one pack installed.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Generate 1-day plan via `/chat/mealplan` | Each `PlannedMeal` has non-empty `instructions` list |
| 2 | Check a built-in recipe meal in the plan | Has at least minimal instructions (not empty array) |

**Evidence:** JSON showing `instructions` arrays non-empty.

### T10.3 Ingredient Extraction (A)

**Preconditions:** Pack installed (e.g., `pasta`).

| Step | Action | Expected |
|------|--------|----------|
| 1 | Generate plan | Each meal has `ingredients` with structured `IngredientLine` objects (item_name, quantity, unit) |
| 2 | Verify ingredient parsing | `item_name` populated, `quantity > 0`, `unit` is valid enum value |

**Evidence:** One full `ingredients` array from a pack-sourced meal.

### T10.4 MATCH Decision Mode (A)

**Preconditions:** Inventory with tomato, pasta, chicken. Pack installed.

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /chat { "mode":"ask", "message":"What can I make right now?" }` | Top 5 ranked suggestions |
| 2 | Verify ordering | Recipes with more matching ingredients rank higher |
| 3 | Verify fields | Each suggestion shows: recipe name, completion %, missing items |
| 4 | Check `confirmation_required` | Must be `false` (informational) |

**Evidence:** Full `reply_text` with ranking visible.

### T10.5 CHECK Feasibility (A)

**Preconditions:** Inventory with partial ingredients for a known recipe.

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /chat { "mode":"ask", "message":"Can I cook garlic butter chicken?" }` | Feasibility verdict + missing items list + up to 3 alternatives |
| 2 | Add all missing ingredients to inventory | — |
| 3 | Repeat CHECK | "Feasible" (≥100%) |
| 4 | Ask about unknown recipe: "Can I cook unicorn surprise?" | Graceful "not found in your recipe library" response |

**Evidence:** `reply_text` for steps 1, 3, 4.

### T10.6 Inventory-Aware Scoring (A)

**Preconditions:** Inventory with ingredients matching one recipe perfectly.

| Step | Action | Expected |
|------|--------|----------|
| 1 | MATCH query | Recipe with full coverage shows 100% (or near), ranks #1 |
| 2 | Remove one ingredient via `consume_used_separately` event | — |
| 3 | Repeat MATCH | Same recipe now has lower completion %, may change rank |

**Evidence:** Side-by-side `reply_text` showing rank shift.

### T10.7 Shopping Diff Wired (A)

**Preconditions:** Plan confirmed from mealplan flow.

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /shopping/diff` with confirmed plan | `missing_items` contains items not in inventory |
| 2 | Items you DO have | NOT in `missing_items`, or quantity is net delta only |
| 3 | Each `ShoppingListItem` | Has `reason` ("needed for plan"), `citations` with recipe source |

**Evidence:** Full `ShoppingDiffResponse` JSON.

### T10.8 Time Constraints (A)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set prefs with `cook_time_weekday_mins: 15` | 200 |
| 2 | MATCH query | `reply_text` includes cook-time note (e.g., "⏱ weekday limit: 15 min") |
| 3 | Remove cook time prefs (set to `null`) | 200 |
| 4 | MATCH query | No cook-time note in reply |

**Evidence:** `reply_text` with/without time annotation.

### T10.9 Propose → Confirm → Apply Semantics (A)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Generate plan | `confirmation_required: true`, `proposal_id` present |
| 2 | Reject: `POST /chat/confirm { confirm: false }` | `applied: false`, no side effects |
| 3 | Regenerate plan | New `proposal_id` |
| 4 | Confirm | `applied: true`, `plan_id` returned |
| 5 | Confirm same `proposal_id` again | Error or `applied: false` (idempotent rejection) |

**Evidence:** Confirm responses for steps 2, 4, 5.

---

## Phase 11 — Planning MVP v2

### T11.1 Multi-Day Planning (A)

**Preconditions:** Prefs set (plan_days=3, meals_per_day=2). Pack installed.

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /chat/mealplan { "message": "plan 5 days 3 meals per day" }` | Plan with 5 days, 3 meals each = 15 meals total |
| 2 | Check day_index values | 1, 2, 3, 4, 5 |
| 3 | Check meal slots | Reasonable distribution (breakfast/lunch/dinner) |
| 4 | Request 1 day | Plan with 1 day |
| 5 | Request 7 days | Plan with 7 days (max cap) |
| 6 | Request 8+ days | Capped at 7 |

**Evidence:** `days` array from each response, day counts.

### T11.2 Aggregated Shopping List (A)

**Preconditions:** Multi-day plan generated and confirmed.

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /shopping/diff` with the multi-day plan | `missing_items` aggregated across all days (no per-day duplicates) |
| 2 | Quantities | Sum aggregated (e.g., "tomato: 2000g" if used across 4 meals) |
| 3 | Items in inventory | Show reduced delta or absent from `missing_items` |

**Evidence:** `ShoppingDiffResponse` with aggregated quantities.

### T11.3 Cooked/Consumed Confirmation (A)

**Preconditions:** Inventory with tomato (500 g), pasta (1000 g).

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /chat { "message": "I cooked tomato pasta" }` | Proposal with `consume_cooked` events for tomato + pasta |
| 2 | Confirm | `applied: true`, `applied_event_ids` list |
| 3 | `GET /inventory/events?limit=5` | Recent events are `consume_cooked` type |
| 4 | `GET /inventory/summary` | Quantities for tomato/pasta reduced |
| 5 | Reject a consume proposal | `applied: false`, no events created |

**Evidence:** Event IDs, inventory summary before/after.

---

## Phase 12 — Restock + Staples Intelligence

### T12.1 Staple Toggle (A)

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /inventory/staples { "item_name": "milk", "unit": "ml" }` | `is_staple: true` |
| 2 | `GET /inventory/staples` | List includes `milk` |
| 3 | `DELETE /inventory/staples { "item_name": "milk", "unit": "ml" }` | `is_staple: false` |
| 4 | `GET /inventory/staples` | `milk` removed |

**Evidence:** Staple list responses.

### T12.2 Low-Stock Detection with Staples (A)

**Preconditions:** Staple "milk" set, inventory milk = 0 or below threshold.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set milk as staple, ensure milk quantity = 0 | — |
| 2 | `GET /inventory/low-stock` | Milk appears with `is_staple: true`, `reason` contains "staple" |
| 3 | Add milk (2000 ml) to inventory | — |
| 4 | `GET /inventory/low-stock` | Milk no longer in low-stock list |

**Evidence:** Low-stock responses before/after.

### T12.3 Shopping List with Staple Items (A)

**Preconditions:** Staple "eggs" at zero stock. Generate a plan.

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /shopping/diff` with plan | `staple_items` list present |
| 2 | Check eggs entry | In `staple_items` (not `missing_items`), reason mentions "staple" |
| 3 | Items in `missing_items` | Have `reason: "needed for plan"` |

**Evidence:** Both `missing_items` and `staple_items` arrays.

---

## Phase 13 — Voice Layer Hardening

### T13.1 In-App Voice Flows (A)

> All tests use `"voice_input": true` in ChatRequest.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Voice MATCH: `"um like what can I make"` | STT normalization removes fillers, returns ranked suggestions, `voice_hint` present and ≤ 200 chars |
| 2 | Voice CHECK: `"uh can I cook tomato pasta"` | Feasibility reply, `voice_hint` present |
| 3 | Voice PLAN: `"plan uh 2 days"` → `/chat/mealplan` with `voice_input: true` | Plan proposal generated, `voice_hint` present |
| 4 | Voice CONSUME: `"we um cooked garlic butter chicken"` | Consume proposal, `voice_hint` present |
| 5 | Non-voice same query | Same quality reply, `voice_hint` is `null` |

**Evidence:** `voice_hint` field in each response, comparison with non-voice.

### T13.1b Browser Mic Test (A — requires microphone)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open `http://localhost:8000` in browser | UI loads |
| 2 | Click 🎤 mic button | Browser requests mic permission |
| 3 | Speak "What can I make?" | Transcript appears in input, sends with `voice_input: true` |
| 4 | Reply appears | Has visible reply text |

**Evidence:** Screenshot of chat with voice-triggered reply.

### T13.2 Alexa Integration — No-Device Path (A)

> Direct HTTP simulation against `POST /alexa/webhook` with crafted Alexa-format JSON.

**Preconditions:** Inventory populated, pack installed, valid JWT.

```
Alexa request template:
{
  "request": {
    "type": "IntentRequest",
    "intent": {
      "name": "<INTENT>",
      "slots": { "<SLOT>": { "value": "<VALUE>" } }
    }
  },
  "session": { "sessionId": "test-session-1" }
}
```

| Step | Intent | Slots | Expected |
|------|--------|-------|----------|
| 1 | `LaunchRequest` (type override: `"type":"LaunchRequest"`, no intent key) | — | Welcome text in `response.outputSpeech.text` |
| 2 | `WhatCanIMakeIntent` | — | Top suggestions in speech text, `shouldEndSession: false` |
| 3 | `CanICookIntent` | `RecipeName: "tomato pasta"` | Feasibility in speech text |
| 4 | `AddToListIntent` | `ItemName: "butter"` | Confirms added as staple |
| 5 | `WeCookedIntent` | `RecipeName: "tomato pasta"` | Confirms consumption, auto-applies (no second confirm needed) |
| 6 | `AMAZON.HelpIntent` | — | Help text |
| 7 | `AMAZON.StopIntent` | — | Goodbye, `shouldEndSession: true` |

**Evidence:** Full JSON response for each step.

### T13.2b Alexa via Developer Console (C)

**Preconditions:** Skill deployed to Alexa Developer Console, endpoint pointed at tunnel/public URL.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open Alexa Developer Console → Test tab | Simulator loads |
| 2 | Type: "open little chef" | Launch response |
| 3 | Type: "what can I make" | Suggestions returned |
| 4 | Type: "can I cook tomato pasta" | Feasibility response |

**Evidence:** Console simulator screenshots.

### T13.2c Alexa on Device (B)

| Step | Action | Expected |
|------|--------|----------|
| 1 | "Alexa, open Little Chef" | Welcome prompt |
| 2 | "What can I make?" | Speaks top suggestions |
| 3 | "Can I cook tomato pasta?" | Speaks feasibility |
| 4 | "We cooked tomato pasta" | Confirms consumption |

**Evidence:** Audio recording or log of skill invocations.

### T13.3 Household Sync (A)

**Preconditions:** Two valid JWTs (User A and User B). Export as `$TOKEN_A`, `$TOKEN_B`.

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | A | `POST /household { "name": "Test Kitchen" }` | 201, `invite_code` returned |
| 2 | A | `GET /household` | Shows household with 1 member |
| 3 | B | `POST /household/join { "invite_code": "<from step 1>" }` | 200, household now has 2 members |
| 4 | B | `GET /household` | Same household, 2 members listed |
| 5 | A | Trigger a consume event (cook tomato pasta + confirm) | Event written |
| 6 | B | `GET /household/events` | Shows `consume_cooked` event from User A |
| 7 | A | `POST /inventory/staples { "item_name":"salt" }` | Staple added |
| 8 | B | `GET /household/events` | Shows `staple_added` event from User A |
| 9 | B | `DELETE /household` | User B leaves |
| 10 | A | `GET /household` | 1 member (A only) |
| 11 | A | `DELETE /household` | Last member → household deleted |
| 12 | A | `GET /household` | 404 |

**Evidence:** Household responses and event list at steps 6, 8.

---

## Phase 14 — Recipe Ingestion + Advanced Constraints

### T14.1a Text Paste Ingestion (A)

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /recipes/paste { "title":"Grandma's Soup", "text_content":"## Ingredients\n- 2 count carrot\n- 500 g potato\n\n## Procedure\nBoil everything." }` | 201, returns `RecipeBook` with `book_id` |
| 2 | `GET /recipes/books/<book_id>` | Book content matches pasted text |
| 3 | `POST /recipes/search { "query":"grandma soup" }` | Finds the pasted recipe |
| 4 | MATCH query | Pasted recipe appears in suggestions (if ingredients match inventory) |

**Evidence:** Book response from step 2, MATCH reply showing user recipe.

### T14.1b Photo Upload (A)

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /recipes/photo` with any JPEG file (multipart) | 201, `RecipePhotoResponse` with `status: "processing"`, `book_id` |
| 2 | `GET /recipes/books/<book_id>` | Book exists (content may be minimal — OCR not fully implemented) |

**Evidence:** Photo response JSON.

### T14.1c PDF Upload (A)

**Preconditions:** A simple PDF file with recipe text.

| Step | Action | Expected |
|------|--------|----------|
| 1 | `POST /recipes/books` with PDF file (multipart, `title: "PDF Recipe"`) | 201, `RecipeBook` |
| 2 | `GET /recipes/books/<book_id>` | `text_content` populated from PDF extraction |

**Evidence:** Book response showing extracted text.

### T14.2 Serving Scaling (A)

**Preconditions:** Prefs set with `servings: 4`. Pack installed.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Generate 1-day plan via `/chat/mealplan` | Plan returned |
| 2 | Check ingredient quantities | Quantities doubled vs default (base is 2 servings) |
| 3 | Update prefs to `servings: 1` | 200 |
| 4 | Generate another plan | Quantities halved vs step 2 |
| 5 | Check floor | No ingredient quantity below 0.25 |

**Evidence:** Ingredient quantities from steps 2 and 4 side-by-side.

### T14.3 Constraint-Aware Suggestions (A)

**Preconditions:** Prefs with `equipment: ["oven", "slow cooker"]`. Pack with oven-requiring recipes installed.

| Step | Action | Expected |
|------|--------|----------|
| 1 | MATCH query | Recipes requiring "oven" get +10% boost (rank higher). Recipes needing equipment user lacks get −5%. `reply_text` contains 🔧 equipment note |
| 2 | CHECK a recipe needing oven | "You have: oven" in reply |
| 3 | CHECK a recipe needing "wok" | "May need: wok" in reply |
| 4 | Set `equipment: []` (empty) | 200 |
| 5 | Repeat MATCH | No equipment boost/penalty (baseline scoring only), no 🔧 note |

**Evidence:** `reply_text` from steps 1–3 and 5, showing equipment annotations.

### T14.3b Equipment in Prefs Roundtrip (A)

| Step | Action | Expected |
|------|--------|----------|
| 1 | `PUT /prefs` with `equipment: ["air fryer", "blender", "grill"]` | 200, returns prefs with same equipment list |
| 2 | `GET /prefs` | `equipment` matches what was set |
| 3 | `PUT /prefs` with `equipment: []` | 200, equipment now empty |

**Evidence:** GET response showing equipment persistence.

---

## Phase Seal Checklist

> Confirm no drift exists between contract expectations and deployed behavior.

### Endpoints (verify all respond 200/201 or correct error)

| Endpoint | Method | Phase | Status |
|----------|--------|-------|--------|
| `/health` | GET | — | ☐ |
| `/auth/me` | GET | — | ☐ |
| `/prefs` | GET, PUT | 10 | ☐ |
| `/chat` | POST | 10 | ☐ |
| `/chat/mealplan` | POST | 10 | ☐ |
| `/chat/confirm` | POST | 10 | ☐ |
| `/chat/inventory` | POST | — | ☐ |
| `/inventory/events` | GET, POST | 10 | ☐ |
| `/inventory/summary` | GET | 10 | ☐ |
| `/inventory/low-stock` | GET | 12 | ☐ |
| `/inventory/staples` | GET, POST, DELETE | 12 | ☐ |
| `/recipes/books` | GET, POST | 10 | ☐ |
| `/recipes/books/{id}` | GET, DELETE | 10 | ☐ |
| `/recipes/paste` | POST | 14 | ☐ |
| `/recipes/photo` | POST | 14 | ☐ |
| `/recipes/search` | POST | 10 | ☐ |
| `/recipes/built-in-packs` | GET | 10 | ☐ |
| `/recipes/built-in-packs/{id}/preview` | GET | 10 | ☐ |
| `/recipes/built-in-packs/install` | POST | 10 | ☐ |
| `/recipes/built-in-packs/uninstall` | POST | 10 | ☐ |
| `/mealplan/generate` | POST | 11 | ☐ |
| `/shopping/diff` | POST | 11 | ☐ |
| `/alexa/webhook` | POST | 13 | ☐ |
| `/household` | GET, POST, DELETE | 13 | ☐ |
| `/household/join` | POST | 13 | ☐ |
| `/household/events` | GET | 13 | ☐ |

### Schema Stability

| Check | Expected | Status |
|-------|----------|--------|
| `ChatRequest` fields | mode, message, include_user_library, location, thread_id, voice_input | ☐ |
| `ChatResponse` fields | reply_text, confirmation_required, proposal_id, proposed_actions, suggested_next_questions, mode, voice_hint | ☐ |
| `UserPrefs` has `equipment: List[str]` | Present, defaults to `[]` | ☐ |
| `InventoryEventType` enum | add, consume_cooked, consume_used_separately, consume_thrown_away, adjust | ☐ |
| `ShoppingDiffResponse` has `staple_items` | Present, defaults to `[]` | ☐ |
| `RecipePasteRequest` exists | title + text_content fields | ☐ |
| `RecipePhotoResponse` exists | book_id + status + message fields | ☐ |

### Feature Discoverability (UI)

| Feature | Where to find | Status |
|---------|---------------|--------|
| Voice input | 🎤 mic button in composer bar | ☐ |
| Chat (ask/fill) | Text input + send button | ☐ |
| Plan generation | `/chat/mealplan` via fill mode or UI plan button | ☐ |
| Proposal confirm/cancel | `btn-confirm` / `btn-cancel` in proposal area | ☐ |
| Prefs management | Prefs section with servings/meals inputs | ☐ |
| Inventory events | Via chat inventory flow | ☐ |
| Shopping list | Shopping diff button (`btn-shopping`) | ☐ |
| Recipe search | Via chat ask mode | ☐ |

### OpenAPI Contract

| Check | How | Status |
|-------|-----|--------|
| OpenAPI doc accessible | `GET /openapi.json` returns valid JSON | ☐ |
| All Phase 10–14 endpoints present | Search for `/recipes/paste`, `/alexa/webhook`, `/household`, `/inventory/staples` in schema | ☐ |
| No undocumented breaking changes | Diff `/openapi.json` against last known-good snapshot | ☐ |

### Pre-Existing Known Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| `test_auth_schema_missing` flake | Low | Order-dependent, passes in isolation. Not a regression. |
| Photo OCR not implemented | Expected | `POST /recipes/photo` returns `status: "processing"` — OCR deferred to future phase. |

---

## Execution Notes

- **Run order matters:** Start from Cross-Phase Happy Path (§0), then run individual phase sections only for edge-case coverage.
- **Two-user tests:** Household sync (T13.3) requires two JWTs. In local dev, use the debug auth override or two Auth0 test accounts.
- **Alexa no-device path (T13.2):** Fully runnable locally via curl against `/alexa/webhook` — no Alexa hardware or console needed.
- **Evidence capture:** Save curl responses to files: `curl ... | jq . > evidence/e2e_T10.4.json`.
- **Reset between runs:** `DELETE /auth/me` clears all user data. Re-authenticate for a clean slate.
