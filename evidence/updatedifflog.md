# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-06T21:37:03.113723+00:00
- Branch: main
- HEAD: 69d620a757194ed8fbe86c36d7b3fb9047c0f68f
- BASE_HEAD: 0f32a326899fdf20ecbf5ba56faeb5e148577a67
- Diff basis: staged

## Cycle Status
- Status: COMPLETE_AWAITING_AUTHORIZATION

## Summary
- Both overlays keep running inside `pointer-events: none` containers with interactive panels still `pointer-events: auto`; visibility toggles rely on `style.display = visible ? "flex" : "none"`, so the overlays never intercept the user bubble’s long-press while remaining interactive.
- Duet bubbles stay on top via `z-index: 50`, overlays share `z-index: 1`, and the inline position tweak was dropped so the user bubble returns to its original bottom-right corner inside the shell.
- Verification run (2026-02-06T21:37:03Z latest): `python -m compileall app`, `python -c "import app.main; print('import ok')"`, `pwsh -NoProfile -Command "./scripts/run_tests.ps1"` (includes `pytest`, `npm --prefix web run build`, proposal renderer smoke test).

## Files Changed (staged)
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md
- tests/test_onboarding.py
- tests/test_ui_onboarding_copy.py
- web/dist/main.js
- web/index.html
- web/src/main.ts
- web/src/style.css

## git status -sb
```
## main...origin/main [ahead 2]
M  app/api/routers/auth.py
M  app/services/prefs_service.py
MM evidence/test_runs.md
MM evidence/test_runs_latest.md
MM evidence/updatedifflog.md
M  tests/test_onboarding.py
MM tests/test_ui_onboarding_copy.py
MM web/dist/main.js
 M web/index.html
MM web/src/main.ts
MM web/src/style.css
```

## Minimal Diff Hunks
- `web/src/main.ts:679-757` — overlays now set `style.zIndex = "1"`, remain non-intercepting, and wrap interactive content in pointer-events-auto panels; `elevateDuetBubbles()` raises both bubbles to `zIndex: 50` without overriding their absolute positions.
- `web/src/main.ts:854-932` — prefs overlay mirrors the pointer-event/z-index structure, and `elevateDuetBubbles()` ensures bubbles stay above while `style.display` controls visibility.
- `web/src/style.css:484-533` — removed the extra `.duet-shell .duet-bubble.user` offset so the user bubble sits bottom-right again while the base bubble CSS still handles absolute positioning.
- `tests/test_ui_onboarding_copy.py:30-65` — string-anchor test asserts overlays set `zIndex = "1"` and both bubbles set `zIndex = "50"` to lock the stacking order.

## Verification Results
- `python -m compileall app`
- `python -c "import app.main; print('import ok')"`
- `pwsh -NoProfile -Command "./scripts/run_tests.ps1"`
