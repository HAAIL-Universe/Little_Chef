# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-05T17:40:35+00:00
- Branch: main
- BASE_HEAD: be361aa0b60a27f37a283a038d211377e93ef845
- Diff basis: staged

## Cycle Status
- Status: COMPLETE_AWAITING_AUTHORIZATION

## Summary
- Addressed runtime mismatch by locking viewport via inline styles and hiding dropdown overlay even when old CSS is served; prevents page drag and unintended visible menu items.
- Flow menu creation now sets dropdown display toggles and absolute positioning directly in JS to ensure single Options button + hidden overlay regardless of stale CSS.
- Rebuilt served asset `web/dist/main.js` via `npm --prefix web run build` to include the JS fixes.
- Reran full verification suite; contracts untouched.

## Files Changed (staged)
- evidence/updatedifflog.md
- evidence/test_runs.md
- evidence/test_runs_latest.md
- web/dist/main.js
- web/src/main.ts

## git status -sb
    ## main...origin/main [ahead 1]
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
    M  web/dist/main.js
    M  web/src/main.ts
    ?? evidence/orchestration_system_snapshot.md
    ?? web/node_modules/

## Minimal Diff Hunks
- web/src/main.ts: dropdown now uses inline display toggling/absolute positioning; added viewport lock helper to force 100dvh + overflow hidden and invoked during wire() init.
- web/dist/main.js: regenerated via `npm --prefix web run build` to include the above JS changes.
- evidence/test_runs*.md: appended latest PASS run from scripts/run_tests.ps1.

## Verification
- python -m compileall app → PASS.
- python -c "import app.main; print('import ok')" → import ok.
- pwsh -NoProfile -Command "./scripts/run_tests.ps1" → PASS (compileall/import/pytest all ok).
- Contract check: Contracts/physics.yaml unchanged.

## Notes (optional)
- Static serving remains from web/dist; inline JS now guards against stale dist/style.css. Untracked left untouched: evidence/orchestration_system_snapshot.md, web/node_modules/.

## Next Steps
- Await AUTHORIZED to push; if desired, refresh dist/style.css in a later cycle to align with src/style.css (not required for current fix).

