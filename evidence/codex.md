## Current Repo State
- HEAD: f24547ddbe03411bb3e17d3223cb3e85b5048eb5 (main, ahead 10)
- Working tree: staging pending (awaiting AUTHORIZED). Staged files: app/services/thread_messages_repo.py; web/src/main.ts; web/dist/main.js; tests/test_ui_new_thread_button.py; evidence/test_runs.md; evidence/test_runs_latest.md; evidence/updatedifflog.md.
- Untracked/ignored: none of concern (node_modules remains ignored).

## Latest Functional Changes (staged, not committed)
- History panel now has a **New Thread** button: generates a new UUID thread_id, clears local transcript UI, updates thread label/Dev Panel, mode unchanged.
- Frontend still shows history drawer; Dev Panel shows thread + mode.
- Dist rebuilt to include New Thread UI and thread_id payload usage.
- Backend thread message persistence now ensures a 	hreads row exists before inserting into 	hread_messages (ON CONFLICT DO NOTHING; tolerant of DB failure).
- Added deterministic UI test anchors for New Thread button / UUID / transcript clear.

## Previous recent change (already committed)
- Thread-scoped /ask and /fill overrides now control routing; frontend sends current mode instead of hardcoded ask; ChatResponse includes mode.

## Tests / Build
- npm run build: PASS (web)
- ./scripts/run_tests.ps1: PASS (51 passed, 1 warning: python_multipart deprecation)
- Latest run recorded in evidence/test_runs_latest.md.

## Open Items / To-Do when resuming
- Commit staged changes after authorization.
- Verify New Thread UX in browser: open history (clock), click New Thread, confirm thread label updates, transcript cleared, next /chat uses new thread_id.
- Confirm backend thread row insertion behaves in hosted DB (best-effort insert in thread_messages_repo).

## Quick status commands for tomorrow
- git status -sb
- git diff --staged --stat
- cat evidence/updatedifflog.md

## Notes
- Do not touch physics/schemas in this patch; mode fields already aligned earlier.
- Keep node_modules ignored; dist is rebuilt and staged.
