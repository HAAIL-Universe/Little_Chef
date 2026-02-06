import { formatProposalSummary, stripProposalPrefix } from "./proposalRenderer.js";
const state = {
    token: "",
    lastPlan: null,
    proposalId: null,
    proposedActions: [],
    chatReply: null,
    chatError: "",
    onboarded: null,
};
const PROPOSAL_CONFIRM_COMMANDS = new Set(["confirm"]);
const PROPOSAL_DENY_COMMANDS = new Set(["deny", "cancel"]);
const flowOptions = [
    { key: "general", label: "General", placeholder: "Ask or fill..." },
    { key: "inventory", label: "Inventory", placeholder: "Ask about inventory, stock, or adjustments..." },
    { key: "mealplan", label: "Meal Plan", placeholder: "Plan meals or ask for ideas..." },
    { key: "prefs", label: "Preferences", placeholder: "Update dislikes, allergies, or servings..." },
];
const duetState = {
    threadId: null,
    history: [],
    drawerOpen: false,
    drawerProgress: 0,
};
let lastServerMode = "ASK";
function currentModeLower() {
    return (lastServerMode || "ASK").toLowerCase();
}
let historyOverlay = null;
let historyToggle = null;
let currentFlowKey = flowOptions[0].key;
let composerBusy = false;
let flowMenuContainer = null;
let flowMenuDropdown = null;
let flowMenuButton = null;
let flowMenuOpen = false;
let flowMenuListenersBound = false;
let devPanelVisible = false;
let inventoryOverlay = null;
let inventoryStatusEl = null;
let inventoryLowList = null;
let inventorySummaryList = null;
let inventoryLoading = false;
let inventoryHasLoaded = false;
let onboardMenu = null;
let onboardPressTimer = null;
let onboardPressStart = null;
let onboardPointerId = null;
let onboardMenuActive = false;
let onboardActiveItem = null;
let onboardIgnoreDocClickUntilMs = 0;
let onboardDragActive = false;
function headers() {
    var _a;
    const h = { "Content-Type": "application/json" };
    const raw = (_a = state.token) === null || _a === void 0 ? void 0 : _a.trim();
    if (raw) {
        const tokenOnly = raw.replace(/^bearer\s+/i, "").replace(/\s+/g, "");
        if (tokenOnly) {
            h["Authorization"] = `Bearer ${tokenOnly}`;
        }
    }
    return h;
}
function setModeFromResponse(json) {
    if (json && typeof json.mode === "string") {
        lastServerMode = json.mode.toUpperCase();
        updateThreadLabel();
    }
}
function setText(id, value) {
    const el = document.getElementById(id);
    if (el)
        el.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}
function hide(id) {
    var _a;
    (_a = document.getElementById(id)) === null || _a === void 0 ? void 0 : _a.classList.add("hidden");
}
function show(id) {
    var _a;
    (_a = document.getElementById(id)) === null || _a === void 0 ? void 0 : _a.classList.remove("hidden");
}
function moveGroupIntoDevPanel(ids, panel, moved) {
    const scopes = ["section", "fieldset", ".panel", ".card", ".debug", "div"];
    let target = null;
    for (const id of ids) {
        const el = document.getElementById(id);
        if (!el)
            continue;
        for (const scope of scopes) {
            const candidate = el.closest(scope);
            if (!candidate)
                continue;
            const tag = candidate.tagName.toLowerCase();
            if (tag === "body" || tag === "main")
                continue;
            if (candidate.id === "duet-shell")
                continue;
            target = candidate;
            break;
        }
        if (target)
            break;
    }
    if (target) {
        if (!moved.has(target)) {
            moved.add(target);
            panel.appendChild(target);
        }
        return;
    }
    const wrapper = document.createElement("div");
    wrapper.className = "dev-panel-group";
    ids.forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
            wrapper.appendChild(el);
        }
    });
    if (wrapper.childElementCount) {
        panel.appendChild(wrapper);
    }
}
function setupDevPanel() {
    const shell = document.getElementById("duet-shell");
    const host = shell || document.querySelector("main.container");
    if (!host || document.getElementById("dev-panel"))
        return;
    const panel = document.createElement("details");
    panel.id = "dev-panel";
    panel.className = "dev-panel";
    panel.open = false;
    const summary = document.createElement("summary");
    summary.textContent = "Dev Panel";
    panel.appendChild(summary);
    const content = document.createElement("div");
    content.className = "dev-panel-content";
    panel.appendChild(content);
    panel.classList.add("hidden");
    host.appendChild(panel);
    const moved = new Set();
    const groups = [
        ["btn-auth", "jwt", "auth-out"],
        ["btn-chat", "chat-input", "chat-reply", "chat-error", "chat-proposal"],
        ["btn-prefs-get", "btn-prefs-put", "prefs-servings", "prefs-meals", "prefs-out"],
        ["btn-plan-gen", "plan-out"],
        ["btn-shopping", "shopping-out"],
    ];
    groups.forEach((ids) => moveGroupIntoDevPanel(ids, content, moved));
}
function renderProposal() {
    const container = document.getElementById("chat-proposal");
    const textEl = document.getElementById("chat-proposal-text");
    if (!container || !textEl)
        return;
    if (!state.proposalId || !state.proposedActions.length) {
        container.classList.add("hidden");
        textEl.textContent = "";
        return;
    }
    const summaries = state.proposedActions.map((action) => {
        if (action.action_type === "upsert_prefs" && action.prefs) {
            return `Update prefs: servings ${action.prefs.servings}, meals/day ${action.prefs.meals_per_day}`;
        }
        if (action.action_type === "create_inventory_event" && action.event) {
            const e = action.event;
            return `Inventory: ${e.event_type} ${e.quantity} ${e.unit} ${e.item_name}`;
        }
        return action.action_type || "proposal";
    });
    textEl.textContent = summaries.join(" | ");
    container.classList.remove("hidden");
}
function clearProposal() {
    state.proposalId = null;
    state.proposedActions = [];
    renderProposal();
}
function detectProposalCommand(message) {
    const normalized = message.trim().toLowerCase();
    if (!normalized)
        return null;
    if (PROPOSAL_CONFIRM_COMMANDS.has(normalized))
        return "confirm";
    if (PROPOSAL_DENY_COMMANDS.has(normalized))
        return "deny";
    return null;
}
async function submitProposalDecision(confirm, thinkingIndex) {
    var _a;
    if (!state.proposalId)
        return;
    setChatError("");
    setDuetStatus(confirm ? "Applying proposal confirmation..." : "Cancelling proposal...");
    setComposerBusy(true);
    try {
        const payload = {
            proposal_id: state.proposalId,
            confirm,
            thread_id: duetState.threadId,
        };
        const response = await doPost("/chat/confirm", payload);
        const success = response.status >= 200 && response.status < 300;
        const assistantText = confirm
            ? success
                ? ((_a = response.json) === null || _a === void 0 ? void 0 : _a.applied)
                    ? "Preferences confirmed."
                    : "No pending preferences added."
                : "Confirmation failed."
            : success
                ? "Preferences update cancelled."
                : "Cancellation failed.";
        if (typeof thinkingIndex === "number") {
            updateHistory(thinkingIndex, assistantText);
        }
        else {
            addHistory("assistant", assistantText);
        }
        state.chatReply = response;
        setText("chat-reply", { status: response.status, json: response.json });
        setDuetStatus(success ? "Reply received." : "Confirmation failed.");
        if (success) {
            clearProposal();
        }
    }
    catch (err) {
        console.error(err);
        setChatError("Network error. Try again.");
        setDuetStatus("Confirmation failed.");
    }
    finally {
        setComposerBusy(false);
    }
}
function setChatError(msg) {
    state.chatError = msg;
    const el = document.getElementById("chat-error");
    if (el)
        el.textContent = msg;
}
function setDuetStatus(msg, isError = false) {
    const el = document.getElementById("duet-status");
    if (!el)
        return;
    el.textContent = msg;
    el.classList.toggle("error", isError);
}
function setComposerPlaceholder() {
    var _a;
    const input = document.getElementById("duet-input");
    if (!input)
        return;
    const flow = (_a = flowOptions.find((f) => f.key === currentFlowKey)) !== null && _a !== void 0 ? _a : flowOptions[0];
    input.placeholder = flow.placeholder;
}
function flowDisplayLabel(key) {
    const flow = flowOptions.find((f) => f.key === key);
    if (!flow)
        return "Unknown";
    return flow.key === "general" ? "Home" : flow.label;
}
function flowMenuCandidates() {
    if (currentFlowKey === "general") {
        return flowOptions.filter((f) => f.key !== "general");
    }
    return flowOptions.filter((f) => f.key !== currentFlowKey).map((f) => (f.key === "general" ? { ...f, label: "Home" } : f));
}
function setFlowMenuOpen(open) {
    flowMenuOpen = open;
    if (flowMenuDropdown) {
        flowMenuDropdown.style.display = open ? "grid" : "none";
        flowMenuDropdown.classList.toggle("open", open);
        if (open) {
            positionFlowMenuDropdown();
        }
    }
    flowMenuButton === null || flowMenuButton === void 0 ? void 0 : flowMenuButton.setAttribute("aria-expanded", open ? "true" : "false");
}
function renderFlowMenu() {
    const dropdown = flowMenuDropdown;
    const trigger = flowMenuButton;
    if (!dropdown || !trigger)
        return;
    dropdown.innerHTML = "";
    flowMenuCandidates().forEach((flow) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "flow-menu-item";
        item.textContent = flow.key === "general" ? "Home" : flow.label;
        item.setAttribute("role", "menuitem");
        item.addEventListener("click", () => {
            selectFlow(flow.key);
            setFlowMenuOpen(false);
        });
        dropdown.appendChild(item);
    });
    const devItem = document.createElement("button");
    devItem.type = "button";
    devItem.className = "flow-menu-item";
    devItem.textContent = "Dev Panel";
    devItem.setAttribute("role", "menuitem");
    devItem.addEventListener("click", () => {
        toggleDevPanel();
        setFlowMenuOpen(false);
    });
    dropdown.appendChild(devItem);
    const currentLabel = flowDisplayLabel(currentFlowKey);
    trigger.innerHTML = "";
    const title = document.createElement("span");
    title.textContent = "Options";
    const mode = document.createElement("span");
    mode.className = "current-label";
    mode.textContent = `Mode: ${currentLabel}`;
    trigger.appendChild(title);
    trigger.appendChild(mode);
    trigger.setAttribute("aria-label", `Options (current: ${currentLabel})`);
}
function toggleDevPanel() {
    const panel = document.getElementById("dev-panel");
    if (!panel)
        return;
    devPanelVisible = !devPanelVisible;
    panel.classList.toggle("hidden", !devPanelVisible);
    panel.open = devPanelVisible;
}
function updateThreadLabel() {
    var _a;
    const label = document.getElementById("duet-thread-label");
    if (!label)
        return;
    label.textContent = `Thread: ${(_a = duetState.threadId) !== null && _a !== void 0 ? _a : "-"} | Mode: ${lastServerMode}`;
}
function syncHistoryUi() {
    const open = duetState.drawerOpen;
    document.body.classList.toggle("history-open", open);
    historyOverlay === null || historyOverlay === void 0 ? void 0 : historyOverlay.classList.toggle("open", open);
    historyOverlay === null || historyOverlay === void 0 ? void 0 : historyOverlay.setAttribute("aria-hidden", open ? "false" : "true");
    if (historyToggle) {
        historyToggle.setAttribute("aria-expanded", open ? "true" : "false");
        historyToggle.classList.toggle("active", open);
    }
}
function renderDuetHistory() {
    const list = document.getElementById("duet-history-list");
    const empty = document.getElementById("duet-history-empty");
    if (!list || !empty)
        return;
    list.innerHTML = "";
    if (!duetState.history.length) {
        empty.classList.remove("hidden");
        return;
    }
    empty.classList.add("hidden");
    [...duetState.history]
        .slice()
        .reverse()
        .forEach((item) => {
        const li = document.createElement("li");
        li.className = item.role;
        li.textContent = item.text;
        list.appendChild(li);
    });
}
function setBubbleText(element, text) {
    if (!element)
        return;
    element.innerHTML = "";
    if (!text)
        return;
    const parts = text.split("\n");
    parts.forEach((line, idx) => {
        element.append(document.createTextNode(line));
        if (idx < parts.length - 1) {
            element.append(document.createElement("br"));
        }
    });
}
function updateDuetBubbles() {
    var _a, _b;
    const assistant = document.getElementById("duet-assistant-text");
    const user = document.getElementById("duet-user-text");
    const lastAssistant = [...duetState.history].reverse().find((h) => h.role === "assistant");
    const lastUser = [...duetState.history].reverse().find((h) => h.role === "user");
    const assistantFallback = "Welcome — I’m Little Chef. To start onboarding, please fill out your preferences (allergies, likes/dislikes, servings, days).";
    const userFallback = "Press and hold to start onboarding with preferences.";
    setBubbleText(assistant, (_a = lastAssistant === null || lastAssistant === void 0 ? void 0 : lastAssistant.text) !== null && _a !== void 0 ? _a : assistantFallback);
    setBubbleText(user, (_b = lastUser === null || lastUser === void 0 ? void 0 : lastUser.text) !== null && _b !== void 0 ? _b : userFallback);
}
function applyDrawerProgress(progress, opts) {
    var _a;
    const history = document.getElementById("duet-history");
    const userBubble = document.getElementById("duet-user-bubble");
    if (!history || !userBubble)
        return;
    ensureHistoryClosedOffset(history);
    const clamped = Math.max(0, Math.min(1, progress));
    duetState.drawerProgress = clamped;
    history.style.setProperty("--drawer-progress", clamped.toString());
    const shouldShow = ((_a = opts === null || opts === void 0 ? void 0 : opts.dragging) !== null && _a !== void 0 ? _a : false) || clamped > 0;
    history.style.display = shouldShow ? "grid" : "none";
    history.style.pointerEvents = shouldShow ? "auto" : "none";
    history.classList.toggle("dragging", !!(opts === null || opts === void 0 ? void 0 : opts.dragging));
    if (opts === null || opts === void 0 ? void 0 : opts.commit) {
        duetState.drawerOpen = clamped > 0.35;
        history.classList.toggle("open", duetState.drawerOpen);
        syncHistoryUi();
    }
    userBubble.style.transform = "";
}
function wireDuetDrag() {
    const userBubble = document.getElementById("duet-user-bubble");
    if (!userBubble)
        return;
    let dragging = false;
    let startY = 0;
    let pointerId = null;
    const endDrag = () => {
        if (!dragging)
            return;
        dragging = false;
        pointerId = null;
        const targetOpen = duetState.drawerProgress > 0.35;
        applyDrawerProgress(targetOpen ? 1 : 0, { commit: true });
    };
    userBubble.addEventListener("pointerdown", (ev) => {
        dragging = true;
        startY = ev.clientY;
        pointerId = ev.pointerId;
        userBubble.setPointerCapture(ev.pointerId);
        applyDrawerProgress(duetState.drawerProgress, { dragging: true });
    });
    userBubble.addEventListener("pointermove", (ev) => {
        if (!dragging || (pointerId !== null && ev.pointerId !== pointerId))
            return;
        const dy = startY - ev.clientY;
        const progress = dy <= 0 ? 0 : Math.min(dy / 120, 1);
        applyDrawerProgress(progress, { dragging: true });
    });
    const cancel = () => {
        if (!dragging)
            return;
        dragging = false;
        pointerId = null;
        applyDrawerProgress(duetState.drawerOpen ? 1 : 0, { commit: true });
    };
    userBubble.addEventListener("pointerup", endDrag);
    userBubble.addEventListener("pointercancel", cancel);
    userBubble.addEventListener("lostpointercapture", cancel);
}
function setDrawerOpen(open) {
    applyDrawerProgress(open ? 1 : 0, { commit: true });
}
function ensureHistoryClosedOffset(historyEl) {
    var _a;
    const stage = document.querySelector(".duet-stage");
    const stageHeight = (_a = stage === null || stage === void 0 ? void 0 : stage.offsetHeight) !== null && _a !== void 0 ? _a : 0;
    const historyHeight = historyEl.offsetHeight || 0;
    const offset = Math.max(historyHeight, stageHeight) + 200; // larger buffer to force fully off-screen
    historyEl.style.setProperty("--history-closed-offset", `${offset}px`);
}
function bindResizeForHistoryOffset() {
    const history = document.getElementById("duet-history");
    if (!history)
        return;
    const recalc = () => ensureHistoryClosedOffset(history);
    window.addEventListener("resize", recalc);
    recalc();
}
function startNewThread() {
    duetState.threadId = crypto.randomUUID();
    duetState.history = [];
    renderDuetHistory();
    updateDuetBubbles();
    updateThreadLabel();
    setDuetStatus("New thread created.");
}
function addHistory(role, text) {
    duetState.history.push({ role, text });
    renderDuetHistory();
    updateDuetBubbles();
    return duetState.history.length - 1;
}
function updateHistory(index, text) {
    if (index < 0 || index >= duetState.history.length)
        return;
    duetState.history[index] = { ...duetState.history[index], text };
    renderDuetHistory();
    updateDuetBubbles();
}
function setupHistoryDrawerUi() {
    const shell = document.getElementById("duet-shell");
    const stage = document.querySelector(".duet-stage");
    if (!shell || !stage)
        return;
    const historyPanel = document.getElementById("duet-history");
    const historyHeader = historyPanel === null || historyPanel === void 0 ? void 0 : historyPanel.querySelector(".history-header");
    if (historyHeader && !historyHeader.querySelector("#duet-new-thread")) {
        const newThreadBtn = document.createElement("button");
        newThreadBtn.id = "duet-new-thread";
        newThreadBtn.type = "button";
        newThreadBtn.className = "pill-btn";
        newThreadBtn.textContent = "New Thread";
        newThreadBtn.addEventListener("click", () => startNewThread());
        historyHeader.appendChild(newThreadBtn);
    }
    if (!historyOverlay) {
        historyOverlay = document.createElement("div");
        historyOverlay.className = "history-overlay";
        historyOverlay.setAttribute("aria-hidden", "true");
        historyOverlay.addEventListener("click", () => setDrawerOpen(false));
        historyOverlay.addEventListener("touchmove", (ev) => {
            ev.preventDefault();
        }, { passive: false });
        historyOverlay.addEventListener("wheel", (ev) => {
            ev.preventDefault();
        }, { passive: false });
        shell.appendChild(historyOverlay);
    }
    if (!historyToggle) {
        historyToggle = document.createElement("button");
        historyToggle.id = "duet-history-toggle";
        historyToggle.type = "button";
        historyToggle.className = "icon-btn history-toggle";
        historyToggle.setAttribute("aria-label", "Toggle history drawer");
        historyToggle.setAttribute("aria-controls", "duet-history");
        historyToggle.setAttribute("aria-expanded", "false");
        historyToggle.textContent = "🕑";
        historyToggle.addEventListener("click", () => setDrawerOpen(!duetState.drawerOpen));
        historyToggle.addEventListener("keydown", (ev) => {
            if (ev.key === "Enter" || ev.key === " ") {
                ev.preventDefault();
                setDrawerOpen(!duetState.drawerOpen);
            }
        });
        stage.appendChild(historyToggle);
    }
}
function wireHistoryHotkeys() {
    document.addEventListener("keydown", (ev) => {
        if (ev.key === "Escape" && duetState.drawerOpen) {
            setDrawerOpen(false);
        }
    });
}
function formatQuantity(quantity, unit, approx) {
    const safe = Number.isFinite(quantity) ? quantity : 0;
    const rounded = Math.abs(safe) >= 10 ? safe.toFixed(1) : safe.toString();
    const trimmed = rounded.replace(/\.0+$/, "").replace(/(\.\d*[1-9])0+$/, "$1");
    const prefix = approx ? "~" : "";
    return `${prefix}${trimmed} ${unit}`;
}
function setInventoryStatus(text) {
    if (inventoryStatusEl) {
        inventoryStatusEl.textContent = text;
    }
}
function renderInventoryLists(low, summary) {
    const lowList = inventoryLowList;
    if (lowList) {
        lowList.innerHTML = "";
        if (!low || !low.length) {
            const li = document.createElement("li");
            li.className = "inventory-empty";
            li.textContent = "No low stock items.";
            lowList.appendChild(li);
        }
        else {
            low.forEach((item) => {
                const li = document.createElement("li");
                const reason = item.reason ? ` - ${item.reason}` : "";
                li.textContent = `${item.item_name} - ${formatQuantity(item.quantity, item.unit)} (threshold ${item.threshold})${reason}`;
                lowList.appendChild(li);
            });
        }
    }
    const summaryList = inventorySummaryList;
    if (summaryList) {
        summaryList.innerHTML = "";
        if (!summary || !summary.length) {
            const li = document.createElement("li");
            li.className = "inventory-empty";
            li.textContent = "No items.";
            summaryList.appendChild(li);
        }
        else {
            summary.forEach((item) => {
                const li = document.createElement("li");
                li.textContent = `${item.item_name} - ${formatQuantity(item.quantity, item.unit, item.approx)}`;
                summaryList.appendChild(li);
            });
        }
    }
}
async function refreshInventoryOverlay(force = false) {
    var _a, _b;
    if (!inventoryOverlay)
        return;
    if (inventoryLoading && !force)
        return;
    inventoryLoading = true;
    setInventoryStatus("Loading...");
    try {
        const [summaryResp, lowResp] = await Promise.all([doGet("/inventory/summary"), doGet("/inventory/low-stock")]);
        if (summaryResp.status === 401 || lowResp.status === 401) {
            setInventoryStatus("Unauthorized (set token in Dev Panel)");
            renderInventoryLists([], []);
            inventoryHasLoaded = true;
            return;
        }
        const summaryItems = Array.isArray((_a = summaryResp.json) === null || _a === void 0 ? void 0 : _a.items) ? summaryResp.json.items : [];
        const lowItems = Array.isArray((_b = lowResp.json) === null || _b === void 0 ? void 0 : _b.items) ? lowResp.json.items : [];
        renderInventoryLists(lowItems, summaryItems);
        const hasAny = lowItems.length > 0 || summaryItems.length > 0;
        setInventoryStatus(hasAny ? "Read-only snapshot" : "No items yet.");
        inventoryHasLoaded = true;
    }
    catch (err) {
        setInventoryStatus("Network error. Try refresh.");
        renderInventoryLists([], []);
        console.error(err);
    }
    finally {
        inventoryLoading = false;
    }
}
function updateInventoryOverlayVisibility() {
    if (!inventoryOverlay)
        return;
    const visible = currentFlowKey === "inventory";
    inventoryOverlay.classList.toggle("hidden", !visible);
    inventoryOverlay.style.display = visible ? "flex" : "none";
    if (visible && (!inventoryHasLoaded || !(inventoryLowList === null || inventoryLowList === void 0 ? void 0 : inventoryLowList.childElementCount))) {
        refreshInventoryOverlay();
    }
}
function setupInventoryGhostOverlay() {
    const shell = document.getElementById("duet-shell");
    const stage = shell === null || shell === void 0 ? void 0 : shell.querySelector(".duet-stage");
    if (!shell || !stage || document.getElementById("inventory-ghost"))
        return;
    const overlay = document.createElement("div");
    overlay.id = "inventory-ghost";
    overlay.className = "inventory-ghost hidden";
    overlay.style.display = "flex";
    overlay.style.flexDirection = "column";
    overlay.style.justifyContent = "center";
    overlay.style.alignItems = "center";
    overlay.style.gap = "14px";
    overlay.style.inset = "10px";
    overlay.style.width = "calc(100% - 20px)";
    overlay.style.height = "calc(100% - 20px)";
    overlay.style.position = "absolute";
    const content = document.createElement("div");
    content.style.display = "grid";
    content.style.gap = "12px";
    content.style.width = "100%";
    content.style.maxWidth = "520px";
    content.style.margin = "0 auto";
    const header = document.createElement("div");
    header.className = "inventory-ghost-header";
    const title = document.createElement("span");
    title.textContent = "Inventory";
    const refresh = document.createElement("button");
    refresh.type = "button";
    refresh.className = "ghost-refresh";
    refresh.textContent = "Refresh";
    refresh.addEventListener("click", () => refreshInventoryOverlay(true));
    header.appendChild(title);
    header.appendChild(refresh);
    const status = document.createElement("div");
    status.id = "inventory-ghost-status";
    status.className = "inventory-ghost-status";
    status.textContent = "Select Inventory to load.";
    const lowSection = document.createElement("div");
    lowSection.className = "inventory-ghost-section";
    lowSection.style.width = "100%";
    const lowTitle = document.createElement("div");
    lowTitle.className = "inventory-ghost-title";
    lowTitle.textContent = "Low stock";
    const lowList = document.createElement("ul");
    lowList.id = "inventory-low-list";
    lowSection.appendChild(lowTitle);
    lowSection.appendChild(lowList);
    const summarySection = document.createElement("div");
    summarySection.className = "inventory-ghost-section";
    summarySection.style.width = "100%";
    const summaryTitle = document.createElement("div");
    summaryTitle.className = "inventory-ghost-title";
    summaryTitle.textContent = "In stock";
    const summaryList = document.createElement("ul");
    summaryList.id = "inventory-summary-list";
    summarySection.appendChild(summaryTitle);
    summarySection.appendChild(summaryList);
    content.appendChild(header);
    content.appendChild(status);
    content.appendChild(lowSection);
    content.appendChild(summarySection);
    overlay.appendChild(content);
    stage.appendChild(overlay);
    inventoryOverlay = overlay;
    inventoryStatusEl = status;
    inventoryLowList = lowList;
    inventorySummaryList = summaryList;
}
async function doGet(path) {
    const res = await fetch(path, { headers: headers() });
    return { status: res.status, json: await res.json().catch(() => null) };
}
async function doPost(path, body) {
    const res = await fetch(path, { method: "POST", headers: headers(), body: JSON.stringify(body) });
    return { status: res.status, json: await res.json().catch(() => null) };
}
function shellOnlyDuetReply(userText) {
    var _a;
    const thread = (_a = duetState.threadId) !== null && _a !== void 0 ? _a : crypto.randomUUID();
    duetState.threadId = thread;
    updateThreadLabel();
    const replyText = "(Shell) Phase 7.1: backend wiring lands in Phase 7.4.";
    const resp = { status: 200, json: { reply_text: replyText, confirmation_required: false, thread_id: thread } };
    state.chatReply = resp;
    setText("chat-reply", resp);
    addHistory("assistant", replyText);
    renderDuetHistory();
    updateDuetBubbles();
    setDuetStatus("Shell-only: local echo shown; backend wiring arrives in Phase 7.4.");
    return resp;
}
async function sendAsk(message, opts) {
    var _a, _b;
    const ensureThread = () => {
        if (!duetState.threadId) {
            duetState.threadId = crypto.randomUUID();
            updateThreadLabel();
        }
        return duetState.threadId;
    };
    const normalizedMessage = message.trim();
    const flowLabel = opts === null || opts === void 0 ? void 0 : opts.flowLabel;
    const displayText = flowLabel ? `[${flowLabel}] ${normalizedMessage}` : normalizedMessage;
    const userIndex = addHistory("user", displayText);
    const thinkingIndex = addHistory("assistant", "...");
    const command = state.proposalId ? detectProposalCommand(normalizedMessage) : null;
    if (command) {
        setDuetStatus(command === "confirm" ? "Applying proposal confirmation..." : "Cancelling proposal...");
        setComposerBusy(true);
        try {
            await submitProposalDecision(command === "confirm", thinkingIndex);
        }
        finally {
            setComposerBusy(false);
        }
        return { userIndex, thinkingIndex };
    }
    setDuetStatus("Contacting backend...");
    setComposerBusy(true);
    try {
        const threadId = ensureThread();
        const res = await fetch("/chat", {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({
                mode: currentModeLower(),
                message,
                include_user_library: true,
                thread_id: threadId,
            }),
        });
        const json = await res.json().catch(() => null);
        if (!res.ok || !json || typeof json.reply_text !== "string") {
            throw new Error((json === null || json === void 0 ? void 0 : json.message) || `ASK failed (status ${res.status})`);
        }
        setModeFromResponse(json);
        const proposalSummary = formatProposalSummary(json);
        const replyText = json.reply_text;
        const replyBase = proposalSummary ? (_a = stripProposalPrefix(replyText)) !== null && _a !== void 0 ? _a : replyText : replyText;
        const assistantText = proposalSummary ? `${proposalSummary}\n\n${replyBase}` : replyBase;
        updateHistory(thinkingIndex, assistantText);
        state.proposalId = (_b = json.proposal_id) !== null && _b !== void 0 ? _b : null;
        state.proposedActions = Array.isArray(json.proposed_actions) ? json.proposed_actions : [];
        renderProposal();
        if (opts === null || opts === void 0 ? void 0 : opts.updateChatPanel) {
            setText("chat-reply", { status: res.status, json });
        }
        setDuetStatus("Reply received.");
    }
    catch (err) {
        updateHistory(thinkingIndex, "Network error. Try again.");
        if (opts === null || opts === void 0 ? void 0 : opts.updateChatPanel) {
            setChatError("Network error. Try again.");
        }
        console.error(err);
    }
    finally {
        setComposerBusy(false);
    }
    return { userIndex, thinkingIndex };
}
function setComposerBusy(busy) {
    composerBusy = busy;
    const input = document.getElementById("duet-input");
    const sendBtn = document.getElementById("duet-send");
    if (sendBtn)
        sendBtn.disabled = busy || !!(input && input.value.trim().length === 0);
    if (input)
        input.readOnly = busy;
}
async function silentGreetOnce() {
    var _a;
    if (!((_a = state.token) === null || _a === void 0 ? void 0 : _a.trim()))
        return;
    const key = "lc_silent_greet_done";
    if (sessionStorage.getItem(key) === "1")
        return;
    sessionStorage.setItem(key, "1");
    try {
        const greetMessage = state.onboarded === false ? "I'm new here" : "hello";
        const res = await doPost("/chat", {
            mode: "ask",
            message: greetMessage,
            include_user_library: true,
        });
        const json = res.json;
        if (res.status === 200 && json && typeof json.reply_text === "string") {
            setModeFromResponse(json);
            duetState.history.push({ role: "assistant", text: json.reply_text });
            renderDuetHistory();
            updateDuetBubbles();
        }
    }
    catch (_err) {
        // Silent failure by design
    }
}
function wire() {
    var _a, _b, _c, _d, _e, _f, _g, _h;
    enforceViewportLock();
    const jwtInput = document.getElementById("jwt");
    (_a = document.getElementById("btn-auth")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", async () => {
        var _a;
        state.token = jwtInput.value.trim();
        clearProposal();
        const result = await doGet("/auth/me");
        setText("auth-out", result);
        state.onboarded = !!((_a = result.json) === null || _a === void 0 ? void 0 : _a.onboarded);
        await silentGreetOnce();
        inventoryHasLoaded = false;
        if (currentFlowKey === "inventory") {
            refreshInventoryOverlay(true);
        }
    });
    (_b = document.getElementById("btn-chat")) === null || _b === void 0 ? void 0 : _b.addEventListener("click", async () => {
        var _a;
        const msg = document.getElementById("chat-input").value;
        clearProposal();
        setChatError("");
        if (msg === null || msg === void 0 ? void 0 : msg.trim()) {
            const flow = (_a = flowOptions.find((f) => f.key === currentFlowKey)) !== null && _a !== void 0 ? _a : flowOptions[0];
            await sendAsk(msg.trim(), { flowLabel: flow.label, updateChatPanel: true });
        }
        else {
            setChatError("Enter a message to send.");
        }
    });
    (_c = document.getElementById("btn-prefs-get")) === null || _c === void 0 ? void 0 : _c.addEventListener("click", async () => {
        const resp = await doGet("/prefs");
        setText("prefs-out", resp);
    });
    (_d = document.getElementById("btn-prefs-put")) === null || _d === void 0 ? void 0 : _d.addEventListener("click", async () => {
        const servings = Number(document.getElementById("prefs-servings").value);
        const meals = Number(document.getElementById("prefs-meals").value);
        const resp = await fetch("/prefs", {
            method: "PUT",
            headers: headers(),
            body: JSON.stringify({ prefs: { servings, meals_per_day: meals } }),
        });
        const json = await resp.json().catch(() => null);
        setText("prefs-out", { status: resp.status, json });
    });
    (_e = document.getElementById("btn-plan-gen")) === null || _e === void 0 ? void 0 : _e.addEventListener("click", async () => {
        const resp = await doPost("/mealplan/generate", { days: 2, meals_per_day: 3 });
        state.lastPlan = resp.json;
        setText("plan-out", resp);
    });
    (_f = document.getElementById("btn-shopping")) === null || _f === void 0 ? void 0 : _f.addEventListener("click", async () => {
        if (!state.lastPlan) {
            setText("shopping-out", "No plan yet. Generate a plan first.");
            return;
        }
        const resp = await doPost("/shopping/diff", { plan: state.lastPlan });
        setText("shopping-out", resp);
    });
    (_g = document.getElementById("btn-confirm")) === null || _g === void 0 ? void 0 : _g.addEventListener("click", async () => {
        if (!state.proposalId)
            return;
        setChatError("");
        setChatError("Shell-only: confirmations land in Phase 7.4.");
        setDuetStatus("Shell-only: confirmations deferred to Phase 7.4.");
        setText("chat-reply", { status: 0, json: { message: "Shell-only confirmation stub (Phase 7.4 wires backend)" } });
        clearProposal();
    });
    (_h = document.getElementById("btn-cancel")) === null || _h === void 0 ? void 0 : _h.addEventListener("click", async () => {
        if (!state.proposalId)
            return;
        setChatError("");
        setChatError("Shell-only: decline stubbed until Phase 7.4.");
        setDuetStatus("Shell-only: confirmations deferred to Phase 7.4.");
        setText("chat-reply", { status: 0, json: { message: "Shell-only decline stub (Phase 7.4 wires backend)" } });
        clearProposal();
    });
    setupFlowChips();
    setupDock();
    bindResizeForHistoryOffset();
    setupInventoryGhostOverlay();
    setupDevPanel();
    wireDuetComposer();
    setupHistoryDrawerUi();
    wireHistoryHotkeys();
    bindOnboardingLongPress();
    updateInventoryOverlayVisibility();
    applyDrawerProgress(duetState.drawerOpen ? 1 : 0, { commit: true });
    renderDuetHistory();
    updateDuetBubbles();
    updateThreadLabel();
    applyDrawerProgress(0, { commit: true });
}
document.addEventListener("DOMContentLoaded", wire);
function wireDuetComposer() {
    const input = document.getElementById("duet-input");
    const sendBtn = document.getElementById("duet-send");
    const micBtn = document.getElementById("duet-mic");
    if (!input || !sendBtn)
        return;
    const syncButtons = () => {
        sendBtn.disabled = composerBusy || input.value.trim().length === 0;
    };
    const send = () => {
        var _a;
        const text = input.value.trim();
        if (!text || composerBusy)
            return;
        setChatError("");
        const flow = (_a = flowOptions.find((f) => f.key === currentFlowKey)) !== null && _a !== void 0 ? _a : flowOptions[0];
        setDuetStatus("Sending to backend...");
        syncButtons();
        const pendingCommand = state.proposalId ? detectProposalCommand(text) : null;
        if (!pendingCommand) {
            clearProposal();
        }
        sendAsk(text, { flowLabel: flow.label });
        input.value = "";
        syncButtons();
    };
    input.addEventListener("input", syncButtons);
    sendBtn.addEventListener("click", send);
    input.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            send();
        }
    });
    micBtn === null || micBtn === void 0 ? void 0 : micBtn.addEventListener("click", () => {
        setDuetStatus("Voice uses client-side transcription; mic will feed text here.", false);
        input.focus();
    });
    setComposerPlaceholder();
}
function setupFlowChips() {
    const shell = document.getElementById("duet-shell");
    const composer = document.getElementById("duet-composer");
    if (!shell || !composer)
        return;
    if (!flowMenuContainer) {
        flowMenuContainer = document.createElement("div");
        flowMenuContainer.id = "flow-chips";
        flowMenuContainer.className = "flow-menu";
    }
    else {
        flowMenuContainer.innerHTML = "";
        flowMenuContainer.className = "flow-menu";
    }
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.id = "flow-menu-trigger";
    trigger.className = "flow-menu-btn";
    trigger.setAttribute("aria-haspopup", "true");
    trigger.setAttribute("aria-expanded", "false");
    trigger.addEventListener("click", () => setFlowMenuOpen(!flowMenuOpen));
    const dropdown = document.createElement("div");
    dropdown.className = "flow-menu-dropdown";
    dropdown.setAttribute("role", "menu");
    dropdown.style.display = "none";
    dropdown.style.position = "absolute";
    dropdown.style.top = "calc(100% + 6px)";
    dropdown.style.left = "0";
    flowMenuContainer.appendChild(trigger);
    flowMenuContainer.appendChild(dropdown);
    flowMenuButton = trigger;
    flowMenuDropdown = dropdown;
    setFlowMenuOpen(false);
    renderFlowMenu();
    if (!flowMenuListenersBound) {
        document.addEventListener("click", (ev) => {
            if (!flowMenuOpen || !flowMenuContainer)
                return;
            if (ev.target instanceof Node && flowMenuContainer.contains(ev.target))
                return;
            setFlowMenuOpen(false);
        });
        document.addEventListener("keydown", (ev) => {
            if (ev.key === "Escape" && flowMenuOpen) {
                setFlowMenuOpen(false);
            }
        });
        flowMenuListenersBound = true;
    }
}
function enforceViewportLock() {
    const html = document.documentElement;
    const body = document.body;
    const main = document.querySelector("main.container");
    const shell = document.getElementById("duet-shell");
    const stage = shell === null || shell === void 0 ? void 0 : shell.querySelector(".duet-stage");
    const composer = document.getElementById("duet-composer");
    const trigger = document.getElementById("flow-menu-trigger");
    const dock = document.getElementById("duet-dock");
    html.style.height = "100%";
    html.style.overscrollBehavior = "none";
    html.style.maxWidth = "100vw";
    html.style.overflow = "hidden";
    body.style.height = "100%";
    body.style.minHeight = "100dvh";
    body.style.maxWidth = "100vw";
    body.style.overflow = "hidden";
    body.style.overscrollBehavior = "none";
    if (main) {
        main.style.height = "100dvh";
        main.style.maxHeight = "100dvh";
        main.style.overflow = "hidden";
    }
    if (shell) {
        shell.style.display = "flex";
        shell.style.flexDirection = "column";
        shell.style.flex = "1 1 auto";
        shell.style.minHeight = "0";
        shell.style.height = "100%";
    }
    if (stage) {
        stage.style.flex = "1 1 auto";
        stage.style.minHeight = "0";
        stage.style.overflowY = "auto";
        stage.style.overscrollBehavior = "contain";
    }
    if (trigger) {
        trigger.style.flex = "0 0 auto";
    }
    if (composer) {
        composer.style.flex = "0 0 auto";
    }
    if (dock) {
        dock.style.display = "flex";
        dock.style.flexDirection = "column";
        dock.style.gap = "10px";
        dock.style.marginTop = "auto";
        dock.style.width = "100%";
    }
}
function selectFlow(key) {
    if (!flowOptions.find((f) => f.key === key))
        return;
    currentFlowKey = key;
    renderFlowMenu();
    setFlowMenuOpen(false);
    setComposerPlaceholder();
    updateInventoryOverlayVisibility();
    if (currentFlowKey === "inventory") {
        refreshInventoryOverlay(true);
    }
}
function ensureOnboardMenu() {
    if (onboardMenu)
        return onboardMenu;
    const menu = document.createElement("div");
    menu.id = "onboard-menu";
    menu.className = "flow-menu-dropdown";
    menu.style.position = "fixed";
    menu.style.display = "none";
    menu.style.zIndex = "999";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "flow-menu-item";
    btn.textContent = "Preferences";
    btn.dataset.onboardItem = "start";
    btn.addEventListener("click", () => {
        hideOnboardMenu();
        startOnboarding();
    });
    menu.appendChild(btn);
    document.body.appendChild(menu);
    onboardMenu = menu;
    return menu;
}
function hideOnboardMenu() {
    if (onboardMenu)
        onboardMenu.style.display = "none";
    onboardMenuActive = false;
    if (onboardActiveItem) {
        onboardActiveItem.classList.remove("active");
        onboardActiveItem.style.outline = "";
    }
    onboardActiveItem = null;
}
function showOnboardMenu(x, y) {
    const menu = ensureOnboardMenu();
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
    menu.style.display = "grid";
    onboardMenuActive = true;
    onboardIgnoreDocClickUntilMs = Date.now() + 800;
    onboardDragActive = true;
}
function startOnboarding() {
    selectFlow("prefs");
    const assistantText = "To get started, let’s set your preferences (allergies, likes/dislikes, servings, days).";
    const userText = "Answer in one message…";
    const assistant = document.getElementById("duet-assistant-text");
    const user = document.getElementById("duet-user-text");
    if (assistant)
        assistant.textContent = assistantText;
    if (user)
        user.textContent = userText;
}
function setupDock() {
    const shell = document.getElementById("duet-shell");
    const composer = document.getElementById("duet-composer");
    if (!shell || !composer)
        return;
    let dock = document.getElementById("duet-dock");
    if (!dock) {
        dock = document.createElement("div");
        dock.id = "duet-dock";
        dock.className = "duet-dock";
        shell.appendChild(dock);
    }
    if (flowMenuContainer && flowMenuContainer.parentElement !== dock) {
        dock.appendChild(flowMenuContainer);
    }
    if (composer.parentElement !== dock) {
        dock.appendChild(composer);
    }
    enforceViewportLock();
}
function bindOnboardingLongPress() {
    const userBubble = document.getElementById("duet-user-bubble");
    if (!userBubble)
        return;
    const clearTimer = () => {
        if (onboardPressTimer !== null) {
            window.clearTimeout(onboardPressTimer);
            onboardPressTimer = null;
        }
    };
    const cancel = (opts) => {
        var _a;
        clearTimer();
        onboardPressStart = null;
        onboardPointerId = null;
        if ((_a = opts === null || opts === void 0 ? void 0 : opts.hideMenu) !== null && _a !== void 0 ? _a : true) {
            hideOnboardMenu();
        }
    };
    userBubble.addEventListener("pointerdown", (ev) => {
        onboardPressStart = { x: ev.clientX, y: ev.clientY };
        clearTimer();
        onboardPointerId = ev.pointerId;
        onboardPressTimer = window.setTimeout(() => {
            showOnboardMenu(ev.clientX, ev.clientY);
            onboardPressTimer = null;
            onboardPressStart = null;
            try {
                userBubble.setPointerCapture(ev.pointerId);
            }
            catch (_err) {
                // ignore if capture not supported
            }
        }, 500);
    });
    userBubble.addEventListener("pointermove", (ev) => {
        if (onboardMenuActive) {
            const el = document.elementFromPoint(ev.clientX, ev.clientY);
            const item = el === null || el === void 0 ? void 0 : el.closest("[data-onboard-item]");
            if (item !== onboardActiveItem) {
                if (onboardActiveItem) {
                    onboardActiveItem.classList.remove("active");
                    onboardActiveItem.style.outline = "";
                }
                onboardActiveItem = item;
                if (onboardActiveItem) {
                    onboardActiveItem.classList.add("active");
                    onboardActiveItem.style.outline = "2px solid #7df";
                }
            }
            return;
        }
        if (!onboardPressStart || onboardPressTimer === null)
            return;
        const dx = Math.abs(ev.clientX - onboardPressStart.x);
        const dy = Math.abs(ev.clientY - onboardPressStart.y);
        if (dx > 6 || dy > 6) {
            cancel();
        }
    });
    userBubble.addEventListener("pointerup", (ev) => {
        if (onboardMenuActive) {
            const startHovered = (onboardActiveItem === null || onboardActiveItem === void 0 ? void 0 : onboardActiveItem.dataset.onboardItem) === "start";
            if (startHovered) {
                startOnboarding();
                hideOnboardMenu();
            }
            onboardDragActive = false;
            cancel({ hideMenu: false });
            return;
        }
        cancel();
    });
    userBubble.addEventListener("pointercancel", () => cancel());
    userBubble.addEventListener("lostpointercapture", () => {
        if (onboardMenuActive) {
            cancel({ hideMenu: false });
        }
        else {
            cancel();
        }
    });
    document.addEventListener("click", (ev) => {
        if (!onboardMenu || onboardMenu.style.display === "none")
            return;
        if (Date.now() < onboardIgnoreDocClickUntilMs)
            return;
        if (onboardDragActive)
            return;
        if (ev.target instanceof Node && onboardMenu.contains(ev.target))
            return;
        hideOnboardMenu();
    });
}
function positionFlowMenuDropdown() {
    const dropdown = flowMenuDropdown;
    const trigger = flowMenuButton;
    if (!dropdown || !trigger)
        return;
    const prevDisplay = dropdown.style.display;
    const prevVisibility = dropdown.style.visibility;
    dropdown.style.visibility = "hidden";
    dropdown.style.display = "grid";
    const dropdownHeight = dropdown.getBoundingClientRect().height || dropdown.offsetHeight || 0;
    const triggerRect = trigger.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const spaceBelow = viewportHeight - triggerRect.bottom;
    const spaceAbove = triggerRect.top;
    dropdown.style.top = "";
    dropdown.style.bottom = "";
    if (spaceBelow >= dropdownHeight + 8) {
        dropdown.style.top = `${trigger.offsetHeight + 6}px`;
    }
    else if (spaceAbove >= dropdownHeight + 8) {
        dropdown.style.bottom = `${trigger.offsetHeight + 6}px`;
    }
    else {
        dropdown.style.top = `${Math.max(6, spaceBelow - 2)}px`;
    }
    dropdown.style.display = prevDisplay;
    dropdown.style.visibility = prevVisibility;
}
