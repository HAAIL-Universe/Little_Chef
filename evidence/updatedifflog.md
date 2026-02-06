# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-06T21:46:10.666893+00:00
- Branch: main
- HEAD: 0324018e1f1f3cb405eddd45d7c3e2a1a6eb2dde
- BASE_HEAD: 0f32a326899fdf20ecbf5ba56faeb5e148577a67
- Diff basis: staged

## Cycle Status
- Status: COMPLETE_AWAITING_AUTHORIZATION

## Summary
- Inventory overlay visibility now depends on `state.inventoryOnboarded` so the overlay stays hidden until inventory data exists; the UI calls `refreshInventoryOverlay(true)` when the inventory flow is selected to detect when data arrives, and `markInventoryOnboarded()` flips the flag once summary/low-stock payloads include items. citeweb/src/main.ts:641-705
- Backend `/auth/me` now reports `inventory_onboarded` (derived from `InventoryService.has_events`) so the UI seeds the flag on sign-in, matching how prefs onboarding is exposed. citeapp/api/routers/auth.py citeapp/schemas.py
- Duet bubbles remain elevated (`zIndex: 50`) while overlays stay at `zIndex: 1`, keeping the long-press target on top even when the prefs panel stretches. citeweb/src/main.ts:611-705 citeweb/src/style.css:484-533
- Tests: `python -m compileall app`; `python -c "import app.main; print('import ok')"`; `pwsh -NoProfile -Command "./scripts/run_tests.ps1"`. citeevidence/test_runs_latest.md

## Files Changed (staged)
- app/api/routers/auth.py
- app/schemas.py
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md
- tests/test_ui_onboarding_copy.py
- web/dist/main.js
- web/index.html
- web/src/main.ts
- web/src/style.css

## git status -sb
```
## main...origin/main [ahead 3]
 M app/api/routers/auth.py
 M app/services/prefs_service.py
 M app/schemas.py
 M evidence/test_runs.md
 M evidence/test_runs_latest.md
 M evidence/updatedifflog.md
 M tests/test_onboarding.py
 M tests/test_ui_onboarding_copy.py
 M web/dist/main.js
 M web/index.html
 M web/src/main.ts
 M web/src/style.css
```

## Minimal Diff Hunks
- `web/src/main.ts:641-705` — overlay visibility now gates on `state.inventoryOnboarded`, triggers `refreshInventoryOverlay(true)` when the inventory flow is selected while unmarked, and calls `markInventoryOnboarded()` after fetches return data.  
- `web/src/main.ts:100-111` & `1074-1094` — state now tracks `inventoryOnboarded` and seeding occurs when `/auth/me` replies (alongside the `inventory_onboarded` flag).  
- `app/api/routers/auth.py` & `app/schemas.py` — `/auth/me` now reports the new `inventory_onboarded` field using `InventoryService.has_events`; the Pydantic schema exposes the field.  
- `tests/test_ui_onboarding_copy.py:30-65` — string-anchor test asserts overlay pointer-events, z-index, and inventory gating statements.

## Verification Results
- `python -m compileall app`
- `python -c "import app.main; print('import ok')"`
- `pwsh -NoProfile -Command "./scripts/run_tests.ps1"`
