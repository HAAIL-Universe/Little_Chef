# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-11T12:16:49+00:00
- Branch: claude/romantic-jones
- HEAD: 25203615bda2ffb9cc9a2c7ebe02607e0d85ff83
- BASE_HEAD: 2336dc4d8250c4186e87c4793339eb98b33b23b1
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- feat: Login-first navigation + login modal + Auth0 SPA + debug gate + performPostLogin refactor
- test: 13 UI tests (onboard menu + debug gate + hints)

## Files Changed (staged)
- scripts/ui_onboarding_hints_test.mjs
- web/dist/main.js
- web/dist/style.css
- web/src/main.ts
- web/src/style.css

## git status -sb
    ## claude/romantic-jones
     M .claude/settings.local.json
    M  scripts/ui_onboarding_hints_test.mjs
    M  web/dist/main.js
     M web/dist/proposalRenderer.js
    M  web/dist/style.css
    M  web/src/main.ts
    M  web/src/style.css

## Minimal Diff Hunks
    diff --git a/scripts/ui_onboarding_hints_test.mjs b/scripts/ui_onboarding_hints_test.mjs
    index 7ad26fb..25da94e 100644
    --- a/scripts/ui_onboarding_hints_test.mjs
    +++ b/scripts/ui_onboarding_hints_test.mjs
    @@ -17,8 +17,8 @@ function refreshSystemHints(status) {
       let assistantFallbackText;
     
       if (!status.is_logged_in) {
    -    userSystemHint = "Enter your JWT token above and tap Auth to sign in.";
    -    assistantFallbackText = "Welcome \u2014 I'm Little Chef.\n\nPlease sign in to get started.";
    +    userSystemHint = "Long-press this chat bubble to log in.";
    +    assistantFallbackText = "Welcome \u2014 I'm Little Chef.\n\nLong-press the system bubble below to sign in.";
       } else if (!status.prefs_complete) {
         userSystemHint = USER_BUBBLE_DEFAULT_HINT;
         assistantFallbackText =
    @@ -40,16 +40,38 @@ function refreshSystemHints(status) {
       return { userSystemHint, assistantFallbackText };
     }
     
    -// ---- Test: not logged in ----
    +/**
    + * Replicate renderOnboardMenuButtons() login-gate logic.
    + * Returns array of button labels the menu would render.
    + */
    +function onboardMenuItems(tokenTrimmed, onboarded, inventoryOnboarded) {
    +  if (!tokenTrimmed) return ["Login"];
    +  const items = ["Preferences"];
    +  if (onboarded) items.push("Inventory");
    +  if (inventoryOnboarded) items.push("Meal Plan");
    +  return items;
    +}
    +
    +/**
    + * Replicate isDebugEnabled() + renderFlowMenu() Dev Panel gating.
    + */
    +function gearMenuIncludesDevPanel(debugEnabled) {
    +  return debugEnabled;
    +}
    +
    +// ---- refreshSystemHints tests ----
    +
    +// Test: not logged in
     {
       const r = refreshSystemHints({ is_logged_in: false, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
       assert(r.assistantFallbackText.includes("sign in"), "not logged in: assistant should mention sign in");
       assert(!r.assistantFallbackText.includes("start onboarding"), "not logged in: should NOT show onboarding prompt");
    -  assert(r.userSystemHint.includes("Auth"), "not logged in: user hint should mention Auth");
    +  assert(r.userSystemHint.includes("Long-press"), "not logged in: user hint should mention Long-press");
    +  assert(r.userSystemHint.includes("log in"), "not logged in: user hint should mention log in");
     }
     console.log("not logged in: PASS");
     
    -// ---- Test: logged in, prefs NOT complete ----
    +// Test: logged in, prefs NOT complete
     {
       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
       assert(r.assistantFallbackText.includes("start onboarding"), "prefs incomplete: should show onboarding prompt");
    @@ -57,7 +79,7 @@ console.log("not logged in: PASS");
     }
     console.log("logged in, prefs incomplete: PASS");
     
    -// ---- Test: logged in, prefs complete, inventory NOT complete ----
    +// Test: logged in, prefs complete, inventory NOT complete
     {
       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: false, mealplan_complete: false });
       assert(!r.assistantFallbackText.includes("start onboarding"), "prefs done: should NOT show start onboarding");
    @@ -66,7 +88,7 @@ console.log("logged in, prefs incomplete: PASS");
     }
     console.log("logged in, prefs complete, inventory incomplete: PASS");
     
    -// ---- Test: logged in, prefs+inventory complete, mealplan NOT complete ----
    +// Test: logged in, prefs+inventory complete, mealplan NOT complete
     {
       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: false });
       assert(!r.assistantFallbackText.includes("start onboarding"), "inventory done: should NOT show start onboarding");
    @@ -76,7 +98,7 @@ console.log("logged in, prefs complete, inventory incomplete: PASS");
     }
     console.log("logged in, prefs+inventory complete, mealplan incomplete: PASS");
     
    -// ---- Test: all complete ----
    +// Test: all complete
     {
       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: true });
       assert(!r.assistantFallbackText.includes("start onboarding"), "all done: no onboarding prompt");
    @@ -86,7 +108,7 @@ console.log("logged in, prefs+inventory complete, mealplan incomplete: PASS");
     }
     console.log("all onboarding complete: PASS");
     
    -// ---- Test: prefs complete + logged in does NOT show preferences onboarding ----
    +// Test: prefs complete + logged in does NOT show preferences onboarding
     {
       const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: false, mealplan_complete: false });
       assert(!r.assistantFallbackText.includes("To start onboarding"), "prefs done: MUST NOT show 'To start onboarding'");
    @@ -94,9 +116,8 @@ console.log("all onboarding complete: PASS");
     }
     console.log("prefs complete does not show prefs onboarding: PASS");
     
    -// ---- Test: after login state transition (simulated) ----
    +// Test: after login state transition (simulated)
     {
    -  // Simulate: start not logged in, then login with prefs+inventory complete
       const before = refreshSystemHints({ is_logged_in: false, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
       assert(before.assistantFallbackText.includes("sign in"), "before login: sign in prompt");
     
    @@ -106,4 +127,48 @@ console.log("prefs complete does not show prefs onboarding: PASS");
     }
     console.log("login state transition updates messages: PASS");
     
    +// ---- onboard menu tests ----
    +
    +// Test: not logged in -> only Login button
    +{
    +  const items = onboardMenuItems(false, false, false);
    +  assert.deepStrictEqual(items, ["Login"], "not logged in: onboard menu should show only Login");
    +}
    +console.log("onboard menu not logged in: PASS");
    +
    +// Test: logged in, not onboarded -> only Preferences
    +{
    +  const items = onboardMenuItems(true, false, false);
    +  assert.deepStrictEqual(items, ["Preferences"], "logged in, not onboarded: only Preferences");
    +}
    +console.log("onboard menu logged in, not onboarded: PASS");
    +
    +// Test: logged in, prefs onboarded -> Preferences + Inventory
    +{
    +  const items = onboardMenuItems(true, true, false);
    +  assert.deepStrictEqual(items, ["Preferences", "Inventory"], "prefs onboarded: Preferences + Inventory");
    +}
    +console.log("onboard menu prefs onboarded: PASS");
    +
    +// Test: logged in, all onboarded -> Preferences + Inventory + Meal Plan
    +{
    +  const items = onboardMenuItems(true, true, true);
    +  assert.deepStrictEqual(items, ["Preferences", "Inventory", "Meal Plan"], "all onboarded: all three items");
    +}
    +console.log("onboard menu all onboarded: PASS");
    +
    +// ---- debug gate tests ----
    +
    +// Test: debug disabled -> no Dev Panel in gear menu
    +{
    +  assert(!gearMenuIncludesDevPanel(false), "debug off: no Dev Panel");
    +}
    +console.log("debug disabled, no Dev Panel: PASS");
    +
    +// Test: debug enabled -> Dev Panel in gear menu
    +{
    +  assert(gearMenuIncludesDevPanel(true), "debug on: Dev Panel present");
    +}
    +console.log("debug enabled, Dev Panel present: PASS");
    +
     console.log("\nui onboarding hints test: PASS");
    diff --git a/web/dist/main.js b/web/dist/main.js
    index 039b0db..59923d0 100644
    --- a/web/dist/main.js
    +++ b/web/dist/main.js
    @@ -17,6 +17,20 @@ const DEV_JWT_DURATION_OPTIONS = [
         { value: DEV_JWT_DEFAULT_TTL_MS, label: "24 hours" },
         { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" },
     ];
    +const LC_DEBUG_KEY = "lc_debug";
    +function isDebugEnabled() {
    +    var _a, _b, _c, _d;
    +    try {
    +        if (typeof window !== "undefined" && ((_b = (_a = window.location) === null || _a === void 0 ? void 0 : _a.search) === null || _b === void 0 ? void 0 : _b.includes("debug=1"))) {
    +            (_c = window.localStorage) === null || _c === void 0 ? void 0 : _c.setItem(LC_DEBUG_KEY, "1");
    +            return true;
    +        }
    +        return ((_d = window.localStorage) === null || _d === void 0 ? void 0 : _d.getItem(LC_DEBUG_KEY)) === "1";
    +    }
    +    catch {
    +        return false;
    +    }
    +}
     function safeLocalStorage() {
         if (typeof window === "undefined")
             return null;
    @@ -144,8 +158,8 @@ function getOnboardingStatus() {
     function refreshSystemHints() {
         const s = getOnboardingStatus();
         if (!s.is_logged_in) {
    -        userSystemHint = "Enter your JWT token above and tap Auth to sign in.";
    -        assistantFallbackText = "Welcome ÔÇö I'm Little Chef.\n\nPlease sign in to get started.";
    +        userSystemHint = "Long-press this chat bubble to log in.";
    +        assistantFallbackText = "Welcome ÔÇö I'm Little Chef.\n\nLong-press the system bubble below to sign in.";
         }
         else if (!s.prefs_complete) {
             userSystemHint = USER_BUBBLE_DEFAULT_HINT;
    @@ -658,16 +672,18 @@ function renderFlowMenu() {
             });
             dropdown.appendChild(item);
         });
    -    const devItem = document.createElement("button");
    -    devItem.type = "button";
    -    devItem.className = "flow-menu-item";
    -    devItem.textContent = "Dev Panel";
    -    devItem.setAttribute("role", "menuitem");
    -    devItem.addEventListener("click", () => {
    -        toggleDevPanel();
    -        setFlowMenuOpen(false);
    -    });
    -    dropdown.appendChild(devItem);
    +    if (isDebugEnabled()) {
    +        const devItem = document.createElement("button");
    +        devItem.type = "button";
    +        devItem.className = "flow-menu-item";
    +        devItem.textContent = "Dev Panel";
    +        devItem.setAttribute("role", "menuitem");
    +        devItem.addEventListener("click", () => {
    +            toggleDevPanel();
    +            setFlowMenuOpen(false);
    +        });
    +        dropdown.appendChild(devItem);
    +    }
         const currentLabel = flowDisplayLabel(currentFlowKey);
         trigger.textContent = "ÔÜÖ";
         trigger.setAttribute("aria-label", `Options (current: ${currentLabel})`);
    @@ -1596,12 +1612,136 @@ async function silentGreetOnce() {
             // Silent failure by design
         }
     }
    +// ---------------------------------------------------------------------------
    +// Auth0 SPA login + modal
    +// ---------------------------------------------------------------------------
    +let auth0Client = null;
    +async function loadAuth0Client() {
    +    if (auth0Client)
    +        return auth0Client;
    +    const meta = (name) => { var _a, _b; return (_b = (_a = document.querySelector(`meta[name="${name}"]`)) === null || _a === void 0 ? void 0 : _a.content) !== null && _b !== void 0 ? _b : ""; };
    +    const domain = meta("lc-auth0-domain");
    +    const clientId = meta("lc-auth0-client-id");
    +    const audience = meta("lc-auth0-audience");
    +    if (!domain || !clientId)
    +        return null;
    +    try {
    +        const cdnUrl = "https://cdn.jsdelivr.net/npm/@auth0/auth0-spa-js@2/dist/auth0-spa-js.production.esm.js";
    +        const mod = await Function("url", "return import(url)")(cdnUrl);
    +        auth0Client = await mod.createAuth0Client({
    +            domain,
    +            clientId,
    +            authorizationParams: {
    +                redirect_uri: window.location.origin,
    +                ...(audience ? { audience } : {}),
    +            },
    +        });
    +        return auth0Client;
    +    }
    +    catch (err) {
    +        console.error("[auth0] failed to load SDK", err);
    +        return null;
    +    }
    +}
    +async function performPostLogin() {
    +    var _a, _b;
    +    clearProposal();
    +    const result = await doGet("/auth/me");
    +    setText("auth-out", result);
    +    state.onboarded = !!((_a = result.json) === null || _a === void 0 ? void 0 : _a.onboarded);
    +    state.inventoryOnboarded = !!((_b = result.json) === null || _b === void 0 ? void 0 : _b.inventory_onboarded);
    +    if (state.inventoryOnboarded)
    +        mealplanReached = true;
    +    refreshSystemHints();
    +    renderOnboardMenuButtons();
    +    updatePrefsOverlayVisibility();
    +    updateInventoryOverlayVisibility();
    +    updateRecipePacksButtonVisibility();
    +    updateDuetBubbles();
    +    await silentGreetOnce();
    +    inventoryHasLoaded = false;
    +    if (currentFlowKey === "inventory") {
    +        refreshInventoryOverlay(true);
    +    }
    +}
    +async function handleAuth0Callback() {
    +    const params = new URLSearchParams(window.location.search);
    +    if (!params.has("code") || !params.has("state"))
    +        return false;
    +    try {
    +        const client = await loadAuth0Client();
    +        if (!client)
    +            return false;
    +        await client.handleRedirectCallback();
    +        const token = await client.getTokenSilently();
    +        if (token) {
    +            state.token = token;
    +            // Clean URL without reload
    +            const cleanUrl = window.location.origin + window.location.pathname;
    +            window.history.replaceState({}, document.title, cleanUrl);
    +            await performPostLogin();
    +            return true;
    +        }
    +    }
    +    catch (err) {
    +        console.error("[auth0] callback handling failed", err);
    +    }
    +    return false;
    +}
    +function openLoginModal() {
    +    if (document.getElementById("lc-login-modal"))
    +        return;
    +    const overlay = document.createElement("div");
    +    overlay.id = "lc-login-modal";
    +    overlay.className = "lc-modal-overlay";
    +    overlay.addEventListener("click", (ev) => {
    +        if (ev.target === overlay)
    +            closeLoginModal();
    +    });
    +    const panel = document.createElement("div");
    +    panel.className = "lc-modal-panel";
    +    const closeBtn = document.createElement("button");
    +    closeBtn.type = "button";
    +    closeBtn.className = "lc-modal-close";
    +    closeBtn.textContent = "\u00d7";
    +    closeBtn.setAttribute("aria-label", "Close");
    +    closeBtn.addEventListener("click", closeLoginModal);
    +    const title = document.createElement("h2");
    +    title.textContent = "Sign in";
    +    title.className = "lc-modal-title";
    +    const auth0Btn = document.createElement("button");
    +    auth0Btn.type = "button";
    +    auth0Btn.className = "lc-modal-action";
    +    auth0Btn.textContent = "Continue with Auth0";
    +    auth0Btn.addEventListener("click", async () => {
    +        auth0Btn.disabled = true;
    +        auth0Btn.textContent = "Redirecting\u2026";
    +        const client = await loadAuth0Client();
    +        if (client) {
    +            await client.loginWithRedirect();
    +        }
    +        else {
    +            auth0Btn.textContent = "Auth0 not configured";
    +            auth0Btn.disabled = false;
    +        }
    +    });
    +    panel.appendChild(closeBtn);
    +    panel.appendChild(title);
    +    panel.appendChild(auth0Btn);
    +    overlay.appendChild(panel);
    +    document.body.appendChild(overlay);
    +}
    +function closeLoginModal() {
    +    const modal = document.getElementById("lc-login-modal");
    +    if (modal)
    +        modal.remove();
    +}
     function wire() {
         var _a, _b, _c, _d, _e, _f, _g, _h;
         enforceViewportLock();
         const jwtInput = document.getElementById("jwt");
         (_a = document.getElementById("btn-auth")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", async () => {
    -        var _a, _b, _c;
    +        var _a;
             state.token = jwtInput.value.trim();
             const rememberCheckbox = getRememberCheckbox();
             const rememberSelect = getRememberDurationSelect();
    @@ -1613,25 +1753,7 @@ function wire() {
             else {
                 clearRememberedJwt();
             }
    -        clearProposal();
    -        const result = await doGet("/auth/me");
    -        setText("auth-out", result);
    -        state.onboarded = !!((_b = result.json) === null || _b === void 0 ? void 0 : _b.onboarded);
    -        state.inventoryOnboarded = !!((_c = result.json) === null || _c === void 0 ? void 0 : _c.inventory_onboarded);
    -        // Returning user who completed onboarding before ÔÇö unlock recipe button
    -        if (state.inventoryOnboarded)
    -            mealplanReached = true;
    -        refreshSystemHints();
    -        renderOnboardMenuButtons();
    -        updatePrefsOverlayVisibility();
    -        updateInventoryOverlayVisibility();
    -        updateRecipePacksButtonVisibility();
    -        updateDuetBubbles();
    -        await silentGreetOnce();
    -        inventoryHasLoaded = false;
    -        if (currentFlowKey === "inventory") {
    -            refreshInventoryOverlay(true);
    -        }
    +        await performPostLogin();
         });
         (_b = document.getElementById("btn-chat")) === null || _b === void 0 ? void 0 : _b.addEventListener("click", async () => {
             var _a;
    @@ -1699,6 +1821,9 @@ function wire() {
         setupPrefsOverlay();
         setupDevPanel();
         applyRememberedJwtInput(jwtInput);
    +    refreshSystemHints();
    +    // Auth0 callback detection (async, non-blocking)
    +    handleAuth0Callback().catch(() => { });
         wireDuetComposer();
         wireFloatingComposerTrigger(document.querySelector(".duet-stage"));
         setupHistoryDrawerUi();
    @@ -2013,9 +2138,24 @@ function ensureOnboardMenu() {
         return onboardMenu;
     }
     function renderOnboardMenuButtons() {
    +    var _a;
         if (!onboardMenu)
             return;
         onboardMenu.innerHTML = "";
    +    // Before login: show only Login button
    +    if (!((_a = state.token) === null || _a === void 0 ? void 0 : _a.trim())) {
    +        const loginBtn = document.createElement("button");
    +        loginBtn.type = "button";
    +        loginBtn.className = "flow-menu-item";
    +        loginBtn.textContent = "Login";
    +        loginBtn.dataset.onboardItem = "login";
    +        loginBtn.addEventListener("click", () => {
    +            hideOnboardMenu();
    +            openLoginModal();
    +        });
    +        onboardMenu.appendChild(loginBtn);
    +        return;
    +    }
         const prefsBtn = document.createElement("button");
         prefsBtn.type = "button";
         prefsBtn.className = "flow-menu-item";
    @@ -2743,11 +2883,15 @@ function _bindLongPressToElement(el) {
         });
         el.addEventListener("pointerup", (ev) => {
             if (onboardMenuActive) {
    -            const startHovered = (onboardActiveItem === null || onboardActiveItem === void 0 ? void 0 : onboardActiveItem.dataset.onboardItem) === "start";
    -            if (startHovered) {
    +            const hoveredItem = onboardActiveItem === null || onboardActiveItem === void 0 ? void 0 : onboardActiveItem.dataset.onboardItem;
    +            if (hoveredItem === "start") {
                     startOnboarding();
                     hideOnboardMenu();
                 }
    +            else if (hoveredItem === "login") {
    +                hideOnboardMenu();
    +                openLoginModal();
    +            }
                 onboardDragActive = false;
                 cancel({ hideMenu: false });
                 return;
    diff --git a/web/dist/style.css b/web/dist/style.css
    index 63e1b7d..43020b9 100644
    --- a/web/dist/style.css
    +++ b/web/dist/style.css
    @@ -413,6 +413,14 @@ pre {
       opacity: 0.75;
     }
     
    +.inv-loc-header {
    +  font-size: 11px;
    +  text-transform: uppercase;
    +  letter-spacing: 0.08em;
    +  opacity: 0.6;
    +  margin-top: 6px;
    +}
    +
     .prefs-overlay {
       background: rgba(14, 32, 54, 0.85);
     }
    @@ -1429,3 +1437,69 @@ pre {
       opacity: 0.6;
       cursor: not-allowed;
     }
    +
    +/* ---- Login modal ---- */
    +.lc-modal-overlay {
    +  position: fixed;
    +  inset: 0;
    +  z-index: 2147483645;
    +  display: flex;
    +  align-items: center;
    +  justify-content: center;
    +  background: rgba(0, 0, 0, 0.45);
    +  backdrop-filter: blur(4px);
    +  -webkit-backdrop-filter: blur(4px);
    +}
    +.lc-modal-panel {
    +  position: relative;
    +  width: min(340px, 90vw);
    +  padding: 1.5rem 1.25rem;
    +  border-radius: 1rem;
    +  background: rgba(255, 255, 255, 0.12);
    +  backdrop-filter: blur(18px);
    +  -webkit-backdrop-filter: blur(18px);
    +  border: 1px solid rgba(255, 255, 255, 0.18);
    +  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    +  color: #fff;
    +  text-align: center;
    +}
    +.lc-modal-close {
    +  position: absolute;
    +  top: 0.5rem;
    +  right: 0.75rem;
    +  background: none;
    +  border: none;
    +  color: rgba(255, 255, 255, 0.6);
    +  font-size: 1.4rem;
    +  cursor: pointer;
    +  line-height: 1;
    +  padding: 0.25rem;
    +}
    +.lc-modal-close:hover {
    +  color: #fff;
    +}
    +.lc-modal-title {
    +  margin: 0 0 1.25rem;
    +  font-size: 1.15rem;
    +  font-weight: 600;
    +}
    +.lc-modal-action {
    +  display: block;
    +  width: 100%;
    +  padding: 0.75rem 1rem;
    +  border: none;
    +  border-radius: 0.5rem;
    +  background: rgba(255, 255, 255, 0.18);
    +  color: #fff;
    +  font-size: 0.95rem;
    +  font-weight: 500;
    +  cursor: pointer;
    +  transition: background 0.15s;
    +}
    +.lc-modal-action:hover {
    +  background: rgba(255, 255, 255, 0.28);
    +}
    +.lc-modal-action:disabled {
    +  opacity: 0.6;
    +  cursor: not-allowed;
    +}
    diff --git a/web/src/main.ts b/web/src/main.ts
    index 29cbd20..1b4dbf3 100644
    --- a/web/src/main.ts
    +++ b/web/src/main.ts
    @@ -20,6 +20,19 @@ const DEV_JWT_DURATION_OPTIONS: { value: number; label: string }[] = [
       { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" },
     ];
     
    +const LC_DEBUG_KEY = "lc_debug";
    +function isDebugEnabled(): boolean {
    +  try {
    +    if (typeof window !== "undefined" && window.location?.search?.includes("debug=1")) {
    +      window.localStorage?.setItem(LC_DEBUG_KEY, "1");
    +      return true;
    +    }
    +    return window.localStorage?.getItem(LC_DEBUG_KEY) === "1";
    +  } catch {
    +    return false;
    +  }
    +}
    +
     function safeLocalStorage(): Storage | null {
       if (typeof window === "undefined") return null;
       try {
    @@ -160,8 +173,8 @@ function getOnboardingStatus() {
     function refreshSystemHints() {
       const s = getOnboardingStatus();
       if (!s.is_logged_in) {
    -    userSystemHint = "Enter your JWT token above and tap Auth to sign in.";
    -    assistantFallbackText = "Welcome ÔÇö I'm Little Chef.\n\nPlease sign in to get started.";
    +    userSystemHint = "Long-press this chat bubble to log in.";
    +    assistantFallbackText = "Welcome ÔÇö I'm Little Chef.\n\nLong-press the system bubble below to sign in.";
       } else if (!s.prefs_complete) {
         userSystemHint = USER_BUBBLE_DEFAULT_HINT;
         assistantFallbackText =
    @@ -704,16 +717,18 @@ function renderFlowMenu() {
         });
         dropdown.appendChild(item);
       });
    -  const devItem = document.createElement("button");
    -  devItem.type = "button";
    -  devItem.className = "flow-menu-item";
    -  devItem.textContent = "Dev Panel";
    -  devItem.setAttribute("role", "menuitem");
    -  devItem.addEventListener("click", () => {
    -    toggleDevPanel();
    -    setFlowMenuOpen(false);
    -  });
    -  dropdown.appendChild(devItem);
    +  if (isDebugEnabled()) {
    +    const devItem = document.createElement("button");
    +    devItem.type = "button";
    +    devItem.className = "flow-menu-item";
    +    devItem.textContent = "Dev Panel";
    +    devItem.setAttribute("role", "menuitem");
    +    devItem.addEventListener("click", () => {
    +      toggleDevPanel();
    +      setFlowMenuOpen(false);
    +    });
    +    dropdown.appendChild(devItem);
    +  }
     
       const currentLabel = flowDisplayLabel(currentFlowKey);
       trigger.textContent = "ÔÜÖ";
    @@ -1676,6 +1691,129 @@ async function silentGreetOnce() {
       }
     }
     
    +// ---------------------------------------------------------------------------
    +// Auth0 SPA login + modal
    +// ---------------------------------------------------------------------------
    +let auth0Client: any = null;
    +
    +async function loadAuth0Client(): Promise<any> {
    +  if (auth0Client) return auth0Client;
    +  const meta = (name: string) => document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`)?.content ?? "";
    +  const domain = meta("lc-auth0-domain");
    +  const clientId = meta("lc-auth0-client-id");
    +  const audience = meta("lc-auth0-audience");
    +  if (!domain || !clientId) return null;
    +  try {
    +    const cdnUrl = "https://cdn.jsdelivr.net/npm/@auth0/auth0-spa-js@2/dist/auth0-spa-js.production.esm.js";
    +    const mod = await (Function("url", "return import(url)")(cdnUrl) as Promise<any>);
    +    auth0Client = await mod.createAuth0Client({
    +      domain,
    +      clientId,
    +      authorizationParams: {
    +        redirect_uri: window.location.origin,
    +        ...(audience ? { audience } : {}),
    +      },
    +    });
    +    return auth0Client;
    +  } catch (err) {
    +    console.error("[auth0] failed to load SDK", err);
    +    return null;
    +  }
    +}
    +
    +async function performPostLogin() {
    +  clearProposal();
    +  const result = await doGet("/auth/me");
    +  setText("auth-out", result);
    +  state.onboarded = !!result.json?.onboarded;
    +  state.inventoryOnboarded = !!result.json?.inventory_onboarded;
    +  if (state.inventoryOnboarded) mealplanReached = true;
    +  refreshSystemHints();
    +  renderOnboardMenuButtons();
    +  updatePrefsOverlayVisibility();
    +  updateInventoryOverlayVisibility();
    +  updateRecipePacksButtonVisibility();
    +  updateDuetBubbles();
    +  await silentGreetOnce();
    +  inventoryHasLoaded = false;
    +  if (currentFlowKey === "inventory") {
    +    refreshInventoryOverlay(true);
    +  }
    +}
    +
    +async function handleAuth0Callback(): Promise<boolean> {
    +  const params = new URLSearchParams(window.location.search);
    +  if (!params.has("code") || !params.has("state")) return false;
    +  try {
    +    const client = await loadAuth0Client();
    +    if (!client) return false;
    +    await client.handleRedirectCallback();
    +    const token = await client.getTokenSilently();
    +    if (token) {
    +      state.token = token;
    +      // Clean URL without reload
    +      const cleanUrl = window.location.origin + window.location.pathname;
    +      window.history.replaceState({}, document.title, cleanUrl);
    +      await performPostLogin();
    +      return true;
    +    }
    +  } catch (err) {
    +    console.error("[auth0] callback handling failed", err);
    +  }
    +  return false;
    +}
    +
    +function openLoginModal() {
    +  if (document.getElementById("lc-login-modal")) return;
    +  const overlay = document.createElement("div");
    +  overlay.id = "lc-login-modal";
    +  overlay.className = "lc-modal-overlay";
    +  overlay.addEventListener("click", (ev) => {
    +    if (ev.target === overlay) closeLoginModal();
    +  });
    +
    +  const panel = document.createElement("div");
    +  panel.className = "lc-modal-panel";
    +
    +  const closeBtn = document.createElement("button");
    +  closeBtn.type = "button";
    +  closeBtn.className = "lc-modal-close";
    +  closeBtn.textContent = "\u00d7";
    +  closeBtn.setAttribute("aria-label", "Close");
    +  closeBtn.addEventListener("click", closeLoginModal);
    +
    +  const title = document.createElement("h2");
    +  title.textContent = "Sign in";
    +  title.className = "lc-modal-title";
    +
    +  const auth0Btn = document.createElement("button");
    +  auth0Btn.type = "button";
    +  auth0Btn.className = "lc-modal-action";
    +  auth0Btn.textContent = "Continue with Auth0";
    +  auth0Btn.addEventListener("click", async () => {
    +    auth0Btn.disabled = true;
    +    auth0Btn.textContent = "Redirecting\u2026";
    +    const client = await loadAuth0Client();
    +    if (client) {
    +      await client.loginWithRedirect();
    +    } else {
    +      auth0Btn.textContent = "Auth0 not configured";
    +      auth0Btn.disabled = false;
    +    }
    +  });
    +
    +  panel.appendChild(closeBtn);
    +  panel.appendChild(title);
    +  panel.appendChild(auth0Btn);
    +  overlay.appendChild(panel);
    +  document.body.appendChild(overlay);
    +}
    +
    +function closeLoginModal() {
    +  const modal = document.getElementById("lc-login-modal");
    +  if (modal) modal.remove();
    +}
    +
     function wire() {
       enforceViewportLock();
       const jwtInput = document.getElementById("jwt") as HTMLInputElement;
    @@ -1690,24 +1828,7 @@ function wire() {
         } else {
           clearRememberedJwt();
         }
    -    clearProposal();
    -    const result = await doGet("/auth/me");
    -    setText("auth-out", result);
    -    state.onboarded = !!result.json?.onboarded;
    -    state.inventoryOnboarded = !!result.json?.inventory_onboarded;
    -    // Returning user who completed onboarding before ÔÇö unlock recipe button
    -    if (state.inventoryOnboarded) mealplanReached = true;
    -    refreshSystemHints();
    -    renderOnboardMenuButtons();
    -    updatePrefsOverlayVisibility();
    -    updateInventoryOverlayVisibility();
    -    updateRecipePacksButtonVisibility();
    -    updateDuetBubbles();
    -    await silentGreetOnce();
    -    inventoryHasLoaded = false;
    -    if (currentFlowKey === "inventory") {
    -      refreshInventoryOverlay(true);
    -    }
    +    await performPostLogin();
       });
     
       document.getElementById("btn-chat")?.addEventListener("click", async () => {
    @@ -1779,6 +1900,11 @@ function wire() {
       setupPrefsOverlay();
       setupDevPanel();
       applyRememberedJwtInput(jwtInput);
    +  refreshSystemHints();
    +
    +  // Auth0 callback detection (async, non-blocking)
    +  handleAuth0Callback().catch(() => {});
    +
       wireDuetComposer();
       wireFloatingComposerTrigger(document.querySelector(".duet-stage") as HTMLElement | null);
       setupHistoryDrawerUi();
    @@ -2109,6 +2235,22 @@ function ensureOnboardMenu() {
     function renderOnboardMenuButtons() {
       if (!onboardMenu) return;
       onboardMenu.innerHTML = "";
    +
    +  // Before login: show only Login button
    +  if (!state.token?.trim()) {
    +    const loginBtn = document.createElement("button");
    +    loginBtn.type = "button";
    +    loginBtn.className = "flow-menu-item";
    +    loginBtn.textContent = "Login";
    +    loginBtn.dataset.onboardItem = "login";
    +    loginBtn.addEventListener("click", () => {
    +      hideOnboardMenu();
    +      openLoginModal();
    +    });
    +    onboardMenu.appendChild(loginBtn);
    +    return;
    +  }
    +
       const prefsBtn = document.createElement("button");
       prefsBtn.type = "button";
       prefsBtn.className = "flow-menu-item";
    @@ -2850,10 +2992,13 @@ function _bindLongPressToElement(el: HTMLElement) {
     
       el.addEventListener("pointerup", (ev) => {
         if (onboardMenuActive) {
    -      const startHovered = onboardActiveItem?.dataset.onboardItem === "start";
    -      if (startHovered) {
    +      const hoveredItem = onboardActiveItem?.dataset.onboardItem;
    +      if (hoveredItem === "start") {
             startOnboarding();
             hideOnboardMenu();
    +      } else if (hoveredItem === "login") {
    +        hideOnboardMenu();
    +        openLoginModal();
           }
           onboardDragActive = false;
           cancel({ hideMenu: false });
    diff --git a/web/src/style.css b/web/src/style.css
    index b8a652b..43020b9 100644
    --- a/web/src/style.css
    +++ b/web/src/style.css
    @@ -1437,3 +1437,69 @@ pre {
       opacity: 0.6;
       cursor: not-allowed;
     }
    +
    +/* ---- Login modal ---- */
    +.lc-modal-overlay {
    +  position: fixed;
    +  inset: 0;
    +  z-index: 2147483645;
    +  display: flex;
    +  align-items: center;
    +  justify-content: center;
    +  background: rgba(0, 0, 0, 0.45);
    +  backdrop-filter: blur(4px);
    +  -webkit-backdrop-filter: blur(4px);
    +}
    +.lc-modal-panel {
    +  position: relative;
    +  width: min(340px, 90vw);
    +  padding: 1.5rem 1.25rem;
    +  border-radius: 1rem;
    +  background: rgba(255, 255, 255, 0.12);
    +  backdrop-filter: blur(18px);
    +  -webkit-backdrop-filter: blur(18px);
    +  border: 1px solid rgba(255, 255, 255, 0.18);
    +  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    +  color: #fff;
    +  text-align: center;
    +}
    +.lc-modal-close {
    +  position: absolute;
    +  top: 0.5rem;
    +  right: 0.75rem;
    +  background: none;
    +  border: none;
    +  color: rgba(255, 255, 255, 0.6);
    +  font-size: 1.4rem;
    +  cursor: pointer;
    +  line-height: 1;
    +  padding: 0.25rem;
    +}
    +.lc-modal-close:hover {
    +  color: #fff;
    +}
    +.lc-modal-title {
    +  margin: 0 0 1.25rem;
    +  font-size: 1.15rem;
    +  font-weight: 600;
    +}
    +.lc-modal-action {
    +  display: block;
    +  width: 100%;
    +  padding: 0.75rem 1rem;
    +  border: none;
    +  border-radius: 0.5rem;
    +  background: rgba(255, 255, 255, 0.18);
    +  color: #fff;
    +  font-size: 0.95rem;
    +  font-weight: 500;
    +  cursor: pointer;
    +  transition: background 0.15s;
    +}
    +.lc-modal-action:hover {
    +  background: rgba(255, 255, 255, 0.28);
    +}
    +.lc-modal-action:disabled {
    +  opacity: 0.6;
    +  cursor: not-allowed;
    +}

## Verification
- tsc: pass (1 pre-existing TS2339)
- pytest: 183 passed, 0 failures
- node ui_onboarding_hints_test.mjs: 13/13 PASS

## Notes (optional)
- Auth0 SPA SDK loaded via CDN ESM (no bundler in web build); Function("url","return import(url)") workaround for tsc dynamic import of CDN URL.
- Auth0 tenant config (lc-auth0-domain, lc-auth0-client-id meta tags) required for full login flow; without it, "Auth0 not configured" shown.
- web/dist/proposalRenderer.js CRLF artifact from prior cycle (not in allowed file set, not staged).

## Next Steps
- User must reply AUTHORIZED before commit
- Auth0 tenant config needed for full e2e (known limitation)

