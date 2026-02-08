# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-08T03:10:51+00:00
- Branch: main
- HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
- BASE_HEAD: c843fd0e27b6e7e1ccc2d1bb065d36e597766401
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Added Dev Panel remember-me row (checkbox + duration selector) and helpers that ensure it sits next to the JWT controls.
- Persisted JWT/token, TTL, and checkbox state via localStorage and reapplied stored values during wire-up.
- Updated scripts/run_tests.ps1 so Playwright installs and runs the new e2e check automatically.

## Files Changed (staged)
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md
- scripts/run_tests.ps1
- web/e2e/dev-panel.spec.ts
- web/package-lock.json
- web/package.json
- web/playwright.config.ts
- web/src/main.ts

## git status -sb
    ## main...origin/main
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
    MM evidence/updatedifflog.md
    M  scripts/run_tests.ps1
    A  web/e2e/dev-panel.spec.ts
    M  web/package-lock.json
    M  web/package.json
    A  web/playwright.config.ts
    M  web/src/main.ts
    ?? temp_diff_run.ps1

## Minimal Diff Hunks
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    index 145cc85..7a24d01 100644
    --- a/evidence/test_runs.md
    +++ b/evidence/test_runs.md
    @@ -12112,3 +12112,194 @@ git unavailable
     git unavailable
     ```
     
    +## Test Run 2026-02-08T02:52:57Z
    +- Status: PASS
    +- Start: 2026-02-08T02:52:57Z
    +- End: 2026-02-08T02:53:06Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 73 passed in 2.86s
    +- git status -sb:
    +```
    +## main...origin/main
    +```
    +- git diff --stat:
    +```
    +
    +```
    +
    +## Test Run 2026-02-08T02:58:24Z
    +- Status: PASS
    +- Start: 2026-02-08T02:58:24Z
    +- End: 2026-02-08T02:58:56Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 73 passed in 3.45s
    +- git status -sb:
    +```
    +## main...origin/main
    + M evidence/test_runs.md
    + M evidence/test_runs_latest.md
    + M scripts/run_tests.ps1
    + M web/dist/main.js
    + M web/package-lock.json
    + M web/package.json
    +?? web/e2e/
    +?? web/playwright.config.ts
    +```
    +- git diff --stat:
    +```
    + evidence/test_runs.md        | 20 ++++++++++++++
    + evidence/test_runs_latest.md | 16 +++++------
    + scripts/run_tests.ps1        |  4 +++
    + web/package-lock.json        | 64 ++++++++++++++++++++++++++++++++++++++++++++
    + web/package.json             |  4 ++-
    + 5 files changed, 99 insertions(+), 9 deletions(-)
    +```
    +
    +## Test Run 2026-02-08T03:00:06Z
    +- Status: FAIL
    +- Start: 2026-02-08T03:00:06Z
    +- End: 2026-02-08T03:00:39Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 73 passed in 3.81s
    +- playwright test:e2e exit: 1
    +- playwright summary:     e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls 
    +- git status -sb:
    +```
    +## main...origin/main
    + M evidence/test_runs.md
    + M evidence/test_runs_latest.md
    + M scripts/run_tests.ps1
    + M web/dist/main.js
    + M web/package-lock.json
    + M web/package.json
    +?? web/e2e/
    +?? web/playwright.config.ts
    +?? web/test-results/
    +```
    +- git diff --stat:
    +```
    + evidence/test_runs.md        | 53 ++++++++++++++++++++++++++++++++++++
    + evidence/test_runs_latest.md | 29 ++++++++++++++------
    + scripts/run_tests.ps1        | 35 +++++++++++++++++++++++-
    + web/package-lock.json        | 64 ++++++++++++++++++++++++++++++++++++++++++++
    + web/package.json             |  4 ++-
    + 5 files changed, 175 insertions(+), 10 deletions(-)
    +```
    +- Failure payload:
    +```
    +=== playwright test:e2e (exit 1) ===
    +
    +> little-chef-web@0.1.0 test:e2e
    +> playwright test --config ./playwright.config.ts
    +
    +
    +Running 1 test using 1 worker
    +
    +  x  1 e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls (17.0s)
    +
    +
    +  1) e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls 
    +
    +    Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed
    +
    +    Locator: locator('#dev-jwt-remember')
    +    Expected: visible
    +    Timeout: 15000ms
    +    Error: element(s) not found
    +
    +    Call log:
    +    [2m  - Expect "toBeVisible" with timeout 15000ms[22m
    +    [2m  - waiting for locator('#dev-jwt-remember')[22m
    +
    +
    +      32 |     await devPanelItem.click();
    +      33 |     const rememberCheckbox = page.locator('#dev-jwt-remember');
    +    > 34 |     await expect(rememberCheckbox).toBeVisible({ timeout: 15000 });
    +         |                                    ^
    +      35 |     const authButton = page.locator('#btn-auth');
    +      36 |     await expect(authButton).toBeVisible({ timeout: 15000 });
    +      37 |     const card = authButton.locator('xpath=ancestor::section[contains(@class,"card")]');
    +        at Z:\LittleChef\web\e2e\dev-panel.spec.ts:34:36
    +
    +    attachment #1: screenshot (image/png) ──────────────────────────────────────────────────────────
    +    test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\test-failed-1.png
    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +
    +    attachment #2: browser-console (text/plain) ────────────────────────────────────────────────────
    +    (no console messages)
    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +
    +    attachment #3: dev-card-html (text/html) ───────────────────────────────────────────────────────
    +    <section class="card legacy-card">
    +          <h1>Little Chef</h1>
    +          <p>Paste JWT, then try chat, prefs, mealplan, and shopping diff.</p>
    +          <label>JWT <input id="jwt" type="text" placeholder="Bearer token"></label>
    +          <button id="btn-auth">Auth /auth/me</button>
    +          <pre id="auth-out"></pre>...
    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +
    +    attachment #5: video (video/webm) ──────────────────────────────────────────────────────────────
    +    test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\video.webm
    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +
    +    Error Context: test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\error-context.md
    +
    +    attachment #7: trace (application/zip) ─────────────────────────────────────────────────────────
    +    test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\trace.zip
    +    Usage:
    +
    +        npx playwright show-trace test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\trace.zip
    +
    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +
    +  1 failed
    +    e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls
    +```
    +
    +## Test Run 2026-02-08T03:09:34Z
    +- Status: PASS
    +- Start: 2026-02-08T03:09:34Z
    +- End: 2026-02-08T03:09:50Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 73 passed in 3.57s
    +- playwright test:e2e exit: 0
    +- playwright summary:   1 passed (3.0s)
    +- git status -sb:
    +```
    +## main...origin/main
    +M  evidence/test_runs.md
    +M  evidence/test_runs_latest.md
    +M  evidence/updatedifflog.md
    +M  scripts/run_tests.ps1
    +A  web/e2e/dev-panel.spec.ts
    +M  web/package-lock.json
    +M  web/package.json
    +A  web/playwright.config.ts
    + M web/src/main.ts
    +```
    +- git diff --stat:
    +```
    + web/src/main.ts | 154 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    + 1 file changed, 154 insertions(+)
    +```
    +
    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    index ce5c49b..88fee17 100644
    --- a/evidence/test_runs_latest.md
    +++ b/evidence/test_runs_latest.md
    @@ -1,19 +1,31 @@
    -﻿Status: PASS
    -Start: 2026-02-08T00:41:35Z
    -End: 2026-02-08T00:41:43Z
    -Branch: git unavailable
    -HEAD: git unavailable
    +Status: PASS
    +Start: 2026-02-08T03:09:34Z
    +End: 2026-02-08T03:09:50Z
    +Branch: main
    +HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
     compileall exit: 0
     import app.main exit: 0
     pytest exit: 0
    -pytest summary: 73 passed in 2.70s
    +pytest summary: 73 passed in 3.57s
    +playwright test:e2e exit: 0
    +playwright summary:   1 passed (3.0s)
     git status -sb:
     ```
    -git unavailable
    +## main...origin/main
    +M  evidence/test_runs.md
    +M  evidence/test_runs_latest.md
    +M  evidence/updatedifflog.md
    +M  scripts/run_tests.ps1
    +A  web/e2e/dev-panel.spec.ts
    +M  web/package-lock.json
    +M  web/package.json
    +A  web/playwright.config.ts
    + M web/src/main.ts
     ```
     git diff --stat:
     ```
    -git unavailable
    + web/src/main.ts | 154 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    + 1 file changed, 154 insertions(+)
     ```
     
    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    index 7134cc3..96563e7 100644
    --- a/evidence/updatedifflog.md
    +++ b/evidence/updatedifflog.md
    @@ -1,210 +1,609 @@
    -﻿# Diff Log (overwrite each cycle)
    +# Diff Log (overwrite each cycle)
     
     ## Cycle Metadata
    -- Timestamp: 2026-02-08T01:17:12+00:00
    +- Timestamp: 2026-02-08T03:02:48+00:00
     - Branch: main
    -- HEAD: c843fd0e27b6e7e1ccc2d1bb065d36e597766401
    -- BASE_HEAD: 3797435293716b050ac0545794e6bba04fac0a1b
    +- HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
    +- BASE_HEAD: c843fd0e27b6e7e1ccc2d1bb065d36e597766401
     - Diff basis: staged
     
     ## Cycle Status
     - Status: COMPLETE
     
     ## Summary
    -- Fixed overwrite_diff_log parameter parsing via named Bullets calls and ASCII hyphen TODO text.
    +- Added Playwright tooling (web/package.json, config) plus a web/e2e/dev-panel.spec.ts harness for the Dev Panel remember-row
    +- Updated scripts/run_tests.ps1 to install browsers, run playwright test:e2e, and log the failing checkbox evidence
     
     ## Files Changed (staged)
    -- evidence/updatedifflog.md
    -- scripts/overwrite_diff_log.ps1
    +- evidence/test_runs.md
    +- evidence/test_runs_latest.md
    +- scripts/run_tests.ps1
    +- web/e2e/dev-panel.spec.ts
    +- web/package-lock.json
    +- web/package.json
    +- web/playwright.config.ts
     
     ## git status -sb
         ## main...origin/main
    -    M  evidence/updatedifflog.md
    -    M  scripts/overwrite_diff_log.ps1
    -    ?? scripts/finalize_helper.ps1
    +    M  evidence/test_runs.md
    +    M  evidence/test_runs_latest.md
    +     M evidence/updatedifflog.md
    +    M  scripts/run_tests.ps1
    +    A  web/e2e/dev-panel.spec.ts
    +    M  web/package-lock.json
    +    M  web/package.json
    +    A  web/playwright.config.ts
    +    ?? temp_run_diff_log.ps1
     
     ## Minimal Diff Hunks
    -    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    -    index a1795ac..e6e5582 100644
    -    --- a/evidence/updatedifflog.md
    -    +++ b/evidence/updatedifflog.md
    -    @@ -1,114 +1,53 @@
    -     # Diff Log (overwrite each cycle)
    +    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    +    index 145cc85..47ed18a 100644
    +    --- a/evidence/test_runs.md
    +    +++ b/evidence/test_runs.md
    +    @@ -12112,3 +12112,162 @@ git unavailable
    +     git unavailable
    +     ```
          
    -     ## Cycle Metadata
    -    -- Timestamp: 2026-02-08T00:40:50+00:00
    -    +- Timestamp: 2026-02-08T01:14:18+00:00
    -     - Branch: main
    -    -- HEAD: 3797435293716b050ac0545794e6bba04fac0a1b
    -    -- BASE_HEAD: 0f6934a95a13fa81aaa413ba89b66ce76ae07500
    -    -- Diff basis: working tree
    -    +- HEAD: c843fd0e27b6e7e1ccc2d1bb065d36e597766401
    -    +- BASE_HEAD: 3797435293716b050ac0545794e6bba04fac0a1b
    -    +- Diff basis: staged
    -     
    -     ## Cycle Status
    -    -- Status: IN_PROCESS
    -    +- Status: COMPLETE
    +    +## Test Run 2026-02-08T02:52:57Z
    +    +- Status: PASS
    +    +- Start: 2026-02-08T02:52:57Z
    +    +- End: 2026-02-08T02:53:06Z
    +    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +    +- Branch: main
    +    +- HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
    +    +- compileall exit: 0
    +    +- import app.main exit: 0
    +    +- pytest exit: 0
    +    +- pytest summary: 73 passed in 2.86s
    +    +- git status -sb:
    +    +```
    +    +## main...origin/main
    +    +```
    +    +- git diff --stat:
    +    +```
    +    +
    +    +```
    +    +
    +    +## Test Run 2026-02-08T02:58:24Z
    +    +- Status: PASS
    +    +- Start: 2026-02-08T02:58:24Z
    +    +- End: 2026-02-08T02:58:56Z
    +    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +    +- Branch: main
    +    +- HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
    +    +- compileall exit: 0
    +    +- import app.main exit: 0
    +    +- pytest exit: 0
    +    +- pytest summary: 73 passed in 3.45s
    +    +- git status -sb:
    +    +```
    +    +## main...origin/main
    +    + M evidence/test_runs.md
    +    + M evidence/test_runs_latest.md
    +    + M scripts/run_tests.ps1
    +    + M web/dist/main.js
    +    + M web/package-lock.json
    +    + M web/package.json
    +    +?? web/e2e/
    +    +?? web/playwright.config.ts
    +    +```
    +    +- git diff --stat:
    +    +```
    +    + evidence/test_runs.md        | 20 ++++++++++++++
    +    + evidence/test_runs_latest.md | 16 +++++------
    +    + scripts/run_tests.ps1        |  4 +++
    +    + web/package-lock.json        | 64 ++++++++++++++++++++++++++++++++++++++++++++
    +    + web/package.json             |  4 ++-
    +    + 5 files changed, 99 insertions(+), 9 deletions(-)
    +    +```
    +    +
    +    +## Test Run 2026-02-08T03:00:06Z
    +    +- Status: FAIL
    +    +- Start: 2026-02-08T03:00:06Z
    +    +- End: 2026-02-08T03:00:39Z
    +    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +    +- Branch: main
    +    +- HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
    +    +- compileall exit: 0
    +    +- import app.main exit: 0
    +    +- pytest exit: 0
    +    +- pytest summary: 73 passed in 3.81s
    +    +- playwright test:e2e exit: 1
    +    +- playwright summary:     e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls 
    +    +- git status -sb:
    +    +```
    +    +## main...origin/main
    +    + M evidence/test_runs.md
    +    + M evidence/test_runs_latest.md
    +    + M scripts/run_tests.ps1
    +    + M web/dist/main.js
    +    + M web/package-lock.json
    +    + M web/package.json
    +    +?? web/e2e/
    +    +?? web/playwright.config.ts
    +    +?? web/test-results/
    +    +```
    +    +- git diff --stat:
    +    +```
    +    + evidence/test_runs.md        | 53 ++++++++++++++++++++++++++++++++++++
    +    + evidence/test_runs_latest.md | 29 ++++++++++++++------
    +    + scripts/run_tests.ps1        | 35 +++++++++++++++++++++++-
    +    + web/package-lock.json        | 64 ++++++++++++++++++++++++++++++++++++++++++++
    +    + web/package.json             |  4 ++-
    +    + 5 files changed, 175 insertions(+), 10 deletions(-)
    +    +```
    +    +- Failure payload:
    +    +```
    +    +=== playwright test:e2e (exit 1) ===
    +    +
    +    +> little-chef-web@0.1.0 test:e2e
    +    +> playwright test --config ./playwright.config.ts
    +    +
    +    +
    +    +Running 1 test using 1 worker
    +    +
    +    +  x  1 e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls (17.0s)
    +    +
    +    +
    +    +  1) e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls 
    +    +
    +    +    Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed
    +    +
    +    +    Locator: locator('#dev-jwt-remember')
    +    +    Expected: visible
    +    +    Timeout: 15000ms
    +    +    Error: element(s) not found
    +    +
    +    +    Call log:
    +    +    [2m  - Expect "toBeVisible" with timeout 15000ms[22m
    +    +    [2m  - waiting for locator('#dev-jwt-remember')[22m
    +    +
    +    +
    +    +      32 |     await devPanelItem.click();
    +    +      33 |     const rememberCheckbox = page.locator('#dev-jwt-remember');
    +    +    > 34 |     await expect(rememberCheckbox).toBeVisible({ timeout: 15000 });
    +    +         |                                    ^
    +    +      35 |     const authButton = page.locator('#btn-auth');
    +    +      36 |     await expect(authButton).toBeVisible({ timeout: 15000 });
    +    +      37 |     const card = authButton.locator('xpath=ancestor::section[contains(@class,"card")]');
    +    +        at Z:\LittleChef\web\e2e\dev-panel.spec.ts:34:36
    +    +
    +    +    attachment #1: screenshot (image/png) ──────────────────────────────────────────────────────────
    +    +    test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\test-failed-1.png
    +    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +    +
    +    +    attachment #2: browser-console (text/plain) ────────────────────────────────────────────────────
    +    +    (no console messages)
    +    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +    +
    +    +    attachment #3: dev-card-html (text/html) ───────────────────────────────────────────────────────
    +    +    <section class="card legacy-card">
    +    +          <h1>Little Chef</h1>
    +    +          <p>Paste JWT, then try chat, prefs, mealplan, and shopping diff.</p>
    +    +          <label>JWT <input id="jwt" type="text" placeholder="Bearer token"></label>
    +    +          <button id="btn-auth">Auth /auth/me</button>
    +    +          <pre id="auth-out"></pre>...
    +    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +    +
    +    +    attachment #5: video (video/webm) ──────────────────────────────────────────────────────────────
    +    +    test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\video.webm
    +    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +    +
    +    +    Error Context: test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\error-context.md
    +    +
    +    +    attachment #7: trace (application/zip) ─────────────────────────────────────────────────────────
    +    +    test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\trace.zip
    +    +    Usage:
    +    +
    +    +        npx playwright show-trace test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\trace.zip
    +    +
    +    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +    +
    +    +  1 failed
    +    +    e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls
    +    +```
    +    +
    +    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    +    index ce5c49b..a06ac30 100644
    +    --- a/evidence/test_runs_latest.md
    +    +++ b/evidence/test_runs_latest.md
    +    @@ -1,19 +1,107 @@
    +    -﻿Status: PASS
    +    -Start: 2026-02-08T00:41:35Z
    +    -End: 2026-02-08T00:41:43Z
    +    -Branch: git unavailable
    +    -HEAD: git unavailable
    +    +Status: FAIL
    +    +Start: 2026-02-08T03:00:06Z
    +    +End: 2026-02-08T03:00:39Z
    +    +Branch: main
    +    +HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
    +     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +     compileall exit: 0
    +     import app.main exit: 0
    +     pytest exit: 0
    +    -pytest summary: 73 passed in 2.70s
    +    +pytest summary: 73 passed in 3.81s
    +    +playwright test:e2e exit: 1
    +    +playwright summary:     e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls 
    +    +Failing tests:
    +    +(see console output)
    +    +Failure payload:
    +    +```
    +    +=== playwright test:e2e (exit 1) ===
    +    +
    +    +> little-chef-web@0.1.0 test:e2e
    +    +> playwright test --config ./playwright.config.ts
    +    +
    +    +
    +    +Running 1 test using 1 worker
    +    +
    +    +  x  1 e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls (17.0s)
    +    +
    +    +
    +    +  1) e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls 
    +    +
    +    +    Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed
    +    +
    +    +    Locator: locator('#dev-jwt-remember')
    +    +    Expected: visible
    +    +    Timeout: 15000ms
    +    +    Error: element(s) not found
    +    +
    +    +    Call log:
    +    +    [2m  - Expect "toBeVisible" with timeout 15000ms[22m
    +    +    [2m  - waiting for locator('#dev-jwt-remember')[22m
    +    +
    +    +
    +    +      32 |     await devPanelItem.click();
    +    +      33 |     const rememberCheckbox = page.locator('#dev-jwt-remember');
    +    +    > 34 |     await expect(rememberCheckbox).toBeVisible({ timeout: 15000 });
    +    +         |                                    ^
    +    +      35 |     const authButton = page.locator('#btn-auth');
    +    +      36 |     await expect(authButton).toBeVisible({ timeout: 15000 });
    +    +      37 |     const card = authButton.locator('xpath=ancestor::section[contains(@class,"card")]');
    +    +        at Z:\LittleChef\web\e2e\dev-panel.spec.ts:34:36
    +    +
    +    +    attachment #1: screenshot (image/png) ──────────────────────────────────────────────────────────
    +    +    test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\test-failed-1.png
    +    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +    +
    +    +    attachment #2: browser-console (text/plain) ────────────────────────────────────────────────────
    +    +    (no console messages)
    +    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +    +
    +    +    attachment #3: dev-card-html (text/html) ───────────────────────────────────────────────────────
    +    +    <section class="card legacy-card">
    +    +          <h1>Little Chef</h1>
    +    +          <p>Paste JWT, then try chat, prefs, mealplan, and shopping diff.</p>
    +    +          <label>JWT <input id="jwt" type="text" placeholder="Bearer token"></label>
    +    +          <button id="btn-auth">Auth /auth/me</button>
    +    +          <pre id="auth-out"></pre>...
    +    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +    +
    +    +    attachment #5: video (video/webm) ──────────────────────────────────────────────────────────────
    +    +    test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\video.webm
    +    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +    +
    +    +    Error Context: test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\error-context.md
    +    +
    +    +    attachment #7: trace (application/zip) ─────────────────────────────────────────────────────────
    +    +    test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\trace.zip
    +    +    Usage:
    +    +
    +    +        npx playwright show-trace test-results\dev-panel-Dev-Panel-rememb-e7c66-ckbox-near-the-JWT-controls\trace.zip
    +    +
    +    +    ────────────────────────────────────────────────────────────────────────────────────────────────
    +    +
    +    +  1 failed
    +    +    e2e\dev-panel.spec.ts:27:3 › Dev Panel remember row › renders remember-me checkbox near the JWT controls
    +    +```
    +     git status -sb:
    +     ```
    +    -git unavailable
    +    +## main...origin/main
    +    + M evidence/test_runs.md
    +    + M evidence/test_runs_latest.md
    +    + M scripts/run_tests.ps1
    +    + M web/dist/main.js
    +    + M web/package-lock.json
    +    + M web/package.json
    +    +?? web/e2e/
    +    +?? web/playwright.config.ts
    +    +?? web/test-results/
    +     ```
    +     git diff --stat:
    +     ```
    +    -git unavailable
    +    + evidence/test_runs.md        | 53 ++++++++++++++++++++++++++++++++++++
    +    + evidence/test_runs_latest.md | 29 ++++++++++++++------
    +    + scripts/run_tests.ps1        | 35 +++++++++++++++++++++++-
    +    + web/package-lock.json        | 64 ++++++++++++++++++++++++++++++++++++++++++++
    +    + web/package.json             |  4 ++-
    +    + 5 files changed, 175 insertions(+), 10 deletions(-)
    +     ```
          
    -     ## Summary
    -    -- Tightened clause parsing: segments now break on uncertainty markers, anchor clamping avoids bread/milk/egg joins, and clause-specific attachments keep weights/dates tied to the right action.
    -    -- Hardened the normalization filter/fixtures (long cupboard/fridge regression) so junk tokens like "maybe" or "total" never surface, and new tests guard the expected items/notes.
    -    -- Eliminated the dependency warnings by providing a repo-level multipart shim that delegates to python-multipart, adding a pytest.ini filter, and registering the httpx warning suppression in tests/conftest.py.
    -    +- Fixed `scripts/overwrite_diff_log.ps1` so the Bullets helper uses named arguments and ASCII TODO text, which prevents the `Missing argument in parameter list` error on older helper invocations.
    +    diff --git a/scripts/run_tests.ps1 b/scripts/run_tests.ps1
    +    index f8078a1..3fa2aa1 100644
    +    --- a/scripts/run_tests.ps1
    +    +++ b/scripts/run_tests.ps1
    +    @@ -55,6 +55,8 @@ function Append-TestRunLog(
    +       [int]$importExit,
    +       [int]$pytestExit,
    +       [string]$pytestSummary,
    +    +  [int]$playwrightTestExit,
    +    +  [string]$playwrightTestSummary,
    +       [string]$gitBranch,
    +       [string]$gitHead,
    +       [string]$gitStatus,
    +    @@ -77,6 +79,8 @@ function Append-TestRunLog(
    +       $lines += "- import app.main exit: $importExit"
    +       $lines += "- pytest exit: $pytestExit"
    +       $lines += "- pytest summary: $pytestSummary"
    +    +  $lines += "- playwright test:e2e exit: $playwrightTestExit"
    +    +  $lines += "- playwright summary: $playwrightTestSummary"
    +       $lines += "- git status -sb:"
    +       $lines += '```'
    +       $lines += $gitStatus
    +    @@ -106,6 +110,8 @@ function Write-TestRunLatest(
    +       [int]$importExit,
    +       [int]$pytestExit,
    +       [string]$pytestSummary,
    +    +  [int]$playwrightTestExit,
    +    +  [string]$playwrightTestSummary,
    +       [string]$failingTests,
    +       [string]$gitBranch,
    +       [string]$gitHead,
    +    @@ -128,6 +134,8 @@ function Write-TestRunLatest(
    +       $lines += "import app.main exit: $importExit"
    +       $lines += "pytest exit: $pytestExit"
    +       $lines += "pytest summary: $pytestSummary"
    +    +  $lines += "playwright test:e2e exit: $playwrightTestExit"
    +    +  $lines += "playwright summary: $playwrightTestSummary"
    +       if ($statusText -eq "FAIL") {
    +         $lines += "Failing tests:"
    +         if ($failingTests) {
    +    @@ -169,6 +177,10 @@ $pytestSummary = "(not run)"
    +     $statusText = "FAIL"
    +     $failingTests = ""
    +     $failurePayload = ""
    +    +$playwrightInstallExit = -1
    +    +$playwrightTestExit = -1
    +    +$playwrightTestSummary = "(not run)"
    +    +$playwrightLines = @()
          
    -    -## Files Changed
    -    -- app/services/inventory_agent.py
    -    -- tests/test_inventory_agent.py
    -    -- tests/conftest.py
    -    -- multipart/__init__.py
    -    -- multipart/multipart.py
    -    -- pytest.ini
    -    -- evidence/test_runs.md
    -    -- evidence/test_runs_latest.md
    -    +## Files Changed (staged)
    -     - evidence/updatedifflog.md
    -    +- scripts/overwrite_diff_log.ps1
    +     $gitBranch = "git unavailable"
    +     $gitHead = "git unavailable"
    +    @@ -215,11 +227,26 @@ try {
    +       & npm --prefix web run build
    +       Info "node scripts/ui_proposal_renderer_test.mjs"
    +       & node "$PSScriptRoot\ui_proposal_renderer_test.mjs"
    +    +  Info "npm --prefix web exec playwright install --with-deps"
    +    +  & npm --prefix web exec playwright install --with-deps
    +    +  $playwrightInstallExit = $LASTEXITCODE
    +    +  if ($playwrightInstallExit -ne 0) { Err "playwright install failed ($playwrightInstallExit)" }
    +    +  Info "npm --prefix web run test:e2e"
    +    +  $playwrightLines = & npm --prefix web run test:e2e 2>&1
    +    +  $playwrightTestExit = $LASTEXITCODE
    +    +  if ($playwrightLines) { $playwrightLines | ForEach-Object { Write-Host $_ } }
    +    +  $nonEmptyPlaywright = $playwrightLines | Where-Object { $_ -and $_.Trim().Length -gt 0 }
    +    +  if ($nonEmptyPlaywright.Count -gt 0) { $playwrightTestSummary = $nonEmptyPlaywright[-1] }
    +    +  if ($playwrightTestExit -eq 0) {
    +    +    Info "playwright test:e2e: ok"
    +    +  } else {
    +    +    Err "playwright test:e2e failed ($playwrightTestExit)"
    +    +  }
    +     }
    +     finally {
    +       $endUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    +       $overall = 0
    +    -  foreach ($code in @($compileExit, $importExit, $pytestExit)) {
    +    +  foreach ($code in @($compileExit, $importExit, $pytestExit, $playwrightTestExit)) {
    +         if ($code -ne 0) { $overall = 1 }
    +       }
    +       if ($overall -eq 0) { $statusText = "PASS" } else { $statusText = "FAIL" }
    +    @@ -238,16 +265,22 @@ finally {
    +           $sections += @("=== pytest (exit $pytestExit) ===")
    +           $sections += (Tail-Lines $pytestLines 200)
    +         }
    +    +    if ($playwrightTestExit -ne 0) {
    +    +      $sections += @("=== playwright test:e2e (exit $playwrightTestExit) ===")
    +    +      $sections += (Tail-Lines $playwrightLines 200)
    +    +    }
    +         $failurePayload = ($sections -join "`n").Trim()
    +       }
          
    -     ## git status -sb
    -    -```
    -    -## main...origin/main [ahead 1]
    -    -MM app/services/inventory_agent.py
    -    -MM evidence/test_runs.md
    -    -MM evidence/test_runs_latest.md
    -    -MM evidence/updatedifflog.md
    -    -M  tests/conftest.py
    -    -MM tests/test_inventory_agent.py
    -    -?? multipart/
    -    -?? pytest.ini
    -    -```
    -    +    ## main...origin/main
    -    +    M  evidence/updatedifflog.md
    -    +    M  scripts/overwrite_diff_log.ps1
    +       Append-TestRunLog -root $root -statusText $statusText -pythonPath $py -startUtc $startUtc -endUtc $endUtc `
    +         -compileExit $compileExit -importExit $importExit -pytestExit $pytestExit -pytestSummary $pytestSummary `
    +    +    -playwrightTestExit $playwrightTestExit -playwrightTestSummary $playwrightTestSummary `
    +         -gitBranch $gitBranch -gitHead $gitHead -gitStatus ($gitStatus -join "`n") -gitDiffStat ($gitDiffStat -join "`n") `
    +         -failurePayload $failurePayload
          
    -     ## Minimal Diff Hunks
    -    -    diff --git a/app/services/inventory_agent.py b/app/services/inventory_agent.py
    -    -    @@
    -    -                 next_match_start = (
    -    -                     matches[idx + 1].start() if idx + 1 < len(matches) else sentence_end
    -    -                 )
    -    -                 general_use_by_data = self._find_general_use_by_after(
    -    -                     lower, match.end(), sentence_end
    -    -                 )
    -    -                 general_use_by: Optional[str] = None
    -    -                 if general_use_by_data:
    -    -                     general_use_by, general_use_by_start = general_use_by_data
    -    -                     if general_use_by_start >= next_match_start:
    -    -                         general_use_by = None
    -    -                 clause_text = lower[start:end]
    -    -                 if self._is_chatter_clause(clause_text):
    -    -                     continue
    -    -             clause_key = (start, end)
    -    -             if measurement_note and existing_index is not None:
    -    -                 self._add_note_value(actions[existing_index], measurement_note)
    -    -                 if use_by_ord:
    -    -                     self._add_note_value(
    -    -                         actions[existing_index], f"use_by={use_by_ord}"
    -    -                     )
    -    -                 elif general_use_by:
    -    -                     self._add_note_value(
    -    -                         actions[existing_index], f"use_by={general_use_by}"
    -    -                     )
    -    -                 clause_action_index[clause_key] = existing_index
    -    -                 continue
    -    -    diff --git a/tests/conftest.py b/tests/conftest.py
    -    -    @@
    -    --import warnings
    -    --
    -    --warnings.filterwarnings(
    -    --    "ignore",
    -    --    message=".*'app' shortcut is now deprecated.*",
    -    --    category=DeprecationWarning,
    -    --)
    -    --import pytest
    -    -+import warnings
    -    -+
    -    -+warnings.filterwarnings(
    -    -+    "ignore",
    -    -+    message=".*'app' shortcut is now deprecated.*",
    -    -+    category=DeprecationWarning,
    -    -+)
    -    -+import pytest
    -    -    diff --git a/multipart/__init__.py b/multipart/__init__.py
    -    -    @@
    -    --from python_multipart import *
    -    -+from python_multipart import *
    -    -+from python_multipart import __all__, __author__, __copyright__, __license__, __version__
    -    -    diff --git a/multipart/multipart.py b/multipart/multipart.py
    -    -    @@
    -    --from python_multipart.multipart import parse_options_header
    -    -+from python_multipart.multipart import parse_options_header
    -    -+__all__ = ["parse_options_header"]
    -    -    diff --git a/pytest.ini b/pytest.ini
    -    -    @@
    -    --[pytest]
    -    --filterwarnings =
    -    --    ignore:The 'app' shortcut is now deprecated.*:DeprecationWarning
    -    -+[pytest]
    -    -+filterwarnings =
    -    -+    ignore:The 'app' shortcut is now deprecated.*:DeprecationWarning
    -    +    diff --git a/scripts/overwrite_diff_log.ps1 b/scripts/overwrite_diff_log.ps1
    -    +    index 6601279..0b2affe 100644
    -    +    --- a/scripts/overwrite_diff_log.ps1
    -    +    +++ b/scripts/overwrite_diff_log.ps1
    -    +    @@ -135,9 +135,12 @@ try {
    -    +         Warn "If you truly want unstaged, re-run with -IncludeUnstaged."
    -    +       }
    -    +
    -    +    -  $summaryLines = Bullets $Summary "TODO: 1–5 bullets (what changed, why, scope)."
    -    +    -  $verificationLines = Bullets $Verification "TODO: verification evidence (static -> runtime -> behavior -> contract)."
    -    +    -  $nextStepsLines = Bullets $NextSteps "TODO: next actions (small, specific)."
    -    +    +  $summaryTodo = "TODO: 1-5 bullets (what changed, why, scope)."
    -    +    +  $verificationTodo = "TODO: verification evidence (static -> runtime -> behavior -> contract)."
    -    +    +  $nextStepsTodo = "TODO: next actions (small, specific)."
    -    +    +  $summaryLines = Bullets -items $Summary -todo $summaryTodo
    -    +    +  $verificationLines = Bullets -items $Verification -todo $verificationTodo
    -    +    +  $nextStepsLines = Bullets -items $NextSteps -todo $nextStepsTodo
    -    +
    -    +       $filesLines = if ($changedFiles.Count -gt 0) { @($changedFiles | ForEach-Object { "- $_" }) } else { @("- (none detected)") }
    +       Write-TestRunLatest -root $root -statusText $statusText -pythonPath $py -startUtc $startUtc -endUtc $endUtc `
    +         -compileExit $compileExit -importExit $importExit -pytestExit $pytestExit -pytestSummary $pytestSummary `
    +    +    -playwrightTestExit $playwrightTestExit -playwrightTestSummary $playwrightTestSummary `
    +         -failingTests $failingTests -gitBranch $gitBranch -gitHead $gitHead -gitStatus ($gitStatus -join "`n") -gitDiffStat ($gitDiffStat -join "`n") `
    +         -failurePayload $failurePayload
          
    -     ## Verification
    -    -- compileall -> `python -m compileall .` (pass)
    -    -- behavior -> `python -m pytest -q` (pass, 73 passed, 0 warnings)
    -    +- .\scripts\overwrite_diff_log.ps1 -Status IN_PROCESS (dry run): pass
    +    diff --git a/web/e2e/dev-panel.spec.ts b/web/e2e/dev-panel.spec.ts
    +    new file mode 100644
    +    index 0000000..2c34c62
    +    --- /dev/null
    +    +++ b/web/e2e/dev-panel.spec.ts
    +    @@ -0,0 +1,40 @@
    +    +import { test, expect } from '@playwright/test';
         +
    -    +## Notes (optional)
    -    +- TODO: blockers, risks, constraints.
    -     
    -     ## Next Steps
    -    -- Stage the worked files listed above, capture `git status -sb` / `git diff --staged --stat`, and pause for Julius to issue `AUTHORIZED` before committing.
    -    +- Awaiting reapply of the inventory STT WIP stash once this helper fix lands.
    -    diff --git a/scripts/overwrite_diff_log.ps1 b/scripts/overwrite_diff_log.ps1
    -    index 6601279..0b2affe 100644
    -    --- a/scripts/overwrite_diff_log.ps1
    -    +++ b/scripts/overwrite_diff_log.ps1
    -    @@ -135,9 +135,12 @@ try {
    -         Warn "If you truly want unstaged, re-run with -IncludeUnstaged."
    +    +test.describe('Dev Panel remember row', () => {
    +    +  let consoleMessages: string[] = [];
    +    +
    +    +  test.beforeEach(async ({ page }) => {
    +    +    consoleMessages = [];
    +    +    page.on('console', (message) => consoleMessages.push(`[${message.type()}] ${message.text()}`));
    +    +  });
    +    +
    +    +  test.afterEach(async ({ page }, testInfo) => {
    +    +    if (testInfo.status !== testInfo.expectedStatus) {
    +    +      const logs = consoleMessages.length ? consoleMessages.join('\n') : '(no console messages)';
    +    +      await testInfo.attach('browser-console', { body: logs, contentType: 'text/plain' });
    +    +      const card = page.locator('section.card.legacy-card:has(#btn-auth)').first();
    +    +      if (await card.count()) {
    +    +        const html = await card.evaluate((node) => (node as HTMLElement)?.outerHTML ?? '');
    +    +        await testInfo.attach('dev-card-html', { body: html, contentType: 'text/html' });
    +    +      }
    +    +      await testInfo.attach('full-page-screenshot', {
    +    +        body: await page.screenshot({ fullPage: true }),
    +    +        contentType: 'image/png',
    +    +      });
    +    +    }
    +    +  });
    +    +
    +    +  test('renders remember-me checkbox near the JWT controls', async ({ page }) => {
    +    +    await page.goto('/', { waitUntil: 'networkidle' });
    +    +    await page.locator('#flow-menu-trigger').click();
    +    +    const devPanelItem = page.locator('.flow-menu-dropdown .flow-menu-item', { hasText: 'Dev Panel' });
    +    +    await expect(devPanelItem).toBeVisible({ timeout: 10000 });
    +    +    await devPanelItem.click();
    +    +    const rememberCheckbox = page.locator('#dev-jwt-remember');
    +    +    await expect(rememberCheckbox).toBeVisible({ timeout: 15000 });
    +    +    const authButton = page.locator('#btn-auth');
    +    +    await expect(authButton).toBeVisible({ timeout: 15000 });
    +    +    const card = authButton.locator('xpath=ancestor::section[contains(@class,"card")]');
    +    +    await expect(card.locator('#dev-jwt-remember')).toHaveCount(1);
    +    +  });
    +    +});
    +    diff --git a/web/package-lock.json b/web/package-lock.json
    +    index 394bcb3..10cc4fa 100644
    +    --- a/web/package-lock.json
    +    +++ b/web/package-lock.json
    +    @@ -8,9 +8,73 @@
    +           "name": "little-chef-web",
    +           "version": "0.1.0",
    +           "devDependencies": {
    +    +        "@playwright/test": "^1.44.0",
    +             "typescript": "^5.4.0"
    +           }
    +         },
    +    +    "node_modules/@playwright/test": {
    +    +      "version": "1.58.2",
    +    +      "resolved": "https://registry.npmjs.org/@playwright/test/-/test-1.58.2.tgz",
    +    +      "integrity": "sha512-akea+6bHYBBfA9uQqSYmlJXn61cTa+jbO87xVLCWbTqbWadRVmhxlXATaOjOgcBaWU4ePo0wB41KMFv3o35IXA==",
    +    +      "dev": true,
    +    +      "license": "Apache-2.0",
    +    +      "dependencies": {
    +    +        "playwright": "1.58.2"
    +    +      },
    +    +      "bin": {
    +    +        "playwright": "cli.js"
    +    +      },
    +    +      "engines": {
    +    +        "node": ">=18"
    +    +      }
    +    +    },
    +    +    "node_modules/fsevents": {
    +    +      "version": "2.3.2",
    +    +      "resolved": "https://registry.npmjs.org/fsevents/-/fsevents-2.3.2.tgz",
    +    +      "integrity": "sha512-xiqMQR4xAeHTuB9uWm+fFRcIOgKBMiOBP+eXiyT7jsgVCq1bkVygt00oASowB7EdtpOHaaPgKt812P9ab+DDKA==",
    +    +      "dev": true,
    +    +      "hasInstallScript": true,
    +    +      "license": "MIT",
    +    +      "optional": true,
    +    +      "os": [
    +    +        "darwin"
    +    +      ],
    +    +      "engines": {
    +    +        "node": "^8.16.0 || ^10.6.0 || >=11.0.0"
    +    +      }
    +    +    },
    +    +    "node_modules/playwright": {
    +    +      "version": "1.58.2",
    +    +      "resolved": "https://registry.npmjs.org/playwright/-/playwright-1.58.2.tgz",
    +    +      "integrity": "sha512-vA30H8Nvkq/cPBnNw4Q8TWz1EJyqgpuinBcHET0YVJVFldr8JDNiU9LaWAE1KqSkRYazuaBhTpB5ZzShOezQ6A==",
    +    +      "dev": true,
    +    +      "license": "Apache-2.0",
    +    +      "dependencies": {
    +    +        "playwright-core": "1.58.2"
    +    +      },
    +    +      "bin": {
    +    +        "playwright": "cli.js"
    +    +      },
    +    +      "engines": {
    +    +        "node": ">=18"
    +    +      },
    +    +      "optionalDependencies": {
    +    +        "fsevents": "2.3.2"
    +    +      }
    +    +    },
    +    +    "node_modules/playwright-core": {
    +    +      "version": "1.58.2",
    +    +      "resolved": "https://registry.npmjs.org/playwright-core/-/playwright-core-1.58.2.tgz",
    +    +      "integrity": "sha512-yZkEtftgwS8CsfYo7nm0KE8jsvm6i/PTgVtB8DL726wNf6H2IMsDuxCpJj59KDaxCtSnrWan2AeDqM7JBaultg==",
    +    +      "dev": true,
    +    +      "license": "Apache-2.0",
    +    +      "bin": {
    +    +        "playwright-core": "cli.js"
    +    +      },
    +    +      "engines": {
    +    +        "node": ">=18"
    +    +      }
    +    +    },
    +         "node_modules/typescript": {
    +           "version": "5.9.3",
    +           "resolved": "https://registry.npmjs.org/typescript/-/typescript-5.9.3.tgz",
    +    diff --git a/web/package.json b/web/package.json
    +    index ef37844..f22d8d7 100644
    +    --- a/web/package.json
    +    +++ b/web/package.json
    +    @@ -3,9 +3,11 @@
    +       "version": "0.1.0",
    +       "type": "module",
    +       "scripts": {
    +    -    "build": "tsc -p tsconfig.json"
    +    +    "build": "tsc -p tsconfig.json",
    +    +    "test:e2e": "playwright test --config ./playwright.config.ts"
    +       },
    +       "devDependencies": {
    +    +    "@playwright/test": "^1.44.0",
    +         "typescript": "^5.4.0"
            }
    -     
    -    -  $summaryLines = Bullets $Summary "TODO: 1–5 bullets (what changed, why, scope)."
    -    -  $verificationLines = Bullets $Verification "TODO: verification evidence (static -> runtime -> behavior -> contract)."
    -    -  $nextStepsLines = Bullets $NextSteps "TODO: next actions (small, specific)."
    -    +  $summaryTodo = "TODO: 1-5 bullets (what changed, why, scope)."
    -    +  $verificationTodo = "TODO: verification evidence (static -> runtime -> behavior -> contract)."
    -    +  $nextStepsTodo = "TODO: next actions (small, specific)."
    -    +  $summaryLines = Bullets -items $Summary -todo $summaryTodo
    -    +  $verificationLines = Bullets -items $Verification -todo $verificationTodo
    -    +  $nextStepsLines = Bullets -items $NextSteps -todo $nextStepsTodo
    -     
    -       $filesLines = if ($changedFiles.Count -gt 0) { @($changedFiles | ForEach-Object { "- $_" }) } else { @("- (none detected)") }
    -     
    +     }
    +    diff --git a/web/playwright.config.ts b/web/playwright.config.ts
    +    new file mode 100644
    +    index 0000000..4129891
    +    --- /dev/null
    +    +++ b/web/playwright.config.ts
    +    @@ -0,0 +1,22 @@
    +    +import { defineConfig } from "@playwright/test";
    +    +
    +    +const reuseServer = process.env.CI ? false : true;
    +    +
    +    +export default defineConfig({
    +    +  testDir: "./e2e",
    +    +  timeout: 60000,
    +    +  use: {
    +    +    baseURL: "http://127.0.0.1:8000",
    +    +    actionTimeout: 15000,
    +    +    navigationTimeout: 30000,
    +    +    trace: "retain-on-failure",
    +    +    screenshot: "only-on-failure",
    +    +    video: "retain-on-failure",
    +    +  },
    +    +  webServer: {
    +    +    command: "pwsh -NoProfile -File ..\\scripts\\run_local.ps1 -NoOpen -NoReload -NoInstall",
    +    +    port: 8000,
    +    +    reuseExistingServer: reuseServer,
    +    +    timeout: 120000,
    +    +  },
    +    +});
     
     ## Verification
    -- .\scripts\overwrite_diff_log.ps1 -Status IN_PROCESS (dry run): pass
    +- python -m compileall app (pass)
    +- python -c "import app.main" (pass)
    +- python -m pytest -q (pass)
    +- scripts/run_tests.ps1 (FAIL: #dev-jwt-remember missing, screenshot + trace captured)
     
     ## Notes (optional)
    -- TODO: blockers, risks, constraints.
    +- Playwright harness captured screenshot/trace for the missing `#dev-jwt-remember` row; follow-up fix should address that DOM hole before rerunning the suite.
     
     ## Next Steps
    -- Awaiting reapply of inventory STT WIP stash once helper fix lands.
    +- Fix Dev Panel so #dev-jwt-remember renders beside the auth controls and rerun scripts/run_tests.ps1 until the e2e check passes
     
    diff --git a/scripts/run_tests.ps1 b/scripts/run_tests.ps1
    index f8078a1..3fa2aa1 100644
    --- a/scripts/run_tests.ps1
    +++ b/scripts/run_tests.ps1
    @@ -55,6 +55,8 @@ function Append-TestRunLog(
       [int]$importExit,
       [int]$pytestExit,
       [string]$pytestSummary,
    +  [int]$playwrightTestExit,
    +  [string]$playwrightTestSummary,
       [string]$gitBranch,
       [string]$gitHead,
       [string]$gitStatus,
    @@ -77,6 +79,8 @@ function Append-TestRunLog(
       $lines += "- import app.main exit: $importExit"
       $lines += "- pytest exit: $pytestExit"
       $lines += "- pytest summary: $pytestSummary"
    +  $lines += "- playwright test:e2e exit: $playwrightTestExit"
    +  $lines += "- playwright summary: $playwrightTestSummary"
       $lines += "- git status -sb:"
       $lines += '```'
       $lines += $gitStatus
    @@ -106,6 +110,8 @@ function Write-TestRunLatest(
       [int]$importExit,
       [int]$pytestExit,
       [string]$pytestSummary,
    +  [int]$playwrightTestExit,
    +  [string]$playwrightTestSummary,
       [string]$failingTests,
       [string]$gitBranch,
       [string]$gitHead,
    @@ -128,6 +134,8 @@ function Write-TestRunLatest(
       $lines += "import app.main exit: $importExit"
       $lines += "pytest exit: $pytestExit"
       $lines += "pytest summary: $pytestSummary"
    +  $lines += "playwright test:e2e exit: $playwrightTestExit"
    +  $lines += "playwright summary: $playwrightTestSummary"
       if ($statusText -eq "FAIL") {
         $lines += "Failing tests:"
         if ($failingTests) {
    @@ -169,6 +177,10 @@ $pytestSummary = "(not run)"
     $statusText = "FAIL"
     $failingTests = ""
     $failurePayload = ""
    +$playwrightInstallExit = -1
    +$playwrightTestExit = -1
    +$playwrightTestSummary = "(not run)"
    +$playwrightLines = @()
     
     $gitBranch = "git unavailable"
     $gitHead = "git unavailable"
    @@ -215,11 +227,26 @@ try {
       & npm --prefix web run build
       Info "node scripts/ui_proposal_renderer_test.mjs"
       & node "$PSScriptRoot\ui_proposal_renderer_test.mjs"
    +  Info "npm --prefix web exec playwright install --with-deps"
    +  & npm --prefix web exec playwright install --with-deps
    +  $playwrightInstallExit = $LASTEXITCODE
    +  if ($playwrightInstallExit -ne 0) { Err "playwright install failed ($playwrightInstallExit)" }
    +  Info "npm --prefix web run test:e2e"
    +  $playwrightLines = & npm --prefix web run test:e2e 2>&1
    +  $playwrightTestExit = $LASTEXITCODE
    +  if ($playwrightLines) { $playwrightLines | ForEach-Object { Write-Host $_ } }
    +  $nonEmptyPlaywright = $playwrightLines | Where-Object { $_ -and $_.Trim().Length -gt 0 }
    +  if ($nonEmptyPlaywright.Count -gt 0) { $playwrightTestSummary = $nonEmptyPlaywright[-1] }
    +  if ($playwrightTestExit -eq 0) {
    +    Info "playwright test:e2e: ok"
    +  } else {
    +    Err "playwright test:e2e failed ($playwrightTestExit)"
    +  }
     }
     finally {
       $endUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
       $overall = 0
    -  foreach ($code in @($compileExit, $importExit, $pytestExit)) {
    +  foreach ($code in @($compileExit, $importExit, $pytestExit, $playwrightTestExit)) {
         if ($code -ne 0) { $overall = 1 }
       }
       if ($overall -eq 0) { $statusText = "PASS" } else { $statusText = "FAIL" }
    @@ -238,16 +265,22 @@ finally {
           $sections += @("=== pytest (exit $pytestExit) ===")
           $sections += (Tail-Lines $pytestLines 200)
         }
    +    if ($playwrightTestExit -ne 0) {
    +      $sections += @("=== playwright test:e2e (exit $playwrightTestExit) ===")
    +      $sections += (Tail-Lines $playwrightLines 200)
    +    }
         $failurePayload = ($sections -join "`n").Trim()
       }
     
       Append-TestRunLog -root $root -statusText $statusText -pythonPath $py -startUtc $startUtc -endUtc $endUtc `
         -compileExit $compileExit -importExit $importExit -pytestExit $pytestExit -pytestSummary $pytestSummary `
    +    -playwrightTestExit $playwrightTestExit -playwrightTestSummary $playwrightTestSummary `
         -gitBranch $gitBranch -gitHead $gitHead -gitStatus ($gitStatus -join "`n") -gitDiffStat ($gitDiffStat -join "`n") `
         -failurePayload $failurePayload
     
       Write-TestRunLatest -root $root -statusText $statusText -pythonPath $py -startUtc $startUtc -endUtc $endUtc `
         -compileExit $compileExit -importExit $importExit -pytestExit $pytestExit -pytestSummary $pytestSummary `
    +    -playwrightTestExit $playwrightTestExit -playwrightTestSummary $playwrightTestSummary `
         -failingTests $failingTests -gitBranch $gitBranch -gitHead $gitHead -gitStatus ($gitStatus -join "`n") -gitDiffStat ($gitDiffStat -join "`n") `
         -failurePayload $failurePayload
     
    diff --git a/web/e2e/dev-panel.spec.ts b/web/e2e/dev-panel.spec.ts
    new file mode 100644
    index 0000000..2c34c62
    --- /dev/null
    +++ b/web/e2e/dev-panel.spec.ts
    @@ -0,0 +1,40 @@
    +import { test, expect } from '@playwright/test';
    +
    +test.describe('Dev Panel remember row', () => {
    +  let consoleMessages: string[] = [];
    +
    +  test.beforeEach(async ({ page }) => {
    +    consoleMessages = [];
    +    page.on('console', (message) => consoleMessages.push(`[${message.type()}] ${message.text()}`));
    +  });
    +
    +  test.afterEach(async ({ page }, testInfo) => {
    +    if (testInfo.status !== testInfo.expectedStatus) {
    +      const logs = consoleMessages.length ? consoleMessages.join('\n') : '(no console messages)';
    +      await testInfo.attach('browser-console', { body: logs, contentType: 'text/plain' });
    +      const card = page.locator('section.card.legacy-card:has(#btn-auth)').first();
    +      if (await card.count()) {
    +        const html = await card.evaluate((node) => (node as HTMLElement)?.outerHTML ?? '');
    +        await testInfo.attach('dev-card-html', { body: html, contentType: 'text/html' });
    +      }
    +      await testInfo.attach('full-page-screenshot', {
    +        body: await page.screenshot({ fullPage: true }),
    +        contentType: 'image/png',
    +      });
    +    }
    +  });
    +
    +  test('renders remember-me checkbox near the JWT controls', async ({ page }) => {
    +    await page.goto('/', { waitUntil: 'networkidle' });
    +    await page.locator('#flow-menu-trigger').click();
    +    const devPanelItem = page.locator('.flow-menu-dropdown .flow-menu-item', { hasText: 'Dev Panel' });
    +    await expect(devPanelItem).toBeVisible({ timeout: 10000 });
    +    await devPanelItem.click();
    +    const rememberCheckbox = page.locator('#dev-jwt-remember');
    +    await expect(rememberCheckbox).toBeVisible({ timeout: 15000 });
    +    const authButton = page.locator('#btn-auth');
    +    await expect(authButton).toBeVisible({ timeout: 15000 });
    +    const card = authButton.locator('xpath=ancestor::section[contains(@class,"card")]');
    +    await expect(card.locator('#dev-jwt-remember')).toHaveCount(1);
    +  });
    +});
    diff --git a/web/package-lock.json b/web/package-lock.json
    index 394bcb3..10cc4fa 100644
    --- a/web/package-lock.json
    +++ b/web/package-lock.json
    @@ -8,9 +8,73 @@
           "name": "little-chef-web",
           "version": "0.1.0",
           "devDependencies": {
    +        "@playwright/test": "^1.44.0",
             "typescript": "^5.4.0"
           }
         },
    +    "node_modules/@playwright/test": {
    +      "version": "1.58.2",
    +      "resolved": "https://registry.npmjs.org/@playwright/test/-/test-1.58.2.tgz",
    +      "integrity": "sha512-akea+6bHYBBfA9uQqSYmlJXn61cTa+jbO87xVLCWbTqbWadRVmhxlXATaOjOgcBaWU4ePo0wB41KMFv3o35IXA==",
    +      "dev": true,
    +      "license": "Apache-2.0",
    +      "dependencies": {
    +        "playwright": "1.58.2"
    +      },
    +      "bin": {
    +        "playwright": "cli.js"
    +      },
    +      "engines": {
    +        "node": ">=18"
    +      }
    +    },
    +    "node_modules/fsevents": {
    +      "version": "2.3.2",
    +      "resolved": "https://registry.npmjs.org/fsevents/-/fsevents-2.3.2.tgz",
    +      "integrity": "sha512-xiqMQR4xAeHTuB9uWm+fFRcIOgKBMiOBP+eXiyT7jsgVCq1bkVygt00oASowB7EdtpOHaaPgKt812P9ab+DDKA==",
    +      "dev": true,
    +      "hasInstallScript": true,
    +      "license": "MIT",
    +      "optional": true,
    +      "os": [
    +        "darwin"
    +      ],
    +      "engines": {
    +        "node": "^8.16.0 || ^10.6.0 || >=11.0.0"
    +      }
    +    },
    +    "node_modules/playwright": {
    +      "version": "1.58.2",
    +      "resolved": "https://registry.npmjs.org/playwright/-/playwright-1.58.2.tgz",
    +      "integrity": "sha512-vA30H8Nvkq/cPBnNw4Q8TWz1EJyqgpuinBcHET0YVJVFldr8JDNiU9LaWAE1KqSkRYazuaBhTpB5ZzShOezQ6A==",
    +      "dev": true,
    +      "license": "Apache-2.0",
    +      "dependencies": {
    +        "playwright-core": "1.58.2"
    +      },
    +      "bin": {
    +        "playwright": "cli.js"
    +      },
    +      "engines": {
    +        "node": ">=18"
    +      },
    +      "optionalDependencies": {
    +        "fsevents": "2.3.2"
    +      }
    +    },
    +    "node_modules/playwright-core": {
    +      "version": "1.58.2",
    +      "resolved": "https://registry.npmjs.org/playwright-core/-/playwright-core-1.58.2.tgz",
    +      "integrity": "sha512-yZkEtftgwS8CsfYo7nm0KE8jsvm6i/PTgVtB8DL726wNf6H2IMsDuxCpJj59KDaxCtSnrWan2AeDqM7JBaultg==",
    +      "dev": true,
    +      "license": "Apache-2.0",
    +      "bin": {
    +        "playwright-core": "cli.js"
    +      },
    +      "engines": {
    +        "node": ">=18"
    +      }
    +    },
         "node_modules/typescript": {
           "version": "5.9.3",
           "resolved": "https://registry.npmjs.org/typescript/-/typescript-5.9.3.tgz",
    diff --git a/web/package.json b/web/package.json
    index ef37844..f22d8d7 100644
    --- a/web/package.json
    +++ b/web/package.json
    @@ -3,9 +3,11 @@
       "version": "0.1.0",
       "type": "module",
       "scripts": {
    -    "build": "tsc -p tsconfig.json"
    +    "build": "tsc -p tsconfig.json",
    +    "test:e2e": "playwright test --config ./playwright.config.ts"
       },
       "devDependencies": {
    +    "@playwright/test": "^1.44.0",
         "typescript": "^5.4.0"
       }
     }
    diff --git a/web/playwright.config.ts b/web/playwright.config.ts
    new file mode 100644
    index 0000000..4129891
    --- /dev/null
    +++ b/web/playwright.config.ts
    @@ -0,0 +1,22 @@
    +import { defineConfig } from "@playwright/test";
    +
    +const reuseServer = process.env.CI ? false : true;
    +
    +export default defineConfig({
    +  testDir: "./e2e",
    +  timeout: 60000,
    +  use: {
    +    baseURL: "http://127.0.0.1:8000",
    +    actionTimeout: 15000,
    +    navigationTimeout: 30000,
    +    trace: "retain-on-failure",
    +    screenshot: "only-on-failure",
    +    video: "retain-on-failure",
    +  },
    +  webServer: {
    +    command: "pwsh -NoProfile -File ..\\scripts\\run_local.ps1 -NoOpen -NoReload -NoInstall",
    +    port: 8000,
    +    reuseExistingServer: reuseServer,
    +    timeout: 120000,
    +  },
    +});
    diff --git a/web/src/main.ts b/web/src/main.ts
    index c1b45ac..dd65d44 100644
    --- a/web/src/main.ts
    +++ b/web/src/main.ts
    @@ -11,6 +11,67 @@ const state = {
       inventoryOnboarded: null as boolean | null,
     };
     
    +const DEV_JWT_STORAGE_KEY = "lc_dev_jwt";
    +const DEV_JWT_EXP_KEY = "lc_dev_jwt_exp_utc_ms";
    +const DEV_JWT_DURATION_KEY = "lc_dev_jwt_duration_ms";
    +const DEV_JWT_DEFAULT_TTL_MS = 24 * 60 * 60 * 1000;
    +const DEV_JWT_DURATION_OPTIONS: { value: number; label: string }[] = [
    +  { value: DEV_JWT_DEFAULT_TTL_MS, label: "24 hours" },
    +  { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" },
    +];
    +
    +function safeLocalStorage(): Storage | null {
    +  if (typeof window === "undefined") return null;
    +  try {
    +    return window.localStorage;
    +  } catch {
    +    return null;
    +  }
    +}
    +
    +function getRememberCheckbox(): HTMLInputElement | null {
    +  return document.getElementById("dev-jwt-remember") as HTMLInputElement | null;
    +}
    +
    +function getRememberDurationSelect(): HTMLSelectElement | null {
    +  return document.getElementById("dev-jwt-remember-duration") as HTMLSelectElement | null;
    +}
    +
    +function saveRememberedJwt(token: string, ttlMs: number) {
    +  const storage = safeLocalStorage();
    +  if (!storage) return;
    +  storage.setItem(DEV_JWT_STORAGE_KEY, token);
    +  storage.setItem(DEV_JWT_EXP_KEY, (Date.now() + ttlMs).toString());
    +  storage.setItem(DEV_JWT_DURATION_KEY, ttlMs.toString());
    +}
    +
    +function clearRememberedJwt() {
    +  const storage = safeLocalStorage();
    +  if (!storage) return;
    +  storage.removeItem(DEV_JWT_STORAGE_KEY);
    +  storage.removeItem(DEV_JWT_EXP_KEY);
    +  storage.removeItem(DEV_JWT_DURATION_KEY);
    +}
    +
    +function loadRememberedJwt(): { token: string; durationMs: number } | null {
    +  const storage = safeLocalStorage();
    +  if (!storage) return null;
    +  const token = storage.getItem(DEV_JWT_STORAGE_KEY);
    +  if (!token) return null;
    +  const expStr = storage.getItem(DEV_JWT_EXP_KEY);
    +  const durationStr = storage.getItem(DEV_JWT_DURATION_KEY);
    +  const expMs = Number(expStr);
    +  if (!expMs || expMs < Date.now()) {
    +    clearRememberedJwt();
    +    return null;
    +  }
    +  const durationMs = Number(durationStr);
    +  return {
    +    token,
    +    durationMs: Number.isFinite(durationMs) && durationMs > 0 ? durationMs : DEV_JWT_DEFAULT_TTL_MS,
    +  };
    +}
    +
     const PROPOSAL_CONFIRM_COMMANDS = new Set(["confirm"]);
     const PROPOSAL_DENY_COMMANDS = new Set(["deny", "cancel"]);
     
    @@ -171,6 +232,89 @@ function setupDevPanel() {
         ["btn-shopping", "shopping-out"],
       ];
       groups.forEach((ids) => moveGroupIntoDevPanel(ids, content, moved));
    +  ensureDevPanelRememberRow();
    +}
    +
    +function ensureDevPanelRememberRow() {
    +  const card = document.querySelector("section.card.legacy-card") as HTMLElement | null;
    +  if (!card) return;
    +  if (getRememberCheckbox()) return;
    +
    +  const row = document.createElement("div");
    +  row.className = "dev-panel-remember-row";
    +  row.style.display = "flex";
    +  row.style.alignItems = "center";
    +  row.style.gap = "12px";
    +  row.style.marginTop = "8px";
    +
    +  const checkboxLabel = document.createElement("label");
    +  checkboxLabel.className = "dev-panel-remember-label";
    +  checkboxLabel.style.display = "inline-flex";
    +  checkboxLabel.style.alignItems = "center";
    +  checkboxLabel.style.gap = "6px";
    +  const checkbox = document.createElement("input");
    +  checkbox.id = "dev-jwt-remember";
    +  checkbox.type = "checkbox";
    +  checkboxLabel.appendChild(checkbox);
    +  checkboxLabel.appendChild(document.createTextNode("Remember me"));
    +
    +  const durationLabel = document.createElement("label");
    +  durationLabel.className = "dev-panel-remember-duration";
    +  durationLabel.style.display = "inline-flex";
    +  durationLabel.style.alignItems = "center";
    +  durationLabel.style.gap = "6px";
    +  durationLabel.textContent = "Duration:";
    +  const durationSelect = document.createElement("select");
    +  durationSelect.id = "dev-jwt-remember-duration";
    +  durationSelect.className = "dev-panel-remember-select";
    +  DEV_JWT_DURATION_OPTIONS.forEach((option) => {
    +    const opt = document.createElement("option");
    +    opt.value = option.value.toString();
    +    opt.textContent = option.label;
    +    durationSelect.appendChild(opt);
    +  });
    +  durationLabel.appendChild(durationSelect);
    +
    +  row.appendChild(checkboxLabel);
    +  row.appendChild(durationLabel);
    +
    +  const authOut = card.querySelector("#auth-out");
    +  if (authOut?.parentElement) {
    +    authOut.parentElement.insertBefore(row, authOut);
    +  } else {
    +    card.appendChild(row);
    +  }
    +}
    +
    +function applyRememberedJwtInput(jwtInput: HTMLInputElement | null) {
    +  ensureDevPanelRememberRow();
    +  const checkbox = getRememberCheckbox();
    +  const durationSelect = getRememberDurationSelect();
    +  if (durationSelect && !durationSelect.value) {
    +    durationSelect.value = DEV_JWT_DEFAULT_TTL_MS.toString();
    +  }
    +  const stored = loadRememberedJwt();
    +  if (stored) {
    +    if (jwtInput) {
    +      jwtInput.value = stored.token;
    +    }
    +    state.token = stored.token;
    +    if (checkbox) {
    +      checkbox.checked = true;
    +    }
    +    if (durationSelect) {
    +      const desired = stored.durationMs.toString();
    +      const has = Array.from(durationSelect.options).some((opt) => opt.value === desired);
    +      durationSelect.value = has ? desired : durationSelect.options[0]?.value ?? desired;
    +    }
    +  } else {
    +    if (checkbox) {
    +      checkbox.checked = false;
    +    }
    +    if (durationSelect) {
    +      durationSelect.value = DEV_JWT_DEFAULT_TTL_MS.toString();
    +    }
    +  }
     }
     
     function renderProposal() {
    @@ -1094,6 +1238,15 @@ function wire() {
       const jwtInput = document.getElementById("jwt") as HTMLInputElement;
       document.getElementById("btn-auth")?.addEventListener("click", async () => {
         state.token = jwtInput.value.trim();
    +    const rememberCheckbox = getRememberCheckbox();
    +    const rememberSelect = getRememberDurationSelect();
    +    if (state.token && rememberCheckbox?.checked) {
    +      const desired = Number(rememberSelect?.value ?? DEV_JWT_DEFAULT_TTL_MS);
    +      const ttl = Number.isFinite(desired) && desired > 0 ? desired : DEV_JWT_DEFAULT_TTL_MS;
    +      saveRememberedJwt(state.token, ttl);
    +    } else {
    +      clearRememberedJwt();
    +    }
         clearProposal();
         const result = await doGet("/auth/me");
         setText("auth-out", result);
    @@ -1177,6 +1330,7 @@ function wire() {
       setupInventoryGhostOverlay();
       setupPrefsOverlay();
       setupDevPanel();
    +  applyRememberedJwtInput(jwtInput);
       wireDuetComposer();
       setupHistoryDrawerUi();
       wireHistoryHotkeys();

## Verification
- python -m compileall app (pass)
- python -c "import app.main" (pass)
- python -m pytest -q (pass)
- scripts/run_tests.ps1 (pass; includes Playwright e2e)

## Notes (optional)
- TODO: blockers, risks, constraints.

## Next Steps
- None

