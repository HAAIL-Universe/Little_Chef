# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-09T10:00:00+00:00
- Branch: main

## Cycle Status
- Status: STAGED — awaiting AUTHORIZED

## Summary
- Reconciled partial rename from `duet-flow-status` → unified to `id="duet-flow-chip"` + `class="duet-flow-chip"` across all HTML/TS/CSS/dist files.
- `web/dist/index.html` was missing the `duet-status-row` wrapper and `duet-flow-chip` element (dist HTML diverged from source); now brought in sync.
- `web/dist/style.css` was missing `.duet-status-row` and `.duet-flow-chip` rules; added to match `web/src/style.css`.
- Added `duet-flow-chip` presence check to `tests/test_ui_mount.py`.
- Created Playwright e2e spec `web/e2e/flow-chip.spec.ts` (initial load `[General]`, flow switch to `[Inventory]`, `[Preferences]`).

## Files Changed
- `web/index.html` — id `duet-flow` → `duet-flow-chip`
- `web/src/main.ts:554` — `getElementById("duet-flow")` → `getElementById("duet-flow-chip")`
- `web/src/style.css:777` — class already `.duet-flow-chip` (no change this cycle)
- `web/dist/index.html:37-40` — added `duet-status-row` wrapper + `duet-flow-chip` div
- `web/dist/main.js:509` — `getElementById("duet-flow")` → `getElementById("duet-flow-chip")`
- `web/dist/style.css:760-786` — added `.duet-status-row` and `.duet-flow-chip` rules; `.duet-status` simplified
- `tests/test_ui_mount.py:18` — added `assert "duet-flow-chip" in html`
- `web/e2e/flow-chip.spec.ts` — NEW: 3 Playwright tests for flow chip
- `evidence/test_runs.md` — appended run entry
- `evidence/test_runs_latest.md` — overwritten with current run

## Key Anchors (source-of-truth for flow tag)
- `web/src/main.ts:80-86` — `flowOptions[]` defines `{key, label, placeholder}` for each flow
- `web/src/main.ts:114` — `currentFlowKey` stores active flow key (default `"general"`)
- `web/src/main.ts:553-559` — `updateFlowStatusText()` reads `currentFlowKey`, formats `[Label]`, writes to `#duet-flow-chip`
- `web/src/main.ts:1778-1792` — `selectFlow(key)` updates `currentFlowKey` and calls `updateFlowStatusText()`
- `web/src/main.ts:1356` — History uses same `flow.label` via `[${flowLabel}] ${message}` bracket format
- `web/index.html:37` — DOM element: `<div class="duet-flow-chip" id="duet-flow-chip">[General]</div>`

## Verification
- `python -m pytest --tb=short` → 96 passed, 2 pre-existing failures (encoding, unrelated)
- `node scripts/ui_proposal_renderer_test.mjs` → PASS
- 2 pre-existing failures confirmed on clean tree via `git stash` / run / `git stash pop`
- Playwright e2e spec written but not run (requires live server + browser — manual gate)
