"use strict";
const state = {
    token: "",
    lastPlan: null,
    proposalId: null,
    proposedActions: [],
    chatReply: null,
    chatError: "",
};
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
let historyOverlay = null;
let historyToggle = null;
let currentFlowKey = flowOptions[0].key;
let composerBusy = false;
let inventoryOverlay = null;
let inventoryStatusEl = null;
let inventoryLowList = null;
let inventorySummaryList = null;
let inventoryLoading = false;
let inventoryHasLoaded = false;
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
function updateThreadLabel() {
    var _a;
    const label = document.getElementById("duet-thread-label");
    if (!label)
        return;
    label.textContent = `Thread: ${(_a = duetState.threadId) !== null && _a !== void 0 ? _a : "-"}`;
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
function updateDuetBubbles() {
    var _a, _b;
    const assistant = document.getElementById("duet-assistant-text");
    const user = document.getElementById("duet-user-text");
    const lastAssistant = [...duetState.history].reverse().find((h) => h.role === "assistant");
    const lastUser = [...duetState.history].reverse().find((h) => h.role === "user");
    if (assistant)
        assistant.textContent = (_a = lastAssistant === null || lastAssistant === void 0 ? void 0 : lastAssistant.text) !== null && _a !== void 0 ? _a : "Hi - how can I help?";
    if (user)
        user.textContent = (_b = lastUser === null || lastUser === void 0 ? void 0 : lastUser.text) !== null && _b !== void 0 ? _b : "Tap mic or type to start";
}
function applyDrawerProgress(progress, opts) {
    const history = document.getElementById("duet-history");
    const userBubble = document.getElementById("duet-user-bubble");
    if (!history || !userBubble)
        return;
    const clamped = Math.max(0, Math.min(1, progress));
    duetState.drawerProgress = clamped;
    history.style.setProperty("--drawer-progress", clamped.toString());
    history.classList.toggle("dragging", !!(opts === null || opts === void 0 ? void 0 : opts.dragging));
    if (opts === null || opts === void 0 ? void 0 : opts.commit) {
        duetState.drawerOpen = clamped > 0.35;
        history.classList.toggle("open", duetState.drawerOpen);
        syncHistoryUi();
    }
    const offset = clamped * 70;
    userBubble.style.transform = `translateY(-${offset}px)`;
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
    const lowTitle = document.createElement("div");
    lowTitle.className = "inventory-ghost-title";
    lowTitle.textContent = "Low stock";
    const lowList = document.createElement("ul");
    lowList.id = "inventory-low-list";
    lowSection.appendChild(lowTitle);
    lowSection.appendChild(lowList);
    const summarySection = document.createElement("div");
    summarySection.className = "inventory-ghost-section";
    const summaryTitle = document.createElement("div");
    summaryTitle.className = "inventory-ghost-title";
    summaryTitle.textContent = "In stock";
    const summaryList = document.createElement("ul");
    summaryList.id = "inventory-summary-list";
    summarySection.appendChild(summaryTitle);
    summarySection.appendChild(summaryList);
    overlay.appendChild(header);
    overlay.appendChild(status);
    overlay.appendChild(lowSection);
    overlay.appendChild(summarySection);
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
    const thread = (_a = duetState.threadId) !== null && _a !== void 0 ? _a : "shell-local";
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
    const flowLabel = opts === null || opts === void 0 ? void 0 : opts.flowLabel;
    const displayText = flowLabel ? `[${flowLabel}] ${message}` : message;
    const userIndex = addHistory("user", displayText);
    const thinkingIndex = addHistory("assistant", "...");
    setDuetStatus("Contacting backend...");
    setComposerBusy(true);
    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({
                mode: "ask",
                message,
                include_user_library: true,
            }),
        });
        const json = await res.json().catch(() => null);
        if (!res.ok || !json || typeof json.reply_text !== "string") {
            throw new Error((json === null || json === void 0 ? void 0 : json.message) || `ASK failed (status ${res.status})`);
        }
        updateHistory(thinkingIndex, json.reply_text);
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
function wire() {
    var _a, _b, _c, _d, _e, _f, _g, _h;
    const jwtInput = document.getElementById("jwt");
    (_a = document.getElementById("btn-auth")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", async () => {
        state.token = jwtInput.value.trim();
        clearProposal();
        const result = await doGet("/auth/me");
        setText("auth-out", result);
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
    setupInventoryGhostOverlay();
    setupDevPanel();
    wireDuetComposer();
    setupHistoryDrawerUi();
    wireHistoryHotkeys();
    wireDuetDrag();
    updateInventoryOverlayVisibility();
    applyDrawerProgress(duetState.drawerOpen ? 1 : 0, { commit: true });
    renderDuetHistory();
    updateDuetBubbles();
    updateThreadLabel();
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
        clearProposal();
        setChatError("");
        const flow = (_a = flowOptions.find((f) => f.key === currentFlowKey)) !== null && _a !== void 0 ? _a : flowOptions[0];
        setDuetStatus("Sending to backend...");
        syncButtons();
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
    let container = document.getElementById("flow-chips");
    if (!container) {
        container = document.createElement("div");
        container.id = "flow-chips";
        container.className = "flow-chips";
        shell.insertBefore(container, composer);
    }
    container.innerHTML = "";
    flowOptions.forEach((flow) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "flow-chip";
        btn.textContent = flow.label;
        btn.setAttribute("data-key", flow.key);
        btn.setAttribute("aria-pressed", flow.key === currentFlowKey ? "true" : "false");
        if (flow.key === currentFlowKey) {
            btn.classList.add("active");
        }
        btn.addEventListener("click", () => selectFlow(flow.key));
        btn.addEventListener("keydown", (ev) => {
            if (ev.key === "Enter" || ev.key === " ") {
                ev.preventDefault();
                selectFlow(flow.key);
            }
        });
        container.appendChild(btn);
    });
}
function selectFlow(key) {
    if (!flowOptions.find((f) => f.key === key))
        return;
    currentFlowKey = key;
    const chips = Array.from(document.querySelectorAll("#flow-chips .flow-chip"));
    chips.forEach((chip) => {
        const active = chip.getAttribute("data-key") === key;
        chip.classList.toggle("active", active);
        chip.setAttribute("aria-pressed", active ? "true" : "false");
    });
    setComposerPlaceholder();
    updateInventoryOverlayVisibility();
    if (currentFlowKey === "inventory") {
        refreshInventoryOverlay(true);
    }
}
