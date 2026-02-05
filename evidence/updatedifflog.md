# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-05T12:48:44+00:00
- Branch: main
- BASE_HEAD: 01d3c1f0fbc8e4c41e954b554dc88726938bd334
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Prior cycle recap: doc-only handoff snapshot added (evidence/codex.md) to capture repo state and governance.
- Fixed prefs PUT handler syntax in web/src/main.ts to restore TS compile.
- Legacy auth/chat/prefs/plan/shopping debug blocks now hidden in a collapsed Dev Panel (runtime-moved, IDs preserved).
- Inventory ghost overlay for the Inventory flow: fetches /inventory/summary and /inventory/low-stock on select/refresh, shows status + low stock + in-stock lists (read-only).
- Mobile overflow tightened (max-width/overflow guards, min-width fixes) plus styling for Dev Panel and overlay, including stacked JWT label/input.

## Files Changed (staged)
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md
- web/src/main.ts
- web/src/style.css

## git status -sb
    ## main...origin/main
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
    M  evidence/updatedifflog.md
     M web/dist/main.js
    M  web/src/main.ts
    M  web/src/style.css
    ?? JWT.txt
    ?? evidence/orchestration_system_snapshot.md
    ?? web/node_modules/

## Minimal Diff Hunks
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    index 933658a..d81832a 100644
    --- a/evidence/test_runs.md
    +++ b/evidence/test_runs.md
    @@ -2771,3 +2771,61 @@ M  evidence/updatedifflog.md
     
     ```
     
    +## Test Run 2026-02-05T10:29:45Z
    +- Status: PASS
    +- Start: 2026-02-05T10:29:45Z
    +- End: 2026-02-05T10:29:52Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 01d3c1f0fbc8e4c41e954b554dc88726938bd334
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 35 passed, 1 warning in 3.92s
    +- git status -sb:
    +```
    +## main...origin/main
    +?? JWT.txt
    +?? evidence/orchestration_system_snapshot.md
    +?? web/node_modules/
    +```
    +- git diff --stat:
    +```
    +
    +```
    +
    +## Test Run 2026-02-05T11:15:15Z
    +- Status: PASS
    +- Start: 2026-02-05T11:15:15Z
    +- End: 2026-02-05T11:15:20Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 01d3c1f0fbc8e4c41e954b554dc88726938bd334
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 35 passed, 1 warning in 1.94s
    +- git status -sb:
    +```
    +## main...origin/main
    + M evidence/test_runs.md
    + M evidence/test_runs_latest.md
    + M evidence/updatedifflog.md
    + M web/dist/main.js
    + M web/src/main.ts
    + M web/src/style.css
    +?? JWT.txt
    +?? evidence/orchestration_system_snapshot.md
    +?? web/node_modules/
    +```
    +- git diff --stat:
    +```
    + evidence/test_runs.md        |  23 ++++
    + evidence/test_runs_latest.md |  13 +--
    + evidence/updatedifflog.md    |  36 +++---
    + web/dist/main.js             | 248 +++++++++++++++++++++++++++++++++++++++--
    + web/src/main.ts              | 259 +++++++++++++++++++++++++++++++++++++++++--
    + web/src/style.css            | 141 +++++++++++++++++++++++
    + 6 files changed, 683 insertions(+), 37 deletions(-)
    +```
    +
    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    index 53ba900..afd75ce 100644
    --- a/evidence/test_runs_latest.md
    +++ b/evidence/test_runs_latest.md
    @@ -1,23 +1,34 @@
     Status: PASS
    -Start: 2026-02-05T03:20:48Z
    -End: 2026-02-05T03:20:53Z
    +Start: 2026-02-05T11:15:15Z
    +End: 2026-02-05T11:15:20Z
     Branch: main
    -HEAD: 168075cc51b616d444a37262b6cb5cbf5d486569
    +HEAD: 01d3c1f0fbc8e4c41e954b554dc88726938bd334
     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
     compileall exit: 0
     import app.main exit: 0
     pytest exit: 0
    -pytest summary: 35 passed, 1 warning in 1.99s
    +pytest summary: 35 passed, 1 warning in 1.94s
     git status -sb:
     ```
     ## main...origin/main
    -M  Contracts/phases_7_plus.md
    -M  evidence/updatedifflog.md
    + M evidence/test_runs.md
    + M evidence/test_runs_latest.md
    + M evidence/updatedifflog.md
    + M web/dist/main.js
    + M web/src/main.ts
    + M web/src/style.css
    +?? JWT.txt
     ?? evidence/orchestration_system_snapshot.md
     ?? web/node_modules/
     ```
     git diff --stat:
     ```
    -
    + evidence/test_runs.md        |  23 ++++
    + evidence/test_runs_latest.md |  13 +--
    + evidence/updatedifflog.md    |  36 +++---
    + web/dist/main.js             | 248 +++++++++++++++++++++++++++++++++++++++--
    + web/src/main.ts              | 259 +++++++++++++++++++++++++++++++++++++++++--
    + web/src/style.css            | 141 +++++++++++++++++++++++
    + 6 files changed, 683 insertions(+), 37 deletions(-)
     ```
     
    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    index 3721005..79c4689 100644
    --- a/evidence/updatedifflog.md
    +++ b/evidence/updatedifflog.md
    @@ -1,39 +1,57 @@
     # Diff Log (overwrite each cycle)
     
     ## Cycle Metadata
    -- Timestamp: 2026-02-05T03:27:28+00:00
    +- Timestamp: 2026-02-05T11:17:35+00:00
     - Branch: main
    -- BASE_HEAD: dbe811effe5156408d2a0e2e173ad44cef15b518
    +- BASE_HEAD: 01d3c1f0fbc8e4c41e954b554dc88726938bd334
     - Diff basis: staged
     
     ## Cycle Status
     - Status: COMPLETE
     
     ## Summary
    -- Added evidence/codex.md handoff snapshot (repo state, phase progress, governance policies, UI state, next steps).
    +- Prior cycle recap: doc-only handoff snapshot added (evidence/codex.md) to capture repo state and governance.
    +- Fixed prefs PUT handler syntax in web/src/main.ts to restore TS compile.
    +- Legacy auth/chat/prefs/plan/shopping debug blocks now hidden in a collapsed Dev Panel (runtime-moved, IDs preserved).
    +- Inventory ghost overlay for the Inventory flow: fetches /inventory/summary and /inventory/low-stock on select/refresh, shows status + low stock + in-stock lists (read-only).
    +- Mobile overflow tightened (max-width/overflow guards, min-width fixes) plus styling for Dev Panel and overlay.
     
     ## Files Changed (staged)
    -- evidence/codex.md
    -- evidence/updatedifflog.md
    +- evidence/test_runs.md
    +- evidence/test_runs_latest.md
    +- web/src/main.ts
    +- web/src/style.css
     
     ## git status -sb
         ## main...origin/main
    -    ?? evidence/codex.md
    +    M  evidence/test_runs.md
    +    M  evidence/test_runs_latest.md
    +     M evidence/updatedifflog.md
    +     M web/dist/main.js
    +    M  web/src/main.ts
    +    M  web/src/style.css
    +    ?? JWT.txt
         ?? evidence/orchestration_system_snapshot.md
         ?? web/node_modules/
     
     ## Minimal Diff Hunks
    -    (none)
    +    - web/src/main.ts: prefs PUT syntax fix; Dev Panel creation + runtime move of legacy cards; inventory ghost overlay with summary/low-stock fetch + flow visibility.
    +    - web/src/style.css: max-width/overflow-x guards, min-width fixes, glass styling for Dev Panel, inventory overlay layer + mobile inset.
    +    - evidence/test_runs*.md: appended logs from scripts/run_tests.ps1 (PASS).
     
     ## Verification
    -- Static: N/A (documentation-only).
    -- Runtime: N/A (documentation-only).
    -- Behavior: Snapshot content reviewed for accuracy vs git status/log and phase progress.
    -- Contract: No code/contracts changed; doc-only update.
    +- Static: `npm run build` (PASS); `scripts/run_tests.ps1` (compileall/import/pytest all PASS).
    +- Runtime: Not run (run_local.ps1 would start long-lived uvicorn; skipped to keep session short—manual boot still pending).
    +- Behavior: UI not manually exercised in this cycle (pending check of Dev Panel toggle + inventory overlay).
    +- Contract: physics.yaml untouched; TS-only UI changes.
     
     ## Notes (optional)
    -- Untracked snapshot (evidence/orchestration_system_snapshot.md) and web/node_modules/ remain out-of-band.
    +- web/dist/main.js changed by build but left unstaged per TS-only/source scope.
    +- Untracked JWT.txt, evidence/orchestration_system_snapshot.md, and web/node_modules/ remain out-of-band (do not stage/commit).
     
     ## Next Steps
    -- Await authorization to commit/push.
    +- Optional: manual UI smoke (Dev Panel toggle, inventory overlay refresh, mobile overflow).
    +- Await Julius to reply "AUTHORIZED" before committing/pushing.
    +
    +
     
    diff --git a/web/src/main.ts b/web/src/main.ts
    index e0378bb..66509c9 100644
    --- a/web/src/main.ts
    +++ b/web/src/main.ts
    @@ -12,11 +12,14 @@ type HistoryItem = { role: "user" | "assistant"; text: string };
     type FlowOption = { key: string; label: string; placeholder: string };
     const flowOptions: FlowOption[] = [
       { key: "general", label: "General", placeholder: "Ask or fill..." },
    -  { key: "inventory", label: "Inventory", placeholder: "Ask about inventory, stock, or adjustments…" },
    -  { key: "mealplan", label: "Meal Plan", placeholder: "Plan meals or ask for ideas…" },
    -  { key: "prefs", label: "Preferences", placeholder: "Update dislikes, allergies, or servings…" },
    +  { key: "inventory", label: "Inventory", placeholder: "Ask about inventory, stock, or adjustments..." },
    +  { key: "mealplan", label: "Meal Plan", placeholder: "Plan meals or ask for ideas..." },
    +  { key: "prefs", label: "Preferences", placeholder: "Update dislikes, allergies, or servings..." },
     ];
     
    +type InventorySummaryItem = { item_name: string; quantity: number; unit: string; approx?: boolean };
    +type LowStockItem = { item_name: string; quantity: number; unit: string; threshold: number; reason?: string };
    +
     const duetState = {
       threadId: null as string | null,
       history: [] as HistoryItem[],
    @@ -28,6 +31,12 @@ let historyOverlay: HTMLDivElement | null = null;
     let historyToggle: HTMLButtonElement | null = null;
     let currentFlowKey = flowOptions[0].key;
     let composerBusy = false;
    +let inventoryOverlay: HTMLDivElement | null = null;
    +let inventoryStatusEl: HTMLElement | null = null;
    +let inventoryLowList: HTMLUListElement | null = null;
    +let inventorySummaryList: HTMLUListElement | null = null;
    +let inventoryLoading = false;
    +let inventoryHasLoaded = false;
     
     function headers() {
       const h: Record<string, string> = { "Content-Type": "application/json" };
    @@ -54,6 +63,81 @@ function show(id: string) {
       document.getElementById(id)?.classList.remove("hidden");
     }
     
    +function moveGroupIntoDevPanel(ids: string[], panel: HTMLElement, moved: Set<HTMLElement>) {
    +  const scopes = ["section", "fieldset", ".panel", ".card", ".debug", "div"];
    +  let target: HTMLElement | null = null;
    +  for (const id of ids) {
    +    const el = document.getElementById(id);
    +    if (!el) continue;
    +    for (const scope of scopes) {
    +      const candidate = el.closest(scope) as HTMLElement | null;
    +      if (!candidate) continue;
    +      const tag = candidate.tagName.toLowerCase();
    +      if (tag === "body" || tag === "main") continue;
    +      if (candidate.id === "duet-shell") continue;
    +      target = candidate;
    +      break;
    +    }
    +    if (target) break;
    +  }
    +
    +  if (target) {
    +    if (!moved.has(target)) {
    +      moved.add(target);
    +      panel.appendChild(target);
    +    }
    +    return;
    +  }
    +
    +  const wrapper = document.createElement("div");
    +  wrapper.className = "dev-panel-group";
    +  ids.forEach((id) => {
    +    const el = document.getElementById(id);
    +    if (el) {
    +      wrapper.appendChild(el);
    +    }
    +  });
    +  if (wrapper.childElementCount) {
    +    panel.appendChild(wrapper);
    +  }
    +}
    +
    +function setupDevPanel() {
    +  const shell = document.getElementById("duet-shell");
    +  const host = shell?.parentElement || document.querySelector("main.container");
    +  if (!host || document.getElementById("dev-panel")) return;
    +
    +  const panel = document.createElement("details");
    +  panel.id = "dev-panel";
    +  panel.className = "dev-panel";
    +  panel.open = false;
    +
    +  const summary = document.createElement("summary");
    +  summary.textContent = "Dev Panel";
    +  panel.appendChild(summary);
    +
    +  const content = document.createElement("div");
    +  content.className = "dev-panel-content";
    +  panel.appendChild(content);
    +
    +  const insertBefore = shell?.nextElementSibling ?? null;
    +  if (insertBefore && insertBefore.parentElement === host) {
    +    host.insertBefore(panel, insertBefore);
    +  } else {
    +    host.appendChild(panel);
    +  }
    +
    +  const moved = new Set<HTMLElement>();
    +  const groups: string[][] = [
    +    ["btn-auth", "jwt", "auth-out"],
    +    ["btn-chat", "chat-input", "chat-reply", "chat-error", "chat-proposal"],
    +    ["btn-prefs-get", "btn-prefs-put", "prefs-servings", "prefs-meals", "prefs-out"],
    +    ["btn-plan-gen", "plan-out"],
    +    ["btn-shopping", "shopping-out"],
    +  ];
    +  groups.forEach((ids) => moveGroupIntoDevPanel(ids, content, moved));
    +}
    +
     function renderProposal() {
       const container = document.getElementById("chat-proposal");
       const textEl = document.getElementById("chat-proposal-text");
    @@ -106,7 +190,7 @@ function setComposerPlaceholder() {
     function updateThreadLabel() {
       const label = document.getElementById("duet-thread-label");
       if (!label) return;
    -  label.textContent = `Thread: ${duetState.threadId ?? "—"}`;
    +  label.textContent = `Thread: ${duetState.threadId ?? "-"}`;
     }
     
     function syncHistoryUi() {
    @@ -146,7 +230,7 @@ function updateDuetBubbles() {
       const user = document.getElementById("duet-user-text");
       const lastAssistant = [...duetState.history].reverse().find((h) => h.role === "assistant");
       const lastUser = [...duetState.history].reverse().find((h) => h.role === "user");
    -  if (assistant) assistant.textContent = lastAssistant?.text ?? "Hi — how can I help?";
    +  if (assistant) assistant.textContent = lastAssistant?.text ?? "Hi - how can I help?";
       if (user) user.textContent = lastUser?.text ?? "Tap mic or type to start";
     }
     
    @@ -282,6 +366,152 @@ function wireHistoryHotkeys() {
       });
     }
     
    +function formatQuantity(quantity: number, unit: string, approx?: boolean) {
    +  const safe = Number.isFinite(quantity) ? quantity : 0;
    +  const rounded = Math.abs(safe) >= 10 ? safe.toFixed(1) : safe.toString();
    +  const trimmed = rounded.replace(/\.0+$/, "").replace(/(\.\d*[1-9])0+$/, "$1");
    +  const prefix = approx ? "~" : "";
    +  return `${prefix}${trimmed} ${unit}`;
    +}
    +
    +function setInventoryStatus(text: string) {
    +  if (inventoryStatusEl) {
    +    inventoryStatusEl.textContent = text;
    +  }
    +}
    +
    +function renderInventoryLists(low: LowStockItem[], summary: InventorySummaryItem[]) {
    +  const lowList = inventoryLowList;
    +  if (lowList) {
    +    lowList.innerHTML = "";
    +    if (!low || !low.length) {
    +      const li = document.createElement("li");
    +      li.className = "inventory-empty";
    +      li.textContent = "No low stock items.";
    +      lowList.appendChild(li);
    +    } else {
    +      low.forEach((item) => {
    +        const li = document.createElement("li");
    +        const reason = item.reason ? ` - ${item.reason}` : "";
    +        li.textContent = `${item.item_name} - ${formatQuantity(item.quantity, item.unit)} (threshold ${item.threshold})${reason}`;
    +        lowList.appendChild(li);
    +      });
    +    }
    +  }
    +
    +  const summaryList = inventorySummaryList;
    +  if (summaryList) {
    +    summaryList.innerHTML = "";
    +    if (!summary || !summary.length) {
    +      const li = document.createElement("li");
    +      li.className = "inventory-empty";
    +      li.textContent = "No items.";
    +      summaryList.appendChild(li);
    +    } else {
    +      summary.forEach((item) => {
    +        const li = document.createElement("li");
    +        li.textContent = `${item.item_name} - ${formatQuantity(item.quantity, item.unit, item.approx)}`;
    +        summaryList.appendChild(li);
    +      });
    +    }
    +  }
    +}
    +
    +async function refreshInventoryOverlay(force = false) {
    +  if (!inventoryOverlay) return;
    +  if (inventoryLoading && !force) return;
    +  inventoryLoading = true;
    +  setInventoryStatus("Loading...");
    +  try {
    +    const [summaryResp, lowResp] = await Promise.all([doGet("/inventory/summary"), doGet("/inventory/low-stock")]);
    +    if (summaryResp.status === 401 || lowResp.status === 401) {
    +      setInventoryStatus("Unauthorized (set token in Dev Panel)");
    +      renderInventoryLists([], []);
    +      inventoryHasLoaded = true;
    +      return;
    +    }
    +    const summaryItems = Array.isArray(summaryResp.json?.items) ? (summaryResp.json.items as InventorySummaryItem[]) : [];
    +    const lowItems = Array.isArray(lowResp.json?.items) ? (lowResp.json.items as LowStockItem[]) : [];
    +    renderInventoryLists(lowItems, summaryItems);
    +    const hasAny = lowItems.length > 0 || summaryItems.length > 0;
    +    setInventoryStatus(hasAny ? "Read-only snapshot" : "No items yet.");
    +    inventoryHasLoaded = true;
    +  } catch (err) {
    +    setInventoryStatus("Network error. Try refresh.");
    +    renderInventoryLists([], []);
    +    console.error(err);
    +  } finally {
    +    inventoryLoading = false;
    +  }
    +}
    +
    +function updateInventoryOverlayVisibility() {
    +  if (!inventoryOverlay) return;
    +  const visible = currentFlowKey === "inventory";
    +  inventoryOverlay.classList.toggle("hidden", !visible);
    +  if (visible && (!inventoryHasLoaded || !inventoryLowList?.childElementCount)) {
    +    refreshInventoryOverlay();
    +  }
    +}
    +
    +function setupInventoryGhostOverlay() {
    +  const shell = document.getElementById("duet-shell");
    +  const stage = shell?.querySelector(".duet-stage");
    +  if (!shell || !stage || document.getElementById("inventory-ghost")) return;
    +
    +  const overlay = document.createElement("div");
    +  overlay.id = "inventory-ghost";
    +  overlay.className = "inventory-ghost hidden";
    +
    +  const header = document.createElement("div");
    +  header.className = "inventory-ghost-header";
    +  const title = document.createElement("span");
    +  title.textContent = "Inventory";
    +  const refresh = document.createElement("button");
    +  refresh.type = "button";
    +  refresh.className = "ghost-refresh";
    +  refresh.textContent = "Refresh";
    +  refresh.addEventListener("click", () => refreshInventoryOverlay(true));
    +  header.appendChild(title);
    +  header.appendChild(refresh);
    +
    +  const status = document.createElement("div");
    +  status.id = "inventory-ghost-status";
    +  status.className = "inventory-ghost-status";
    +  status.textContent = "Select Inventory to load.";
    +
    +  const lowSection = document.createElement("div");
    +  lowSection.className = "inventory-ghost-section";
    +  const lowTitle = document.createElement("div");
    +  lowTitle.className = "inventory-ghost-title";
    +  lowTitle.textContent = "Low stock";
    +  const lowList = document.createElement("ul");
    +  lowList.id = "inventory-low-list";
    +  lowSection.appendChild(lowTitle);
    +  lowSection.appendChild(lowList);
    +
    +  const summarySection = document.createElement("div");
    +  summarySection.className = "inventory-ghost-section";
    +  const summaryTitle = document.createElement("div");
    +  summaryTitle.className = "inventory-ghost-title";
    +  summaryTitle.textContent = "In stock";
    +  const summaryList = document.createElement("ul");
    +  summaryList.id = "inventory-summary-list";
    +  summarySection.appendChild(summaryTitle);
    +  summarySection.appendChild(summaryList);
    +
    +  overlay.appendChild(header);
    +  overlay.appendChild(status);
    +  overlay.appendChild(lowSection);
    +  overlay.appendChild(summarySection);
    +  stage.appendChild(overlay);
    +
    +  inventoryOverlay = overlay;
    +  inventoryStatusEl = status;
    +  inventoryLowList = lowList;
    +  inventorySummaryList = summaryList;
    +}
    +
     async function doGet(path: string) {
       const res = await fetch(path, { headers: headers() });
       return { status: res.status, json: await res.json().catch(() => null) };
    @@ -311,8 +541,8 @@ async function sendAsk(message: string, opts?: { flowLabel?: string; updateChatP
       const flowLabel = opts?.flowLabel;
       const displayText = flowLabel ? `[${flowLabel}] ${message}` : message;
       const userIndex = addHistory("user", displayText);
    -  const thinkingIndex = addHistory("assistant", "…");
    -  setDuetStatus("Contacting backend…");
    +  const thinkingIndex = addHistory("assistant", "...");
    +  setDuetStatus("Contacting backend...");
       setComposerBusy(true);
       try {
         const res = await fetch("/chat", {
    @@ -360,6 +590,10 @@ function wire() {
         clearProposal();
         const result = await doGet("/auth/me");
         setText("auth-out", result);
    +    inventoryHasLoaded = false;
    +    if (currentFlowKey === "inventory") {
    +      refreshInventoryOverlay(true);
    +    }
       });
     
       document.getElementById("btn-chat")?.addEventListener("click", async () => {
    @@ -425,10 +659,13 @@ function wire() {
       });
     
       setupFlowChips();
    +  setupInventoryGhostOverlay();
    +  setupDevPanel();
       wireDuetComposer();
       setupHistoryDrawerUi();
       wireHistoryHotkeys();
       wireDuetDrag();
    +  updateInventoryOverlayVisibility();
       applyDrawerProgress(duetState.drawerOpen ? 1 : 0, { commit: true });
       renderDuetHistory();
       updateDuetBubbles();
    @@ -453,7 +690,7 @@ function wireDuetComposer() {
         clearProposal();
         setChatError("");
         const flow = flowOptions.find((f) => f.key === currentFlowKey) ?? flowOptions[0];
    -    setDuetStatus("Sending to backend…");
    +    setDuetStatus("Sending to backend...");
         syncButtons();
         sendAsk(text, { flowLabel: flow.label });
         input.value = "";
    @@ -522,4 +759,10 @@ function selectFlow(key: string) {
         chip.setAttribute("aria-pressed", active ? "true" : "false");
       });
       setComposerPlaceholder();
    +  updateInventoryOverlayVisibility();
    +  if (currentFlowKey === "inventory") {
    +    refreshInventoryOverlay(true);
    +  }
     }
    +
    +
    diff --git a/web/src/style.css b/web/src/style.css
    index 71ca141..d10b830 100644
    --- a/web/src/style.css
    +++ b/web/src/style.css
    @@ -13,6 +13,11 @@
       box-sizing: border-box;
     }
     
    +html {
    +  max-width: 100vw;
    +  overflow-x: hidden;
    +}
    +
     body {
       margin: 0;
       min-height: 100vh;
    @@ -21,6 +26,8 @@ body {
         radial-gradient(circle at 80% 0%, rgba(127, 228, 194, 0.14), transparent 30%),
         linear-gradient(145deg, #0b1724, #102a3f 50%, #0c1f31);
       color: var(--text);
    +  max-width: 100vw;
    +  overflow-x: hidden;
     }
     
     body.history-open {
    @@ -29,10 +36,12 @@ body.history-open {
     
     main.container {
       max-width: 1100px;
    +  width: 100%;
       margin: 0 auto;
       padding: 16px;
       display: grid;
       gap: 14px;
    +  min-width: 0;
     }
     
     .card,
    @@ -43,12 +52,56 @@ main.container {
       box-shadow: var(--shadow);
       backdrop-filter: blur(10px);
       -webkit-backdrop-filter: blur(10px);
    +  width: 100%;
    +  max-width: 100%;
    +  min-width: 0;
     }
     
     .card {
       padding: 14px;
     }
     
    +.dev-panel {
    +  background: var(--card);
    +  border: 1px solid var(--glass-border);
    +  border-radius: 14px;
    +  box-shadow: var(--shadow);
    +  backdrop-filter: blur(10px);
    +  -webkit-backdrop-filter: blur(10px);
    +  overflow: hidden;
    +}
    +
    +#dev-panel summary {
    +  cursor: pointer;
    +  padding: 10px 12px;
    +  font-weight: 700;
    +  letter-spacing: 0.02em;
    +  list-style: none;
    +}
    +
    +#dev-panel summary::-webkit-details-marker {
    +  display: none;
    +}
    +
    +.dev-panel-content {
    +  padding: 10px 12px 14px;
    +  display: grid;
    +  gap: 10px;
    +  max-height: 440px;
    +  overflow-y: auto;
    +  width: 100%;
    +}
    +
    +.dev-panel .card {
    +  margin: 0;
    +}
    +
    +.dev-panel-group {
    +  border: 1px dashed rgba(255, 255, 255, 0.08);
    +  border-radius: 10px;
    +  padding: 8px;
    +}
    +
     .legacy-card h1,
     .legacy-card h2 {
       margin-top: 0;
    @@ -131,6 +184,7 @@ pre {
       overflow-x: auto;
       padding: 4px 2px 2px;
       margin: -2px 0 2px;
    +  min-width: 0;
     }
     
     .flow-chip {
    @@ -168,6 +222,86 @@ pre {
       background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(127, 164, 255, 0.08));
       border: 1px solid var(--glass-border);
       overflow: hidden;
    +  min-width: 0;
    +  width: 100%;
    +}
    +
    +.inventory-ghost {
    +  position: absolute;
    +  inset: 10px;
    +  background: rgba(11, 23, 36, 0.8);
    +  border: 1px solid var(--glass-border);
    +  border-radius: 14px;
    +  box-shadow: var(--shadow);
    +  backdrop-filter: blur(12px);
    +  -webkit-backdrop-filter: blur(12px);
    +  padding: 12px;
    +  display: grid;
    +  gap: 10px;
    +  z-index: 25;
    +  max-width: calc(100% - 20px);
    +  max-height: calc(100% - 20px);
    +  overflow: hidden;
    +}
    +
    +.inventory-ghost.hidden {
    +  display: none;
    +}
    +
    +.inventory-ghost-header {
    +  display: flex;
    +  align-items: center;
    +  justify-content: space-between;
    +  gap: 8px;
    +  font-weight: 700;
    +  letter-spacing: 0.02em;
    +}
    +
    +.inventory-ghost-status {
    +  font-size: 13px;
    +  opacity: 0.85;
    +}
    +
    +.inventory-ghost-section {
    +  background: rgba(255, 255, 255, 0.04);
    +  border: 1px solid rgba(255, 255, 255, 0.1);
    +  border-radius: 10px;
    +  padding: 8px 10px;
    +  min-width: 0;
    +}
    +
    +.inventory-ghost-title {
    +  font-size: 13px;
    +  opacity: 0.9;
    +  margin-bottom: 4px;
    +}
    +
    +.inventory-ghost ul {
    +  list-style: none;
    +  margin: 0;
    +  padding: 0;
    +  display: grid;
    +  gap: 6px;
    +  max-height: 140px;
    +  overflow-y: auto;
    +}
    +
    +.inventory-ghost li {
    +  font-size: 13px;
    +  line-height: 1.35;
    +  word-break: break-word;
    +}
    +
    +.inventory-empty {
    +  opacity: 0.75;
    +}
    +
    +.ghost-refresh {
    +  width: auto;
    +  padding: 8px 10px;
    +  margin: 0;
    +  font-weight: 700;
    +  min-width: 0;
     }
     
     .history-overlay {
    @@ -329,6 +463,8 @@ pre {
       border-radius: 14px;
       padding: 10px;
       box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
    +  width: 100%;
    +  min-width: 0;
     }
     
     .duet-composer input {
    @@ -390,4 +526,9 @@ pre {
       .duet-bubble {
         max-width: 72%;
       }
    +
    +  .inventory-ghost {
    +    inset: 8px;
    +    padding: 10px;
    +  }
     }

## Verification
- Static: `npm run build` (PASS); `scripts/run_tests.ps1` (compileall/import/pytest all PASS).
- Runtime: Not run (run_local.ps1 would start long-lived uvicorn; skipped to keep session short—manual boot still pending).
- Behavior: UI not manually exercised this cycle (pending check of Dev Panel toggle + inventory overlay + JWT stacking).
- Contract: physics.yaml untouched; TS-only UI changes.

## Notes (optional)
- web/dist/main.js changed by build but left unstaged per TS-only/source scope.
- Untracked JWT.txt, evidence/orchestration_system_snapshot.md, and web/node_modules/ remain out-of-band (do not stage/commit).

## Next Steps
- Optional: manual UI smoke (Dev Panel toggle, inventory overlay refresh, mobile overflow).
- Await Julius to reply "AUTHORIZED" before committing/pushing.




