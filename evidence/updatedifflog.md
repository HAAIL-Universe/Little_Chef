# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-08T15:04:13+00:00
- Branch: recovery/evidence-20260208
- HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
- BASE_HEAD: 17d15fe7f340c11e6ea2476bb5826f50d39e7ad3
- Diff basis: unstaged (working tree)

## Cycle Status
- Status: COMPLETE

## Summary
- Expanded isNormalChatFlow to include prefs, inventory, meal-plan, and general so the badge/ellipsis mutations run for all normal chat flows
- sendAsk/updateDuetBubbles now rely on the shared guard before addHistory() so Prefs chats collapse into … and increment the unread badge
- Re-run the full scripts/run_tests.ps1 suite (Python compileall, pytest, npm build, renderer test, Playwright badge + long-press specs) to confirm the wider guard introduces no regressions

## Files Changed (unstaged (working tree))
- evidence/test_runs.md
- evidence/test_runs_latest.md
- web/dist/main.js
- web/src/main.ts

## git status -sb
    ## recovery/evidence-20260208
    MM evidence/test_runs.md
    MM evidence/test_runs_latest.md
    M  evidence/updatedifflog.md
    MM web/dist/main.js
    MM web/src/main.ts
    ?? web/test-results/

## Minimal Diff Hunks
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    index c19d8ae..a365fc9 100644
    --- a/evidence/test_runs.md
    +++ b/evidence/test_runs.md
    @@ -13223,3 +13223,31 @@ A  web/e2e/onboard-longpress.spec.ts
      2 files changed, 24957 insertions(+), 12407 deletions(-)
     ```
     
    +## Test Run 2026-02-08T15:03:44Z
    +- Status: PASS
    +- Start: 2026-02-08T15:03:44Z
    +- End: 2026-02-08T15:04:02Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: recovery/evidence-20260208
    +- HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 73 passed in 3.10s
    +- playwright test:e2e exit: 0
    +- playwright summary:   3 passed (4.9s)
    +- git status -sb:
    +```
    +## recovery/evidence-20260208
    +M  evidence/test_runs.md
    +M  evidence/test_runs_latest.md
    +M  evidence/updatedifflog.md
    +M  web/dist/main.js
    +MM web/src/main.ts
    +```
    +- git diff --stat:
    +```
    + web/src/main.ts | 3 ++-
    + 1 file changed, 2 insertions(+), 1 deletion(-)
    +```
    +
    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    index 42763d4..5145fac 100644
    --- a/evidence/test_runs_latest.md
    +++ b/evidence/test_runs_latest.md
    @@ -1,25 +1,27 @@
     Status: PASS
    -Start: 2026-02-08T14:58:08Z
    -End: 2026-02-08T14:58:26Z
    +Start: 2026-02-08T15:03:44Z
    +End: 2026-02-08T15:04:02Z
     Branch: recovery/evidence-20260208
     HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
     compileall exit: 0
     import app.main exit: 0
     pytest exit: 0
    -pytest summary: 73 passed in 3.79s
    +pytest summary: 73 passed in 3.10s
     playwright test:e2e exit: 0
    -playwright summary:   3 passed (5.1s)
    +playwright summary:   3 passed (4.9s)
     git status -sb:
     ```
     ## recovery/evidence-20260208
    - M evidence/updatedifflog.md
    - M web/src/main.ts
    +M  evidence/test_runs.md
    +M  evidence/test_runs_latest.md
    +M  evidence/updatedifflog.md
    +M  web/dist/main.js
    +MM web/src/main.ts
     ```
     git diff --stat:
     ```
    - evidence/updatedifflog.md | 37352 +++++++++++++++++++++++++++++---------------
    - web/src/main.ts           |    12 +-
    - 2 files changed, 24957 insertions(+), 12407 deletions(-)
    + web/src/main.ts | 3 ++-
    + 1 file changed, 2 insertions(+), 1 deletion(-)
     ```
     
    diff --git a/web/dist/main.js b/web/dist/main.js
    index 5da558b..9af3ced 100644
    --- a/web/dist/main.js
    +++ b/web/dist/main.js
    @@ -117,6 +117,7 @@ const OVERLAY_ROOT_ID = "duet-overlay-root";
     const OVERLAY_ROOT_Z_INDEX = 2147483640;
     const ONBOARD_MENU_EDGE_MARGIN = 8;
     const USER_BUBBLE_ELLIPSIS = "…";
    +const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
     let overlayRoot = null;
     let onboardPressTimer = null;
     let onboardPressStart = null;
    @@ -550,7 +551,7 @@ function updateDuetBubbles() {
         setBubbleText(user, showEllipsis ? USER_BUBBLE_ELLIPSIS : fallbackText);
     }
     function isNormalChatFlow() {
    -    return currentFlowKey !== "prefs";
    +    return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
     }
     function setUserBubbleEllipsis(enabled) {
         if (userBubbleEllipsisActive === enabled) {
    diff --git a/web/src/main.ts b/web/src/main.ts
    index fb6fa32..b326ccf 100644
    --- a/web/src/main.ts
    +++ b/web/src/main.ts
    @@ -130,6 +130,7 @@ const OVERLAY_ROOT_ID = "duet-overlay-root";
     const OVERLAY_ROOT_Z_INDEX = 2147483640;
     const ONBOARD_MENU_EDGE_MARGIN = 8;
     const USER_BUBBLE_ELLIPSIS = "…";
    +const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
     let overlayRoot: HTMLDivElement | null = null;
     let onboardPressTimer: number | null = null;
     let onboardPressStart: { x: number; y: number } | null = null;
    @@ -568,7 +569,7 @@ function updateDuetBubbles() {
     }
     
     function isNormalChatFlow() {
    -  return currentFlowKey !== "prefs";
    +  return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
     }
     
     function setUserBubbleEllipsis(enabled: boolean) {

## Verification
- static: python -m compileall app (pass)
- runtime: pwsh -NoProfile -File .\\scripts\\run_tests.ps1
- behavior: npm --prefix web run test:e2e (badge + long-press specs pass)
- contract: UI-only TS/Playwright updates, no physics or manifesto edits

## Notes (optional)
- TODO: blockers, risks, constraints.

## Next Steps
- Stage the updated JS + evidence artifacts and wait for Julius AUTHORIZED before committing

