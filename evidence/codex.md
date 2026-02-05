## Current Repo State
- HEAD: dbe811effe5156408d2a0e2e173ad44cef15b518
- Branch: main (clean tracked); unstaged untracked: evidence/orchestration_system_snapshot.md, web/node_modules/

## Phase Progress
- 7.1: closed (shell-only duet UI; TS/dist policy; diff-log governance)
- 7.2: closed (history drawer lock-to-scroll, inverted chronology; churn policies)
- 7.3: closed (flow selector chips; shell-only; evidence/test_runs* staging policy)
- 7.4A: closed (ASK wiring to /chat; physics drift resolved; OpenAPI contract test added)
- 7.5: plan updated (inventory ghost overlay, dev panel hiding legacy blocks, mobile overflow acceptance; physics-safe)

## Key Governance Policies (Locked)
- evidence/test_runs.md & evidence/test_runs_latest.md: expected churn on each run; stage when modified.
- web/package-lock.json: stage only if adjacent to tracked web/package.json.
- web/node_modules/: local-only; never stage/commit.
- evidence/orchestration_system_snapshot.md: out-of-band; never stage/commit.
- Diff Log Gate: overwrite evidence/updatedifflog.md each cycle; stage it.
- Authorization Gate: halt before commit until authorized.

## UI State (Whats on screen now)
- Primary: duet shell with flow chips + composer.
- Legacy blocks still visible: Chat/Prefs/Mealplan/Shopping diff debug panels + JWT auth block.
- Planned fix: move legacy blocks into collapsed Dev Panel; fix mobile overflow (no right-side cut-off).

## Open Items / Next Steps
- Confirm Phase 7+ doc update is physics-safe (no new endpoints/schemas promised).
- Next target: implement Phase 7.5 UI (Inventory ghost overlay, Dev Panel, mobile scaling fixes).
- Risks/notes: diff log notes untracked snapshot/node_modules only.

## How To Resume Tomorrow
- Commands: git status -sb; git log -1 --oneline; open vidence/codex.md; open vidence/updatedifflog.md.
- Next directive expected: Phase 7.5 UI implementation (overlay + dev panel + mobile overflow fix).
