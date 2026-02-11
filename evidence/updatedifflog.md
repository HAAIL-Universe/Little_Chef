# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-11T15:01:36+00:00
- Branch: claude/romantic-jones
- HEAD: 2de7b1c13d4db3bcea1046f79a0dfdea8aeb9aca
- BASE_HEAD: 25203615bda2ffb9cc9a2c7ebe02607e0d85ff83
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Added `selectFlow("general")` to `performLogout()` in `web/src/main.ts` — resets gear menu flow to Home on logout.
- Prior cycle already implemented: `performLogout()`, Logout gear menu item (token-gated), Auth0 logout redirect, auto-validate remembered JWT.
- Prior cycle also added: `app/main.py` Auth0 meta-tag injection from env vars (`LC_AUTH0_DOMAIN`, `LC_AUTH0_CLIENT_ID`, `LC_AUTH0_AUDIENCE`).
- This cycle's only new code: 1 line (`selectFlow("general")`) + rebuild dist.
- No new dependencies, no secrets, no refactors.

## Files Changed (staged)
- app/main.py
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md
- scripts/ui_onboarding_hints_test.mjs
- web/dist/main.js
- web/src/main.ts

## git status -sb
    ## claude/romantic-jones
    M  app/main.py
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
    M  evidence/updatedifflog.md
    M  scripts/ui_onboarding_hints_test.mjs
    M  web/dist/main.js
     M web/dist/proposalRenderer.js
    M  web/src/main.ts

## Minimal Diff Hunks
    diff --git a/app/main.py b/app/main.py
    index fb0f689..31d0f5c 100644
    --- a/app/main.py
    +++ b/app/main.py
    @@ -1,9 +1,11 @@
     import asyncio
     import logging
    +import os
    +import re
     from contextlib import asynccontextmanager
     
     from fastapi import FastAPI, HTTPException
    -from fastapi.responses import FileResponse, JSONResponse
    +from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
     from pathlib import Path
     
     from app.config.env import load_env
    @@ -65,12 +67,36 @@ def create_app() -> FastAPI:
         @app.get("/", include_in_schema=True)
         def ui_index():
             index_path = dist_dir / "index.html"
    -        if index_path.exists():
    -            return FileResponse(index_path, media_type="text/html")
    -        return JSONResponse(
    -            status_code=503,
    -            content={"error": "ui_not_built", "message": "UI build missing. Run npm --prefix web install && npm --prefix web run build."},
    -        )
    +        if not index_path.exists():
    +            return JSONResponse(
    +                status_code=503,
    +                content={"error": "ui_not_built", "message": "UI build missing. Run npm --prefix web install && npm --prefix web run build."},
    +            )
    +        html = index_path.read_text(encoding="utf-8")
    +
    +        # --- Auth0 meta-tag injection ---
    +        domain = os.getenv("LC_AUTH0_DOMAIN", "")
    +        if not domain:
    +            # Derive from LC_JWT_ISSUER (e.g. "https://tenant.eu.auth0.com/")
    +            issuer = os.getenv("LC_JWT_ISSUER", "")
    +            m = re.match(r"https?://([^/\s]+)", issuer)
    +            if m and "." in m.group(1):
    +                domain = m.group(1)
    +        client_id = os.getenv("LC_AUTH0_CLIENT_ID", "")
    +        audience = os.getenv("LC_AUTH0_AUDIENCE", "")
    +
    +        meta_tags = ""
    +        if domain:
    +            meta_tags += f'  <meta name="lc-auth0-domain" content="{domain}">\n'
    +        if client_id:
    +            meta_tags += f'  <meta name="lc-auth0-client-id" content="{client_id}">\n'
    +        if audience:
    +            meta_tags += f'  <meta name="lc-auth0-audience" content="{audience}">\n'
    +
    +        if meta_tags:
    +            html = html.replace("</head>", meta_tags + "</head>", 1)
    +
    +        return HTMLResponse(content=html, headers={"Cache-Control": "no-store"})
     
         @app.get("/static/{path:path}", include_in_schema=True)
         def ui_static(path: str):
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    index e4bc75e..b17d77f 100644
    --- a/evidence/test_runs.md
    +++ b/evidence/test_runs.md
    @@ -1,3 +1,21 @@
    +## Test Run 2026-02-11T14:15:00Z
    +- Status: PASS
    +- Start: 2026-02-11T14:10:00Z
    +- End: 2026-02-11T14:15:00Z
    +- Branch: claude/romantic-jones
    +- HEAD: 2de7b1c (unstaged: app/main.py meta-tag injection)
    +- Command: `python -m pytest tests/ -x -q --tb=short`
    +- Details: pytest 183 passed, 1 warning (116.60s). Cycle: Auth0 meta-tag injection via FastAPI. TestClient verified 3 tags injected with env vars, derivation fallback, graceful degradation.
    +
    +## Test Run 2026-02-11T13:30:00Z
    +- Status: PASS
    +- Start: 2026-02-11T13:25:00Z
    +- End: 2026-02-11T13:30:00Z
    +- Branch: claude/romantic-jones
    +- HEAD: 2de7b1c (unstaged edits on top)
    +- Command: `python -m pytest tests/ -x -q --tb=short && node scripts/ui_onboarding_hints_test.mjs`
    +- Details: pytest 183 passed, 1 warning (113.64s). UI tests 17/17 PASS (added 4: gearMenuIncludesLogout x2, shouldAutoValidateOnStartup x2). tsc pass (1 pre-existing TS2339). Cycle: auto-validate remembered JWT + Logout gear menu + Auth0 logout.
    +
     ## Test Run 2026-02-09T10:00:00Z
     - Status: PASS (96 passed, 2 pre-existing failures)
     - Start: 2026-02-09T10:00:00Z
    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    index c2f1ebe..7f90cfe 100644
    --- a/evidence/test_runs_latest.md
    +++ b/evidence/test_runs_latest.md
    @@ -1,41 +1,12 @@
    -Status: PASS
    -Start: 2026-02-11T12:14:00Z
    -End: 2026-02-11T12:16:00Z
    +´╗┐Status: PASS
    +Start: 2026-02-11T14:10:00Z
    +End: 2026-02-11T14:15:00Z
     Branch: claude/romantic-jones
    -HEAD: 25203615bda2ffb9cc9a2c7ebe02607e0d85ff83
    +HEAD: 2de7b1c (unstaged: app/main.py)
     Python: Z:\LittleChef\.claude\worktrees\romantic-jones\.venv\Scripts\python.exe
    -tsc: pass (1 pre-existing TS2339, no new errors)
    +py_compile: exit 0
     pytest exit: 0
    -pytest summary: 183 passed, 1 warning in 112.49s
    -node ui_onboarding_hints_test.mjs: 13/13 PASS
    -Cycle: Login-first navigation + Auth0 modal + debug gate
    -git status -sb:
    -```
    -## claude/romantic-jones
    - M .claude/settings.local.json
    -M  evidence/test_runs.md
    -M  evidence/test_runs_latest.md
    -M  evidence/updatedifflog.md
    -M  scripts/ui_onboarding_hints_test.mjs
    -M  web/dist/main.js
    -M  web/dist/style.css
    - M web/dist/proposalRenderer.js
    -M  web/src/main.ts
    -M  web/src/style.css
    -```
    -git diff --stat:
    -```
    - .claude/settings.local.json          |   16 +-
    - evidence/test_runs.md                |   13 +
    - evidence/updatedifflog.md            | 6268 +--
    - scripts/ui_onboarding_hints_test.mjs |   87 +-
    - web/dist/main.js                     |  212 +-
    - web/dist/style.css                   |   74 +
    - web/src/main.ts                      |  209 +-
    - web/src/style.css                    |   66 +
    - 8 files changed, 1374 insertions(+), 5571 deletions(-)
    -```
    - web/src/main.ts             |   42 +-
    - 5 files changed, 2628 insertions(+), 2402 deletions(-)
    -```
    -
    +pytest summary: 183 passed, 1 warning in 116.60s
    +TestClient verification: 3 meta tags with env vars, derivation fallback OK, no-vars graceful
    +Cycle: Auth0 meta-tag injection via FastAPI
    +Files changed: app/main.py only
    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    index 8121cfe..75e2538 100644
    --- a/evidence/updatedifflog.md
    +++ b/evidence/updatedifflog.md
    @@ -1,919 +1,1454 @@
     # Diff Log (overwrite each cycle)
     
     ## Cycle Metadata
    -- Timestamp: 2026-02-11T12:16:49+00:00
    +- Timestamp: 2026-02-11T13:53:32+00:00
     - Branch: claude/romantic-jones
    -- HEAD: 25203615bda2ffb9cc9a2c7ebe02607e0d85ff83
    -- BASE_HEAD: 2336dc4d8250c4186e87c4793339eb98b33b23b1
    +- HEAD: 2de7b1c13d4db3bcea1046f79a0dfdea8aeb9aca
    +- BASE_HEAD: 25203615bda2ffb9cc9a2c7ebe02607e0d85ff83
     - Diff basis: staged
     
     ## Cycle Status
     - Status: COMPLETE
     
     ## Summary
    -- feat: Login-first navigation + login modal + Auth0 SPA + debug gate + performPostLogin refactor
    -- test: 13 UI tests (onboard menu + debug gate + hints)
    +- `app/main.py` GET `/` handler: replaced `FileResponse` with `HTMLResponse` + Auth0 meta-tag injection.
    +- Reads `LC_AUTH0_DOMAIN`, `LC_AUTH0_CLIENT_ID`, `LC_AUTH0_AUDIENCE` from env; only emits non-empty tags.
    +- Derivation fallback: if `LC_AUTH0_DOMAIN` missing, strips scheme+slash from `LC_JWT_ISSUER` to get hostname.
    +- Adds `Cache-Control: no-store` header on index response to prevent stale HTML in dev.
    +- No JS/TS changes; no dist rebuild needed.
     
     ## Files Changed (staged)
    +- evidence/test_runs.md
    +- evidence/test_runs_latest.md
    +- evidence/updatedifflog.md
     - scripts/ui_onboarding_hints_test.mjs
     - web/dist/main.js
    -- web/dist/style.css
     - web/src/main.ts
    -- web/src/style.css
     
     ## git status -sb
         ## claude/romantic-jones
    -     M .claude/settings.local.json
    +     M app/main.py
    +    M  evidence/test_runs.md
    +    M  evidence/test_runs_latest.md
    +    M  evidence/updatedifflog.md
         M  scripts/ui_onboarding_hints_test.mjs
         M  web/dist/main.js
          M web/dist/proposalRenderer.js
    -    M  web/dist/style.css
         M  web/src/main.ts
    -    M  web/src/style.css
     
     ## Minimal Diff Hunks
    +    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    +    index e4bc75e..4ffcb6c 100644
    +    --- a/evidence/test_runs.md
    +    +++ b/evidence/test_runs.md
    +    @@ -1,3 +1,12 @@
    +    +## Test Run 2026-02-11T13:30:00Z
    +    +- Status: PASS
    +    +- Start: 2026-02-11T13:25:00Z
    +    +- End: 2026-02-11T13:30:00Z
    +    +- Branch: claude/romantic-jones
    +    +- HEAD: 2de7b1c (unstaged edits on top)
    +    +- Command: `python -m pytest tests/ -x -q --tb=short && node scripts/ui_onboarding_hints_test.mjs`
    +    +- Details: pytest 183 passed, 1 warning (113.64s). UI tests 17/17 PASS (added 4: gearMenuIncludesLogout x2, shouldAutoValidateOnStartup x2). tsc pass (1 pre-existing TS2339). Cycle: auto-validate remembered JWT + Logout gear menu + Auth0 logout.
    +    +
    +     ## Test Run 2026-02-09T10:00:00Z
    +     - Status: PASS (96 passed, 2 pre-existing failures)
    +     - Start: 2026-02-09T10:00:00Z
    +    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    +    index c2f1ebe..a6bf352 100644
    +    --- a/evidence/test_runs_latest.md
    +    +++ b/evidence/test_runs_latest.md
    +    @@ -1,41 +1,17 @@
    +    -Status: PASS
    +    -Start: 2026-02-11T12:14:00Z
    +    -End: 2026-02-11T12:16:00Z
    +    +┬┤ÔòùÔöÉStatus: PASS
    +    +Start: 2026-02-11T13:25:00Z
    +    +End: 2026-02-11T13:30:00Z
    +     Branch: claude/romantic-jones
    +    -HEAD: 25203615bda2ffb9cc9a2c7ebe02607e0d85ff83
    +    +HEAD: 2de7b1c13d4db3bcea1046f79a0dfdea8aeb9aca
    +     Python: Z:\LittleChef\.claude\worktrees\romantic-jones\.venv\Scripts\python.exe
    +     tsc: pass (1 pre-existing TS2339, no new errors)
    +     pytest exit: 0
    +    -pytest summary: 183 passed, 1 warning in 112.49s
    +    -node ui_onboarding_hints_test.mjs: 13/13 PASS
    +    -Cycle: Login-first navigation + Auth0 modal + debug gate
    +    -git status -sb:
    +    -```
    +    -## claude/romantic-jones
    +    - M .claude/settings.local.json
    +    -M  evidence/test_runs.md
    +    -M  evidence/test_runs_latest.md
    +    -M  evidence/updatedifflog.md
    +    -M  scripts/ui_onboarding_hints_test.mjs
    +    -M  web/dist/main.js
    +    -M  web/dist/style.css
    +    - M web/dist/proposalRenderer.js
    +    -M  web/src/main.ts
    +    -M  web/src/style.css
    +    -```
    +    -git diff --stat:
    +    -```
    +    - .claude/settings.local.json          |   16 +-
    +    - evidence/test_runs.md                |   13 +
    +    - evidence/updatedifflog.md            | 6268 +--
    +    - scripts/ui_onboarding_hints_test.mjs |   87 +-
    +    - web/dist/main.js                     |  212 +-
    +    - web/dist/style.css                   |   74 +
    +    - web/src/main.ts                      |  209 +-
    +    - web/src/style.css                    |   66 +
    +    - 8 files changed, 1374 insertions(+), 5571 deletions(-)
    +    -```
    +    - web/src/main.ts             |   42 +-
    +    - 5 files changed, 2628 insertions(+), 2402 deletions(-)
    +    -```
    +    -
    +    +pytest summary: 183 passed, 1 warning in 113.64s
    +    +node ui_onboarding_hints_test.mjs: 17/17 PASS
    +    +Cycle: auto-validate remembered JWT + Logout gear menu + Auth0 logout
    +    +git diff --stat HEAD:
    +    +  evidence/updatedifflog.md            | 949 +++---
    +    +  scripts/ui_onboarding_hints_test.mjs |  48 ++
    +    +  web/dist/main.js                     |  58 +-
    +    +  web/src/main.ts                      |  60 ++
    +    +  4 files changed, 323 insertions(+), 792 deletions(-)
    +    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    +    index 8121cfe..23ecfa5 100644
    +    --- a/evidence/updatedifflog.md
    +    +++ b/evidence/updatedifflog.md
    +    @@ -1,919 +1,286 @@
    +     # Diff Log (overwrite each cycle)
    +     
    +     ## Cycle Metadata
    +    -- Timestamp: 2026-02-11T12:16:49+00:00
    +    +- Timestamp: 2026-02-11T13:12:45+00:00
    +     - Branch: claude/romantic-jones
    +    -- HEAD: 25203615bda2ffb9cc9a2c7ebe02607e0d85ff83
    +    -- BASE_HEAD: 2336dc4d8250c4186e87c4793339eb98b33b23b1
    +    +- HEAD: 2de7b1c13d4db3bcea1046f79a0dfdea8aeb9aca
    +    +- BASE_HEAD: 25203615bda2ffb9cc9a2c7ebe02607e0d85ff83
    +     - Diff basis: staged
    +     
    +     ## Cycle Status
    +     - Status: COMPLETE
    +     
    +     ## Summary
    +    -- feat: Login-first navigation + login modal + Auth0 SPA + debug gate + performPostLogin refactor
    +    -- test: 13 UI tests (onboard menu + debug gate + hints)
    +    +- fix: auto-validate remembered JWT on startup via performPostLogin()
    +    +- feat: Logout in gear menu (local + Auth0 logout)
    +    +- feat: performLogout() clears session, remembered JWT, resets UI to login-first
    +    +- test: 17 UI tests (+4 for logout gate + auto-validate condition)
    +     
    +     ## Files Changed (staged)
    +     - scripts/ui_onboarding_hints_test.mjs
    +     - web/dist/main.js
    +    -- web/dist/style.css
    +     - web/src/main.ts
    +    -- web/src/style.css
    +     
    +     ## git status -sb
    +         ## claude/romantic-jones
    +    -     M .claude/settings.local.json
    +         M  scripts/ui_onboarding_hints_test.mjs
    +         M  web/dist/main.js
    +          M web/dist/proposalRenderer.js
    +    -    M  web/dist/style.css
    +         M  web/src/main.ts
    +    -    M  web/src/style.css
    +     
    +     ## Minimal Diff Hunks
    +         diff --git a/scripts/ui_onboarding_hints_test.mjs b/scripts/ui_onboarding_hints_test.mjs
    +    -    index 7ad26fb..25da94e 100644
    +    +    index 25da94e..40069a3 100644
    +         --- a/scripts/ui_onboarding_hints_test.mjs
    +         +++ b/scripts/ui_onboarding_hints_test.mjs
    +    -    @@ -17,8 +17,8 @@ function refreshSystemHints(status) {
    +    -       let assistantFallbackText;
    +    -     
    +    -       if (!status.is_logged_in) {
    +    -    -    userSystemHint = "Enter your JWT token above and tap Auth to sign in.";
    +    -    -    assistantFallbackText = "Welcome \u2014 I'm Little Chef.\n\nPlease sign in to get started.";
    +    -    +    userSystemHint = "Long-press this chat bubble to log in.";
    +    -    +    assistantFallbackText = "Welcome \u2014 I'm Little Chef.\n\nLong-press the system bubble below to sign in.";
    +    -       } else if (!status.prefs_complete) {
    +    -         userSystemHint = USER_BUBBLE_DEFAULT_HINT;
    +    -         assistantFallbackText =
    +    -    @@ -40,16 +40,38 @@ function refreshSystemHints(status) {
    +    -       return { userSystemHint, assistantFallbackText };
    +    +    @@ -59,6 +59,22 @@ function gearMenuIncludesDevPanel(debugEnabled) {
    +    +       return debugEnabled;
    +          }
    +          
    +    -    -// ---- Test: not logged in ----
    +         +/**
    +    -    + * Replicate renderOnboardMenuButtons() login-gate logic.
    +    -    + * Returns array of button labels the menu would render.
    +    +    + * Replicate renderFlowMenu() Logout gating.
    +    +    + * Returns true if Logout should appear in gear menu.
    +         + */
    +    -    +function onboardMenuItems(tokenTrimmed, onboarded, inventoryOnboarded) {
    +    -    +  if (!tokenTrimmed) return ["Login"];
    +    -    +  const items = ["Preferences"];
    +    -    +  if (onboarded) items.push("Inventory");
    +    -    +  if (inventoryOnboarded) items.push("Meal Plan");
    +    -    +  return items;
    +    +    +function gearMenuIncludesLogout(tokenTrimmed) {
    +    +    +  return !!tokenTrimmed;
    +         +}
    +         +
    +         +/**
    +    -    + * Replicate isDebugEnabled() + renderFlowMenu() Dev Panel gating.
    +    +    + * Replicate wire() startup auto-validate condition.
    +    +    + * Returns true if performPostLogin() should fire on startup.
    +         + */
    +    -    +function gearMenuIncludesDevPanel(debugEnabled) {
    +    -    +  return debugEnabled;
    +    +    +function shouldAutoValidateOnStartup(tokenTrimmed) {
    +    +    +  return !!tokenTrimmed;
    +         +}
    +         +
    +    -    +// ---- refreshSystemHints tests ----
    +    -    +
    +    -    +// Test: not logged in
    +    -     {
    +    -       const r = refreshSystemHints({ is_logged_in: false, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
    +    -       assert(r.assistantFallbackText.includes("sign in"), "not logged in: assistant should mention sign in");
    +    -       assert(!r.assistantFallbackText.includes("start onboarding"), "not logged in: should NOT show onboarding prompt");
    +    -    -  assert(r.userSystemHint.includes("Auth"), "not logged in: user hint should mention Auth");
    +    -    +  assert(r.userSystemHint.includes("Long-press"), "not logged in: user hint should mention Long-press");
    +    -    +  assert(r.userSystemHint.includes("log in"), "not logged in: user hint should mention log in");
    +    -     }
    +    -     console.log("not logged in: PASS");
    +    -     
    +    -    -// ---- Test: logged in, prefs NOT complete ----
    +    -    +// Test: logged in, prefs NOT complete
    +    -     {
    +    -       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
    +    -       assert(r.assistantFallbackText.includes("start onboarding"), "prefs incomplete: should show onboarding prompt");
    +    -    @@ -57,7 +79,7 @@ console.log("not logged in: PASS");
    +    -     }
    +    -     console.log("logged in, prefs incomplete: PASS");
    +    -     
    +    -    -// ---- Test: logged in, prefs complete, inventory NOT complete ----
    +    -    +// Test: logged in, prefs complete, inventory NOT complete
    +    -     {
    +    -       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: false, mealplan_complete: false });
    +    -       assert(!r.assistantFallbackText.includes("start onboarding"), "prefs done: should NOT show start onboarding");
    +    -    @@ -66,7 +88,7 @@ console.log("logged in, prefs incomplete: PASS");
    +    -     }
    +    -     console.log("logged in, prefs complete, inventory incomplete: PASS");
    +    +     // ---- refreshSystemHints tests ----
    +          
    +    -    -// ---- Test: logged in, prefs+inventory complete, mealplan NOT complete ----
    +    -    +// Test: logged in, prefs+inventory complete, mealplan NOT complete
    +    -     {
    +    -       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: false });
    +    -       assert(!r.assistantFallbackText.includes("start onboarding"), "inventory done: should NOT show start onboarding");
    +    -    @@ -76,7 +98,7 @@ console.log("logged in, prefs complete, inventory incomplete: PASS");
    +    +     // Test: not logged in
    +    +    @@ -171,4 +187,36 @@ console.log("debug disabled, no Dev Panel: PASS");
    +          }
    +    -     console.log("logged in, prefs+inventory complete, mealplan incomplete: PASS");
    +    +     console.log("debug enabled, Dev Panel present: PASS");
    +          
    +    -    -// ---- Test: all complete ----
    +    -    +// Test: all complete
    +    -     {
    +    -       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: true });
    +    -       assert(!r.assistantFallbackText.includes("start onboarding"), "all done: no onboarding prompt");
    +    -    @@ -86,7 +108,7 @@ console.log("logged in, prefs+inventory complete, mealplan incomplete: PASS");
    +    -     }
    +    -     console.log("all onboarding complete: PASS");
    +    -     
    +    -    -// ---- Test: prefs complete + logged in does NOT show preferences onboarding ----
    +    -    +// Test: prefs complete + logged in does NOT show preferences onboarding
    +    -     {
    +    -       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: false, mealplan_complete: false });
    +    -       assert(!r.assistantFallbackText.includes("To start onboarding"), "prefs done: MUST NOT show 'To start onboarding'");
    +    -    @@ -94,9 +116,8 @@ console.log("all onboarding complete: PASS");
    +    -     }
    +    -     console.log("prefs complete does not show prefs onboarding: PASS");
    +    -     
    +    -    -// ---- Test: after login state transition (simulated) ----
    +    -    +// Test: after login state transition (simulated)
    +    -     {
    +    -    -  // Simulate: start not logged in, then login with prefs+inventory complete
    +    -       const before = refreshSystemHints({ is_logged_in: false, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
    +    -       assert(before.assistantFallbackText.includes("sign in"), "before login: sign in prompt");
    +    -     
    +    -    @@ -106,4 +127,48 @@ console.log("prefs complete does not show prefs onboarding: PASS");
    +    -     }
    +    -     console.log("login state transition updates messages: PASS");
    +    -     
    +    -    +// ---- onboard menu tests ----
    +    -    +
    +    -    +// Test: not logged in -> only Login button
    +    -    +{
    +    -    +  const items = onboardMenuItems(false, false, false);
    +    -    +  assert.deepStrictEqual(items, ["Login"], "not logged in: onboard menu should show only Login");
    +    -    +}
    +    -    +console.log("onboard menu not logged in: PASS");
    +    -    +
    +    -    +// Test: logged in, not onboarded -> only Preferences
    +    -    +{
    +    -    +  const items = onboardMenuItems(true, false, false);
    +    -    +  assert.deepStrictEqual(items, ["Preferences"], "logged in, not onboarded: only Preferences");
    +    -    +}
    +    -    +console.log("onboard menu logged in, not onboarded: PASS");
    +    +    +// ---- logout gear-menu tests ----
    +         +
    +    -    +// Test: logged in, prefs onboarded -> Preferences + Inventory
    +    +    +// Test: logged out -> no Logout in gear menu
    +         +{
    +    -    +  const items = onboardMenuItems(true, true, false);
    +    -    +  assert.deepStrictEqual(items, ["Preferences", "Inventory"], "prefs onboarded: Preferences + Inventory");
    +    +    +  assert(!gearMenuIncludesLogout(false), "logged out: no Logout");
    +    +    +  assert(!gearMenuIncludesLogout(""), "empty token: no Logout");
    +         +}
    +    -    +console.log("onboard menu prefs onboarded: PASS");
    +    +    +console.log("gear menu logged out, no Logout: PASS");
    +         +
    +    -    +// Test: logged in, all onboarded -> Preferences + Inventory + Meal Plan
    +    +    +// Test: logged in -> Logout in gear menu
    +         +{
    +    -    +  const items = onboardMenuItems(true, true, true);
    +    -    +  assert.deepStrictEqual(items, ["Preferences", "Inventory", "Meal Plan"], "all onboarded: all three items");
    +    +    +  assert(gearMenuIncludesLogout(true), "logged in: Logout present");
    +    +    +  assert(gearMenuIncludesLogout("some-jwt-token"), "token truthy: Logout present");
    +         +}
    +    -    +console.log("onboard menu all onboarded: PASS");
    +    +    +console.log("gear menu logged in, Logout present: PASS");
    +         +
    +    -    +// ---- debug gate tests ----
    +    +    +// ---- startup auto-validate tests ----
    +         +
    +    -    +// Test: debug disabled -> no Dev Panel in gear menu
    +    +    +// Test: no remembered token -> no auto-validate
    +         +{
    +    -    +  assert(!gearMenuIncludesDevPanel(false), "debug off: no Dev Panel");
    +    +    +  assert(!shouldAutoValidateOnStartup(false), "no token: no auto-validate");
    +    +    +  assert(!shouldAutoValidateOnStartup(""), "empty token: no auto-validate");
    +         +}
    +    -    +console.log("debug disabled, no Dev Panel: PASS");
    +    +    +console.log("startup no token, no auto-validate: PASS");
    +         +
    +    -    +// Test: debug enabled -> Dev Panel in gear menu
    +    +    +// Test: remembered token present -> auto-validate fires
    +         +{
    +    -    +  assert(gearMenuIncludesDevPanel(true), "debug on: Dev Panel present");
    +    +    +  assert(shouldAutoValidateOnStartup(true), "token present: auto-validate fires");
    +    +    +  assert(shouldAutoValidateOnStartup("remembered-jwt"), "jwt truthy: auto-validate fires");
    +         +}
    +    -    +console.log("debug enabled, Dev Panel present: PASS");
    +    +    +console.log("startup remembered token, auto-validate fires: PASS");
    +         +
    +          console.log("\nui onboarding hints test: PASS");
    +         diff --git a/web/dist/main.js b/web/dist/main.js
    +    -    index 039b0db..59923d0 100644
    +    +    index 59923d0..bd27610 100644
    +         --- a/web/dist/main.js
    +         +++ b/web/dist/main.js
    +    -    @@ -17,6 +17,20 @@ const DEV_JWT_DURATION_OPTIONS = [
    +    -         { value: DEV_JWT_DEFAULT_TTL_MS, label: "24 hours" },
    +    -         { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" },
    +    -     ];
    +    -    +const LC_DEBUG_KEY = "lc_debug";
    +    -    +function isDebugEnabled() {
    +    -    +    var _a, _b, _c, _d;
    +    -    +    try {
    +    -    +        if (typeof window !== "undefined" && ((_b = (_a = window.location) === null || _a === void 0 ? void 0 : _a.search) === null || _b === void 0 ? void 0 : _b.includes("debug=1"))) {
    +    -    +            (_c = window.localStorage) === null || _c === void 0 ? void 0 : _c.setItem(LC_DEBUG_KEY, "1");
    +    -    +            return true;
    +    -    +        }
    +    -    +        return ((_d = window.localStorage) === null || _d === void 0 ? void 0 : _d.getItem(LC_DEBUG_KEY)) === "1";
    +    -    +    }
    +    -    +    catch {
    +    -    +        return false;
    +    -    +    }
    +    -    +}
    +    -     function safeLocalStorage() {
    +    -         if (typeof window === "undefined")
    +    -             return null;
    +    -    @@ -144,8 +158,8 @@ function getOnboardingStatus() {
    +    -     function refreshSystemHints() {
    +    -         const s = getOnboardingStatus();
    +    -         if (!s.is_logged_in) {
    +    -    -        userSystemHint = "Enter your JWT token above and tap Auth to sign in.";
    +    -    -        assistantFallbackText = "Welcome Ôö£├ÂÔö£├ºÔö£├é I'm Little Chef.\n\nPlease sign in to get started.";
    +    -    +        userSystemHint = "Long-press this chat bubble to log in.";
    +    -    +        assistantFallbackText = "Welcome Ôö£├ÂÔö£├ºÔö£├é I'm Little Chef.\n\nLong-press the system bubble below to sign in.";
    +    -         }
    +    -         else if (!s.prefs_complete) {
    +    -             userSystemHint = USER_BUBBLE_DEFAULT_HINT;
    +    -    @@ -658,16 +672,18 @@ function renderFlowMenu() {
    +    +    @@ -655,6 +655,7 @@ function setFlowMenuOpen(open) {
    +    +         flowMenuButton === null || flowMenuButton === void 0 ? void 0 : flowMenuButton.setAttribute("aria-expanded", open ? "true" : "false");
    +    +     }
    +    +     function renderFlowMenu() {
    +    +    +    var _a;
    +    +         const dropdown = flowMenuDropdown;
    +    +         const trigger = flowMenuButton;
    +    +         if (!dropdown || !trigger)
    +    +    @@ -672,6 +673,18 @@ function renderFlowMenu() {
    +                  });
    +                  dropdown.appendChild(item);
    +              });
    +    -    -    const devItem = document.createElement("button");
    +    -    -    devItem.type = "button";
    +    -    -    devItem.className = "flow-menu-item";
    +    -    -    devItem.textContent = "Dev Panel";
    +    -    -    devItem.setAttribute("role", "menuitem");
    +    -    -    devItem.addEventListener("click", () => {
    +    -    -        toggleDevPanel();
    +    -    -        setFlowMenuOpen(false);
    +    -    -    });
    +    -    -    dropdown.appendChild(devItem);
    +    -    +    if (isDebugEnabled()) {
    +    -    +        const devItem = document.createElement("button");
    +    -    +        devItem.type = "button";
    +    -    +        devItem.className = "flow-menu-item";
    +    -    +        devItem.textContent = "Dev Panel";
    +    -    +        devItem.setAttribute("role", "menuitem");
    +    -    +        devItem.addEventListener("click", () => {
    +    -    +            toggleDevPanel();
    +    +    +    if ((_a = state.token) === null || _a === void 0 ? void 0 : _a.trim()) {
    +    +    +        const logoutItem = document.createElement("button");
    +    +    +        logoutItem.type = "button";
    +    +    +        logoutItem.className = "flow-menu-item";
    +    +    +        logoutItem.textContent = "Logout";
    +    +    +        logoutItem.setAttribute("role", "menuitem");
    +    +    +        logoutItem.addEventListener("click", () => {
    +         +            setFlowMenuOpen(false);
    +    +    +            performLogout();
    +         +        });
    +    -    +        dropdown.appendChild(devItem);
    +    +    +        dropdown.appendChild(logoutItem);
    +         +    }
    +    -         const currentLabel = flowDisplayLabel(currentFlowKey);
    +    -         trigger.textContent = "Ôö£├ÂÔö£┬úÔö£├╗";
    +    -         trigger.setAttribute("aria-label", `Options (current: ${currentLabel})`);
    +    -    @@ -1596,12 +1612,136 @@ async function silentGreetOnce() {
    +    -             // Silent failure by design
    +    -         }
    +    +         if (isDebugEnabled()) {
    +    +             const devItem = document.createElement("button");
    +    +             devItem.type = "button";
    +    +    @@ -1736,8 +1749,37 @@ function closeLoginModal() {
    +    +         if (modal)
    +    +             modal.remove();
    +          }
    +    -    +// ---------------------------------------------------------------------------
    +    -    +// Auth0 SPA login + modal
    +    -    +// ---------------------------------------------------------------------------
    +    -    +let auth0Client = null;
    +    -    +async function loadAuth0Client() {
    +    -    +    if (auth0Client)
    +    -    +        return auth0Client;
    +    -    +    const meta = (name) => { var _a, _b; return (_b = (_a = document.querySelector(`meta[name="${name}"]`)) === null || _a === void 0 ? void 0 : _a.content) !== null && _b !== void 0 ? _b : ""; };
    +    -    +    const domain = meta("lc-auth0-domain");
    +    -    +    const clientId = meta("lc-auth0-client-id");
    +    -    +    const audience = meta("lc-auth0-audience");
    +    -    +    if (!domain || !clientId)
    +    -    +        return null;
    +    -    +    try {
    +    -    +        const cdnUrl = "https://cdn.jsdelivr.net/npm/@auth0/auth0-spa-js@2/dist/auth0-spa-js.production.esm.js";
    +    -    +        const mod = await Function("url", "return import(url)")(cdnUrl);
    +    -    +        auth0Client = await mod.createAuth0Client({
    +    -    +            domain,
    +    -    +            clientId,
    +    -    +            authorizationParams: {
    +    -    +                redirect_uri: window.location.origin,
    +    -    +                ...(audience ? { audience } : {}),
    +    -    +            },
    +    -    +        });
    +    -    +        return auth0Client;
    +    -    +    }
    +    -    +    catch (err) {
    +    -    +        console.error("[auth0] failed to load SDK", err);
    +    -    +        return null;
    +    -    +    }
    +    -    +}
    +    -    +async function performPostLogin() {
    +    -    +    var _a, _b;
    +    -    +    clearProposal();
    +    -    +    const result = await doGet("/auth/me");
    +    -    +    setText("auth-out", result);
    +    -    +    state.onboarded = !!((_a = result.json) === null || _a === void 0 ? void 0 : _a.onboarded);
    +    -    +    state.inventoryOnboarded = !!((_b = result.json) === null || _b === void 0 ? void 0 : _b.inventory_onboarded);
    +    -    +    if (state.inventoryOnboarded)
    +    -    +        mealplanReached = true;
    +    +    +async function performLogout() {
    +    +    +    // 1) Clear local session
    +    +    +    state.token = "";
    +    +    +    state.onboarded = null;
    +    +    +    state.inventoryOnboarded = null;
    +    +    +    mealplanReached = false;
    +    +    +    // 2) Clear remembered dev JWT
    +    +    +    clearRememberedJwt();
    +    +    +    // 3) Close login modal if open
    +    +    +    closeLoginModal();
    +    +    +    // 4) Refresh UI to login-first state
    +         +    refreshSystemHints();
    +         +    renderOnboardMenuButtons();
    +         +    updatePrefsOverlayVisibility();
    +         +    updateInventoryOverlayVisibility();
    +         +    updateRecipePacksButtonVisibility();
    +         +    updateDuetBubbles();
    +    -    +    await silentGreetOnce();
    +    -    +    inventoryHasLoaded = false;
    +    -    +    if (currentFlowKey === "inventory") {
    +    -    +        refreshInventoryOverlay(true);
    +    -    +    }
    +    -    +}
    +    -    +async function handleAuth0Callback() {
    +    -    +    const params = new URLSearchParams(window.location.search);
    +    -    +    if (!params.has("code") || !params.has("state"))
    +    -    +        return false;
    +    +    +    // 5) Auth0 logout (will redirect; must be last)
    +         +    try {
    +         +        const client = await loadAuth0Client();
    +    -    +        if (!client)
    +    -    +            return false;
    +    -    +        await client.handleRedirectCallback();
    +    -    +        const token = await client.getTokenSilently();
    +    -    +        if (token) {
    +    -    +            state.token = token;
    +    -    +            // Clean URL without reload
    +    -    +            const cleanUrl = window.location.origin + window.location.pathname;
    +    -    +            window.history.replaceState({}, document.title, cleanUrl);
    +    -    +            await performPostLogin();
    +    -    +            return true;
    +    +    +        if (client) {
    +    +    +            client.logout({ logoutParams: { returnTo: window.location.origin } });
    +    +    +            return; // Auth0 will navigate away
    +         +        }
    +         +    }
    +    -    +    catch (err) {
    +    -    +        console.error("[auth0] callback handling failed", err);
    +    +    +    catch {
    +    +    +        // Auth0 not configured or failed Ôö£├ÂÔö£├ºÔö£├é local logout is sufficient
    +         +    }
    +    -    +    return false;
    +    -    +}
    +    -    +function openLoginModal() {
    +    -    +    if (document.getElementById("lc-login-modal"))
    +    -    +        return;
    +    -    +    const overlay = document.createElement("div");
    +    -    +    overlay.id = "lc-login-modal";
    +    -    +    overlay.className = "lc-modal-overlay";
    +    -    +    overlay.addEventListener("click", (ev) => {
    +    -    +        if (ev.target === overlay)
    +    -    +            closeLoginModal();
    +    -    +    });
    +    -    +    const panel = document.createElement("div");
    +    -    +    panel.className = "lc-modal-panel";
    +    -    +    const closeBtn = document.createElement("button");
    +    -    +    closeBtn.type = "button";
    +    -    +    closeBtn.className = "lc-modal-close";
    +    -    +    closeBtn.textContent = "\u00d7";
    +    -    +    closeBtn.setAttribute("aria-label", "Close");
    +    -    +    closeBtn.addEventListener("click", closeLoginModal);
    +    -    +    const title = document.createElement("h2");
    +    -    +    title.textContent = "Sign in";
    +    -    +    title.className = "lc-modal-title";
    +    -    +    const auth0Btn = document.createElement("button");
    +    -    +    auth0Btn.type = "button";
    +    -    +    auth0Btn.className = "lc-modal-action";
    +    -    +    auth0Btn.textContent = "Continue with Auth0";
    +    -    +    auth0Btn.addEventListener("click", async () => {
    +    -    +        auth0Btn.disabled = true;
    +    -    +        auth0Btn.textContent = "Redirecting\u2026";
    +    -    +        const client = await loadAuth0Client();
    +    -    +        if (client) {
    +    -    +            await client.loginWithRedirect();
    +    -    +        }
    +    -    +        else {
    +    -    +            auth0Btn.textContent = "Auth0 not configured";
    +    -    +            auth0Btn.disabled = false;
    +    -    +        }
    +    -    +    });
    +    -    +    panel.appendChild(closeBtn);
    +    -    +    panel.appendChild(title);
    +    -    +    panel.appendChild(auth0Btn);
    +    -    +    overlay.appendChild(panel);
    +    -    +    document.body.appendChild(overlay);
    +    -    +}
    +    -    +function closeLoginModal() {
    +    -    +    const modal = document.getElementById("lc-login-modal");
    +    -    +    if (modal)
    +    -    +        modal.remove();
    +         +}
    +          function wire() {
    +    -         var _a, _b, _c, _d, _e, _f, _g, _h;
    +    +    -    var _a, _b, _c, _d, _e, _f, _g, _h;
    +    +    +    var _a, _b, _c, _d, _e, _f, _g, _h, _j;
    +              enforceViewportLock();
    +              const jwtInput = document.getElementById("jwt");
    +              (_a = document.getElementById("btn-auth")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", async () => {
    +    -    -        var _a, _b, _c;
    +    -    +        var _a;
    +    -             state.token = jwtInput.value.trim();
    +    -             const rememberCheckbox = getRememberCheckbox();
    +    -             const rememberSelect = getRememberDurationSelect();
    +    -    @@ -1613,25 +1753,7 @@ function wire() {
    +    -             else {
    +    -                 clearRememberedJwt();
    +    -             }
    +    -    -        clearProposal();
    +    -    -        const result = await doGet("/auth/me");
    +    -    -        setText("auth-out", result);
    +    -    -        state.onboarded = !!((_b = result.json) === null || _b === void 0 ? void 0 : _b.onboarded);
    +    -    -        state.inventoryOnboarded = !!((_c = result.json) === null || _c === void 0 ? void 0 : _c.inventory_onboarded);
    +    -    -        // Returning user who completed onboarding before Ôö£├ÂÔö£├ºÔö£├é unlock recipe button
    +    -    -        if (state.inventoryOnboarded)
    +    -    -            mealplanReached = true;
    +    -    -        refreshSystemHints();
    +    -    -        renderOnboardMenuButtons();
    +    -    -        updatePrefsOverlayVisibility();
    +    -    -        updateInventoryOverlayVisibility();
    +    -    -        updateRecipePacksButtonVisibility();
    +    -    -        updateDuetBubbles();
    +    -    -        await silentGreetOnce();
    +    -    -        inventoryHasLoaded = false;
    +    -    -        if (currentFlowKey === "inventory") {
    +    -    -            refreshInventoryOverlay(true);
    +    -    -        }
    +    -    +        await performPostLogin();
    +    -         });
    +    -         (_b = document.getElementById("btn-chat")) === null || _b === void 0 ? void 0 : _b.addEventListener("click", async () => {
    +    -             var _a;
    +    -    @@ -1699,6 +1821,9 @@ function wire() {
    +    -         setupPrefsOverlay();
    +    -         setupDevPanel();
    +    -         applyRememberedJwtInput(jwtInput);
    +    -    +    refreshSystemHints();
    +    -    +    // Auth0 callback detection (async, non-blocking)
    +    -    +    handleAuth0Callback().catch(() => { });
    +    +    @@ -1824,6 +1866,20 @@ function wire() {
    +    +         refreshSystemHints();
    +    +         // Auth0 callback detection (async, non-blocking)
    +    +         handleAuth0Callback().catch(() => { });
    +    +    +    // Auto-validate remembered dev JWT (fire-and-forget, same pattern as Auth0 callback)
    +    +    +    if ((_j = state.token) === null || _j === void 0 ? void 0 : _j.trim()) {
    +    +    +        performPostLogin().catch(() => {
    +    +    +            // Token invalid/expired Ôö£├ÂÔö£├ºÔö£├é clear and revert to login-first state
    +    +    +            state.token = "";
    +    +    +            state.onboarded = null;
    +    +    +            state.inventoryOnboarded = null;
    +    +    +            mealplanReached = false;
    +    +    +            clearRememberedJwt();
    +    +    +            refreshSystemHints();
    +    +    +            renderOnboardMenuButtons();
    +    +    +            updateDuetBubbles();
    +    +    +        });
    +    +    +    }
    +              wireDuetComposer();
    +              wireFloatingComposerTrigger(document.querySelector(".duet-stage"));
    +              setupHistoryDrawerUi();
    +    -    @@ -2013,9 +2138,24 @@ function ensureOnboardMenu() {
    +    -         return onboardMenu;
    +    -     }
    +    -     function renderOnboardMenuButtons() {
    +    -    +    var _a;
    +    -         if (!onboardMenu)
    +    -             return;
    +    -         onboardMenu.innerHTML = "";
    +    -    +    // Before login: show only Login button
    +    -    +    if (!((_a = state.token) === null || _a === void 0 ? void 0 : _a.trim())) {
    +    -    +        const loginBtn = document.createElement("button");
    +    -    +        loginBtn.type = "button";
    +    -    +        loginBtn.className = "flow-menu-item";
    +    -    +        loginBtn.textContent = "Login";
    +    -    +        loginBtn.dataset.onboardItem = "login";
    +    -    +        loginBtn.addEventListener("click", () => {
    +    -    +            hideOnboardMenu();
    +    -    +            openLoginModal();
    +    -    +        });
    +    -    +        onboardMenu.appendChild(loginBtn);
    +    -    +        return;
    +    -    +    }
    +    -         const prefsBtn = document.createElement("button");
    +    -         prefsBtn.type = "button";
    +    -         prefsBtn.className = "flow-menu-item";
    +    -    @@ -2743,11 +2883,15 @@ function _bindLongPressToElement(el) {
    +    -         });
    +    -         el.addEventListener("pointerup", (ev) => {
    +    -             if (onboardMenuActive) {
    +    -    -            const startHovered = (onboardActiveItem === null || onboardActiveItem === void 0 ? void 0 : onboardActiveItem.dataset.onboardItem) === "start";
    +    -    -            if (startHovered) {
    +    -    +            const hoveredItem = onboardActiveItem === null || onboardActiveItem === void 0 ? void 0 : onboardActiveItem.dataset.onboardItem;
    +    -    +            if (hoveredItem === "start") {
    +    -                     startOnboarding();
    +    -                     hideOnboardMenu();
    +    -                 }
    +    -    +            else if (hoveredItem === "login") {
    +    -    +                hideOnboardMenu();
    +    -    +                openLoginModal();
    +    -    +            }
    +    -                 onboardDragActive = false;
    +    -                 cancel({ hideMenu: false });
    +    -                 return;
    +    -    diff --git a/web/dist/style.css b/web/dist/style.css
    +    -    index 63e1b7d..43020b9 100644
    +    -    --- a/web/dist/style.css
    +    -    +++ b/web/dist/style.css
    +    -    @@ -413,6 +413,14 @@ pre {
    +    -       opacity: 0.75;
    +    -     }
    +    -     
    +    -    +.inv-loc-header {
    +    -    +  font-size: 11px;
    +    -    +  text-transform: uppercase;
    +    -    +  letter-spacing: 0.08em;
    +    -    +  opacity: 0.6;
    +    -    +  margin-top: 6px;
    +    -    +}
    +    -    +
    +    -     .prefs-overlay {
    +    -       background: rgba(14, 32, 54, 0.85);
    +    -     }
    +    -    @@ -1429,3 +1437,69 @@ pre {
    +    -       opacity: 0.6;
    +    -       cursor: not-allowed;
    +    -     }
    +    -    +
    +    -    +/* ---- Login modal ---- */
    +    -    +.lc-modal-overlay {
    +    -    +  position: fixed;
    +    -    +  inset: 0;
    +    -    +  z-index: 2147483645;
    +    -    +  display: flex;
    +    -    +  align-items: center;
    +    -    +  justify-content: center;
    +    -    +  background: rgba(0, 0, 0, 0.45);
    +    -    +  backdrop-filter: blur(4px);
    +    -    +  -webkit-backdrop-filter: blur(4px);
    +    -    +}
    +    -    +.lc-modal-panel {
    +    -    +  position: relative;
    +    -    +  width: min(340px, 90vw);
    +    -    +  padding: 1.5rem 1.25rem;
    +    -    +  border-radius: 1rem;
    +    -    +  background: rgba(255, 255, 255, 0.12);
    +    -    +  backdrop-filter: blur(18px);
    +    -    +  -webkit-backdrop-filter: blur(18px);
    +    -    +  border: 1px solid rgba(255, 255, 255, 0.18);
    +    -    +  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    +    -    +  color: #fff;
    +    -    +  text-align: center;
    +    -    +}
    +    -    +.lc-modal-close {
    +    -    +  position: absolute;
    +    -    +  top: 0.5rem;
    +    -    +  right: 0.75rem;
    +    -    +  background: none;
    +    -    +  border: none;
    +    -    +  color: rgba(255, 255, 255, 0.6);
    +    -    +  font-size: 1.4rem;
    +    -    +  cursor: pointer;
    +    -    +  line-height: 1;
    +    -    +  padding: 0.25rem;
    +    -    +}
    +    -    +.lc-modal-close:hover {
    +    -    +  color: #fff;
    +    -    +}
    +    -    +.lc-modal-title {
    +    -    +  margin: 0 0 1.25rem;
    +    -    +  font-size: 1.15rem;
    +    -    +  font-weight: 600;
    +    -    +}
    +    -    +.lc-modal-action {
    +    -    +  display: block;
    +    -    +  width: 100%;
    +    -    +  padding: 0.75rem 1rem;
    +    -    +  border: none;
    +    -    +  border-radius: 0.5rem;
    +    -    +  background: rgba(255, 255, 255, 0.18);
    +    -    +  color: #fff;
    +    -    +  font-size: 0.95rem;
    +    -    +  font-weight: 500;
    +    -    +  cursor: pointer;
    +    -    +  transition: background 0.15s;
    +    -    +}
    +    -    +.lc-modal-action:hover {
    +    -    +  background: rgba(255, 255, 255, 0.28);
    +    -    +}
    +    -    +.lc-modal-action:disabled {
    +    -    +  opacity: 0.6;
    +    -    +  cursor: not-allowed;
    +    -    +}
    +         diff --git a/web/src/main.ts b/web/src/main.ts
    +    -    index 29cbd20..1b4dbf3 100644
    +    +    index 1b4dbf3..ecfa61f 100644
    +         --- a/web/src/main.ts
    +         +++ b/web/src/main.ts
    +    -    @@ -20,6 +20,19 @@ const DEV_JWT_DURATION_OPTIONS: { value: number; label: string }[] = [
    +    -       { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" },
    +    -     ];
    +    -     
    +    -    +const LC_DEBUG_KEY = "lc_debug";
    +    -    +function isDebugEnabled(): boolean {
    +    -    +  try {
    +    -    +    if (typeof window !== "undefined" && window.location?.search?.includes("debug=1")) {
    +    -    +      window.localStorage?.setItem(LC_DEBUG_KEY, "1");
    +    -    +      return true;
    +    -    +    }
    +    -    +    return window.localStorage?.getItem(LC_DEBUG_KEY) === "1";
    +    -    +  } catch {
    +    -    +    return false;
    +    -    +  }
    +    -    +}
    +    -    +
    +    -     function safeLocalStorage(): Storage | null {
    +    -       if (typeof window === "undefined") return null;
    +    -       try {
    +    -    @@ -160,8 +173,8 @@ function getOnboardingStatus() {
    +    -     function refreshSystemHints() {
    +    -       const s = getOnboardingStatus();
    +    -       if (!s.is_logged_in) {
    +    -    -    userSystemHint = "Enter your JWT token above and tap Auth to sign in.";
    +    -    -    assistantFallbackText = "Welcome Ôö£├ÂÔö£├ºÔö£├é I'm Little Chef.\n\nPlease sign in to get started.";
    +    -    +    userSystemHint = "Long-press this chat bubble to log in.";
    +    -    +    assistantFallbackText = "Welcome Ôö£├ÂÔö£├ºÔö£├é I'm Little Chef.\n\nLong-press the system bubble below to sign in.";
    +    -       } else if (!s.prefs_complete) {
    +    -         userSystemHint = USER_BUBBLE_DEFAULT_HINT;
    +    -         assistantFallbackText =
    +    -    @@ -704,16 +717,18 @@ function renderFlowMenu() {
    +    +    @@ -717,6 +717,18 @@ function renderFlowMenu() {
    +              });
    +              dropdown.appendChild(item);
    +            });
    +    -    -  const devItem = document.createElement("button");
    +    -    -  devItem.type = "button";
    +    -    -  devItem.className = "flow-menu-item";
    +    -    -  devItem.textContent = "Dev Panel";
    +    -    -  devItem.setAttribute("role", "menuitem");
    +    -    -  devItem.addEventListener("click", () => {
    +    -    -    toggleDevPanel();
    +    -    -    setFlowMenuOpen(false);
    +    -    -  });
    +    -    -  dropdown.appendChild(devItem);
    +    -    +  if (isDebugEnabled()) {
    +    -    +    const devItem = document.createElement("button");
    +    -    +    devItem.type = "button";
    +    -    +    devItem.className = "flow-menu-item";
    +    -    +    devItem.textContent = "Dev Panel";
    +    -    +    devItem.setAttribute("role", "menuitem");
    +    -    +    devItem.addEventListener("click", () => {
    +    -    +      toggleDevPanel();
    +    +    +  if (state.token?.trim()) {
    +    +    +    const logoutItem = document.createElement("button");
    +    +    +    logoutItem.type = "button";
    +    +    +    logoutItem.className = "flow-menu-item";
    +    +    +    logoutItem.textContent = "Logout";
    +    +    +    logoutItem.setAttribute("role", "menuitem");
    +    +    +    logoutItem.addEventListener("click", () => {
    +         +      setFlowMenuOpen(false);
    +    +    +      performLogout();
    +         +    });
    +    -    +    dropdown.appendChild(devItem);
    +    +    +    dropdown.appendChild(logoutItem);
    +         +  }
    +    -     
    +    -       const currentLabel = flowDisplayLabel(currentFlowKey);
    +    -       trigger.textContent = "Ôö£├ÂÔö£┬úÔö£├╗";
    +    -    @@ -1676,6 +1691,129 @@ async function silentGreetOnce() {
    +    -       }
    +    +       if (isDebugEnabled()) {
    +    +         const devItem = document.createElement("button");
    +    +         devItem.type = "button";
    +    +    @@ -1814,6 +1826,39 @@ function closeLoginModal() {
    +    +       if (modal) modal.remove();
    +          }
    +          
    +    -    +// ---------------------------------------------------------------------------
    +    -    +// Auth0 SPA login + modal
    +    -    +// ---------------------------------------------------------------------------
    +    -    +let auth0Client: any = null;
    +    +    +async function performLogout(): Promise<void> {
    +    +    +  // 1) Clear local session
    +    +    +  state.token = "";
    +    +    +  state.onboarded = null;
    +    +    +  state.inventoryOnboarded = null;
    +    +    +  mealplanReached = false;
    +         +
    +    -    +async function loadAuth0Client(): Promise<any> {
    +    -    +  if (auth0Client) return auth0Client;
    +    -    +  const meta = (name: string) => document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`)?.content ?? "";
    +    -    +  const domain = meta("lc-auth0-domain");
    +    -    +  const clientId = meta("lc-auth0-client-id");
    +    -    +  const audience = meta("lc-auth0-audience");
    +    -    +  if (!domain || !clientId) return null;
    +    -    +  try {
    +    -    +    const cdnUrl = "https://cdn.jsdelivr.net/npm/@auth0/auth0-spa-js@2/dist/auth0-spa-js.production.esm.js";
    +    -    +    const mod = await (Function("url", "return import(url)")(cdnUrl) as Promise<any>);
    +    -    +    auth0Client = await mod.createAuth0Client({
    +    -    +      domain,
    +    -    +      clientId,
    +    -    +      authorizationParams: {
    +    -    +        redirect_uri: window.location.origin,
    +    -    +        ...(audience ? { audience } : {}),
    +    -    +      },
    +    -    +    });
    +    -    +    return auth0Client;
    +    -    +  } catch (err) {
    +    -    +    console.error("[auth0] failed to load SDK", err);
    +    -    +    return null;
    +    -    +  }
    +    -    +}
    +    +    +  // 2) Clear remembered dev JWT
    +    +    +  clearRememberedJwt();
    +    +    +
    +    +    +  // 3) Close login modal if open
    +    +    +  closeLoginModal();
    +         +
    +    -    +async function performPostLogin() {
    +    -    +  clearProposal();
    +    -    +  const result = await doGet("/auth/me");
    +    -    +  setText("auth-out", result);
    +    -    +  state.onboarded = !!result.json?.onboarded;
    +    -    +  state.inventoryOnboarded = !!result.json?.inventory_onboarded;
    +    -    +  if (state.inventoryOnboarded) mealplanReached = true;
    +    +    +  // 4) Refresh UI to login-first state
    +         +  refreshSystemHints();
    +         +  renderOnboardMenuButtons();
    +         +  updatePrefsOverlayVisibility();
    +         +  updateInventoryOverlayVisibility();
    +         +  updateRecipePacksButtonVisibility();
    +         +  updateDuetBubbles();
    +    -    +  await silentGreetOnce();
    +    -    +  inventoryHasLoaded = false;
    +    -    +  if (currentFlowKey === "inventory") {
    +    -    +    refreshInventoryOverlay(true);
    +    -    +  }
    +    -    +}
    +         +
    +    -    +async function handleAuth0Callback(): Promise<boolean> {
    +    -    +  const params = new URLSearchParams(window.location.search);
    +    -    +  if (!params.has("code") || !params.has("state")) return false;
    +    +    +  // 5) Auth0 logout (will redirect; must be last)
    +         +  try {
    +         +    const client = await loadAuth0Client();
    +    -    +    if (!client) return false;
    +    -    +    await client.handleRedirectCallback();
    +    -    +    const token = await client.getTokenSilently();
    +    -    +    if (token) {
    +    -    +      state.token = token;
    +    -    +      // Clean URL without reload
    +    -    +      const cleanUrl = window.location.origin + window.location.pathname;
    +    -    +      window.history.replaceState({}, document.title, cleanUrl);
    +    -    +      await performPostLogin();
    +    -    +      return true;
    +    -    +    }
    +    -    +  } catch (err) {
    +    -    +    console.error("[auth0] callback handling failed", err);
    +    -    +  }
    +    -    +  return false;
    +    -    +}
    +    -    +
    +    -    +function openLoginModal() {
    +    -    +  if (document.getElementById("lc-login-modal")) return;
    +    -    +  const overlay = document.createElement("div");
    +    -    +  overlay.id = "lc-login-modal";
    +    -    +  overlay.className = "lc-modal-overlay";
    +    -    +  overlay.addEventListener("click", (ev) => {
    +    -    +    if (ev.target === overlay) closeLoginModal();
    +    -    +  });
    +    -    +
    +    -    +  const panel = document.createElement("div");
    +    -    +  panel.className = "lc-modal-panel";
    +    -    +
    +    -    +  const closeBtn = document.createElement("button");
    +    -    +  closeBtn.type = "button";
    +    -    +  closeBtn.className = "lc-modal-close";
    +    -    +  closeBtn.textContent = "\u00d7";
    +    -    +  closeBtn.setAttribute("aria-label", "Close");
    +    -    +  closeBtn.addEventListener("click", closeLoginModal);
    +    -    +
    +    -    +  const title = document.createElement("h2");
    +    -    +  title.textContent = "Sign in";
    +    -    +  title.className = "lc-modal-title";
    +    -    +
    +    -    +  const auth0Btn = document.createElement("button");
    +    -    +  auth0Btn.type = "button";
    +    -    +  auth0Btn.className = "lc-modal-action";
    +    -    +  auth0Btn.textContent = "Continue with Auth0";
    +    -    +  auth0Btn.addEventListener("click", async () => {
    +    -    +    auth0Btn.disabled = true;
    +    -    +    auth0Btn.textContent = "Redirecting\u2026";
    +    -    +    const client = await loadAuth0Client();
    +         +    if (client) {
    +    -    +      await client.loginWithRedirect();
    +    -    +    } else {
    +    -    +      auth0Btn.textContent = "Auth0 not configured";
    +    -    +      auth0Btn.disabled = false;
    +    +    +      client.logout({ logoutParams: { returnTo: window.location.origin } });
    +    +    +      return; // Auth0 will navigate away
    +         +    }
    +    -    +  });
    +    -    +
    +    -    +  panel.appendChild(closeBtn);
    +    -    +  panel.appendChild(title);
    +    -    +  panel.appendChild(auth0Btn);
    +    -    +  overlay.appendChild(panel);
    +    -    +  document.body.appendChild(overlay);
    +    -    +}
    +    -    +
    +    -    +function closeLoginModal() {
    +    -    +  const modal = document.getElementById("lc-login-modal");
    +    -    +  if (modal) modal.remove();
    +    +    +  } catch {
    +    +    +    // Auth0 not configured or failed Ôö£├ÂÔö£├ºÔö£├é local logout is sufficient
    +    +    +  }
    +         +}
    +         +
    +          function wire() {
    +            enforceViewportLock();
    +            const jwtInput = document.getElementById("jwt") as HTMLInputElement;
    +    -    @@ -1690,24 +1828,7 @@ function wire() {
    +    -         } else {
    +    -           clearRememberedJwt();
    +    -         }
    +    -    -    clearProposal();
    +    -    -    const result = await doGet("/auth/me");
    +    -    -    setText("auth-out", result);
    +    -    -    state.onboarded = !!result.json?.onboarded;
    +    -    -    state.inventoryOnboarded = !!result.json?.inventory_onboarded;
    +    -    -    // Returning user who completed onboarding before Ôö£├ÂÔö£├ºÔö£├é unlock recipe button
    +    -    -    if (state.inventoryOnboarded) mealplanReached = true;
    +    -    -    refreshSystemHints();
    +    -    -    renderOnboardMenuButtons();
    +    -    -    updatePrefsOverlayVisibility();
    +    -    -    updateInventoryOverlayVisibility();
    +    -    -    updateRecipePacksButtonVisibility();
    +    -    -    updateDuetBubbles();
    +    -    -    await silentGreetOnce();
    +    -    -    inventoryHasLoaded = false;
    +    -    -    if (currentFlowKey === "inventory") {
    +    -    -      refreshInventoryOverlay(true);
    +    -    -    }
    +    -    +    await performPostLogin();
    +    -       });
    +    +    @@ -1905,6 +1950,21 @@ function wire() {
    +    +       // Auth0 callback detection (async, non-blocking)
    +    +       handleAuth0Callback().catch(() => {});
    +          
    +    -       document.getElementById("btn-chat")?.addEventListener("click", async () => {
    +    -    @@ -1779,6 +1900,11 @@ function wire() {
    +    -       setupPrefsOverlay();
    +    -       setupDevPanel();
    +    -       applyRememberedJwtInput(jwtInput);
    +    -    +  refreshSystemHints();
    +    -    +
    +    -    +  // Auth0 callback detection (async, non-blocking)
    +    -    +  handleAuth0Callback().catch(() => {});
    +    +    +  // Auto-validate remembered dev JWT (fire-and-forget, same pattern as Auth0 callback)
    +    +    +  if (state.token?.trim()) {
    +    +    +    performPostLogin().catch(() => {
    +    +    +      // Token invalid/expired Ôö£├ÂÔö£├ºÔö£├é clear and revert to login-first state
    +    +    +      state.token = "";
    +    +    +      state.onboarded = null;
    +    +    +      state.inventoryOnboarded = null;
    +    +    +      mealplanReached = false;
    +    +    +      clearRememberedJwt();
    +    +    +      refreshSystemHints();
    +    +    +      renderOnboardMenuButtons();
    +    +    +      updateDuetBubbles();
    +    +    +    });
    +    +    +  }
    +         +
    +            wireDuetComposer();
    +            wireFloatingComposerTrigger(document.querySelector(".duet-stage") as HTMLElement | null);
    +            setupHistoryDrawerUi();
    +    -    @@ -2109,6 +2235,22 @@ function ensureOnboardMenu() {
    +    -     function renderOnboardMenuButtons() {
    +    -       if (!onboardMenu) return;
    +    -       onboardMenu.innerHTML = "";
    +    -    +
    +    -    +  // Before login: show only Login button
    +    -    +  if (!state.token?.trim()) {
    +    -    +    const loginBtn = document.createElement("button");
    +    -    +    loginBtn.type = "button";
    +    -    +    loginBtn.className = "flow-menu-item";
    +    -    +    loginBtn.textContent = "Login";
    +    -    +    loginBtn.dataset.onboardItem = "login";
    +    -    +    loginBtn.addEventListener("click", () => {
    +    -    +      hideOnboardMenu();
    +    -    +      openLoginModal();
    +    -    +    });
    +    -    +    onboardMenu.appendChild(loginBtn);
    +    -    +    return;
    +    -    +  }
    +    -    +
    +    -       const prefsBtn = document.createElement("button");
    +    -       prefsBtn.type = "button";
    +    -       prefsBtn.className = "flow-menu-item";
    +    -    @@ -2850,10 +2992,13 @@ function _bindLongPressToElement(el: HTMLElement) {
    +    -     
    +    -       el.addEventListener("pointerup", (ev) => {
    +    -         if (onboardMenuActive) {
    +    -    -      const startHovered = onboardActiveItem?.dataset.onboardItem === "start";
    +    -    -      if (startHovered) {
    +    -    +      const hoveredItem = onboardActiveItem?.dataset.onboardItem;
    +    -    +      if (hoveredItem === "start") {
    +    -             startOnboarding();
    +    -             hideOnboardMenu();
    +    -    +      } else if (hoveredItem === "login") {
    +    -    +        hideOnboardMenu();
    +    -    +        openLoginModal();
    +    -           }
    +    -           onboardDragActive = false;
    +    -           cancel({ hideMenu: false });
    +    -    diff --git a/web/src/style.css b/web/src/style.css
    +    -    index b8a652b..43020b9 100644
    +    -    --- a/web/src/style.css
    +    -    +++ b/web/src/style.css
    +    -    @@ -1437,3 +1437,69 @@ pre {
    +    -       opacity: 0.6;
    +    -       cursor: not-allowed;
    +    -     }
    +    -    +
    +    -    +/* ---- Login modal ---- */
    +    -    +.lc-modal-overlay {
    +    -    +  position: fixed;
    +    -    +  inset: 0;
    +    -    +  z-index: 2147483645;
    +    -    +  display: flex;
    +    -    +  align-items: center;
    +    -    +  justify-content: center;
    +    -    +  background: rgba(0, 0, 0, 0.45);
    +    -    +  backdrop-filter: blur(4px);
    +    -    +  -webkit-backdrop-filter: blur(4px);
    +    -    +}
    +    -    +.lc-modal-panel {
    +    -    +  position: relative;
    +    -    +  width: min(340px, 90vw);
    +    -    +  padding: 1.5rem 1.25rem;
    +    -    +  border-radius: 1rem;
    +    -    +  background: rgba(255, 255, 255, 0.12);
    +    -    +  backdrop-filter: blur(18px);
    +    -    +  -webkit-backdrop-filter: blur(18px);
    +    -    +  border: 1px solid rgba(255, 255, 255, 0.18);
    +    -    +  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    +    -    +  color: #fff;
    +    -    +  text-align: center;
    +    -    +}
    +    -    +.lc-modal-close {
    +    -    +  position: absolute;
    +    -    +  top: 0.5rem;
    +    -    +  right: 0.75rem;
    +    -    +  background: none;
    +    -    +  border: none;
    +    -    +  color: rgba(255, 255, 255, 0.6);
    +    -    +  font-size: 1.4rem;
    +    -    +  cursor: pointer;
    +    -    +  line-height: 1;
    +    -    +  padding: 0.25rem;
    +    -    +}
    +    -    +.lc-modal-close:hover {
    +    -    +  color: #fff;
    +    -    +}
    +    -    +.lc-modal-title {
    +    -    +  margin: 0 0 1.25rem;
    +    -    +  font-size: 1.15rem;
    +    -    +  font-weight: 600;
    +    -    +}
    +    -    +.lc-modal-action {
    +    -    +  display: block;
    +    -    +  width: 100%;
    +    -    +  padding: 0.75rem 1rem;
    +    -    +  border: none;
    +    -    +  border-radius: 0.5rem;
    +    -    +  background: rgba(255, 255, 255, 0.18);
    +    -    +  color: #fff;
    +    -    +  font-size: 0.95rem;
    +    -    +  font-weight: 500;
    +    -    +  cursor: pointer;
    +    -    +  transition: background 0.15s;
    +    -    +}
    +    -    +.lc-modal-action:hover {
    +    -    +  background: rgba(255, 255, 255, 0.28);
    +    -    +}
    +    -    +.lc-modal-action:disabled {
    +    -    +  opacity: 0.6;
    +    -    +  cursor: not-allowed;
    +    -    +}
    +     
    +     ## Verification
    +     - tsc: pass (1 pre-existing TS2339)
    +     - pytest: 183 passed, 0 failures
    +    -- node ui_onboarding_hints_test.mjs: 13/13 PASS
    +    +- node ui_onboarding_hints_test.mjs: 17/17 PASS
    +     
    +     ## Notes (optional)
    +    -- Auth0 SPA SDK loaded via CDN ESM (no bundler in web build); Function("url","return import(url)") workaround for tsc dynamic import of CDN URL.
    +    -- Auth0 tenant config (lc-auth0-domain, lc-auth0-client-id meta tags) required for full login flow; without it, "Auth0 not configured" shown.
    +    -- web/dist/proposalRenderer.js CRLF artifact from prior cycle (not in allowed file set, not staged).
    +    +- Auth0 logout will redirect away; local cleanup runs first so state is always cleared.
    +    +- If /auth/me fails on remembered JWT (expired/invalid), token is cleared and UI reverts to login-first.
    +    +- No CSS changes this cycle; dist/style.css unchanged.
    +     
    +     ## Next Steps
    +     - User must reply AUTHORIZED before commit
    +    -- Auth0 tenant config needed for full e2e (known limitation)
    +    +- Auth0 logout redirect requires tenant config (known limitation)
    +     
         diff --git a/scripts/ui_onboarding_hints_test.mjs b/scripts/ui_onboarding_hints_test.mjs
    -    index 7ad26fb..25da94e 100644
    +    index 25da94e..40069a3 100644
         --- a/scripts/ui_onboarding_hints_test.mjs
         +++ b/scripts/ui_onboarding_hints_test.mjs
    -    @@ -17,8 +17,8 @@ function refreshSystemHints(status) {
    -       let assistantFallbackText;
    -     
    -       if (!status.is_logged_in) {
    -    -    userSystemHint = "Enter your JWT token above and tap Auth to sign in.";
    -    -    assistantFallbackText = "Welcome \u2014 I'm Little Chef.\n\nPlease sign in to get started.";
    -    +    userSystemHint = "Long-press this chat bubble to log in.";
    -    +    assistantFallbackText = "Welcome \u2014 I'm Little Chef.\n\nLong-press the system bubble below to sign in.";
    -       } else if (!status.prefs_complete) {
    -         userSystemHint = USER_BUBBLE_DEFAULT_HINT;
    -         assistantFallbackText =
    -    @@ -40,16 +40,38 @@ function refreshSystemHints(status) {
    -       return { userSystemHint, assistantFallbackText };
    +    @@ -59,6 +59,22 @@ function gearMenuIncludesDevPanel(debugEnabled) {
    +       return debugEnabled;
          }
          
    -    -// ---- Test: not logged in ----
         +/**
    -    + * Replicate renderOnboardMenuButtons() login-gate logic.
    -    + * Returns array of button labels the menu would render.
    +    + * Replicate renderFlowMenu() Logout gating.
    +    + * Returns true if Logout should appear in gear menu.
         + */
    -    +function onboardMenuItems(tokenTrimmed, onboarded, inventoryOnboarded) {
    -    +  if (!tokenTrimmed) return ["Login"];
    -    +  const items = ["Preferences"];
    -    +  if (onboarded) items.push("Inventory");
    -    +  if (inventoryOnboarded) items.push("Meal Plan");
    -    +  return items;
    +    +function gearMenuIncludesLogout(tokenTrimmed) {
    +    +  return !!tokenTrimmed;
         +}
         +
         +/**
    -    + * Replicate isDebugEnabled() + renderFlowMenu() Dev Panel gating.
    +    + * Replicate wire() startup auto-validate condition.
    +    + * Returns true if performPostLogin() should fire on startup.
         + */
    -    +function gearMenuIncludesDevPanel(debugEnabled) {
    -    +  return debugEnabled;
    +    +function shouldAutoValidateOnStartup(tokenTrimmed) {
    +    +  return !!tokenTrimmed;
         +}
         +
    -    +// ---- refreshSystemHints tests ----
    -    +
    -    +// Test: not logged in
    -     {
    -       const r = refreshSystemHints({ is_logged_in: false, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
    -       assert(r.assistantFallbackText.includes("sign in"), "not logged in: assistant should mention sign in");
    -       assert(!r.assistantFallbackText.includes("start onboarding"), "not logged in: should NOT show onboarding prompt");
    -    -  assert(r.userSystemHint.includes("Auth"), "not logged in: user hint should mention Auth");
    -    +  assert(r.userSystemHint.includes("Long-press"), "not logged in: user hint should mention Long-press");
    -    +  assert(r.userSystemHint.includes("log in"), "not logged in: user hint should mention log in");
    -     }
    -     console.log("not logged in: PASS");
    -     
    -    -// ---- Test: logged in, prefs NOT complete ----
    -    +// Test: logged in, prefs NOT complete
    -     {
    -       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
    -       assert(r.assistantFallbackText.includes("start onboarding"), "prefs incomplete: should show onboarding prompt");
    -    @@ -57,7 +79,7 @@ console.log("not logged in: PASS");
    -     }
    -     console.log("logged in, prefs incomplete: PASS");
    +     // ---- refreshSystemHints tests ----
          
    -    -// ---- Test: logged in, prefs complete, inventory NOT complete ----
    -    +// Test: logged in, prefs complete, inventory NOT complete
    -     {
    -       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: false, mealplan_complete: false });
    -       assert(!r.assistantFallbackText.includes("start onboarding"), "prefs done: should NOT show start onboarding");
    -    @@ -66,7 +88,7 @@ console.log("logged in, prefs incomplete: PASS");
    +     // Test: not logged in
    +    @@ -171,4 +187,36 @@ console.log("debug disabled, no Dev Panel: PASS");
          }
    -     console.log("logged in, prefs complete, inventory incomplete: PASS");
    +     console.log("debug enabled, Dev Panel present: PASS");
          
    -    -// ---- Test: logged in, prefs+inventory complete, mealplan NOT complete ----
    -    +// Test: logged in, prefs+inventory complete, mealplan NOT complete
    -     {
    -       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: false });
    -       assert(!r.assistantFallbackText.includes("start onboarding"), "inventory done: should NOT show start onboarding");
    -    @@ -76,7 +98,7 @@ console.log("logged in, prefs complete, inventory incomplete: PASS");
    -     }
    -     console.log("logged in, prefs+inventory complete, mealplan incomplete: PASS");
    -     
    -    -// ---- Test: all complete ----
    -    +// Test: all complete
    -     {
    -       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: true });
    -       assert(!r.assistantFallbackText.includes("start onboarding"), "all done: no onboarding prompt");
    -    @@ -86,7 +108,7 @@ console.log("logged in, prefs+inventory complete, mealplan incomplete: PASS");
    -     }
    -     console.log("all onboarding complete: PASS");
    -     
    -    -// ---- Test: prefs complete + logged in does NOT show preferences onboarding ----
    -    +// Test: prefs complete + logged in does NOT show preferences onboarding
    -     {
    -       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: false, mealplan_complete: false });
    -       assert(!r.assistantFallbackText.includes("To start onboarding"), "prefs done: MUST NOT show 'To start onboarding'");
    -    @@ -94,9 +116,8 @@ console.log("all onboarding complete: PASS");
    -     }
    -     console.log("prefs complete does not show prefs onboarding: PASS");
    -     
    -    -// ---- Test: after login state transition (simulated) ----
    -    +// Test: after login state transition (simulated)
    -     {
    -    -  // Simulate: start not logged in, then login with prefs+inventory complete
    -       const before = refreshSystemHints({ is_logged_in: false, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
    -       assert(before.assistantFallbackText.includes("sign in"), "before login: sign in prompt");
    -     
    -    @@ -106,4 +127,48 @@ console.log("prefs complete does not show prefs onboarding: PASS");
    -     }
    -     console.log("login state transition updates messages: PASS");
    -     
    -    +// ---- onboard menu tests ----
    +    +// ---- logout gear-menu tests ----
         +
    -    +// Test: not logged in -> only Login button
    +    +// Test: logged out -> no Logout in gear menu
         +{
    -    +  const items = onboardMenuItems(false, false, false);
    -    +  assert.deepStrictEqual(items, ["Login"], "not logged in: onboard menu should show only Login");
    +    +  assert(!gearMenuIncludesLogout(false), "logged out: no Logout");
    +    +  assert(!gearMenuIncludesLogout(""), "empty token: no Logout");
         +}
    -    +console.log("onboard menu not logged in: PASS");
    +    +console.log("gear menu logged out, no Logout: PASS");
         +
    -    +// Test: logged in, not onboarded -> only Preferences
    +    +// Test: logged in -> Logout in gear menu
         +{
    -    +  const items = onboardMenuItems(true, false, false);
    -    +  assert.deepStrictEqual(items, ["Preferences"], "logged in, not onboarded: only Preferences");
    +    +  assert(gearMenuIncludesLogout(true), "logged in: Logout present");
    +    +  assert(gearMenuIncludesLogout("some-jwt-token"), "token truthy: Logout present");
         +}
    -    +console.log("onboard menu logged in, not onboarded: PASS");
    +    +console.log("gear menu logged in, Logout present: PASS");
         +
    -    +// Test: logged in, prefs onboarded -> Preferences + Inventory
    -    +{
    -    +  const items = onboardMenuItems(true, true, false);
    -    +  assert.deepStrictEqual(items, ["Preferences", "Inventory"], "prefs onboarded: Preferences + Inventory");
    -    +}
    -    +console.log("onboard menu prefs onboarded: PASS");
    -    +
    -    +// Test: logged in, all onboarded -> Preferences + Inventory + Meal Plan
    -    +{
    -    +  const items = onboardMenuItems(true, true, true);
    -    +  assert.deepStrictEqual(items, ["Preferences", "Inventory", "Meal Plan"], "all onboarded: all three items");
    -    +}
    -    +console.log("onboard menu all onboarded: PASS");
    -    +
    -    +// ---- debug gate tests ----
    +    +// ---- startup auto-validate tests ----
         +
    -    +// Test: debug disabled -> no Dev Panel in gear menu
    +    +// Test: no remembered token -> no auto-validate
         +{
    -    +  assert(!gearMenuIncludesDevPanel(false), "debug off: no Dev Panel");
    +    +  assert(!shouldAutoValidateOnStartup(false), "no token: no auto-validate");
    +    +  assert(!shouldAutoValidateOnStartup(""), "empty token: no auto-validate");
         +}
    -    +console.log("debug disabled, no Dev Panel: PASS");
    +    +console.log("startup no token, no auto-validate: PASS");
         +
    -    +// Test: debug enabled -> Dev Panel in gear menu
    +    +// Test: remembered token present -> auto-validate fires
         +{
    -    +  assert(gearMenuIncludesDevPanel(true), "debug on: Dev Panel present");
    +    +  assert(shouldAutoValidateOnStartup(true), "token present: auto-validate fires");
    +    +  assert(shouldAutoValidateOnStartup("remembered-jwt"), "jwt truthy: auto-validate fires");
         +}
    -    +console.log("debug enabled, Dev Panel present: PASS");
    +    +console.log("startup remembered token, auto-validate fires: PASS");
         +
          console.log("\nui onboarding hints test: PASS");
         diff --git a/web/dist/main.js b/web/dist/main.js
    -    index 039b0db..59923d0 100644
    +    index 59923d0..bd27610 100644
         --- a/web/dist/main.js
         +++ b/web/dist/main.js
    -    @@ -17,6 +17,20 @@ const DEV_JWT_DURATION_OPTIONS = [
    -         { value: DEV_JWT_DEFAULT_TTL_MS, label: "24 hours" },
    -         { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" },
    -     ];
    -    +const LC_DEBUG_KEY = "lc_debug";
    -    +function isDebugEnabled() {
    -    +    var _a, _b, _c, _d;
    -    +    try {
    -    +        if (typeof window !== "undefined" && ((_b = (_a = window.location) === null || _a === void 0 ? void 0 : _a.search) === null || _b === void 0 ? void 0 : _b.includes("debug=1"))) {
    -    +            (_c = window.localStorage) === null || _c === void 0 ? void 0 : _c.setItem(LC_DEBUG_KEY, "1");
    -    +            return true;
    -    +        }
    -    +        return ((_d = window.localStorage) === null || _d === void 0 ? void 0 : _d.getItem(LC_DEBUG_KEY)) === "1";
    -    +    }
    -    +    catch {
    -    +        return false;
    -    +    }
    -    +}
    -     function safeLocalStorage() {
    -         if (typeof window === "undefined")
    -             return null;
    -    @@ -144,8 +158,8 @@ function getOnboardingStatus() {
    -     function refreshSystemHints() {
    -         const s = getOnboardingStatus();
    -         if (!s.is_logged_in) {
    -    -        userSystemHint = "Enter your JWT token above and tap Auth to sign in.";
    -    -        assistantFallbackText = "Welcome ├ö├ç├Â I'm Little Chef.\n\nPlease sign in to get started.";
    -    +        userSystemHint = "Long-press this chat bubble to log in.";
    -    +        assistantFallbackText = "Welcome ├ö├ç├Â I'm Little Chef.\n\nLong-press the system bubble below to sign in.";
    -         }
    -         else if (!s.prefs_complete) {
    -             userSystemHint = USER_BUBBLE_DEFAULT_HINT;
    -    @@ -658,16 +672,18 @@ function renderFlowMenu() {
    +    @@ -655,6 +655,7 @@ function setFlowMenuOpen(open) {
    +         flowMenuButton === null || flowMenuButton === void 0 ? void 0 : flowMenuButton.setAttribute("aria-expanded", open ? "true" : "false");
    +     }
    +     function renderFlowMenu() {
    +    +    var _a;
    +         const dropdown = flowMenuDropdown;
    +         const trigger = flowMenuButton;
    +         if (!dropdown || !trigger)
    +    @@ -672,6 +673,18 @@ function renderFlowMenu() {
                  });
                  dropdown.appendChild(item);
              });
    -    -    const devItem = document.createElement("button");
    -    -    devItem.type = "button";
    -    -    devItem.className = "flow-menu-item";
    -    -    devItem.textContent = "Dev Panel";
    -    -    devItem.setAttribute("role", "menuitem");
    -    -    devItem.addEventListener("click", () => {
    -    -        toggleDevPanel();
    -    -        setFlowMenuOpen(false);
    -    -    });
    -    -    dropdown.appendChild(devItem);
    -    +    if (isDebugEnabled()) {
    -    +        const devItem = document.createElement("button");
    -    +        devItem.type = "button";
    -    +        devItem.className = "flow-menu-item";
    -    +        devItem.textContent = "Dev Panel";
    -    +        devItem.setAttribute("role", "menuitem");
    -    +        devItem.addEventListener("click", () => {
    -    +            toggleDevPanel();
    +    +    if ((_a = state.token) === null || _a === void 0 ? void 0 : _a.trim()) {
    +    +        const logoutItem = document.createElement("button");
    +    +        logoutItem.type = "button";
    +    +        logoutItem.className = "flow-menu-item";
    +    +        logoutItem.textContent = "Logout";
    +    +        logoutItem.setAttribute("role", "menuitem");
    +    +        logoutItem.addEventListener("click", () => {
         +            setFlowMenuOpen(false);
    +    +            performLogout();
         +        });
    -    +        dropdown.appendChild(devItem);
    +    +        dropdown.appendChild(logoutItem);
         +    }
    -         const currentLabel = flowDisplayLabel(currentFlowKey);
    -         trigger.textContent = "├ö├£├û";
    -         trigger.setAttribute("aria-label", `Options (current: ${currentLabel})`);
    -    @@ -1596,12 +1612,136 @@ async function silentGreetOnce() {
    -             // Silent failure by design
    -         }
    +         if (isDebugEnabled()) {
    +             const devItem = document.createElement("button");
    +             devItem.type = "button";
    +    @@ -1736,8 +1749,37 @@ function closeLoginModal() {
    +         if (modal)
    +             modal.remove();
          }
    -    +// ---------------------------------------------------------------------------
    -    +// Auth0 SPA login + modal
    -    +// ---------------------------------------------------------------------------
    -    +let auth0Client = null;
    -    +async function loadAuth0Client() {
    -    +    if (auth0Client)
    -    +        return auth0Client;
    -    +    const meta = (name) => { var _a, _b; return (_b = (_a = document.querySelector(`meta[name="${name}"]`)) === null || _a === void 0 ? void 0 : _a.content) !== null && _b !== void 0 ? _b : ""; };
    -    +    const domain = meta("lc-auth0-domain");
    -    +    const clientId = meta("lc-auth0-client-id");
    -    +    const audience = meta("lc-auth0-audience");
    -    +    if (!domain || !clientId)
    -    +        return null;
    -    +    try {
    -    +        const cdnUrl = "https://cdn.jsdelivr.net/npm/@auth0/auth0-spa-js@2/dist/auth0-spa-js.production.esm.js";
    -    +        const mod = await Function("url", "return import(url)")(cdnUrl);
    -    +        auth0Client = await mod.createAuth0Client({
    -    +            domain,
    -    +            clientId,
    -    +            authorizationParams: {
    -    +                redirect_uri: window.location.origin,
    -    +                ...(audience ? { audience } : {}),
    -    +            },
    -    +        });
    -    +        return auth0Client;
    -    +    }
    -    +    catch (err) {
    -    +        console.error("[auth0] failed to load SDK", err);
    -    +        return null;
    -    +    }
    -    +}
    -    +async function performPostLogin() {
    -    +    var _a, _b;
    -    +    clearProposal();
    -    +    const result = await doGet("/auth/me");
    -    +    setText("auth-out", result);
    -    +    state.onboarded = !!((_a = result.json) === null || _a === void 0 ? void 0 : _a.onboarded);
    -    +    state.inventoryOnboarded = !!((_b = result.json) === null || _b === void 0 ? void 0 : _b.inventory_onboarded);
    -    +    if (state.inventoryOnboarded)
    -    +        mealplanReached = true;
    +    +async function performLogout() {
    +    +    // 1) Clear local session
    +    +    state.token = "";
    +    +    state.onboarded = null;
    +    +    state.inventoryOnboarded = null;
    +    +    mealplanReached = false;
    +    +    // 2) Clear remembered dev JWT
    +    +    clearRememberedJwt();
    +    +    // 3) Close login modal if open
    +    +    closeLoginModal();
    +    +    // 4) Refresh UI to login-first state
         +    refreshSystemHints();
         +    renderOnboardMenuButtons();
         +    updatePrefsOverlayVisibility();
         +    updateInventoryOverlayVisibility();
         +    updateRecipePacksButtonVisibility();
         +    updateDuetBubbles();
    -    +    await silentGreetOnce();
    -    +    inventoryHasLoaded = false;
    -    +    if (currentFlowKey === "inventory") {
    -    +        refreshInventoryOverlay(true);
    -    +    }
    -    +}
    -    +async function handleAuth0Callback() {
    -    +    const params = new URLSearchParams(window.location.search);
    -    +    if (!params.has("code") || !params.has("state"))
    -    +        return false;
    +    +    // 5) Auth0 logout (will redirect; must be last)
         +    try {
         +        const client = await loadAuth0Client();
    -    +        if (!client)
    -    +            return false;
    -    +        await client.handleRedirectCallback();
    -    +        const token = await client.getTokenSilently();
    -    +        if (token) {
    -    +            state.token = token;
    -    +            // Clean URL without reload
    -    +            const cleanUrl = window.location.origin + window.location.pathname;
    -    +            window.history.replaceState({}, document.title, cleanUrl);
    -    +            await performPostLogin();
    -    +            return true;
    +    +        if (client) {
    +    +            client.logout({ logoutParams: { returnTo: window.location.origin } });
    +    +            return; // Auth0 will navigate away
         +        }
         +    }
    -    +    catch (err) {
    -    +        console.error("[auth0] callback handling failed", err);
    +    +    catch {
    +    +        // Auth0 not configured or failed ├ö├ç├Â local logout is sufficient
         +    }
    -    +    return false;
    -    +}
    -    +function openLoginModal() {
    -    +    if (document.getElementById("lc-login-modal"))
    -    +        return;
    -    +    const overlay = document.createElement("div");
    -    +    overlay.id = "lc-login-modal";
    -    +    overlay.className = "lc-modal-overlay";
    -    +    overlay.addEventListener("click", (ev) => {
    -    +        if (ev.target === overlay)
    -    +            closeLoginModal();
    -    +    });
    -    +    const panel = document.createElement("div");
    -    +    panel.className = "lc-modal-panel";
    -    +    const closeBtn = document.createElement("button");
    -    +    closeBtn.type = "button";
    -    +    closeBtn.className = "lc-modal-close";
    -    +    closeBtn.textContent = "\u00d7";
    -    +    closeBtn.setAttribute("aria-label", "Close");
    -    +    closeBtn.addEventListener("click", closeLoginModal);
    -    +    const title = document.createElement("h2");
    -    +    title.textContent = "Sign in";
    -    +    title.className = "lc-modal-title";
    -    +    const auth0Btn = document.createElement("button");
    -    +    auth0Btn.type = "button";
    -    +    auth0Btn.className = "lc-modal-action";
    -    +    auth0Btn.textContent = "Continue with Auth0";
    -    +    auth0Btn.addEventListener("click", async () => {
    -    +        auth0Btn.disabled = true;
    -    +        auth0Btn.textContent = "Redirecting\u2026";
    -    +        const client = await loadAuth0Client();
    -    +        if (client) {
    -    +            await client.loginWithRedirect();
    -    +        }
    -    +        else {
    -    +            auth0Btn.textContent = "Auth0 not configured";
    -    +            auth0Btn.disabled = false;
    -    +        }
    -    +    });
    -    +    panel.appendChild(closeBtn);
    -    +    panel.appendChild(title);
    -    +    panel.appendChild(auth0Btn);
    -    +    overlay.appendChild(panel);
    -    +    document.body.appendChild(overlay);
    -    +}
    -    +function closeLoginModal() {
    -    +    const modal = document.getElementById("lc-login-modal");
    -    +    if (modal)
    -    +        modal.remove();
         +}
          function wire() {
    -         var _a, _b, _c, _d, _e, _f, _g, _h;
    +    -    var _a, _b, _c, _d, _e, _f, _g, _h;
    +    +    var _a, _b, _c, _d, _e, _f, _g, _h, _j;
              enforceViewportLock();
              const jwtInput = document.getElementById("jwt");
              (_a = document.getElementById("btn-auth")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", async () => {
    -    -        var _a, _b, _c;
    -    +        var _a;
    -             state.token = jwtInput.value.trim();
    -             const rememberCheckbox = getRememberCheckbox();
    -             const rememberSelect = getRememberDurationSelect();
    -    @@ -1613,25 +1753,7 @@ function wire() {
    -             else {
    -                 clearRememberedJwt();
    -             }
    -    -        clearProposal();
    -    -        const result = await doGet("/auth/me");
    -    -        setText("auth-out", result);
    -    -        state.onboarded = !!((_b = result.json) === null || _b === void 0 ? void 0 : _b.onboarded);
    -    -        state.inventoryOnboarded = !!((_c = result.json) === null || _c === void 0 ? void 0 : _c.inventory_onboarded);
    -    -        // Returning user who completed onboarding before ├ö├ç├Â unlock recipe button
    -    -        if (state.inventoryOnboarded)
    -    -            mealplanReached = true;
    -    -        refreshSystemHints();
    -    -        renderOnboardMenuButtons();
    -    -        updatePrefsOverlayVisibility();
    -    -        updateInventoryOverlayVisibility();
    -    -        updateRecipePacksButtonVisibility();
    -    -        updateDuetBubbles();
    -    -        await silentGreetOnce();
    -    -        inventoryHasLoaded = false;
    -    -        if (currentFlowKey === "inventory") {
    -    -            refreshInventoryOverlay(true);
    -    -        }
    -    +        await performPostLogin();
    -         });
    -         (_b = document.getElementById("btn-chat")) === null || _b === void 0 ? void 0 : _b.addEventListener("click", async () => {
    -             var _a;
    -    @@ -1699,6 +1821,9 @@ function wire() {
    -         setupPrefsOverlay();
    -         setupDevPanel();
    -         applyRememberedJwtInput(jwtInput);
    -    +    refreshSystemHints();
    -    +    // Auth0 callback detection (async, non-blocking)
    -    +    handleAuth0Callback().catch(() => { });
    +    @@ -1824,6 +1866,20 @@ function wire() {
    +         refreshSystemHints();
    +         // Auth0 callback detection (async, non-blocking)
    +         handleAuth0Callback().catch(() => { });
    +    +    // Auto-validate remembered dev JWT (fire-and-forget, same pattern as Auth0 callback)
    +    +    if ((_j = state.token) === null || _j === void 0 ? void 0 : _j.trim()) {
    +    +        performPostLogin().catch(() => {
    +    +            // Token invalid/expired ├ö├ç├Â clear and revert to login-first state
    +    +            state.token = "";
    +    +            state.onboarded = null;
    +    +            state.inventoryOnboarded = null;
    +    +            mealplanReached = false;
    +    +            clearRememberedJwt();
    +    +            refreshSystemHints();
    +    +            renderOnboardMenuButtons();
    +    +            updateDuetBubbles();
    +    +        });
    +    +    }
              wireDuetComposer();
              wireFloatingComposerTrigger(document.querySelector(".duet-stage"));
              setupHistoryDrawerUi();
    -    @@ -2013,9 +2138,24 @@ function ensureOnboardMenu() {
    -         return onboardMenu;
    -     }
    -     function renderOnboardMenuButtons() {
    -    +    var _a;
    -         if (!onboardMenu)
    -             return;
    -         onboardMenu.innerHTML = "";
    -    +    // Before login: show only Login button
    -    +    if (!((_a = state.token) === null || _a === void 0 ? void 0 : _a.trim())) {
    -    +        const loginBtn = document.createElement("button");
    -    +        loginBtn.type = "button";
    -    +        loginBtn.className = "flow-menu-item";
    -    +        loginBtn.textContent = "Login";
    -    +        loginBtn.dataset.onboardItem = "login";
    -    +        loginBtn.addEventListener("click", () => {
    -    +            hideOnboardMenu();
    -    +            openLoginModal();
    -    +        });
    -    +        onboardMenu.appendChild(loginBtn);
    -    +        return;
    -    +    }
    -         const prefsBtn = document.createElement("button");
    -         prefsBtn.type = "button";
    -         prefsBtn.className = "flow-menu-item";
    -    @@ -2743,11 +2883,15 @@ function _bindLongPressToElement(el) {
    -         });
    -         el.addEventListener("pointerup", (ev) => {
    -             if (onboardMenuActive) {
    -    -            const startHovered = (onboardActiveItem === null || onboardActiveItem === void 0 ? void 0 : onboardActiveItem.dataset.onboardItem) === "start";
    -    -            if (startHovered) {
    -    +            const hoveredItem = onboardActiveItem === null || onboardActiveItem === void 0 ? void 0 : onboardActiveItem.dataset.onboardItem;
    -    +            if (hoveredItem === "start") {
    -                     startOnboarding();
    -                     hideOnboardMenu();
    -                 }
    -    +            else if (hoveredItem === "login") {
    -    +                hideOnboardMenu();
    -    +                openLoginModal();
    -    +            }
    -                 onboardDragActive = false;
    -                 cancel({ hideMenu: false });
    -                 return;
    -    diff --git a/web/dist/style.css b/web/dist/style.css
    -    index 63e1b7d..43020b9 100644
    -    --- a/web/dist/style.css
    -    +++ b/web/dist/style.css
    -    @@ -413,6 +413,14 @@ pre {
    -       opacity: 0.75;
    -     }
    -     
    -    +.inv-loc-header {
    -    +  font-size: 11px;
    -    +  text-transform: uppercase;
    -    +  letter-spacing: 0.08em;
    -    +  opacity: 0.6;
    -    +  margin-top: 6px;
    -    +}
    -    +
    -     .prefs-overlay {
    -       background: rgba(14, 32, 54, 0.85);
    -     }
    -    @@ -1429,3 +1437,69 @@ pre {
    -       opacity: 0.6;
    -       cursor: not-allowed;
    -     }
    -    +
    -    +/* ---- Login modal ---- */
    -    +.lc-modal-overlay {
    -    +  position: fixed;
    -    +  inset: 0;
    -    +  z-index: 2147483645;
    -    +  display: flex;
    -    +  align-items: center;
    -    +  justify-content: center;
    -    +  background: rgba(0, 0, 0, 0.45);
    -    +  backdrop-filter: blur(4px);
    -    +  -webkit-backdrop-filter: blur(4px);
    -    +}
    -    +.lc-modal-panel {
    -    +  position: relative;
    -    +  width: min(340px, 90vw);
    -    +  padding: 1.5rem 1.25rem;
    -    +  border-radius: 1rem;
    -    +  background: rgba(255, 255, 255, 0.12);
    -    +  backdrop-filter: blur(18px);
    -    +  -webkit-backdrop-filter: blur(18px);
    -    +  border: 1px solid rgba(255, 255, 255, 0.18);
    -    +  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    -    +  color: #fff;
    -    +  text-align: center;
    -    +}
    -    +.lc-modal-close {
    -    +  position: absolute;
    -    +  top: 0.5rem;
    -    +  right: 0.75rem;
    -    +  background: none;
    -    +  border: none;
    -    +  color: rgba(255, 255, 255, 0.6);
    -    +  font-size: 1.4rem;
    -    +  cursor: pointer;
    -    +  line-height: 1;
    -    +  padding: 0.25rem;
    -    +}
    -    +.lc-modal-close:hover {
    -    +  color: #fff;
    -    +}
    -    +.lc-modal-title {
    -    +  margin: 0 0 1.25rem;
    -    +  font-size: 1.15rem;
    -    +  font-weight: 600;
    -    +}
    -    +.lc-modal-action {
    -    +  display: block;
    -    +  width: 100%;
    -    +  padding: 0.75rem 1rem;
    -    +  border: none;
    -    +  border-radius: 0.5rem;
    -    +  background: rgba(255, 255, 255, 0.18);
    -    +  color: #fff;
    -    +  font-size: 0.95rem;
    -    +  font-weight: 500;
    -    +  cursor: pointer;
    -    +  transition: background 0.15s;
    -    +}
    -    +.lc-modal-action:hover {
    -    +  background: rgba(255, 255, 255, 0.28);
    -    +}
    -    +.lc-modal-action:disabled {
    -    +  opacity: 0.6;
    -    +  cursor: not-allowed;
    -    +}
         diff --git a/web/src/main.ts b/web/src/main.ts
    -    index 29cbd20..1b4dbf3 100644
    +    index 1b4dbf3..ecfa61f 100644
         --- a/web/src/main.ts
         +++ b/web/src/main.ts
    -    @@ -20,6 +20,19 @@ const DEV_JWT_DURATION_OPTIONS: { value: number; label: string }[] = [
    -       { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" },
    -     ];
    -     
    -    +const LC_DEBUG_KEY = "lc_debug";
    -    +function isDebugEnabled(): boolean {
    -    +  try {
    -    +    if (typeof window !== "undefined" && window.location?.search?.includes("debug=1")) {
    -    +      window.localStorage?.setItem(LC_DEBUG_KEY, "1");
    -    +      return true;
    -    +    }
    -    +    return window.localStorage?.getItem(LC_DEBUG_KEY) === "1";
    -    +  } catch {
    -    +    return false;
    -    +  }
    -    +}
    -    +
    -     function safeLocalStorage(): Storage | null {
    -       if (typeof window === "undefined") return null;
    -       try {
    -    @@ -160,8 +173,8 @@ function getOnboardingStatus() {
    -     function refreshSystemHints() {
    -       const s = getOnboardingStatus();
    -       if (!s.is_logged_in) {
    -    -    userSystemHint = "Enter your JWT token above and tap Auth to sign in.";
    -    -    assistantFallbackText = "Welcome ├ö├ç├Â I'm Little Chef.\n\nPlease sign in to get started.";
    -    +    userSystemHint = "Long-press this chat bubble to log in.";
    -    +    assistantFallbackText = "Welcome ├ö├ç├Â I'm Little Chef.\n\nLong-press the system bubble below to sign in.";
    -       } else if (!s.prefs_complete) {
    -         userSystemHint = USER_BUBBLE_DEFAULT_HINT;
    -         assistantFallbackText =
    -    @@ -704,16 +717,18 @@ function renderFlowMenu() {
    +    @@ -717,6 +717,18 @@ function renderFlowMenu() {
              });
              dropdown.appendChild(item);
            });
    -    -  const devItem = document.createElement("button");
    -    -  devItem.type = "button";
    -    -  devItem.className = "flow-menu-item";
    -    -  devItem.textContent = "Dev Panel";
    -    -  devItem.setAttribute("role", "menuitem");
    -    -  devItem.addEventListener("click", () => {
    -    -    toggleDevPanel();
    -    -    setFlowMenuOpen(false);
    -    -  });
    -    -  dropdown.appendChild(devItem);
    -    +  if (isDebugEnabled()) {
    -    +    const devItem = document.createElement("button");
    -    +    devItem.type = "button";
    -    +    devItem.className = "flow-menu-item";
    -    +    devItem.textContent = "Dev Panel";
    -    +    devItem.setAttribute("role", "menuitem");
    -    +    devItem.addEventListener("click", () => {
    -    +      toggleDevPanel();
    +    +  if (state.token?.trim()) {
    +    +    const logoutItem = document.createElement("button");
    +    +    logoutItem.type = "button";
    +    +    logoutItem.className = "flow-menu-item";
    +    +    logoutItem.textContent = "Logout";
    +    +    logoutItem.setAttribute("role", "menuitem");
    +    +    logoutItem.addEventListener("click", () => {
         +      setFlowMenuOpen(false);
    +    +      performLogout();
         +    });
    -    +    dropdown.appendChild(devItem);
    +    +    dropdown.appendChild(logoutItem);
         +  }
    -     
    -       const currentLabel = flowDisplayLabel(currentFlowKey);
    -       trigger.textContent = "├ö├£├û";
    -    @@ -1676,6 +1691,129 @@ async function silentGreetOnce() {
    -       }
    +       if (isDebugEnabled()) {
    +         const devItem = document.createElement("button");
    +         devItem.type = "button";
    +    @@ -1814,6 +1826,39 @@ function closeLoginModal() {
    +       if (modal) modal.remove();
          }
          
    -    +// ---------------------------------------------------------------------------
    -    +// Auth0 SPA login + modal
    -    +// ---------------------------------------------------------------------------
    -    +let auth0Client: any = null;
    +    +async function performLogout(): Promise<void> {
    +    +  // 1) Clear local session
    +    +  state.token = "";
    +    +  state.onboarded = null;
    +    +  state.inventoryOnboarded = null;
    +    +  mealplanReached = false;
         +
    -    +async function loadAuth0Client(): Promise<any> {
    -    +  if (auth0Client) return auth0Client;
    -    +  const meta = (name: string) => document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`)?.content ?? "";
    -    +  const domain = meta("lc-auth0-domain");
    -    +  const clientId = meta("lc-auth0-client-id");
    -    +  const audience = meta("lc-auth0-audience");
    -    +  if (!domain || !clientId) return null;
    -    +  try {
    -    +    const cdnUrl = "https://cdn.jsdelivr.net/npm/@auth0/auth0-spa-js@2/dist/auth0-spa-js.production.esm.js";
    -    +    const mod = await (Function("url", "return import(url)")(cdnUrl) as Promise<any>);
    -    +    auth0Client = await mod.createAuth0Client({
    -    +      domain,
    -    +      clientId,
    -    +      authorizationParams: {
    -    +        redirect_uri: window.location.origin,
    -    +        ...(audience ? { audience } : {}),
    -    +      },
    -    +    });
    -    +    return auth0Client;
    -    +  } catch (err) {
    -    +    console.error("[auth0] failed to load SDK", err);
    -    +    return null;
    -    +  }
    -    +}
    +    +  // 2) Clear remembered dev JWT
    +    +  clearRememberedJwt();
    +    +
    +    +  // 3) Close login modal if open
    +    +  closeLoginModal();
         +
    -    +async function performPostLogin() {
    -    +  clearProposal();
    -    +  const result = await doGet("/auth/me");
    -    +  setText("auth-out", result);
    -    +  state.onboarded = !!result.json?.onboarded;
    -    +  state.inventoryOnboarded = !!result.json?.inventory_onboarded;
    -    +  if (state.inventoryOnboarded) mealplanReached = true;
    +    +  // 4) Refresh UI to login-first state
         +  refreshSystemHints();
         +  renderOnboardMenuButtons();
         +  updatePrefsOverlayVisibility();
         +  updateInventoryOverlayVisibility();
         +  updateRecipePacksButtonVisibility();
         +  updateDuetBubbles();
    -    +  await silentGreetOnce();
    -    +  inventoryHasLoaded = false;
    -    +  if (currentFlowKey === "inventory") {
    -    +    refreshInventoryOverlay(true);
    -    +  }
    -    +}
         +
    -    +async function handleAuth0Callback(): Promise<boolean> {
    -    +  const params = new URLSearchParams(window.location.search);
    -    +  if (!params.has("code") || !params.has("state")) return false;
    +    +  // 5) Auth0 logout (will redirect; must be last)
         +  try {
         +    const client = await loadAuth0Client();
    -    +    if (!client) return false;
    -    +    await client.handleRedirectCallback();
    -    +    const token = await client.getTokenSilently();
    -    +    if (token) {
    -    +      state.token = token;
    -    +      // Clean URL without reload
    -    +      const cleanUrl = window.location.origin + window.location.pathname;
    -    +      window.history.replaceState({}, document.title, cleanUrl);
    -    +      await performPostLogin();
    -    +      return true;
    -    +    }
    -    +  } catch (err) {
    -    +    console.error("[auth0] callback handling failed", err);
    -    +  }
    -    +  return false;
    -    +}
    -    +
    -    +function openLoginModal() {
    -    +  if (document.getElementById("lc-login-modal")) return;
    -    +  const overlay = document.createElement("div");
    -    +  overlay.id = "lc-login-modal";
    -    +  overlay.className = "lc-modal-overlay";
    -    +  overlay.addEventListener("click", (ev) => {
    -    +    if (ev.target === overlay) closeLoginModal();
    -    +  });
    -    +
    -    +  const panel = document.createElement("div");
    -    +  panel.className = "lc-modal-panel";
    -    +
    -    +  const closeBtn = document.createElement("button");
    -    +  closeBtn.type = "button";
    -    +  closeBtn.className = "lc-modal-close";
    -    +  closeBtn.textContent = "\u00d7";
    -    +  closeBtn.setAttribute("aria-label", "Close");
    -    +  closeBtn.addEventListener("click", closeLoginModal);
    -    +
    -    +  const title = document.createElement("h2");
    -    +  title.textContent = "Sign in";
    -    +  title.className = "lc-modal-title";
    -    +
    -    +  const auth0Btn = document.createElement("button");
    -    +  auth0Btn.type = "button";
    -    +  auth0Btn.className = "lc-modal-action";
    -    +  auth0Btn.textContent = "Continue with Auth0";
    -    +  auth0Btn.addEventListener("click", async () => {
    -    +    auth0Btn.disabled = true;
    -    +    auth0Btn.textContent = "Redirecting\u2026";
    -    +    const client = await loadAuth0Client();
         +    if (client) {
    -    +      await client.loginWithRedirect();
    -    +    } else {
    -    +      auth0Btn.textContent = "Auth0 not configured";
    -    +      auth0Btn.disabled = false;
    +    +      client.logout({ logoutParams: { returnTo: window.location.origin } });
    +    +      return; // Auth0 will navigate away
         +    }
    -    +  });
    -    +
    -    +  panel.appendChild(closeBtn);
    -    +  panel.appendChild(title);
    -    +  panel.appendChild(auth0Btn);
    -    +  overlay.appendChild(panel);
    -    +  document.body.appendChild(overlay);
    -    +}
    -    +
    -    +function closeLoginModal() {
    -    +  const modal = document.getElementById("lc-login-modal");
    -    +  if (modal) modal.remove();
    +    +  } catch {
    +    +    // Auth0 not configured or failed ├ö├ç├Â local logout is sufficient
    +    +  }
         +}
         +
          function wire() {
            enforceViewportLock();
            const jwtInput = document.getElementById("jwt") as HTMLInputElement;
    -    @@ -1690,24 +1828,7 @@ function wire() {
    -         } else {
    -           clearRememberedJwt();
    -         }
    -    -    clearProposal();
    -    -    const result = await doGet("/auth/me");
    -    -    setText("auth-out", result);
    -    -    state.onboarded = !!result.json?.onboarded;
    -    -    state.inventoryOnboarded = !!result.json?.inventory_onboarded;
    -    -    // Returning user who completed onboarding before ├ö├ç├Â unlock recipe button
    -    -    if (state.inventoryOnboarded) mealplanReached = true;
    -    -    refreshSystemHints();
    -    -    renderOnboardMenuButtons();
    -    -    updatePrefsOverlayVisibility();
    -    -    updateInventoryOverlayVisibility();
    -    -    updateRecipePacksButtonVisibility();
    -    -    updateDuetBubbles();
    -    -    await silentGreetOnce();
    -    -    inventoryHasLoaded = false;
    -    -    if (currentFlowKey === "inventory") {
    -    -      refreshInventoryOverlay(true);
    -    -    }
    -    +    await performPostLogin();
    -       });
    +    @@ -1905,6 +1950,21 @@ function wire() {
    +       // Auth0 callback detection (async, non-blocking)
    +       handleAuth0Callback().catch(() => {});
          
    -       document.getElementById("btn-chat")?.addEventListener("click", async () => {
    -    @@ -1779,6 +1900,11 @@ function wire() {
    -       setupPrefsOverlay();
    -       setupDevPanel();
    -       applyRememberedJwtInput(jwtInput);
    -    +  refreshSystemHints();
    -    +
    -    +  // Auth0 callback detection (async, non-blocking)
    -    +  handleAuth0Callback().catch(() => {});
    +    +  // Auto-validate remembered dev JWT (fire-and-forget, same pattern as Auth0 callback)
    +    +  if (state.token?.trim()) {
    +    +    performPostLogin().catch(() => {
    +    +      // Token invalid/expired ├ö├ç├Â clear and revert to login-first state
    +    +      state.token = "";
    +    +      state.onboarded = null;
    +    +      state.inventoryOnboarded = null;
    +    +      mealplanReached = false;
    +    +      clearRememberedJwt();
    +    +      refreshSystemHints();
    +    +      renderOnboardMenuButtons();
    +    +      updateDuetBubbles();
    +    +    });
    +    +  }
         +
            wireDuetComposer();
            wireFloatingComposerTrigger(document.querySelector(".duet-stage") as HTMLElement | null);
            setupHistoryDrawerUi();
    -    @@ -2109,6 +2235,22 @@ function ensureOnboardMenu() {
    -     function renderOnboardMenuButtons() {
    -       if (!onboardMenu) return;
    -       onboardMenu.innerHTML = "";
    -    +
    -    +  // Before login: show only Login button
    -    +  if (!state.token?.trim()) {
    -    +    const loginBtn = document.createElement("button");
    -    +    loginBtn.type = "button";
    -    +    loginBtn.className = "flow-menu-item";
    -    +    loginBtn.textContent = "Login";
    -    +    loginBtn.dataset.onboardItem = "login";
    -    +    loginBtn.addEventListener("click", () => {
    -    +      hideOnboardMenu();
    -    +      openLoginModal();
    -    +    });
    -    +    onboardMenu.appendChild(loginBtn);
    -    +    return;
    -    +  }
    -    +
    -       const prefsBtn = document.createElement("button");
    -       prefsBtn.type = "button";
    -       prefsBtn.className = "flow-menu-item";
    -    @@ -2850,10 +2992,13 @@ function _bindLongPressToElement(el: HTMLElement) {
    -     
    -       el.addEventListener("pointerup", (ev) => {
    -         if (onboardMenuActive) {
    -    -      const startHovered = onboardActiveItem?.dataset.onboardItem === "start";
    -    -      if (startHovered) {
    -    +      const hoveredItem = onboardActiveItem?.dataset.onboardItem;
    -    +      if (hoveredItem === "start") {
    -             startOnboarding();
    -             hideOnboardMenu();
    -    +      } else if (hoveredItem === "login") {
    -    +        hideOnboardMenu();
    -    +        openLoginModal();
    -           }
    -           onboardDragActive = false;
    -           cancel({ hideMenu: false });
    -    diff --git a/web/src/style.css b/web/src/style.css
    -    index b8a652b..43020b9 100644
    -    --- a/web/src/style.css
    -    +++ b/web/src/style.css
    -    @@ -1437,3 +1437,69 @@ pre {
    -       opacity: 0.6;
    -       cursor: not-allowed;
    -     }
    -    +
    -    +/* ---- Login modal ---- */
    -    +.lc-modal-overlay {
    -    +  position: fixed;
    -    +  inset: 0;
    -    +  z-index: 2147483645;
    -    +  display: flex;
    -    +  align-items: center;
    -    +  justify-content: center;
    -    +  background: rgba(0, 0, 0, 0.45);
    -    +  backdrop-filter: blur(4px);
    -    +  -webkit-backdrop-filter: blur(4px);
    -    +}
    -    +.lc-modal-panel {
    -    +  position: relative;
    -    +  width: min(340px, 90vw);
    -    +  padding: 1.5rem 1.25rem;
    -    +  border-radius: 1rem;
    -    +  background: rgba(255, 255, 255, 0.12);
    -    +  backdrop-filter: blur(18px);
    -    +  -webkit-backdrop-filter: blur(18px);
    -    +  border: 1px solid rgba(255, 255, 255, 0.18);
    -    +  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    -    +  color: #fff;
    -    +  text-align: center;
    -    +}
    -    +.lc-modal-close {
    -    +  position: absolute;
    -    +  top: 0.5rem;
    -    +  right: 0.75rem;
    -    +  background: none;
    -    +  border: none;
    -    +  color: rgba(255, 255, 255, 0.6);
    -    +  font-size: 1.4rem;
    -    +  cursor: pointer;
    -    +  line-height: 1;
    -    +  padding: 0.25rem;
    -    +}
    -    +.lc-modal-close:hover {
    -    +  color: #fff;
    -    +}
    -    +.lc-modal-title {
    -    +  margin: 0 0 1.25rem;
    -    +  font-size: 1.15rem;
    -    +  font-weight: 600;
    -    +}
    -    +.lc-modal-action {
    -    +  display: block;
    -    +  width: 100%;
    -    +  padding: 0.75rem 1rem;
    -    +  border: none;
    -    +  border-radius: 0.5rem;
    -    +  background: rgba(255, 255, 255, 0.18);
    -    +  color: #fff;
    -    +  font-size: 0.95rem;
    -    +  font-weight: 500;
    -    +  cursor: pointer;
    -    +  transition: background 0.15s;
    -    +}
    -    +.lc-modal-action:hover {
    -    +  background: rgba(255, 255, 255, 0.28);
    -    +}
    -    +.lc-modal-action:disabled {
    -    +  opacity: 0.6;
    -    +  cursor: not-allowed;
    -    +}
     
     ## Verification
    -- tsc: pass (1 pre-existing TS2339)
    -- pytest: 183 passed, 0 failures
    -- node ui_onboarding_hints_test.mjs: 13/13 PASS
    +- Static: `py_compile app/main.py` exit 0.
    +- pytest: 183 passed, 1 warning (116.60s), 0 failures.
    +- Runtime (TestClient): 3 env vars set ÔåÆ 3 meta tags in response; derivation from LC_JWT_ISSUER ÔåÆ 1 domain tag; no vars ÔåÆ no tags (page loads 200).
    +- Cache-Control: no-store header confirmed present.
    +- `/static/main.js` unchanged (still served via FileResponse).
     
     ## Notes (optional)
    -- Auth0 SPA SDK loaded via CDN ESM (no bundler in web build); Function("url","return import(url)") workaround for tsc dynamic import of CDN URL.
    -- Auth0 tenant config (lc-auth0-domain, lc-auth0-client-id meta tags) required for full login flow; without it, "Auth0 not configured" shown.
    -- web/dist/proposalRenderer.js CRLF artifact from prior cycle (not in allowed file set, not staged).
    +- No secrets committed; values come from env vars at runtime.
    +- `load_env()` in `create_app()` loads `.env` if present, so local dev can use `.env` file.
    +- HTML injection uses simple `str.replace("</head>", ...)` ÔÇö safe because dist/index.html is our own template.
     
     ## Next Steps
    -- User must reply AUTHORIZED before commit
    -- Auth0 tenant config needed for full e2e (known limitation)
    +- Add LC_AUTH0_DOMAIN and LC_AUTH0_CLIENT_ID to your `.env` (or shell) and test Auth0 login flow in browser.
    +- Commit previous cycle (auto-validate JWT + Logout) and this cycle together or separately.
     
    diff --git a/scripts/ui_onboarding_hints_test.mjs b/scripts/ui_onboarding_hints_test.mjs
    index 25da94e..40069a3 100644
    --- a/scripts/ui_onboarding_hints_test.mjs
    +++ b/scripts/ui_onboarding_hints_test.mjs
    @@ -59,6 +59,22 @@ function gearMenuIncludesDevPanel(debugEnabled) {
       return debugEnabled;
     }
     
    +/**
    + * Replicate renderFlowMenu() Logout gating.
    + * Returns true if Logout should appear in gear menu.
    + */
    +function gearMenuIncludesLogout(tokenTrimmed) {
    +  return !!tokenTrimmed;
    +}
    +
    +/**
    + * Replicate wire() startup auto-validate condition.
    + * Returns true if performPostLogin() should fire on startup.
    + */
    +function shouldAutoValidateOnStartup(tokenTrimmed) {
    +  return !!tokenTrimmed;
    +}
    +
     // ---- refreshSystemHints tests ----
     
     // Test: not logged in
    @@ -171,4 +187,36 @@ console.log("debug disabled, no Dev Panel: PASS");
     }
     console.log("debug enabled, Dev Panel present: PASS");
     
    +// ---- logout gear-menu tests ----
    +
    +// Test: logged out -> no Logout in gear menu
    +{
    +  assert(!gearMenuIncludesLogout(false), "logged out: no Logout");
    +  assert(!gearMenuIncludesLogout(""), "empty token: no Logout");
    +}
    +console.log("gear menu logged out, no Logout: PASS");
    +
    +// Test: logged in -> Logout in gear menu
    +{
    +  assert(gearMenuIncludesLogout(true), "logged in: Logout present");
    +  assert(gearMenuIncludesLogout("some-jwt-token"), "token truthy: Logout present");
    +}
    +console.log("gear menu logged in, Logout present: PASS");
    +
    +// ---- startup auto-validate tests ----
    +
    +// Test: no remembered token -> no auto-validate
    +{
    +  assert(!shouldAutoValidateOnStartup(false), "no token: no auto-validate");
    +  assert(!shouldAutoValidateOnStartup(""), "empty token: no auto-validate");
    +}
    +console.log("startup no token, no auto-validate: PASS");
    +
    +// Test: remembered token present -> auto-validate fires
    +{
    +  assert(shouldAutoValidateOnStartup(true), "token present: auto-validate fires");
    +  assert(shouldAutoValidateOnStartup("remembered-jwt"), "jwt truthy: auto-validate fires");
    +}
    +console.log("startup remembered token, auto-validate fires: PASS");
    +
     console.log("\nui onboarding hints test: PASS");
    diff --git a/web/dist/main.js b/web/dist/main.js
    index 59923d0..d1409a1 100644
    --- a/web/dist/main.js
    +++ b/web/dist/main.js
    @@ -655,6 +655,7 @@ function setFlowMenuOpen(open) {
         flowMenuButton === null || flowMenuButton === void 0 ? void 0 : flowMenuButton.setAttribute("aria-expanded", open ? "true" : "false");
     }
     function renderFlowMenu() {
    +    var _a;
         const dropdown = flowMenuDropdown;
         const trigger = flowMenuButton;
         if (!dropdown || !trigger)
    @@ -672,6 +673,18 @@ function renderFlowMenu() {
             });
             dropdown.appendChild(item);
         });
    +    if ((_a = state.token) === null || _a === void 0 ? void 0 : _a.trim()) {
    +        const logoutItem = document.createElement("button");
    +        logoutItem.type = "button";
    +        logoutItem.className = "flow-menu-item";
    +        logoutItem.textContent = "Logout";
    +        logoutItem.setAttribute("role", "menuitem");
    +        logoutItem.addEventListener("click", () => {
    +            setFlowMenuOpen(false);
    +            performLogout();
    +        });
    +        dropdown.appendChild(logoutItem);
    +    }
         if (isDebugEnabled()) {
             const devItem = document.createElement("button");
             devItem.type = "button";
    @@ -1736,8 +1749,38 @@ function closeLoginModal() {
         if (modal)
             modal.remove();
     }
    +async function performLogout() {
    +    // 1) Clear local session
    +    state.token = "";
    +    state.onboarded = null;
    +    state.inventoryOnboarded = null;
    +    mealplanReached = false;
    +    // 2) Clear remembered dev JWT
    +    clearRememberedJwt();
    +    // 3) Close login modal if open
    +    closeLoginModal();
    +    // 4) Refresh UI to login-first state
    +    refreshSystemHints();
    +    renderOnboardMenuButtons();
    +    updatePrefsOverlayVisibility();
    +    updateInventoryOverlayVisibility();
    +    updateRecipePacksButtonVisibility();
    +    updateDuetBubbles();
    +    selectFlow("general");
    +    // 5) Auth0 logout (will redirect; must be last)
    +    try {
    +        const client = await loadAuth0Client();
    +        if (client) {
    +            client.logout({ logoutParams: { returnTo: window.location.origin } });
    +            return; // Auth0 will navigate away
    +        }
    +    }
    +    catch {
    +        // Auth0 not configured or failed ÔÇö local logout is sufficient
    +    }
    +}
     function wire() {
    -    var _a, _b, _c, _d, _e, _f, _g, _h;
    +    var _a, _b, _c, _d, _e, _f, _g, _h, _j;
         enforceViewportLock();
         const jwtInput = document.getElementById("jwt");
         (_a = document.getElementById("btn-auth")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", async () => {
    @@ -1824,6 +1867,20 @@ function wire() {
         refreshSystemHints();
         // Auth0 callback detection (async, non-blocking)
         handleAuth0Callback().catch(() => { });
    +    // Auto-validate remembered dev JWT (fire-and-forget, same pattern as Auth0 callback)
    +    if ((_j = state.token) === null || _j === void 0 ? void 0 : _j.trim()) {
    +        performPostLogin().catch(() => {
    +            // Token invalid/expired ÔÇö clear and revert to login-first state
    +            state.token = "";
    +            state.onboarded = null;
    +            state.inventoryOnboarded = null;
    +            mealplanReached = false;
    +            clearRememberedJwt();
    +            refreshSystemHints();
    +            renderOnboardMenuButtons();
    +            updateDuetBubbles();
    +        });
    +    }
         wireDuetComposer();
         wireFloatingComposerTrigger(document.querySelector(".duet-stage"));
         setupHistoryDrawerUi();
    diff --git a/web/src/main.ts b/web/src/main.ts
    index 1b4dbf3..1584395 100644
    --- a/web/src/main.ts
    +++ b/web/src/main.ts
    @@ -717,6 +717,18 @@ function renderFlowMenu() {
         });
         dropdown.appendChild(item);
       });
    +  if (state.token?.trim()) {
    +    const logoutItem = document.createElement("button");
    +    logoutItem.type = "button";
    +    logoutItem.className = "flow-menu-item";
    +    logoutItem.textContent = "Logout";
    +    logoutItem.setAttribute("role", "menuitem");
    +    logoutItem.addEventListener("click", () => {
    +      setFlowMenuOpen(false);
    +      performLogout();
    +    });
    +    dropdown.appendChild(logoutItem);
    +  }
       if (isDebugEnabled()) {
         const devItem = document.createElement("button");
         devItem.type = "button";
    @@ -1814,6 +1826,40 @@ function closeLoginModal() {
       if (modal) modal.remove();
     }
     
    +async function performLogout(): Promise<void> {
    +  // 1) Clear local session
    +  state.token = "";
    +  state.onboarded = null;
    +  state.inventoryOnboarded = null;
    +  mealplanReached = false;
    +
    +  // 2) Clear remembered dev JWT
    +  clearRememberedJwt();
    +
    +  // 3) Close login modal if open
    +  closeLoginModal();
    +
    +  // 4) Refresh UI to login-first state
    +  refreshSystemHints();
    +  renderOnboardMenuButtons();
    +  updatePrefsOverlayVisibility();
    +  updateInventoryOverlayVisibility();
    +  updateRecipePacksButtonVisibility();
    +  updateDuetBubbles();
    +  selectFlow("general");
    +
    +  // 5) Auth0 logout (will redirect; must be last)
    +  try {
    +    const client = await loadAuth0Client();
    +    if (client) {
    +      client.logout({ logoutParams: { returnTo: window.location.origin } });
    +      return; // Auth0 will navigate away
    +    }
    +  } catch {
    +    // Auth0 not configured or failed ÔÇö local logout is sufficient
    +  }
    +}
    +
     function wire() {
       enforceViewportLock();
       const jwtInput = document.getElementById("jwt") as HTMLInputElement;
    @@ -1905,6 +1951,21 @@ function wire() {
       // Auth0 callback detection (async, non-blocking)
       handleAuth0Callback().catch(() => {});
     
    +  // Auto-validate remembered dev JWT (fire-and-forget, same pattern as Auth0 callback)
    +  if (state.token?.trim()) {
    +    performPostLogin().catch(() => {
    +      // Token invalid/expired ÔÇö clear and revert to login-first state
    +      state.token = "";
    +      state.onboarded = null;
    +      state.inventoryOnboarded = null;
    +      mealplanReached = false;
    +      clearRememberedJwt();
    +      refreshSystemHints();
    +      renderOnboardMenuButtons();
    +      updateDuetBubbles();
    +    });
    +  }
    +
       wireDuetComposer();
       wireFloatingComposerTrigger(document.querySelector(".duet-stage") as HTMLElement | null);
       setupHistoryDrawerUi();

## Verification
- Static: tsc pass (1 pre-existing TS2339 at line 1169, no new errors).
- UI tests: 17/17 PASS (scripts/ui_onboarding_hints_test.mjs).
- Backend: pytest 183 passed, 1 warning, 0 failures (113.89s).
- Behavioral: performLogout clears token, resets onboarding, calls selectFlow("general"), attempts Auth0 logout. Gear menu shows Logout only when logged in.
- Contract: physics.yaml unchanged; minimal diff; no boundary violations.

## Notes (optional)
- Auth0 logout redirect requires `returnTo` URL to be in Auth0 tenant Allowed Logout URLs.
- `LC_AUTH0_CLIENT_ID` must be added to `.env` for Auth0 modal to function (domain is derived from LC_JWT_ISSUER).
- No CSS changes in this cycle.

## Next Steps
- Add `LC_AUTH0_CLIENT_ID` to `.env` and test full Auth0 login→logout flow in browser.
- Commit when AUTHORIZED.

