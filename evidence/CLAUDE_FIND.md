# CLAUDE_FIND — Phase 14 Build Commentary

## Phase 13–14 Overview
**Goal:** Voice hardening (13) + Recipe ingestion & advanced constraints (14).

| Slice | Commit | Description | New Tests | Total |
|-------|--------|-------------|-----------|-------|
| 13.1–13.3 | `a21129f` | Voice stabilization + Alexa + Household sync | 61 | 378 |
| 14.1–14.3 | `5f00521` | Recipe ingestion + Serving scaling + Constraints | 26 | 404 |

**Branch:** `claude/romantic-jones`
**Baseline:** Phase 12 @ `08ab376` (317 tests)
**DB changes:** None. All in-memory.

---

## Phase 13 — Voice Layer Hardening

### 13.1 — Voice Flow Stabilization (24 tests)

**stt_normalize.py (new):**
- `normalize_stt(text)`: removes filler words (um/uh/er/like), restores contractions (whats→what's, cant→can't via 20+ entry map), collapses multi-spaces.
- `voice_hint_for(reply_text, max_chars=200)`: extracts first sentence or truncates at word boundary for TTS output.

**schemas.py:**
- Added `voice_input: bool = False` to `ChatRequest` — flags dictation messages
- Added `voice_hint: Optional[str]` to `ChatResponse` — TTS-friendly truncation

**chat_service.py / chef_agent.py:**
- Apply `normalize_stt()` when `voice_input=True` before regex routing
- Attach `voice_hint_for()` to ask-mode and fill-mode responses when voice

### 13.2 — Alexa Integration (18 tests)

**alexa_service.py (new):**
- `AlexaService.handle_request()` routes Alexa intents to ChefAgent/InventoryService
- 4 intents: `WhatCanIMakeIntent` → handle_match, `CanICookIntent` → handle_check, `AddToListIntent` → set_staple, `CookedRecipeIntent` → handle_consume + auto-confirm
- Session types: launch/ended/help/stop/cancel

**api/routers/alexa.py (new):**
- POST `/alexa/webhook` with lazy service init via `_get_alexa_service()`

### 13.3 — Household Sync Concept (19 tests)

**household_service.py (new):**
- In-memory `HouseholdService`: create/join (invite code)/leave/broadcast_event/get_events/get_member_ids
- Keeps last 100 events per household
- Schemas: HouseholdMember, Household, HouseholdEvent, request/response models

**api/routers/household.py (new):**
- 5 endpoints: POST/GET/DELETE `/household`, POST `/household/join`, GET `/household/events`

---

## Phase 14 — Recipe Ingestion + Advanced Constraints

### 14.1 — Recipe Ingestion (8 tests)

**recipe_service.py:**
- `paste_text()`: creates recipe book from raw text, saved as text/markdown
- `_extract_pdf_text()`: 3-strategy PDF extraction (PyMuPDF → pdfminer → binary scan fallback)
- `upload_book()` enhanced: attempts PDF extraction for application/pdf uploads

**api/routers/recipes.py:**
- POST `/recipes/paste`: accepts `RecipePasteRequest{title, text_content}`, returns 201 with `RecipeBook`
- POST `/recipes/photo`: accepts file upload, returns 201 with `RecipePhotoResponse{book_id, status=processing, message}`
- New schemas: `RecipePasteRequest`, `RecipePhotoResponse`

### 14.2 — Serving Scaling (7 tests)

**recipe_service.py:**
- `scale_ingredients(ingredients, original_servings, target_servings)`: proportional scaling with 0.25 minimum floor, preserves optional flags
- Edge cases: zero/negative original, same servings = no-op

**mealplan_service.py:**
- `generate()` now accepts `target_servings` param
- When target differs from recipe default (2), scales all meal ingredients

**chef_agent.py:**
- `handle_fill()` passes `prefs.servings` (or 0 if no prefs) to mealplan generation

### 14.3 — Equipment/Constraint-Aware Suggestions (11 tests)

**schemas.py:**
- Added `equipment: List[str]` to `UserPrefs` (default empty list)

**recipe_service.py:**
- `_EQUIPMENT_KEYWORDS`: 12 equipment types with keyword aliases (air fryer, slow cooker, instant pot, blender, stand mixer, grill, oven, stovetop, microwave, wok, dutch oven, sous vide)
- `detect_equipment(text)`: scans recipe text for equipment mentions

**chef_agent.py:**
- MATCH flow: +10% score boost for recipes matching user equipment, -5% penalty for missing equipment
- CHECK flow: reports which equipment user has vs. may need
- Both flows include `instructions_text` in catalog for equipment detection
- Explainable: 🔧 note appended to MATCH response when equipment prefs set

---

## Files Modified (Phase 13–14)

| File | Change |
|------|--------|
| `app/schemas.py` | voice_input, voice_hint, equipment, RecipePasteRequest, RecipePhotoResponse |
| `app/services/stt_normalize.py` | NEW — STT normalization + TTS hints |
| `app/services/alexa_service.py` | NEW — Alexa intent routing |
| `app/services/household_service.py` | NEW — household CRUD + event broadcasting |
| `app/services/recipe_service.py` | paste_text, _extract_pdf_text, scale_ingredients, detect_equipment |
| `app/services/chat_service.py` | STT normalization + voice_hint injection |
| `app/services/chef_agent.py` | STT in fill, equipment scoring, instructions_text, target_servings |
| `app/services/mealplan_service.py` | target_servings param + scale_ingredients call |
| `app/api/routers/alexa.py` | NEW — POST /alexa/webhook |
| `app/api/routers/household.py` | NEW — 5 household endpoints |
| `app/api/routers/recipes.py` | paste + photo endpoints |
| `app/main.py` | register alexa + household routers |
| `tests/conftest.py` | alexa + household resets |
| `tests/test_voice_flows.py` | NEW — 24 tests |
| `tests/test_alexa_integration.py` | NEW — 18 tests |
| `tests/test_household_sync.py` | NEW — 19 tests |
| `tests/test_phase14.py` | NEW — 26 tests |

---

## Phase 15 Boundary

STOPPED BEFORE PHASE 15. Phases 13.1–13.3 and 14.1–14.3 are complete.

