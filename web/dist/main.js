import { formatProposalSummary, stripProposalPrefix } from "./proposalRenderer.js";
const state = {
    token: "",
    lastPlan: null,
    proposalId: null,
    proposedActions: [],
    chatReply: null,
    chatError: "",
    onboarded: null,
    inventoryOnboarded: null,
};
const DEV_JWT_STORAGE_KEY = "lc_dev_jwt";
const DEV_JWT_EXP_KEY = "lc_dev_jwt_exp_utc_ms";
const DEV_JWT_DURATION_KEY = "lc_dev_jwt_duration_ms";
const DEV_JWT_DEFAULT_TTL_MS = 24 * 60 * 60 * 1000;
const DEV_JWT_DURATION_OPTIONS = [
    { value: DEV_JWT_DEFAULT_TTL_MS, label: "24 hours" },
    { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" },
];
function safeLocalStorage() {
    if (typeof window === "undefined")
        return null;
    try {
        return window.localStorage;
    }
    catch {
        return null;
    }
}
function getRememberCheckbox() {
    return document.getElementById("dev-jwt-remember");
}
function getRememberDurationSelect() {
    return document.getElementById("dev-jwt-remember-duration");
}
function saveRememberedJwt(token, ttlMs) {
    const storage = safeLocalStorage();
    if (!storage)
        return;
    storage.setItem(DEV_JWT_STORAGE_KEY, token);
    storage.setItem(DEV_JWT_EXP_KEY, (Date.now() + ttlMs).toString());
    storage.setItem(DEV_JWT_DURATION_KEY, ttlMs.toString());
}
function clearRememberedJwt() {
    const storage = safeLocalStorage();
    if (!storage)
        return;
    storage.removeItem(DEV_JWT_STORAGE_KEY);
    storage.removeItem(DEV_JWT_EXP_KEY);
    storage.removeItem(DEV_JWT_DURATION_KEY);
}
function loadRememberedJwt() {
    const storage = safeLocalStorage();
    if (!storage)
        return null;
    const token = storage.getItem(DEV_JWT_STORAGE_KEY);
    if (!token)
        return null;
    const expStr = storage.getItem(DEV_JWT_EXP_KEY);
    const durationStr = storage.getItem(DEV_JWT_DURATION_KEY);
    const expMs = Number(expStr);
    if (!expMs || expMs < Date.now()) {
        clearRememberedJwt();
        return null;
    }
    const durationMs = Number(durationStr);
    return {
        token,
        durationMs: Number.isFinite(durationMs) && durationMs > 0 ? durationMs : DEV_JWT_DEFAULT_TTL_MS,
    };
}
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
let historyBadgeCount = 0;
let historyBadgeEl = null;
let proposalActionsContainer = null;
let proposalConfirmButton = null;
let proposalEditButton = null;
let proposalDenyButton = null;
const proposalDismissedIds = new Set();
let lastResponseRequiresConfirmation = false;
let userBubbleEllipsisActive = false;
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
let prefsOverlay = null;
let prefsOverlayStatusEl = null;
let prefsOverlaySummaryEl = null;
let prefsOverlayDetails = null;
let prefsOverlayLoading = false;
let prefsOverlayHasLoaded = false;
let onboardMenu = null;
const OVERLAY_ROOT_ID = "duet-overlay-root";
const OVERLAY_ROOT_Z_INDEX = 2147483640;
const ONBOARD_MENU_EDGE_MARGIN = 8;
const USER_BUBBLE_SENT_TEXT = "👍";
const USER_BUBBLE_DEFAULT_HINT = "Long-press this chat bubble to navigate > Preferences";
let userSystemHint = USER_BUBBLE_DEFAULT_HINT;
const HISTORY_BADGE_DISPLAY_MAX = 99;
const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
let overlayRoot = null;
let onboardPressTimer = null;
let onboardPressStart = null;
let onboardPointerId = null;
let onboardMenuActive = false;
let onboardActiveItem = null;
let onboardIgnoreDocClickUntilMs = 0;
let onboardDragActive = false;
const COMPOSER_TRIPLE_TAP_WINDOW_MS = 450;
let composerVisible = false;
let stageTripleTapCount = 0;
let stageTripleTapResetTimer = null;
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
    ensureDevPanelRememberRow();
}
function ensureDevPanelRememberRow() {
    const card = document.querySelector("section.card.legacy-card");
    if (!card)
        return;
    if (getRememberCheckbox())
        return;
    const row = document.createElement("div");
    row.className = "dev-panel-remember-row";
    row.style.display = "flex";
    row.style.alignItems = "center";
    row.style.gap = "12px";
    row.style.marginTop = "8px";
    const checkboxLabel = document.createElement("label");
    checkboxLabel.className = "dev-panel-remember-label";
    checkboxLabel.style.display = "inline-flex";
    checkboxLabel.style.alignItems = "center";
    checkboxLabel.style.gap = "6px";
    const checkbox = document.createElement("input");
    checkbox.id = "dev-jwt-remember";
    checkbox.type = "checkbox";
    checkboxLabel.appendChild(checkbox);
    checkboxLabel.appendChild(document.createTextNode("Remember me"));
    const durationLabel = document.createElement("label");
    durationLabel.className = "dev-panel-remember-duration";
    durationLabel.style.display = "inline-flex";
    durationLabel.style.alignItems = "center";
    durationLabel.style.gap = "6px";
    durationLabel.textContent = "Duration:";
    const durationSelect = document.createElement("select");
    durationSelect.id = "dev-jwt-remember-duration";
    durationSelect.className = "dev-panel-remember-select";
    DEV_JWT_DURATION_OPTIONS.forEach((option) => {
        const opt = document.createElement("option");
        opt.value = option.value.toString();
        opt.textContent = option.label;
        durationSelect.appendChild(opt);
    });
    durationLabel.appendChild(durationSelect);
    row.appendChild(checkboxLabel);
    row.appendChild(durationLabel);
    const authOut = card.querySelector("#auth-out");
    if (authOut === null || authOut === void 0 ? void 0 : authOut.parentElement) {
        authOut.parentElement.insertBefore(row, authOut);
    }
    else {
        card.appendChild(row);
    }
}
function applyRememberedJwtInput(jwtInput) {
    var _a, _b;
    ensureDevPanelRememberRow();
    const checkbox = getRememberCheckbox();
    const durationSelect = getRememberDurationSelect();
    if (durationSelect && !durationSelect.value) {
        durationSelect.value = DEV_JWT_DEFAULT_TTL_MS.toString();
    }
    const stored = loadRememberedJwt();
    if (stored) {
        if (jwtInput) {
            jwtInput.value = stored.token;
        }
        state.token = stored.token;
        if (checkbox) {
            checkbox.checked = true;
        }
        if (durationSelect) {
            const desired = stored.durationMs.toString();
            const has = Array.from(durationSelect.options).some((opt) => opt.value === desired);
            durationSelect.value = has ? desired : (_b = (_a = durationSelect.options[0]) === null || _a === void 0 ? void 0 : _a.value) !== null && _b !== void 0 ? _b : desired;
        }
    }
    else {
        if (checkbox) {
            checkbox.checked = false;
        }
        if (durationSelect) {
            durationSelect.value = DEV_JWT_DEFAULT_TTL_MS.toString();
        }
    }
}
function renderProposal() {
    const container = document.getElementById("chat-proposal");
    const textEl = document.getElementById("chat-proposal-text");
    if (!container || !textEl)
        return;
    if (!state.proposalId || !state.proposedActions.length) {
        container.classList.add("hidden");
        textEl.textContent = "";
        updateProposalActionsVisibility();
        return;
    }
    const summaries = state.proposedActions.map((action) => {
        if (action.action_type === "upsert_prefs" && action.prefs) {
            return `Update prefs: servings ${action.prefs.servings}, ${action.prefs.plan_days} days, meals/day ${action.prefs.meals_per_day}`;
        }
        if (action.action_type === "create_inventory_event" && action.event) {
            const e = action.event;
            return `Inventory: ${e.event_type} ${e.quantity} ${e.unit} ${e.item_name}`;
        }
        return action.action_type || "proposal";
    });
    textEl.textContent = summaries.join(" | ");
    container.classList.remove("hidden");
    updateProposalActionsVisibility();
}
function clearProposal() {
    if (state.proposalId) {
        proposalDismissedIds.delete(state.proposalId);
    }
    lastResponseRequiresConfirmation = false;
    state.proposalId = null;
    state.proposedActions = [];
    renderProposal();
}
function shouldShowProposalActions() {
    const proposalId = state.proposalId;
    if (!proposalId || !state.proposedActions.length)
        return false;
    if (!lastResponseRequiresConfirmation)
        return false;
    return !proposalDismissedIds.has(proposalId);
}
function createProposalActionButton(id, icon, extraClass, label, handler) {
    const btn = document.createElement("button");
    btn.id = id;
    btn.type = "button";
    btn.className = `icon-btn proposal-action-btn ${extraClass}`;
    btn.setAttribute("aria-label", label);
    btn.setAttribute("data-testid", id);
    btn.textContent = icon;
    btn.addEventListener("click", handler);
    return btn;
}
function ensureProposalActions() {
    if (!proposalActionsContainer || !proposalActionsContainer.isConnected) {
        const container = document.createElement("div");
        container.id = "proposal-actions";
        container.className = "proposal-actions";
        container.setAttribute("aria-hidden", "true");
        if (!proposalConfirmButton) {
            proposalConfirmButton = createProposalActionButton("proposal-confirm", "✔", "confirm", "Confirm proposal", () => handleProposalConfirm());
        }
        if (!proposalEditButton) {
            proposalEditButton = createProposalActionButton("proposal-edit", "✏", "edit", "Edit proposal", () => handleProposalEdit());
        }
        if (!proposalDenyButton) {
            proposalDenyButton = createProposalActionButton("proposal-deny", "✖", "deny", "Deny proposal", () => handleProposalDeny());
        }
        container.append(proposalConfirmButton, proposalEditButton, proposalDenyButton);
        proposalActionsContainer = container;
    }
    if (!proposalActionsContainer) {
        return null;
    }
    const stage = document.querySelector(".duet-stage");
    const target = stage !== null && stage !== void 0 ? stage : document.body;
    if (proposalActionsContainer.parentElement !== target) {
        target.appendChild(proposalActionsContainer);
    }
    return proposalActionsContainer;
}
function updateProposalActionsVisibility() {
    const container = ensureProposalActions();
    if (!container)
        return;
    const visible = shouldShowProposalActions();
    container.classList.toggle("visible", visible);
    container.setAttribute("aria-hidden", visible ? "false" : "true");
    [proposalConfirmButton, proposalEditButton, proposalDenyButton].forEach((btn) => {
        if (btn) {
            btn.disabled = !visible;
        }
    });
}
function handleProposalConfirm() {
    if (!state.proposalId)
        return;
    void sendAsk("confirm");
}
function handleProposalEdit() {
    showFloatingComposer();
    const input = document.getElementById("duet-input");
    if (input) {
        input.placeholder = "Type your changes (e.g. 'add milk allergy')…";
        input.addEventListener("blur", () => { input.placeholder = ""; }, { once: true });
    }
    setDuetStatus("Send your changes to update the proposal.");
}
function handleProposalDeny() {
    const proposalId = state.proposalId;
    if (proposalId) {
        proposalDismissedIds.add(proposalId);
        // Clear server-side pending proposal
        void submitProposalDecision(false);
    }
    lastResponseRequiresConfirmation = false;
    updateProposalActionsVisibility();
    setDuetStatus("Proposal dismissed.");
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
    var _a, _b, _c;
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
        const flowLabel = currentFlowKey === "inventory" ? "Inventory" : "Preferences";
        const assistantText = confirm
            ? success
                ? ((_a = response.json) === null || _a === void 0 ? void 0 : _a.applied)
                    ? `${flowLabel} confirmed.`
                    : `No pending ${flowLabel.toLowerCase()} added.`
                : "Confirmation failed."
            : success
                ? `${flowLabel} update cancelled.`
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
            const confirmedPrefs = ((_b = response.json) === null || _b === void 0 ? void 0 : _b.applied) &&
                state.proposedActions.some((action) => action.action_type === "upsert_prefs");
            if (confirmedPrefs) {
                state.onboarded = true;
                ensureOnboardMenu();
                renderOnboardMenuButtons();
                updatePrefsOverlayVisibility();
                userSystemHint = "Long-press this chat bubble to navigate > Inventory";
                setUserBubbleEllipsis(false);
                setBubbleText(document.getElementById("duet-user-text"), userSystemHint);
            }
            const confirmedInventory = ((_c = response.json) === null || _c === void 0 ? void 0 : _c.applied) &&
                state.proposedActions.some((action) => action.action_type === "create_inventory_event");
            if (confirmedInventory) {
                state.inventoryOnboarded = true;
                ensureOnboardMenu();
                renderOnboardMenuButtons();
                updateInventoryOverlayVisibility();
                userSystemHint = "Long-press this chat bubble to finish onboarding > Meal Plan";
                setUserBubbleEllipsis(false);
                setBubbleText(document.getElementById("duet-user-text"), userSystemHint);
            }
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
function updateFlowStatusText() {
    var _a;
    const el = document.getElementById("duet-flow-chip");
    if (!el)
        return;
    const flow = (_a = flowOptions.find((f) => f.key === currentFlowKey)) !== null && _a !== void 0 ? _a : flowOptions[0];
    const label = flow.key === "general" ? "General" : flow.label;
    el.textContent = `[${label}]`;
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
    trigger.textContent = "⚙";
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
function setUserBubbleLabel(isSystem) {
    const label = document.querySelector("#duet-user-bubble .bubble-label");
    if (label instanceof HTMLElement) {
        label.textContent = isSystem ? "System" : "You";
    }
}
function updateDuetBubbles() {
    var _a, _b;
    const assistant = document.getElementById("duet-assistant-text");
    const user = document.getElementById("duet-user-text");
    const lastAssistant = [...duetState.history].reverse().find((h) => h.role === "assistant");
    const lastUser = [...duetState.history].reverse().find((h) => h.role === "user");
    const assistantFallback = "Welcome — I’m Little Chef.\n\nTo start onboarding, follow the instructions below.";
    setBubbleText(assistant, (_a = lastAssistant === null || lastAssistant === void 0 ? void 0 : lastAssistant.text) !== null && _a !== void 0 ? _a : assistantFallback);
    const showSentText = userBubbleEllipsisActive && isNormalChatFlow();
    const fallbackText = isNormalChatFlow() ? userSystemHint : (_b = lastUser === null || lastUser === void 0 ? void 0 : lastUser.text) !== null && _b !== void 0 ? _b : userSystemHint;
    setBubbleText(user, showSentText ? USER_BUBBLE_SENT_TEXT : fallbackText);
    const userBubble = document.getElementById("duet-user-bubble");
    if (userBubble) {
        userBubble.classList.toggle("sent-mode", showSentText);
    }
    setUserBubbleLabel(!showSentText);
}
function updateUserBubbleVisibility() {
    const userBubble = document.getElementById("duet-user-bubble");
    if (!userBubble)
        return;
    const hide = currentFlowKey === "inventory";
    userBubble.style.display = hide ? "none" : "";
}
function isNormalChatFlow() {
    return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
}
function setUserBubbleEllipsis(enabled) {
    if (userBubbleEllipsisActive === enabled) {
        return;
    }
    userBubbleEllipsisActive = enabled;
    if (!enabled) {
        updateDuetBubbles();
    }
}
function applyDrawerProgress(progress, opts) {
    var _a;
    const history = document.getElementById("duet-history");
    const stage = document.querySelector(".duet-stage");
    const userBubble = document.getElementById("duet-user-bubble");
    if (!history || !stage || !userBubble)
        return;
    ensureHistoryClosedOffset(history);
    const clamped = Math.max(0, Math.min(1, progress));
    duetState.drawerProgress = clamped;
    history.style.setProperty("--drawer-progress", clamped.toString());
    const shouldShow = ((_a = opts === null || opts === void 0 ? void 0 : opts.dragging) !== null && _a !== void 0 ? _a : false) || clamped > 0;
    history.style.display = shouldShow ? "grid" : "none";
    history.style.pointerEvents = shouldShow ? "auto" : "none";
    history.classList.toggle("dragging", !!(opts === null || opts === void 0 ? void 0 : opts.dragging));
    stage.classList.toggle("history-open", shouldShow);
    if (opts === null || opts === void 0 ? void 0 : opts.commit) {
        duetState.drawerOpen = clamped > 0.35;
        history.classList.toggle("open", duetState.drawerOpen);
        syncHistoryUi();
        if (duetState.drawerOpen) {
            handleHistoryOpened();
        }
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
function handleHistoryOpened() {
    resetHistoryBadge();
    setUserBubbleEllipsis(false);
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
function elevateDuetBubbles() {
    const assistantBubble = document.getElementById("duet-assistant-bubble");
    const userBubble = document.getElementById("duet-user-bubble");
    if (assistantBubble) {
        assistantBubble.style.zIndex = "50";
    }
    if (userBubble) {
        userBubble.style.zIndex = "50";
    }
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
    resetHistoryBadge();
}
function ensureHistoryBadgeElement() {
    if (!historyToggle)
        return null;
    if (historyBadgeEl && historyBadgeEl.isConnected) {
        return historyBadgeEl;
    }
    const badge = document.createElement("span");
    badge.className = "history-badge";
    badge.setAttribute("aria-hidden", "true");
    historyToggle.appendChild(badge);
    historyBadgeEl = badge;
    return badge;
}
function updateHistoryBadge() {
    const badge = ensureHistoryBadgeElement();
    if (!badge)
        return;
    if (historyBadgeCount > 0) {
        badge.textContent =
            historyBadgeCount > HISTORY_BADGE_DISPLAY_MAX
                ? `${HISTORY_BADGE_DISPLAY_MAX}+`
                : historyBadgeCount.toString();
        badge.classList.add("visible");
        badge.setAttribute("aria-hidden", "false");
    }
    else {
        badge.textContent = "";
        badge.classList.remove("visible");
        badge.setAttribute("aria-hidden", "true");
    }
}
function incrementHistoryBadge() {
    historyBadgeCount = Math.max(0, historyBadgeCount + 1);
    updateHistoryBadge();
}
function resetHistoryBadge() {
    historyBadgeCount = 0;
    updateHistoryBadge();
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
function markInventoryOnboarded(hasData) {
    const already = !!state.inventoryOnboarded;
    state.inventoryOnboarded = !!state.inventoryOnboarded || hasData;
    if (!already && state.inventoryOnboarded) {
        ensureOnboardMenu();
        renderOnboardMenuButtons();
        userSystemHint = "Long-press this chat bubble to finish onboarding > Meal Plan";
        setUserBubbleEllipsis(false);
        setBubbleText(document.getElementById("duet-user-text"), userSystemHint);
        updateInventoryOverlayVisibility();
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
        markInventoryOnboarded(hasAny);
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
    const wantsInventory = currentFlowKey === "inventory";
    const canShowInventory = !!state.inventoryOnboarded;
    const visible = wantsInventory && canShowInventory;
    inventoryOverlay.classList.toggle("hidden", !visible);
    inventoryOverlay.style.display = visible ? "flex" : "none";
    if (wantsInventory) {
        if (!canShowInventory) {
            refreshInventoryOverlay(true);
        }
        else if (visible && (!inventoryHasLoaded || !(inventoryLowList === null || inventoryLowList === void 0 ? void 0 : inventoryLowList.childElementCount))) {
            refreshInventoryOverlay();
        }
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
    overlay.style.display = "none";
    overlay.style.pointerEvents = "none";
    overlay.style.zIndex = "1";
    overlay.style.flexDirection = "column";
    overlay.style.justifyContent = "center";
    overlay.style.alignItems = "center";
    overlay.style.gap = "14px";
    overlay.style.inset = "10px";
    overlay.style.width = "calc(100% - 20px)";
    overlay.style.height = "calc(100% - 20px)";
    overlay.style.position = "absolute";
    const panel = document.createElement("div");
    panel.className = "prefs-overlay-content";
    panel.style.display = "grid";
    panel.style.pointerEvents = "auto";
    panel.style.gap = "12px";
    panel.style.width = "100%";
    panel.style.maxWidth = "520px";
    panel.style.margin = "0 auto";
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
    panel.appendChild(header);
    panel.appendChild(status);
    panel.appendChild(lowSection);
    panel.appendChild(summarySection);
    overlay.appendChild(panel);
    stage.appendChild(overlay);
    inventoryOverlay = overlay;
    inventoryStatusEl = status;
    inventoryLowList = lowList;
    inventorySummaryList = summaryList;
}
function setPrefsOverlayStatus(text) {
    if (prefsOverlayStatusEl) {
        prefsOverlayStatusEl.textContent = text;
    }
}
function renderPrefsOverlay(prefs) {
    const details = prefsOverlayDetails;
    const summaryEl = prefsOverlaySummaryEl;
    if (!details || !summaryEl)
        return;
    details.innerHTML = "";
    if (!prefs) {
        summaryEl.textContent = "No preferences yet.";
        const empty = document.createElement("div");
        empty.className = "prefs-overlay-empty";
        empty.textContent = "No preferences saved yet.";
        details.appendChild(empty);
        return;
    }
    const servings = Number.isFinite(prefs.servings) ? prefs.servings : "—";
    const meals = Number.isFinite(prefs.meals_per_day) ? prefs.meals_per_day : "—";
    const days = Number.isFinite(prefs.plan_days) ? prefs.plan_days : "—";
    summaryEl.textContent = `${servings} servings · ${days} days · ${meals} meals/day`;
    const sections = [
        { title: "Allergies", items: Array.isArray(prefs.allergies) ? prefs.allergies : [] },
        { title: "Dislikes", items: Array.isArray(prefs.dislikes) ? prefs.dislikes : [] },
        { title: "Likes", items: Array.isArray(prefs.cuisine_likes) ? prefs.cuisine_likes : [] },
    ];
    sections.forEach((section) => {
        const sectionEl = document.createElement("div");
        sectionEl.className = "prefs-overlay-section inventory-ghost-section";
        const titleEl = document.createElement("div");
        titleEl.className = "prefs-overlay-title inventory-ghost-title";
        titleEl.textContent = section.title;
        sectionEl.appendChild(titleEl);
        const list = document.createElement("ul");
        list.className = "prefs-overlay-list";
        if (!section.items.length) {
            const li = document.createElement("li");
            li.className = "inventory-empty";
            li.textContent = "None yet.";
            list.appendChild(li);
        }
        else {
            section.items.forEach((item) => {
                const li = document.createElement("li");
                li.textContent = item;
                list.appendChild(li);
            });
        }
        sectionEl.appendChild(list);
        details.appendChild(sectionEl);
    });
    if (prefs.notes) {
        const notesSection = document.createElement("div");
        notesSection.className = "prefs-overlay-section";
        const notesTitle = document.createElement("div");
        notesTitle.className = "prefs-overlay-title";
        notesTitle.textContent = "Notes";
        const notesBody = document.createElement("div");
        notesBody.className = "prefs-overlay-notes";
        notesBody.textContent = prefs.notes;
        notesSection.appendChild(notesTitle);
        notesSection.appendChild(notesBody);
        details.appendChild(notesSection);
    }
}
async function refreshPrefsOverlay(force = false) {
    if (!prefsOverlay)
        return;
    if (prefsOverlayLoading && !force)
        return;
    prefsOverlayLoading = true;
    setPrefsOverlayStatus("Loading...");
    try {
        const resp = await doGet("/prefs");
        if (resp.status === 401) {
            setPrefsOverlayStatus("Unauthorized (set token in Dev Panel)");
            renderPrefsOverlay(null);
            prefsOverlayHasLoaded = true;
            return;
        }
        const payload = resp.json;
        const hasData = payload && typeof payload === "object" && payload !== null && (typeof payload.servings === "number" || Array.isArray(payload.allergies));
        renderPrefsOverlay(hasData ? payload : null);
        setPrefsOverlayStatus(hasData ? "Read-only snapshot" : "No preferences yet.");
        prefsOverlayHasLoaded = true;
    }
    catch (err) {
        setPrefsOverlayStatus("Network error. Try refresh.");
        renderPrefsOverlay(null);
        console.error(err);
    }
    finally {
        prefsOverlayLoading = false;
    }
}
function updatePrefsOverlayVisibility() {
    if (!prefsOverlay)
        return;
    const visible = currentFlowKey === "prefs" && !!state.onboarded;
    prefsOverlay.classList.toggle("hidden", !visible);
    prefsOverlay.style.display = visible ? "flex" : "none";
    if (visible && (!prefsOverlayHasLoaded || !(prefsOverlayDetails === null || prefsOverlayDetails === void 0 ? void 0 : prefsOverlayDetails.childElementCount))) {
        refreshPrefsOverlay();
    }
}
function setupPrefsOverlay() {
    const shell = document.getElementById("duet-shell");
    const stage = shell === null || shell === void 0 ? void 0 : shell.querySelector(".duet-stage");
    if (!shell || !stage || document.getElementById("prefs-ghost"))
        return;
    const overlay = document.createElement("div");
    overlay.id = "prefs-ghost";
    overlay.className = "inventory-ghost prefs-overlay hidden";
    overlay.style.display = "none";
    overlay.style.pointerEvents = "none";
    overlay.style.zIndex = "1";
    overlay.style.flexDirection = "column";
    overlay.style.justifyContent = "center";
    overlay.style.alignItems = "center";
    overlay.style.gap = "14px";
    overlay.style.position = "absolute";
    overlay.style.inset = "10px";
    overlay.style.width = "calc(100% - 20px)";
    overlay.style.height = "calc(100% - 20px)";
    const panel = document.createElement("div");
    panel.style.display = "grid";
    panel.style.pointerEvents = "auto";
    panel.style.gap = "12px";
    panel.style.width = "100%";
    panel.style.maxWidth = "520px";
    panel.style.margin = "0 auto";
    const header = document.createElement("div");
    header.className = "inventory-ghost-header";
    const title = document.createElement("span");
    title.textContent = "Preferences";
    const refresh = document.createElement("button");
    refresh.type = "button";
    refresh.className = "ghost-refresh";
    refresh.textContent = "Refresh";
    refresh.addEventListener("click", () => refreshPrefsOverlay(true));
    header.appendChild(title);
    header.appendChild(refresh);
    const status = document.createElement("div");
    status.id = "prefs-ghost-status";
    status.className = "inventory-ghost-status";
    status.textContent = "Select Preferences to load.";
    const summary = document.createElement("div");
    summary.id = "prefs-ghost-summary";
    summary.className = "prefs-ghost-summary";
    summary.textContent = "No preferences yet.";
    const details = document.createElement("div");
    details.className = "prefs-ghost-details";
    details.style.display = "grid";
    details.style.gap = "10px";
    details.style.width = "100%";
    panel.appendChild(header);
    panel.appendChild(status);
    panel.appendChild(summary);
    panel.appendChild(details);
    overlay.appendChild(panel);
    stage.appendChild(overlay);
    prefsOverlay = overlay;
    prefsOverlayStatusEl = status;
    prefsOverlaySummaryEl = summary;
    prefsOverlayDetails = details;
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
    const isNormalChat = isNormalChatFlow();
    if (isNormalChat) {
        setUserBubbleEllipsis(true);
        incrementHistoryBadge();
    }
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
        const endpoint = currentFlowKey === "inventory" ? "/chat/inventory" : "/chat";
        const mode = currentFlowKey === "inventory" || currentFlowKey === "prefs" ? "fill" : currentModeLower();
        const res = await fetch(endpoint, {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({
                mode,
                message,
                include_user_library: true,
                thread_id: threadId,
            }),
        });
        const json = await res.json().catch(() => null);
        if (!res.ok || !json || typeof json.reply_text !== "string") {
            throw new Error((json === null || json === void 0 ? void 0 : json.message) || `ASK failed (status ${res.status})`);
        }
        lastResponseRequiresConfirmation = !!json.confirmation_required;
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
        var _a, _b, _c;
        state.token = jwtInput.value.trim();
        const rememberCheckbox = getRememberCheckbox();
        const rememberSelect = getRememberDurationSelect();
        if (state.token && (rememberCheckbox === null || rememberCheckbox === void 0 ? void 0 : rememberCheckbox.checked)) {
            const desired = Number((_a = rememberSelect === null || rememberSelect === void 0 ? void 0 : rememberSelect.value) !== null && _a !== void 0 ? _a : DEV_JWT_DEFAULT_TTL_MS);
            const ttl = Number.isFinite(desired) && desired > 0 ? desired : DEV_JWT_DEFAULT_TTL_MS;
            saveRememberedJwt(state.token, ttl);
        }
        else {
            clearRememberedJwt();
        }
        clearProposal();
        const result = await doGet("/auth/me");
        setText("auth-out", result);
        state.onboarded = !!((_b = result.json) === null || _b === void 0 ? void 0 : _b.onboarded);
        state.inventoryOnboarded = !!((_c = result.json) === null || _c === void 0 ? void 0 : _c.inventory_onboarded);
        renderOnboardMenuButtons();
        updatePrefsOverlayVisibility();
        updateInventoryOverlayVisibility();
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
    // setupDock();
    bindResizeForHistoryOffset();
    setupInventoryGhostOverlay();
    setupPrefsOverlay();
    setupDevPanel();
    applyRememberedJwtInput(jwtInput);
    wireDuetComposer();
    wireFloatingComposerTrigger(document.querySelector(".duet-stage"));
    setupHistoryDrawerUi();
    wireHistoryHotkeys();
    bindOnboardingLongPress();
    updateInventoryOverlayVisibility();
    updatePrefsOverlayVisibility();
    applyDrawerProgress(duetState.drawerOpen ? 1 : 0, { commit: true });
    renderDuetHistory();
    updateDuetBubbles();
    updateThreadLabel();
    applyDrawerProgress(0, { commit: true });
    elevateDuetBubbles();
    updateFlowStatusText();
}
document.addEventListener("DOMContentLoaded", wire);
function wireDuetComposer() {
    const input = document.getElementById("duet-input");
    const sendBtn = document.getElementById("duet-send");
    const micBtn = document.getElementById("duet-mic");
    if (!input || !sendBtn)
        return;
    hideFloatingComposer();
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
        hideFloatingComposer();
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
function showFloatingComposer() {
    const composer = document.getElementById("duet-composer");
    if (!composer || composerVisible)
        return;
    composer.classList.add("visible");
    composer.setAttribute("aria-hidden", "false");
    composerVisible = true;
    syncFlowMenuVisibility();
    setFlowMenuOpen(false);
    const input = document.getElementById("duet-input");
    setComposerPlaceholder();
    window.requestAnimationFrame(() => input === null || input === void 0 ? void 0 : input.focus());
}
function hideFloatingComposer() {
    const composer = document.getElementById("duet-composer");
    if (!composer)
        return;
    composer.classList.remove("visible");
    composer.setAttribute("aria-hidden", "true");
    composerVisible = false;
    syncFlowMenuVisibility();
    const input = document.getElementById("duet-input");
    input === null || input === void 0 ? void 0 : input.blur();
}
function wireFloatingComposerTrigger(stage) {
    if (!stage)
        return;
    stage.addEventListener("pointerdown", () => {
        stageTripleTapCount += 1;
        if (stageTripleTapResetTimer !== null) {
            window.clearTimeout(stageTripleTapResetTimer);
        }
        stageTripleTapResetTimer = window.setTimeout(() => {
            stageTripleTapCount = 0;
            stageTripleTapResetTimer = null;
        }, COMPOSER_TRIPLE_TAP_WINDOW_MS);
        if (stageTripleTapCount < 3) {
            return;
        }
        stageTripleTapCount = 0;
        if (stageTripleTapResetTimer !== null) {
            window.clearTimeout(stageTripleTapResetTimer);
            stageTripleTapResetTimer = null;
        }
        showFloatingComposer();
    });
}
function syncFlowMenuVisibility() {
    if (!flowMenuContainer)
        return;
    const trigger = document.getElementById("flow-menu-trigger");
    if (composerVisible) {
        // Show trigger as a red ✕ close button instead of hiding it
        flowMenuContainer.classList.remove("hidden");
        if (trigger) {
            trigger.classList.add("close-mode");
            trigger.textContent = "✕";
            trigger.setAttribute("aria-label", "Close composer");
        }
        // Hide the dropdown while in close mode
        if (flowMenuDropdown) {
            flowMenuDropdown.style.display = "none";
            flowMenuDropdown.classList.remove("open");
        }
    }
    else {
        if (trigger) {
            trigger.classList.remove("close-mode");
            trigger.textContent = "⚙";
            trigger.setAttribute("aria-label", `Options (current: ${flowDisplayLabel(currentFlowKey)})`);
        }
    }
}
function setupFlowChips() {
    const shell = document.getElementById("duet-shell");
    const composer = document.getElementById("duet-composer");
    const stage = shell === null || shell === void 0 ? void 0 : shell.querySelector(".duet-stage");
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
    trigger.className = "flow-menu-toggle";
    trigger.setAttribute("aria-haspopup", "true");
    trigger.setAttribute("aria-expanded", "false");
    trigger.addEventListener("click", () => {
        if (composerVisible) {
            hideFloatingComposer();
            return;
        }
        setFlowMenuOpen(!flowMenuOpen);
    });
    const dropdown = document.createElement("div");
    dropdown.className = "flow-menu-dropdown";
    dropdown.setAttribute("role", "menu");
    dropdown.style.display = "none";
    dropdown.style.position = "absolute";
    dropdown.style.zIndex = "10";
    dropdown.style.top = "calc(100% + 6px)";
    flowMenuContainer.appendChild(trigger);
    flowMenuContainer.appendChild(dropdown);
    flowMenuButton = trigger;
    flowMenuDropdown = dropdown;
    setFlowMenuOpen(false);
    renderFlowMenu();
    const menuHost = stage !== null && stage !== void 0 ? stage : shell;
    if (flowMenuContainer && menuHost && flowMenuContainer.parentElement !== menuHost) {
        menuHost.appendChild(flowMenuContainer);
    }
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
    updatePrefsOverlayVisibility();
    updateUserBubbleVisibility();
    if (currentFlowKey === "inventory") {
        refreshInventoryOverlay(true);
        if (!state.inventoryOnboarded) {
            addHistory("assistant", "Welcome to the inventory. This is where your cupboard, fridge, and freezer food will be displayed.\n\nFirst, you need to input the current stock you have.");
            userSystemHint = "Triple-tap to start chat and input inventory";
            setUserBubbleEllipsis(false);
        }
    }
    if (currentFlowKey === "prefs") {
        lastServerMode = "FILL";
        updateThreadLabel();
        refreshPrefsOverlay(true);
    }
    updateFlowStatusText();
}
function ensureOverlayRoot() {
    var _a;
    if (overlayRoot && overlayRoot.isConnected) {
        return overlayRoot;
    }
    const existing = document.getElementById(OVERLAY_ROOT_ID);
    if (existing) {
        overlayRoot = existing;
        return overlayRoot;
    }
    const rootHost = (_a = document.body) !== null && _a !== void 0 ? _a : document.documentElement;
    if (!rootHost) {
        throw new Error("Document root not found for overlay host");
    }
    const root = document.createElement("div");
    root.id = OVERLAY_ROOT_ID;
    root.style.position = "fixed";
    root.style.inset = "0";
    root.style.pointerEvents = "none";
    root.style.zIndex = OVERLAY_ROOT_Z_INDEX.toString();
    rootHost.appendChild(root);
    overlayRoot = root;
    return overlayRoot;
}
function ensureOnboardMenu() {
    const host = ensureOverlayRoot();
    if (!onboardMenu) {
        const menu = document.createElement("div");
        menu.id = "onboard-menu";
        menu.className = "flow-menu-dropdown";
        menu.style.position = "fixed";
        menu.style.display = "none";
        menu.style.zIndex = "999";
        host.appendChild(menu);
        onboardMenu = menu;
    }
    renderOnboardMenuButtons();
    return onboardMenu;
}
function renderOnboardMenuButtons() {
    if (!onboardMenu)
        return;
    onboardMenu.innerHTML = "";
    const prefsBtn = document.createElement("button");
    prefsBtn.type = "button";
    prefsBtn.className = "flow-menu-item";
    prefsBtn.textContent = "Preferences";
    prefsBtn.dataset.onboardItem = "start";
    prefsBtn.addEventListener("click", () => {
        hideOnboardMenu();
        startOnboarding();
    });
    onboardMenu.appendChild(prefsBtn);
    if (state.onboarded) {
        const invBtn = document.createElement("button");
        invBtn.type = "button";
        invBtn.className = "flow-menu-item";
        invBtn.textContent = "Inventory";
        invBtn.dataset.onboardItem = "inventory";
        invBtn.addEventListener("click", () => {
            hideOnboardMenu();
            selectFlow("inventory");
        });
        onboardMenu.appendChild(invBtn);
    }
    if (state.inventoryOnboarded) {
        const planBtn = document.createElement("button");
        planBtn.type = "button";
        planBtn.className = "flow-menu-item";
        planBtn.textContent = "Meal Plan";
        planBtn.dataset.onboardItem = "mealplan";
        planBtn.addEventListener("click", () => {
            hideOnboardMenu();
            selectFlow("mealplan");
        });
        onboardMenu.appendChild(planBtn);
    }
}
function clampNumber(value, min, max) {
    if (max < min) {
        return min;
    }
    return Math.min(Math.max(value, min), max);
}
function hideOnboardMenu() {
    if (onboardMenu) {
        onboardMenu.style.display = "none";
        onboardMenu.style.visibility = "hidden";
        onboardMenu.classList.remove("open");
    }
    onboardMenuActive = false;
    if (onboardActiveItem) {
        onboardActiveItem.classList.remove("active");
        onboardActiveItem.style.outline = "";
    }
    onboardActiveItem = null;
}
function showOnboardMenu(x, y) {
    const menu = ensureOnboardMenu();
    // Rebuild menu contents immediately before showing to ensure button visibility
    // reflects the latest `state.inventoryOnboarded` value (prevents race in E2E).
    renderOnboardMenuButtons();
    menu.style.display = "grid";
    menu.classList.add("open");
    menu.style.visibility = "hidden";
    menu.style.left = "0px";
    menu.style.top = "0px";
    const rect = menu.getBoundingClientRect();
    const width = rect.width || menu.offsetWidth || 0;
    const height = rect.height || menu.offsetHeight || 0;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const offset = ONBOARD_MENU_EDGE_MARGIN;
    const maxLeft = Math.max(offset, viewportWidth - width - offset);
    const maxTop = Math.max(offset, viewportHeight - height - offset);
    const desiredLeft = clampNumber(x - width - offset, offset, maxLeft);
    const desiredTop = clampNumber(y - height - offset, offset, maxTop);
    menu.style.left = `${desiredLeft}px`;
    menu.style.top = `${desiredTop}px`;
    menu.style.visibility = "visible";
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
    setUserBubbleLabel(true);
}
function setupDock() {
    // Dock layout is temporarily disabled; keep the legacy logic here in case we re-enable it later.
    /*
    const shell = document.getElementById("duet-shell");
    const composer = document.getElementById("duet-composer");
    if (!shell || !composer) return;
    let dock = document.getElementById("duet-dock") as HTMLDivElement | null;
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
    */
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
    dropdown.style.left = "";
    dropdown.style.right = "-4px";
    if (spaceBelow >= dropdownHeight + 8) {
        dropdown.style.top = `${trigger.offsetHeight + 6}px`;
    }
    else if (spaceAbove >= dropdownHeight + 8) {
        dropdown.style.bottom = `${trigger.offsetHeight + 6}px`;
    }
    else if (spaceBelow >= spaceAbove) {
        dropdown.style.top = `${Math.max(6, spaceBelow - 2)}px`;
    }
    else {
        dropdown.style.bottom = `${Math.max(6, spaceAbove - 2)}px`;
    }
    dropdown.style.display = prevDisplay;
    dropdown.style.visibility = prevVisibility;
}
