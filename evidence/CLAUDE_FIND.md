# CLAUDE_FIND — Phase 12 Build Commentary

## Phase 12 Overview
**Goal:** Close the cooking-to-restocking loop with staples intelligence.

| Slice | Commit | Description | New Tests | Total |
|-------|--------|-------------|-----------|-------|
| 12.1–12.3 | `a3d9ff1` | Staple toggle + explainable low-stock + shopping refinement | 16 | 317 |

**Branch:** `claude/romantic-jones`
**Baseline:** Phase 11.3 @ `cb0c5fd` (301 tests)
**DB changes:** None. In-memory staples storage.
**New endpoints:** GET/POST/DELETE `/inventory/staples`

**Branch:** `claude/romantic-jones`
**Baseline:** Phase 10.9 @ `57f8ee5` (275 tests)
**DB changes:** None. No new migrations.
**New endpoints:** None. All changes use existing routing.

---

## 12.1 — Always-Keep-Stocked Toggle

### What changed

**inventory_service.py:**
- Added `_staples: Dict[str, Set[Tuple[str, str]]]` keyed by user_id → set of (normalized_name, unit).
- Added `set_staple()`, `remove_staple()`, `list_staples()`, `is_staple()` methods.

**schemas.py:**
- Added `StapleItem(item_name, unit)`, `StapleToggleRequest`, `StapleToggleResponse`, `StaplesListResponse`.

**inventory.py router:**
- Added 3 endpoints: GET/POST/DELETE `/inventory/staples`.

### Design decisions

1. **In-memory storage:** Consistent with existing architecture (ProposalStore, PrefsService, RecipeBookService all use in-memory dicts). No DB table needed for MVP.

2. **Normalized key:** Staples are stored as `(name.strip().lower(), unit)` tuples — same normalization as inventory summary. This ensures "Milk" and "milk" are treated as the same staple.

3. **DELETE with JSON body:** FastAPI supports DELETE with request body. TestClient needs `client.request("DELETE", url, json=...)` since `.delete()` doesn't accept `json=` keyword.

### Tests (7 tests)
- Empty initial list, set+list, remove, idempotent set, auth required, multiple items

---

## 12.2 — Explainable Low-Stock Detection

### What changed

**inventory_service.py — low_stock() rewrite:**
- Uses `summary_keys` set to track ALL items in summary (not just low ones).
- For each low item: reason = "staple: low/out of stock" if staple, else "below threshold".
- Added is_staple flag to LowStockItem responses.
- After processing summary, iterates user staples to add zero-inventory staples that were never added to inventory.

### Design decisions

1. **summary_keys vs seen_keys:** Original bug used a `seen_keys` set that only tracked items below threshold. A fully-stocked staple like "Milk at 500ml" wouldn't be in `seen_keys`, so it would fall through to the "never added" branch and appear as "staple: out of stock." Fixed by tracking all summary items in `summary_keys`.

2. **Explainable by default:** Every LowStockItem now has a non-empty `reason` string. The contract says "keep it explainable" — this satisfies it at the API level.

### Tests (5 tests)
- Below threshold → "below threshold" reason
- Staple below threshold → "staple: low/out of stock"
- Never-added staple → "staple: out of stock"
- Fully stocked staple → excluded from list
- All items have non-empty reasons

---

## 12.3 — Shopping List Refinement

### What changed

**schemas.py:**
- Added `staple_items: List[ShoppingListItem]` to ShoppingDiffResponse.
- Changed ShoppingListItem.reason default: "missing for meal plan" → "needed for plan".

**shopping_service.py:**
- Added `_staple_shortfall()` method: checks staples against inventory/thresholds, returns items with reason "auto-added: staple low/out of stock".
- `diff()` returns both `missing_items` (plan-based) and `staple_items` (restock-based).
- Staples already in plan's `required` dict are skipped to prevent duplication.

### Design decisions

1. **Two lists, not one:** The contract says "distinguish needed for plan vs added as staple." Separate `missing_items` and `staple_items` fields make this unambiguous at the API level. UI can render them differently.

2. **Deduplication:** If "Tomato" is both a staple and a plan ingredient, it appears ONLY in `missing_items` with reason "needed for plan." This avoids double-counting.

3. **Reason string change:** "missing for meal plan" → "needed for plan" — shorter, clearer. Existing tests only checked `assert item["reason"]` (truthy), not exact strings, so this was safe.

4. **Restock quantity:** `max(threshold - have, 1)` — suggests restocking to threshold level, minimum 1 unit.

### Tests (4 tests)
- Plan items get "needed for plan" reason
- Staple items appear in separate list with "auto-added" reason
- No duplication between plan and staple lists
- Fully stocked staples excluded, multiple staples work

---

## Files Modified (Phase 12 total)

| File | Change |
|------|--------|
| app/schemas.py | ✏️ StapleItem, StapleToggle*, StaplesListResponse, is_staple, staple_items, reason text |
| app/services/inventory_service.py | ✏️ _staples dict, set/remove/list/is_staple, low_stock() rewrite |
| app/api/routers/inventory.py | ✏️ 3 staple endpoints |
| app/services/shopping_service.py | ✏️ _staple_shortfall(), reason text, staple_items in diff() |
| tests/test_staples_restock.py | ✨ new (16 tests) |

**Legend:** ✨ = new file, ✏️ = modified

---

## What Phase 13 would need (not implemented)

Per the contract, Phase 13 covers "Voice layer hardening":
- 13.1 In-app voice flows stabilized (dictation for MATCH/CHECK/PLAN/consume)
- 13.2 Alexa integration (optional)
- 13.3 Household sync concept (optional)

None of this was started. STOPPED BEFORE PHASE 13.
