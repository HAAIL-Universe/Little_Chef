# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-08T22:55:00+00:00
- Branch: main

## Cycle Status
- Status: COMPLETE

## Summary
- Relaxed the traffic-light visibility trigger so that any `confirmation_required: true` response keeps the stack visible even if `state.proposalId` was already tracked or the UI rehydrated mid-flow. The stack still uses the right-hand glass chrome and the Deny handler now suppresses the stack deterministically via `proposalDismissedIds`.
- Added `lastResponseRequiresConfirmation` to match the latest server reply (`sendAsk` now updates it) and ensured `clearProposal`/Deny reset it so the stack hides once the proposal is dismissed or confirmed.
- Playwright still covers Confirm/Edit/Deny behavior (`proposal-actions.spec.ts`); rerunning `npm run test:e2e` after the trigger change proves the stack appears whenever we simulate `confirmation_required` and Confirm sends the `confirm` payload.

## Files Changed
- web/src/main.ts
- web/src/style.css
- web/dist/main.js
- web/dist/style.css
- evidence/test_runs.md
- evidence/test_runs_latest.md

## Key Anchors
- `web/src/main.ts:104-150` – `lastResponseRequiresConfirmation` tracks whether the last backend reply requested verification, giving the stack a reliable trigger even after navigation or redraws.
- `web/src/main.ts:338-406` – `renderProposal()`/`clearProposal()` now call `updateProposalActionsVisibility()` and `shouldShowProposalActions()` checks `lastResponseRequiresConfirmation`, so confirmation responses show the stack regardless of prior dismissals.
- `web/src/main.ts:1230-1290` – `sendAsk()` now flips `lastResponseRequiresConfirmation` based on `json.confirmation_required`, plus Deny clears it without backend traffic.
- Playwright spec `web/e2e/proposal-actions.spec.ts` keeps asserting the stack appears on confirmed proposals and that Confirm sends `confirm` to `/chat/confirm`.

## Verification
- `cd web && npm run build`
- `cd web && npm run test:e2e`
- See `evidence/test_runs.md` and `evidence/test_runs_latest.md` for the 2026-02-08T22:54:37Z Playwright run after the trigger change.

## Notes
- No global glass/green theme tokens were touched; the new stack still relies on `.icon-btn` and scoped `#proposal-actions` overrides.
