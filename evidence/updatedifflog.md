# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-08T19:47:01+00:00
- Branch: recovery/evidence-20260208
- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
- BASE_HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Sent bubble now displays \ Sent\ across flows with history badge clamped at 99+ and kept as an overlay dot.
- History badge CSS now renders as a small overlay circle; dist/style.css was patched to carry the new selector.
- Playwright badge spec + TypeScript build recompiled the updated UI bundle.

## Files Changed (staged)
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md
- web/dist/main.js
- web/dist/style.css
- web/e2e/history-badge.spec.ts
- web/src/main.ts

## git status -sb
    ## recovery/evidence-20260208
     M app/services/inventory_agent.py
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
    M  evidence/updatedifflog.md
     M tests/test_inventory_agent.py
    M  web/dist/main.js
    M  web/dist/style.css
    M  web/e2e/history-badge.spec.ts
    M  web/src/main.ts

## Minimal Diff Hunks
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    index a365fc9..e73c946 100644
    --- a/evidence/test_runs.md
    +++ b/evidence/test_runs.md
    @@ -1,3 +1,57 @@
    +## Test Run 2026-02-08T18:57:15Z
    +- Status: PASS
    +- Start: 2026-02-08T18:57:15Z
    +- End: 2026-02-08T18:57:20Z
    +- Python: Z:\LittleChef\.venv\Scripts\python.exe
    +- Branch: recovery/evidence-20260208
    +- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +- compileall exit: 0
    +- python -m pytest -q exit: 0
    +- pytest summary: 74 passed in 3.80s
    +- git status -sb:
    +```
    +## recovery/evidence-20260208
    + M app/services/inventory_agent.py
    + M evidence/test_runs.md
    + M evidence/test_runs_latest.md
    + M evidence/updatedifflog.md
    + M tests/test_inventory_agent.py
    +```
    +- git diff --stat:
    +```
    + app/services/inventory_agent.py | 193 ++++++++++++++++++++++++++++++++++++++--
    + evidence/test_runs.md           |  25 ++++++
    + evidence/test_runs_latest.md    |  40 ++++-----
    + evidence/updatedifflog.md       | 171 +++++------------------------------
    + tests/test_inventory_agent.py   |  88 ++++++++++++++++++
    + 5 files changed, 337 insertions(+), 180 deletions(-)
    +```
    +
    +## Test Run 2026-02-08T18:45:19Z
    +- Status: PASS
    +- Start: 2026-02-08T18:45:19Z
    +- End: 2026-02-08T18:47:49Z
    +- Python: Z:\LittleChef\.venv\Scripts\python.exe
    +- Branch: recovery/evidence-20260208
    +- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +- compileall exit: 0
    +- python -m pytest -q exit: 0
    +- pytest summary: 74 passed in 4.57s
    +- git status -sb:
    +```
    +## recovery/evidence-20260208
    + M app/services/inventory_agent.py
    + M evidence/updatedifflog.md
    + M tests/test_inventory_agent.py
    +```
    +- git diff --stat:
    +```
    + app/services/inventory_agent.py | 121 ++++++++++++++++++++++++++++--
    + evidence/updatedifflog.md       | 161 +++++-----------------------------------
    + tests/test_inventory_agent.py   |  88 ++++++++++++++++++++++
    + 3 files changed, 219 insertions(+), 151 deletions(-)
    +```
    +
     ## Test Run 2026-02-08T00:40:46Z
     - Status: PASS
     - Start: 2026-02-08T00:40:40Z
    @@ -13251,3 +13305,38 @@ MM web/src/main.ts
      1 file changed, 2 insertions(+), 1 deletion(-)
     ```
     
    +## Test Run 2026-02-08T19:41:40Z
    +- Status: PASS
    +- Start: 2026-02-08T19:41:40Z
    +- End: 2026-02-08T19:42:35Z
    +- Python: C:\Users\krisd\AppData\Local\Programs\Python\Python312\python.exe
    +- Branch: recovery/evidence-20260208
    +- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +- compileall exit: 0
    +- python -m pytest -q exit: 0
    +- npm --prefix web run build exit: 0
    +- npm --prefix web run test:e2e exit: 0
    +- git status -sb:
    +```
    +## recovery/evidence-20260208
    + M app/services/inventory_agent.py
    + M evidence/test_runs.md
    + M evidence/test_runs_latest.md
    + M evidence/updatedifflog.md
    + M tests/test_inventory_agent.py
    + M web/dist/main.js
    + M web/e2e/history-badge.spec.ts
    + M web/src/main.ts
    +```
    +- git diff --stat:
    +```
    + app/services/inventory_agent.py | 193 ++++++++++++++++++++++++++++++++++++++--
    + evidence/test_runs.md           |  89 ++++++++++++++++++
    + evidence/test_runs_latest.md    |  44 ++++-----
    + evidence/updatedifflog.md       | 185 ++++++++------------------------------
    + tests/test_inventory_agent.py   |  88 ++++++++++++++++++
    + web/dist/main.js                |  12 ++-
    + web/e2e/history-badge.spec.ts   |   6 +-
    + web/src/main.ts                 |  12 ++-
    + 8 files changed, 441 insertions(+), 188 deletions(-)
    +```
    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    index 5145fac..b226613 100644
    --- a/evidence/test_runs_latest.md
    +++ b/evidence/test_runs_latest.md
    @@ -1,27 +1,34 @@
     Status: PASS
    -Start: 2026-02-08T15:03:44Z
    -End: 2026-02-08T15:04:02Z
    +Start: 2026-02-08T19:41:40Z
    +End: 2026-02-08T19:42:35Z
     Branch: recovery/evidence-20260208
    -HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    -Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +Python: C:\Users\krisd\AppData\Local\Programs\Python\Python312\python.exe
     compileall exit: 0
    -import app.main exit: 0
    -pytest exit: 0
    -pytest summary: 73 passed in 3.10s
    -playwright test:e2e exit: 0
    -playwright summary:   3 passed (4.9s)
    +python -m pytest -q exit: 0
    +npm --prefix web run build exit: 0
    +npm --prefix web run test:e2e exit: 0
     git status -sb:
     ```
     ## recovery/evidence-20260208
    -M  evidence/test_runs.md
    -M  evidence/test_runs_latest.md
    -M  evidence/updatedifflog.md
    -M  web/dist/main.js
    -MM web/src/main.ts
    + M app/services/inventory_agent.py
    + M evidence/test_runs.md
    + M evidence/test_runs_latest.md
    + M evidence/updatedifflog.md
    + M tests/test_inventory_agent.py
    + M web/dist/main.js
    + M web/e2e/history-badge.spec.ts
    + M web/src/main.ts
     ```
     git diff --stat:
     ```
    - web/src/main.ts | 3 ++-
    - 1 file changed, 2 insertions(+), 1 deletion(-)
    + app/services/inventory_agent.py | 193 ++++++++++++++++++++++++++++++++++++++--
    + evidence/test_runs.md           |  89 ++++++++++++++++++
    + evidence/test_runs_latest.md    |  44 ++++-----
    + evidence/updatedifflog.md       | 185 ++++++++------------------------------
    + tests/test_inventory_agent.py   |  88 ++++++++++++++++++
    + web/dist/main.js                |  12 ++-
    + web/e2e/history-badge.spec.ts   |   6 +-
    + web/src/main.ts                 |  12 ++-
    + 8 files changed, 441 insertions(+), 188 deletions(-)
     ```
    -
    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    index 14341ae..17fab82 100644
    --- a/evidence/updatedifflog.md
    +++ b/evidence/updatedifflog.md
    @@ -1,165 +1,521 @@
    -# Diff Log (overwrite each cycle)
    +﻿# Diff Log (overwrite each cycle)
     
     ## Cycle Metadata
    -- Timestamp: 2026-02-08T15:04:13+00:00
    +- Timestamp: 2026-02-08T19:44:08+00:00
     - Branch: recovery/evidence-20260208
    -- HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    -- BASE_HEAD: 17d15fe7f340c11e6ea2476bb5826f50d39e7ad3
    -- Diff basis: unstaged (working tree)
    +- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +- BASE_HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    +- Diff basis: staged
     
     ## Cycle Status
     - Status: COMPLETE
     
     ## Summary
    -- Expanded isNormalChatFlow to include prefs, inventory, meal-plan, and general so the badge/ellipsis mutations run for all normal chat flows
    -- sendAsk/updateDuetBubbles now rely on the shared guard before addHistory() so Prefs chats collapse into … and increment the unread badge
    -- Re-run the full scripts/run_tests.ps1 suite (Python compileall, pytest, npm build, renderer test, Playwright badge + long-press specs) to confirm the wider guard introduces no regressions
    +- Sent bubble now displays \ Sent\ across flows with history badge clamped at 99+ and kept as an overlay dot.
    +- Playwright badge spec + TypeScript build recompiled the updated UI bundle.
    +- Test logs refreshed to capture compileall, pytest, npm build, and Playwright runs.
     
    -## Files Changed (unstaged (working tree))
    +## Files Changed (staged)
     - evidence/test_runs.md
     - evidence/test_runs_latest.md
    +- evidence/updatedifflog.md
     - web/dist/main.js
    +- web/e2e/history-badge.spec.ts
     - web/src/main.ts
     
     ## git status -sb
         ## recovery/evidence-20260208
    -    MM evidence/test_runs.md
    -    MM evidence/test_runs_latest.md
    +     M app/services/inventory_agent.py
    +    M  evidence/test_runs.md
    +    M  evidence/test_runs_latest.md
         M  evidence/updatedifflog.md
    -    MM web/dist/main.js
    -    MM web/src/main.ts
    -    ?? web/test-results/
    +     M tests/test_inventory_agent.py
    +    M  web/dist/main.js
    +    M  web/e2e/history-badge.spec.ts
    +    M  web/src/main.ts
     
     ## Minimal Diff Hunks
         diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    -    index c19d8ae..a365fc9 100644
    +    index a365fc9..e73c946 100644
         --- a/evidence/test_runs.md
         +++ b/evidence/test_runs.md
    -    @@ -13223,3 +13223,31 @@ A  web/e2e/onboard-longpress.spec.ts
    -      2 files changed, 24957 insertions(+), 12407 deletions(-)
    +    @@ -1,3 +1,57 @@
    +    +## Test Run 2026-02-08T18:57:15Z
    +    +- Status: PASS
    +    +- Start: 2026-02-08T18:57:15Z
    +    +- End: 2026-02-08T18:57:20Z
    +    +- Python: Z:\LittleChef\.venv\Scripts\python.exe
    +    +- Branch: recovery/evidence-20260208
    +    +- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +    +- compileall exit: 0
    +    +- python -m pytest -q exit: 0
    +    +- pytest summary: 74 passed in 3.80s
    +    +- git status -sb:
    +    +```
    +    +## recovery/evidence-20260208
    +    + M app/services/inventory_agent.py
    +    + M evidence/test_runs.md
    +    + M evidence/test_runs_latest.md
    +    + M evidence/updatedifflog.md
    +    + M tests/test_inventory_agent.py
    +    +```
    +    +- git diff --stat:
    +    +```
    +    + app/services/inventory_agent.py | 193 ++++++++++++++++++++++++++++++++++++++--
    +    + evidence/test_runs.md           |  25 ++++++
    +    + evidence/test_runs_latest.md    |  40 ++++-----
    +    + evidence/updatedifflog.md       | 171 +++++------------------------------
    +    + tests/test_inventory_agent.py   |  88 ++++++++++++++++++
    +    + 5 files changed, 337 insertions(+), 180 deletions(-)
    +    +```
    +    +
    +    +## Test Run 2026-02-08T18:45:19Z
    +    +- Status: PASS
    +    +- Start: 2026-02-08T18:45:19Z
    +    +- End: 2026-02-08T18:47:49Z
    +    +- Python: Z:\LittleChef\.venv\Scripts\python.exe
    +    +- Branch: recovery/evidence-20260208
    +    +- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +    +- compileall exit: 0
    +    +- python -m pytest -q exit: 0
    +    +- pytest summary: 74 passed in 4.57s
    +    +- git status -sb:
    +    +```
    +    +## recovery/evidence-20260208
    +    + M app/services/inventory_agent.py
    +    + M evidence/updatedifflog.md
    +    + M tests/test_inventory_agent.py
    +    +```
    +    +- git diff --stat:
    +    +```
    +    + app/services/inventory_agent.py | 121 ++++++++++++++++++++++++++++--
    +    + evidence/updatedifflog.md       | 161 +++++-----------------------------------
    +    + tests/test_inventory_agent.py   |  88 ++++++++++++++++++++++
    +    + 3 files changed, 219 insertions(+), 151 deletions(-)
    +    +```
    +    +
    +     ## Test Run 2026-02-08T00:40:46Z
    +     - Status: PASS
    +     - Start: 2026-02-08T00:40:40Z
    +    @@ -13251,3 +13305,38 @@ MM web/src/main.ts
    +      1 file changed, 2 insertions(+), 1 deletion(-)
          ```
          
    -    +## Test Run 2026-02-08T15:03:44Z
    +    +## Test Run 2026-02-08T19:41:40Z
         +- Status: PASS
    -    +- Start: 2026-02-08T15:03:44Z
    -    +- End: 2026-02-08T15:04:02Z
    -    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +    +- Start: 2026-02-08T19:41:40Z
    +    +- End: 2026-02-08T19:42:35Z
    +    +- Python: C:\Users\krisd\AppData\Local\Programs\Python\Python312\python.exe
         +- Branch: recovery/evidence-20260208
    -    +- HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    +    +- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
         +- compileall exit: 0
    -    +- import app.main exit: 0
    -    +- pytest exit: 0
    -    +- pytest summary: 73 passed in 3.10s
    -    +- playwright test:e2e exit: 0
    -    +- playwright summary:   3 passed (4.9s)
    +    +- python -m pytest -q exit: 0
    +    +- npm --prefix web run build exit: 0
    +    +- npm --prefix web run test:e2e exit: 0
         +- git status -sb:
         +```
         +## recovery/evidence-20260208
    -    +M  evidence/test_runs.md
    -    +M  evidence/test_runs_latest.md
    -    +M  evidence/updatedifflog.md
    -    +M  web/dist/main.js
    -    +MM web/src/main.ts
    +    + M app/services/inventory_agent.py
    +    + M evidence/test_runs.md
    +    + M evidence/test_runs_latest.md
    +    + M evidence/updatedifflog.md
    +    + M tests/test_inventory_agent.py
    +    + M web/dist/main.js
    +    + M web/e2e/history-badge.spec.ts
    +    + M web/src/main.ts
         +```
         +- git diff --stat:
         +```
    -    + web/src/main.ts | 3 ++-
    -    + 1 file changed, 2 insertions(+), 1 deletion(-)
    +    + app/services/inventory_agent.py | 193 ++++++++++++++++++++++++++++++++++++++--
    +    + evidence/test_runs.md           |  89 ++++++++++++++++++
    +    + evidence/test_runs_latest.md    |  44 ++++-----
    +    + evidence/updatedifflog.md       | 185 ++++++++------------------------------
    +    + tests/test_inventory_agent.py   |  88 ++++++++++++++++++
    +    + web/dist/main.js                |  12 ++-
    +    + web/e2e/history-badge.spec.ts   |   6 +-
    +    + web/src/main.ts                 |  12 ++-
    +    + 8 files changed, 441 insertions(+), 188 deletions(-)
         +```
    -    +
         diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    -    index 42763d4..5145fac 100644
    +    index 5145fac..b226613 100644
         --- a/evidence/test_runs_latest.md
         +++ b/evidence/test_runs_latest.md
    -    @@ -1,25 +1,27 @@
    +    @@ -1,27 +1,34 @@
          Status: PASS
    -    -Start: 2026-02-08T14:58:08Z
    -    -End: 2026-02-08T14:58:26Z
    -    +Start: 2026-02-08T15:03:44Z
    -    +End: 2026-02-08T15:04:02Z
    +    -Start: 2026-02-08T15:03:44Z
    +    -End: 2026-02-08T15:04:02Z
    +    +Start: 2026-02-08T19:41:40Z
    +    +End: 2026-02-08T19:42:35Z
          Branch: recovery/evidence-20260208
    -     HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    -     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +    -HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    +    -Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +    +HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +    +Python: C:\Users\krisd\AppData\Local\Programs\Python\Python312\python.exe
          compileall exit: 0
    -     import app.main exit: 0
    -     pytest exit: 0
    -    -pytest summary: 73 passed in 3.79s
    -    +pytest summary: 73 passed in 3.10s
    -     playwright test:e2e exit: 0
    -    -playwright summary:   3 passed (5.1s)
    -    +playwright summary:   3 passed (4.9s)
    +    -import app.main exit: 0
    +    -pytest exit: 0
    +    -pytest summary: 73 passed in 3.10s
    +    -playwright test:e2e exit: 0
    +    -playwright summary:   3 passed (4.9s)
    +    +python -m pytest -q exit: 0
    +    +npm --prefix web run build exit: 0
    +    +npm --prefix web run test:e2e exit: 0
          git status -sb:
          ```
          ## recovery/evidence-20260208
    -    - M evidence/updatedifflog.md
    -    - M web/src/main.ts
    -    +M  evidence/test_runs.md
    -    +M  evidence/test_runs_latest.md
    -    +M  evidence/updatedifflog.md
    -    +M  web/dist/main.js
    -    +MM web/src/main.ts
    +    -M  evidence/test_runs.md
    +    -M  evidence/test_runs_latest.md
    +    -M  evidence/updatedifflog.md
    +    -M  web/dist/main.js
    +    -MM web/src/main.ts
    +    + M app/services/inventory_agent.py
    +    + M evidence/test_runs.md
    +    + M evidence/test_runs_latest.md
    +    + M evidence/updatedifflog.md
    +    + M tests/test_inventory_agent.py
    +    + M web/dist/main.js
    +    + M web/e2e/history-badge.spec.ts
    +    + M web/src/main.ts
          ```
          git diff --stat:
          ```
    -    - evidence/updatedifflog.md | 37352 +++++++++++++++++++++++++++++---------------
    -    - web/src/main.ts           |    12 +-
    -    - 2 files changed, 24957 insertions(+), 12407 deletions(-)
    -    + web/src/main.ts | 3 ++-
    -    + 1 file changed, 2 insertions(+), 1 deletion(-)
    +    - web/src/main.ts | 3 ++-
    +    - 1 file changed, 2 insertions(+), 1 deletion(-)
    +    + app/services/inventory_agent.py | 193 ++++++++++++++++++++++++++++++++++++++--
    +    + evidence/test_runs.md           |  89 ++++++++++++++++++
    +    + evidence/test_runs_latest.md    |  44 ++++-----
    +    + evidence/updatedifflog.md       | 185 ++++++++------------------------------
    +    + tests/test_inventory_agent.py   |  88 ++++++++++++++++++
    +    + web/dist/main.js                |  12 ++-
    +    + web/e2e/history-badge.spec.ts   |   6 +-
    +    + web/src/main.ts                 |  12 ++-
    +    + 8 files changed, 441 insertions(+), 188 deletions(-)
          ```
    +    -
    +    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    +    index 14341ae..d7e3bac 100644
    +    --- a/evidence/updatedifflog.md
    +    +++ b/evidence/updatedifflog.md
    +    @@ -1,165 +1,56 @@
    +     # Diff Log (overwrite each cycle)
    +     
    +     ## Cycle Metadata
    +    -- Timestamp: 2026-02-08T15:04:13+00:00
    +    +- Timestamp: 2026-02-08T18:57:56Z
    +     - Branch: recovery/evidence-20260208
    +    -- HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    +    -- BASE_HEAD: 17d15fe7f340c11e6ea2476bb5826f50d39e7ad3
    +    -- Diff basis: unstaged (working tree)
    +    +- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +    +- BASE_HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    +    +- Diff basis: staged
    +     
    +     ## Cycle Status
    +     - Status: COMPLETE
    +     
    +    -## Summary
    +    -- Expanded isNormalChatFlow to include prefs, inventory, meal-plan, and general so the badge/ellipsis mutations run for all normal chat flows
    +    -- sendAsk/updateDuetBubbles now rely on the shared guard before addHistory() so Prefs chats collapse into … and increment the unread badge
    +    -- Re-run the full scripts/run_tests.ps1 suite (Python compileall, pytest, npm build, renderer test, Playwright badge + long-press specs) to confirm the wider guard introduces no regressions
    +    +## Intent & Acceptance
    +    +- Harden the candidate extractor to skip container/non-food tokens, strip lead-in chatter before cleaning, and preserve cereal tokens when they are explicitly present in the clause.
    +     
    +    -## Files Changed (unstaged (working tree))
    +    -- evidence/test_runs.md
    +    -- evidence/test_runs_latest.md
    +    -- web/dist/main.js
    +    -- web/src/main.ts
    +    +## Files, Anchors & Hints
    +    +- `app/services/inventory_agent.py:150-210` now declares `BARE_FILLER_WORDS`, `FRACTION_LEFT_PATTERN`, `LEAD_PREFIXES`, and cereal tokens plus the expanded `DATE_STRIP_PATTERN` so the cleaning helpers see the new guard list.
    +    +- `app/services/inventory_agent.py:520-570` extracts cereal tokens early, sanitizes the left clause, and calls `_is_disallowed_item_name` just before any action is appended, guaranteeing the new filler/container/fraction/“okay little chef” rejection runs in every branch.
    +    +- `app/services/inventory_agent.py:820-890` now strips the new lead-in prefixes inside `_clean_segment_text` so phrases like “quick stock check” or “half left” are gone before stop words run.
    +    +- `tests/test_inventory_agent.py` still drives the container-scan fixture and now backs the “no junk names/dates” requirement.
    +    +- Evidence logs document the latest manual runs.
    +    +
    +    +## Files Changed (staged)
    +    +- `app/services/inventory_agent.py`
    +    +- `tests/test_inventory_agent.py`
    +    +- `evidence/test_runs.md`
    +    +- `evidence/test_runs_latest.md`
    +    +- `evidence/updatedifflog.md`
    +     
    +     ## git status -sb
    +    -    ## recovery/evidence-20260208
    +    -    MM evidence/test_runs.md
    +    -    MM evidence/test_runs_latest.md
    +    -    M  evidence/updatedifflog.md
    +    -    MM web/dist/main.js
    +    -    MM web/src/main.ts
    +    -    ?? web/test-results/
    +    +```
    +    +## recovery/evidence-20260208
    +    + M app/services/inventory_agent.py
    +    + M evidence/test_runs.md
    +    + M evidence/test_runs_latest.md
    +    + M evidence/updatedifflog.md
    +    + M tests/test_inventory_agent.py
    +    +```
    +     
    +     ## Minimal Diff Hunks
    +    -    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    +    -    index c19d8ae..a365fc9 100644
    +    -    --- a/evidence/test_runs.md
    +    -    +++ b/evidence/test_runs.md
    +    -    @@ -13223,3 +13223,31 @@ A  web/e2e/onboard-longpress.spec.ts
    +    -      2 files changed, 24957 insertions(+), 12407 deletions(-)
    +    -     ```
    +    -     
    +    -    +## Test Run 2026-02-08T15:03:44Z
    +    -    +- Status: PASS
    +    -    +- Start: 2026-02-08T15:03:44Z
    +    -    +- End: 2026-02-08T15:04:02Z
    +    -    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +    -    +- Branch: recovery/evidence-20260208
    +    -    +- HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    +    -    +- compileall exit: 0
    +    -    +- import app.main exit: 0
    +    -    +- pytest exit: 0
    +    -    +- pytest summary: 73 passed in 3.10s
    +    -    +- playwright test:e2e exit: 0
    +    -    +- playwright summary:   3 passed (4.9s)
    +    -    +- git status -sb:
    +    -    +```
    +    -    +## recovery/evidence-20260208
    +    -    +M  evidence/test_runs.md
    +    -    +M  evidence/test_runs_latest.md
    +    -    +M  evidence/updatedifflog.md
    +    -    +M  web/dist/main.js
    +    -    +MM web/src/main.ts
    +    -    +```
    +    -    +- git diff --stat:
    +    -    +```
    +    -    + web/src/main.ts | 3 ++-
    +    -    + 1 file changed, 2 insertions(+), 1 deletion(-)
    +    -    +```
    +    -    +
    +    -    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    +    -    index 42763d4..5145fac 100644
    +    -    --- a/evidence/test_runs_latest.md
    +    -    +++ b/evidence/test_runs_latest.md
    +    -    @@ -1,25 +1,27 @@
    +    -     Status: PASS
    +    -    -Start: 2026-02-08T14:58:08Z
    +    -    -End: 2026-02-08T14:58:26Z
    +    -    +Start: 2026-02-08T15:03:44Z
    +    -    +End: 2026-02-08T15:04:02Z
    +    -     Branch: recovery/evidence-20260208
    +    -     HEAD: ec7c6ccec7afdcc50f8764f179ca086b78fc52b8
    +    -     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +    -     compileall exit: 0
    +    -     import app.main exit: 0
    +    -     pytest exit: 0
    +    -    -pytest summary: 73 passed in 3.79s
    +    -    +pytest summary: 73 passed in 3.10s
    +    -     playwright test:e2e exit: 0
    +    -    -playwright summary:   3 passed (5.1s)
    +    -    +playwright summary:   3 passed (4.9s)
    +    -     git status -sb:
    +    -     ```
    +    -     ## recovery/evidence-20260208
    +    -    - M evidence/updatedifflog.md
    +    -    - M web/src/main.ts
    +    -    +M  evidence/test_runs.md
    +    -    +M  evidence/test_runs_latest.md
    +    -    +M  evidence/updatedifflog.md
    +    -    +M  web/dist/main.js
    +    -    +MM web/src/main.ts
    +    -     ```
    +    -     git diff --stat:
    +    -     ```
    +    -    - evidence/updatedifflog.md | 37352 +++++++++++++++++++++++++++++---------------
    +    -    - web/src/main.ts           |    12 +-
    +    -    - 2 files changed, 24957 insertions(+), 12407 deletions(-)
    +    -    + web/src/main.ts | 3 ++-
    +    -    + 1 file changed, 2 insertions(+), 1 deletion(-)
    +    -     ```
    +    -     
    +    -    diff --git a/web/dist/main.js b/web/dist/main.js
    +    -    index 5da558b..9af3ced 100644
    +    -    --- a/web/dist/main.js
    +    -    +++ b/web/dist/main.js
    +    -    @@ -117,6 +117,7 @@ const OVERLAY_ROOT_ID = "duet-overlay-root";
    +    -     const OVERLAY_ROOT_Z_INDEX = 2147483640;
    +    -     const ONBOARD_MENU_EDGE_MARGIN = 8;
    +    -     const USER_BUBBLE_ELLIPSIS = "…";
    +    -    +const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
    +    -     let overlayRoot = null;
    +    -     let onboardPressTimer = null;
    +    -     let onboardPressStart = null;
    +    -    @@ -550,7 +551,7 @@ function updateDuetBubbles() {
    +    -         setBubbleText(user, showEllipsis ? USER_BUBBLE_ELLIPSIS : fallbackText);
    +    -     }
    +    -     function isNormalChatFlow() {
    +    -    -    return currentFlowKey !== "prefs";
    +    -    +    return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
    +    -     }
    +    -     function setUserBubbleEllipsis(enabled) {
    +    -         if (userBubbleEllipsisActive === enabled) {
    +    -    diff --git a/web/src/main.ts b/web/src/main.ts
    +    -    index fb6fa32..b326ccf 100644
    +    -    --- a/web/src/main.ts
    +    -    +++ b/web/src/main.ts
    +    -    @@ -130,6 +130,7 @@ const OVERLAY_ROOT_ID = "duet-overlay-root";
    +    -     const OVERLAY_ROOT_Z_INDEX = 2147483640;
    +    -     const ONBOARD_MENU_EDGE_MARGIN = 8;
    +    -     const USER_BUBBLE_ELLIPSIS = "…";
    +    -    +const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
    +    -     let overlayRoot: HTMLDivElement | null = null;
    +    -     let onboardPressTimer: number | null = null;
    +    -     let onboardPressStart: { x: number; y: number } | null = null;
    +    -    @@ -568,7 +569,7 @@ function updateDuetBubbles() {
    +    -     }
    +    -     
    +    -     function isNormalChatFlow() {
    +    -    -  return currentFlowKey !== "prefs";
    +    -    +  return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
    +    -     }
    +    -     
    +    -     function setUserBubbleEllipsis(enabled: boolean) {
    +    +- `app/services/inventory_agent.py:150-210` – new filler/lead-in/cereal constants and regexes.
    +    +- `app/services/inventory_agent.py:520-570` – cereal override + left-clause guard + `_is_disallowed_item_name` invocation.
    +    +- `app/services/inventory_agent.py:820-890` – `_clean_segment_text` now calls `_strip_leading_prefixes`.
    +    +- `evidence/test_runs*.md` – top entries capture the compileall+pytest run above.
    +     
    +     ## Verification
    +    -- static: python -m compileall app (pass)
    +    -- runtime: pwsh -NoProfile -File .\\scripts\\run_tests.ps1
    +    -- behavior: npm --prefix web run test:e2e (badge + long-press specs pass)
    +    -- contract: UI-only TS/Playwright updates, no physics or manifesto edits
    +    +- static: `python -m compileall .` (exit 0)
    +    +- behavior: `python -m pytest -q` (exit 0, 74 passed in 3.80s)
    +    +- build: `cd web && npm run build` (exit 0)
    +     
    +    -## Notes (optional)
    +    -- TODO: blockers, risks, constraints.
    +    +## Notes
    +    +- No UI/theme files touched; only the backend parser, regression tests, and evidence logs changed this cycle.
          
    +     ## Next Steps
    +    -- Stage the updated JS + evidence artifacts and wait for Julius AUTHORIZED before committing
    +    -
    +    +1) Leave only the staged files above and wait for Julius’s `AUTHORIZED` before committing.
    +    +2) If the UI surface changes again, rerun the history badge/evidence suite to keep regression tests healthy.
         diff --git a/web/dist/main.js b/web/dist/main.js
    -    index 5da558b..9af3ced 100644
    +    index 9af3ced..60da41f 100644
         --- a/web/dist/main.js
         +++ b/web/dist/main.js
    -    @@ -117,6 +117,7 @@ const OVERLAY_ROOT_ID = "duet-overlay-root";
    +    @@ -116,7 +116,8 @@ let onboardMenu = null;
    +     const OVERLAY_ROOT_ID = "duet-overlay-root";
          const OVERLAY_ROOT_Z_INDEX = 2147483640;
          const ONBOARD_MENU_EDGE_MARGIN = 8;
    -     const USER_BUBBLE_ELLIPSIS = "…";
    -    +const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
    +    -const USER_BUBBLE_ELLIPSIS = "…";
    +    +const USER_BUBBLE_SENT_TEXT = "Sent";
    +    +const HISTORY_BADGE_DISPLAY_MAX = 99;
    +     const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
          let overlayRoot = null;
          let onboardPressTimer = null;
    -     let onboardPressStart = null;
    -    @@ -550,7 +551,7 @@ function updateDuetBubbles() {
    -         setBubbleText(user, showEllipsis ? USER_BUBBLE_ELLIPSIS : fallbackText);
    +    @@ -546,9 +547,9 @@ function updateDuetBubbles() {
    +         const assistantFallback = "Welcome — I’m Little Chef. To start onboarding, please fill out your preferences (allergies, likes/dislikes, servings, days).";
    +         const userFallback = "Press and hold to start onboarding with preferences.";
    +         setBubbleText(assistant, (_a = lastAssistant === null || lastAssistant === void 0 ? void 0 : lastAssistant.text) !== null && _a !== void 0 ? _a : assistantFallback);
    +    -    const showEllipsis = userBubbleEllipsisActive && isNormalChatFlow();
    +    +    const showSentText = userBubbleEllipsisActive && isNormalChatFlow();
    +         const fallbackText = isNormalChatFlow() ? userFallback : (_b = lastUser === null || lastUser === void 0 ? void 0 : lastUser.text) !== null && _b !== void 0 ? _b : userFallback;
    +    -    setBubbleText(user, showEllipsis ? USER_BUBBLE_ELLIPSIS : fallbackText);
    +    +    setBubbleText(user, showSentText ? USER_BUBBLE_SENT_TEXT : fallbackText);
          }
          function isNormalChatFlow() {
    -    -    return currentFlowKey !== "prefs";
    -    +    return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
    -     }
    -     function setUserBubbleEllipsis(enabled) {
    -         if (userBubbleEllipsisActive === enabled) {
    +         return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
    +    @@ -749,7 +750,10 @@ function updateHistoryBadge() {
    +         if (!badge)
    +             return;
    +         if (historyBadgeCount > 0) {
    +    -        badge.textContent = historyBadgeCount.toString();
    +    +        badge.textContent =
    +    +            historyBadgeCount > HISTORY_BADGE_DISPLAY_MAX
    +    +                ? `${HISTORY_BADGE_DISPLAY_MAX}+`
    +    +                : historyBadgeCount.toString();
    +             badge.classList.add("visible");
    +             badge.setAttribute("aria-hidden", "false");
    +         }
    +    diff --git a/web/e2e/history-badge.spec.ts b/web/e2e/history-badge.spec.ts
    +    index 24c5c44..3c01e4e 100644
    +    --- a/web/e2e/history-badge.spec.ts
    +    +++ b/web/e2e/history-badge.spec.ts
    +    @@ -1,7 +1,7 @@
    +     import { expect, test } from "@playwright/test";
    +     
    +     test.describe("History badge and bubble", () => {
    +    -  test("ellipsis bubble and badge track normal chat activity", async ({ page }) => {
    +    +  test("sent bubble and badge track normal chat activity", async ({ page }) => {
    +         await page.goto("/", { waitUntil: "networkidle" });
    +         const bubbleText = page.locator("#duet-user-bubble .bubble-text");
    +         await expect(bubbleText).toBeVisible({ timeout: 15000 });
    +    @@ -16,7 +16,7 @@ test.describe("History badge and bubble", () => {
    +         for (let i = 1; i <= 3; i += 1) {
    +           await input.fill(`message ${i}`);
    +           await sendBtn.evaluate((btn) => (btn as HTMLButtonElement).click());
    +    -      await expect(bubbleText).toHaveText("…", { timeout: 5000 });
    +    +      await expect(bubbleText).toHaveText("Sent", { timeout: 5000 });
    +         }
    +     
    +         await expect(badge).toHaveText("3", { timeout: 5000 });
    +    @@ -37,6 +37,6 @@ test.describe("History badge and bubble", () => {
    +         await sendBtn.evaluate((btn) => (btn as HTMLButtonElement).click());
    +         await expect(badge).toHaveText("1", { timeout: 5000 });
    +         await expect(badge).toHaveClass(/visible/, { timeout: 5000 });
    +    -    await expect(bubbleText).toHaveText("…", { timeout: 5000 });
    +    +    await expect(bubbleText).toHaveText("Sent", { timeout: 5000 });
    +       });
    +     });
         diff --git a/web/src/main.ts b/web/src/main.ts
    -    index fb6fa32..b326ccf 100644
    +    index b326ccf..c7a399e 100644
         --- a/web/src/main.ts
         +++ b/web/src/main.ts
    -    @@ -130,6 +130,7 @@ const OVERLAY_ROOT_ID = "duet-overlay-root";
    +    @@ -129,7 +129,8 @@ let onboardMenu: HTMLDivElement | null = null;
    +     const OVERLAY_ROOT_ID = "duet-overlay-root";
          const OVERLAY_ROOT_Z_INDEX = 2147483640;
          const ONBOARD_MENU_EDGE_MARGIN = 8;
    -     const USER_BUBBLE_ELLIPSIS = "…";
    -    +const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
    +    -const USER_BUBBLE_ELLIPSIS = "…";
    +    +const USER_BUBBLE_SENT_TEXT = "Sent";
    +    +const HISTORY_BADGE_DISPLAY_MAX = 99;
    +     const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
          let overlayRoot: HTMLDivElement | null = null;
          let onboardPressTimer: number | null = null;
    -     let onboardPressStart: { x: number; y: number } | null = null;
    -    @@ -568,7 +569,7 @@ function updateDuetBubbles() {
    +    @@ -563,9 +564,9 @@ function updateDuetBubbles() {
    +         "Welcome — I’m Little Chef. To start onboarding, please fill out your preferences (allergies, likes/dislikes, servings, days).";
    +       const userFallback = "Press and hold to start onboarding with preferences.";
    +       setBubbleText(assistant, lastAssistant?.text ?? assistantFallback);
    +    -  const showEllipsis = userBubbleEllipsisActive && isNormalChatFlow();
    +    +  const showSentText = userBubbleEllipsisActive && isNormalChatFlow();
    +       const fallbackText = isNormalChatFlow() ? userFallback : lastUser?.text ?? userFallback;
    +    -  setBubbleText(user, showEllipsis ? USER_BUBBLE_ELLIPSIS : fallbackText);
    +    +  setBubbleText(user, showSentText ? USER_BUBBLE_SENT_TEXT : fallbackText);
          }
          
          function isNormalChatFlow() {
    -    -  return currentFlowKey !== "prefs";
    -    +  return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
    -     }
    -     
    -     function setUserBubbleEllipsis(enabled: boolean) {
    +    @@ -785,7 +786,10 @@ function updateHistoryBadge() {
    +       const badge = ensureHistoryBadgeElement();
    +       if (!badge) return;
    +       if (historyBadgeCount > 0) {
    +    -    badge.textContent = historyBadgeCount.toString();
    +    +    badge.textContent =
    +    +      historyBadgeCount > HISTORY_BADGE_DISPLAY_MAX
    +    +        ? `${HISTORY_BADGE_DISPLAY_MAX}+`
    +    +        : historyBadgeCount.toString();
    +         badge.classList.add("visible");
    +         badge.setAttribute("aria-hidden", "false");
    +       } else {
     
     ## Verification
    -- static: python -m compileall app (pass)
    -- runtime: pwsh -NoProfile -File .\\scripts\\run_tests.ps1
    -- behavior: npm --prefix web run test:e2e (badge + long-press specs pass)
    -- contract: UI-only TS/Playwright updates, no physics or manifesto edits
    +- python -m compileall . (pass)
    +- python -m pytest -q (pass)
    +- npm --prefix web run build (pass)
    +- npm --prefix web run test:e2e (pass)
     
     ## Notes (optional)
     - TODO: blockers, risks, constraints.
     
     ## Next Steps
    -- Stage the updated JS + evidence artifacts and wait for Julius AUTHORIZED before committing
    +- Hold for Julius AUTHORIZED before committing.
     
    diff --git a/web/dist/main.js b/web/dist/main.js
    index 9af3ced..60da41f 100644
    --- a/web/dist/main.js
    +++ b/web/dist/main.js
    @@ -116,7 +116,8 @@ let onboardMenu = null;
     const OVERLAY_ROOT_ID = "duet-overlay-root";
     const OVERLAY_ROOT_Z_INDEX = 2147483640;
     const ONBOARD_MENU_EDGE_MARGIN = 8;
    -const USER_BUBBLE_ELLIPSIS = "…";
    +const USER_BUBBLE_SENT_TEXT = "Sent";
    +const HISTORY_BADGE_DISPLAY_MAX = 99;
     const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
     let overlayRoot = null;
     let onboardPressTimer = null;
    @@ -546,9 +547,9 @@ function updateDuetBubbles() {
         const assistantFallback = "Welcome — I’m Little Chef. To start onboarding, please fill out your preferences (allergies, likes/dislikes, servings, days).";
         const userFallback = "Press and hold to start onboarding with preferences.";
         setBubbleText(assistant, (_a = lastAssistant === null || lastAssistant === void 0 ? void 0 : lastAssistant.text) !== null && _a !== void 0 ? _a : assistantFallback);
    -    const showEllipsis = userBubbleEllipsisActive && isNormalChatFlow();
    +    const showSentText = userBubbleEllipsisActive && isNormalChatFlow();
         const fallbackText = isNormalChatFlow() ? userFallback : (_b = lastUser === null || lastUser === void 0 ? void 0 : lastUser.text) !== null && _b !== void 0 ? _b : userFallback;
    -    setBubbleText(user, showEllipsis ? USER_BUBBLE_ELLIPSIS : fallbackText);
    +    setBubbleText(user, showSentText ? USER_BUBBLE_SENT_TEXT : fallbackText);
     }
     function isNormalChatFlow() {
         return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
    @@ -749,7 +750,10 @@ function updateHistoryBadge() {
         if (!badge)
             return;
         if (historyBadgeCount > 0) {
    -        badge.textContent = historyBadgeCount.toString();
    +        badge.textContent =
    +            historyBadgeCount > HISTORY_BADGE_DISPLAY_MAX
    +                ? `${HISTORY_BADGE_DISPLAY_MAX}+`
    +                : historyBadgeCount.toString();
             badge.classList.add("visible");
             badge.setAttribute("aria-hidden", "false");
         }
    diff --git a/web/dist/style.css b/web/dist/style.css
    index a80fb36..f231036 100644
    --- a/web/dist/style.css
    +++ b/web/dist/style.css
    @@ -480,6 +480,32 @@ pre {
       box-shadow: 0 8px 18px rgba(0, 0, 0, 0.35);
     }
     
    +.history-badge {
    +  position: absolute;
    +  top: -4px;
    +  right: -4px;
    +  min-width: 18px;
    +  height: 18px;
    +  padding: 0 6px;
    +  border-radius: 999px;
    +  background: var(--accent);
    +  color: #051225;
    +  font-size: 11px;
    +  font-weight: 700;
    +  line-height: 1;
    +  display: inline-flex;
    +  align-items: center;
    +  justify-content: center;
    +  border: 1px solid rgba(255, 255, 255, 0.8);
    +  pointer-events: none;
    +  opacity: 0;
    +  transition: opacity 120ms ease;
    +}
    +
    +.history-badge.visible {
    +  opacity: 1;
    +}
    +
     .duet-bubble {
       position: absolute;
       max-width: 60%;
    diff --git a/web/e2e/history-badge.spec.ts b/web/e2e/history-badge.spec.ts
    index 24c5c44..3c01e4e 100644
    --- a/web/e2e/history-badge.spec.ts
    +++ b/web/e2e/history-badge.spec.ts
    @@ -1,7 +1,7 @@
     import { expect, test } from "@playwright/test";
     
     test.describe("History badge and bubble", () => {
    -  test("ellipsis bubble and badge track normal chat activity", async ({ page }) => {
    +  test("sent bubble and badge track normal chat activity", async ({ page }) => {
         await page.goto("/", { waitUntil: "networkidle" });
         const bubbleText = page.locator("#duet-user-bubble .bubble-text");
         await expect(bubbleText).toBeVisible({ timeout: 15000 });
    @@ -16,7 +16,7 @@ test.describe("History badge and bubble", () => {
         for (let i = 1; i <= 3; i += 1) {
           await input.fill(`message ${i}`);
           await sendBtn.evaluate((btn) => (btn as HTMLButtonElement).click());
    -      await expect(bubbleText).toHaveText("…", { timeout: 5000 });
    +      await expect(bubbleText).toHaveText("Sent", { timeout: 5000 });
         }
     
         await expect(badge).toHaveText("3", { timeout: 5000 });
    @@ -37,6 +37,6 @@ test.describe("History badge and bubble", () => {
         await sendBtn.evaluate((btn) => (btn as HTMLButtonElement).click());
         await expect(badge).toHaveText("1", { timeout: 5000 });
         await expect(badge).toHaveClass(/visible/, { timeout: 5000 });
    -    await expect(bubbleText).toHaveText("…", { timeout: 5000 });
    +    await expect(bubbleText).toHaveText("Sent", { timeout: 5000 });
       });
     });
    diff --git a/web/src/main.ts b/web/src/main.ts
    index b326ccf..c7a399e 100644
    --- a/web/src/main.ts
    +++ b/web/src/main.ts
    @@ -129,7 +129,8 @@ let onboardMenu: HTMLDivElement | null = null;
     const OVERLAY_ROOT_ID = "duet-overlay-root";
     const OVERLAY_ROOT_Z_INDEX = 2147483640;
     const ONBOARD_MENU_EDGE_MARGIN = 8;
    -const USER_BUBBLE_ELLIPSIS = "…";
    +const USER_BUBBLE_SENT_TEXT = "Sent";
    +const HISTORY_BADGE_DISPLAY_MAX = 99;
     const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
     let overlayRoot: HTMLDivElement | null = null;
     let onboardPressTimer: number | null = null;
    @@ -563,9 +564,9 @@ function updateDuetBubbles() {
         "Welcome — I’m Little Chef. To start onboarding, please fill out your preferences (allergies, likes/dislikes, servings, days).";
       const userFallback = "Press and hold to start onboarding with preferences.";
       setBubbleText(assistant, lastAssistant?.text ?? assistantFallback);
    -  const showEllipsis = userBubbleEllipsisActive && isNormalChatFlow();
    +  const showSentText = userBubbleEllipsisActive && isNormalChatFlow();
       const fallbackText = isNormalChatFlow() ? userFallback : lastUser?.text ?? userFallback;
    -  setBubbleText(user, showEllipsis ? USER_BUBBLE_ELLIPSIS : fallbackText);
    +  setBubbleText(user, showSentText ? USER_BUBBLE_SENT_TEXT : fallbackText);
     }
     
     function isNormalChatFlow() {
    @@ -785,7 +786,10 @@ function updateHistoryBadge() {
       const badge = ensureHistoryBadgeElement();
       if (!badge) return;
       if (historyBadgeCount > 0) {
    -    badge.textContent = historyBadgeCount.toString();
    +    badge.textContent =
    +      historyBadgeCount > HISTORY_BADGE_DISPLAY_MAX
    +        ? `${HISTORY_BADGE_DISPLAY_MAX}+`
    +        : historyBadgeCount.toString();
         badge.classList.add("visible");
         badge.setAttribute("aria-hidden", "false");
       } else {

## Verification
- python -m compileall . (pass)
- python -m pytest -q (pass)
- npm --prefix web run build (pass)
- npm --prefix web run test:e2e (pass)

## Notes (optional)
- TODO: blockers, risks, constraints.

## Next Steps
- Hold for Julius AUTHORIZED before committing.

