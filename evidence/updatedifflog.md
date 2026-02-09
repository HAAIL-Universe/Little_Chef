# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-08T23:47:24+00:00
- Branch: main

## Cycle Status
- Status: COMPLETE

## Summary
- Appended the traffic-light stack into `.duet-stage` so it now shares the same chassis column as the history clock and settings cog, with `#proposal-actions` using `position: absolute` plus `top: 50%`/`transform: translateY(-50%)` so it stays centered vertically inside the stage.
- The history toggle and flow-menu button now share a `right: 16px` column (matching `#proposal-actions`), and `ensureProposalActions()` re-parents the stack into `.duet-stage` whenever the stage exists.
- `#duet-status` now contains `.status-text` + `.status-tag`, and `setDuetStatus()`/`updateDuetStatusTag()` keep the replying message and `[Flow]` tag in sync with the current flow so the user always sees the active namespace on the right side.

## Files Changed
- web/index.html
- web/src/main.ts
- web/src/style.css
- web/dist/main.js
- web/dist/style.css
- Note: existing Playwright coverage still applies; this cycle was focused on layout/DOM polish.

## Key Anchors
- `web/index.html:32-38` – `#duet-status` now contains `.status-text` and `.status-tag` spans for the message + flow tag.
- `web/src/main.ts:520-590` – `setDuetStatus()` updates the new spans and calls `updateDuetStatusTag()`; `updateDuetStatusTag()` reads `currentFlowKey` and `selectFlow()` re-invokes it whenever the flow changes.
- `web/src/main.ts:400-432` – `ensureProposalActions()` re-parents the traffic-light stack into `.duet-stage`.
- `web/src/style.css:450-520` / `web/dist/style.css:450-520` – `.duet-status` became flex, `.status-tag` styled as a pill, `#proposal-actions` uses absolute centering, and history/settings offsets now match `right: 16px`.

## Verification
- `cd web && npm run build`
- Playwright suite still covered by the prior 23:20 `npm run test:e2e` run documented in `evidence/test_runs.md`.

## Notes
- No global glass/green theme tokens were changed; the new layout stays within the existing palette.
