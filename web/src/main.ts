import { formatProposalSummary, stripProposalPrefix } from "./proposalRenderer.js";

const state = {
  token: "",
  lastPlan: null as any,
  proposalId: null as string | null,
  proposedActions: [] as any[],
  chatReply: null as any,
  chatError: "",
  onboarded: null as boolean | null,
  inventoryOnboarded: null as boolean | null,
};

const DEV_JWT_STORAGE_KEY = "lc_dev_jwt";
const DEV_JWT_EXP_KEY = "lc_dev_jwt_exp_utc_ms";
const DEV_JWT_DURATION_KEY = "lc_dev_jwt_duration_ms";
const DEV_JWT_DEFAULT_TTL_MS = 24 * 60 * 60 * 1000;
const DEV_JWT_DURATION_OPTIONS: { value: number; label: string }[] = [
  { value: DEV_JWT_DEFAULT_TTL_MS, label: "24 hours" },
  { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" },
];

function safeLocalStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function getRememberCheckbox(): HTMLInputElement | null {
  return document.getElementById("dev-jwt-remember") as HTMLInputElement | null;
}

function getRememberDurationSelect(): HTMLSelectElement | null {
  return document.getElementById("dev-jwt-remember-duration") as HTMLSelectElement | null;
}

function saveRememberedJwt(token: string, ttlMs: number) {
  const storage = safeLocalStorage();
  if (!storage) return;
  storage.setItem(DEV_JWT_STORAGE_KEY, token);
  storage.setItem(DEV_JWT_EXP_KEY, (Date.now() + ttlMs).toString());
  storage.setItem(DEV_JWT_DURATION_KEY, ttlMs.toString());
}

function clearRememberedJwt() {
  const storage = safeLocalStorage();
  if (!storage) return;
  storage.removeItem(DEV_JWT_STORAGE_KEY);
  storage.removeItem(DEV_JWT_EXP_KEY);
  storage.removeItem(DEV_JWT_DURATION_KEY);
}

function loadRememberedJwt(): { token: string; durationMs: number } | null {
  const storage = safeLocalStorage();
  if (!storage) return null;
  const token = storage.getItem(DEV_JWT_STORAGE_KEY);
  if (!token) return null;
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

type HistoryItem = { role: "user" | "assistant"; text: string };

type FlowOption = { key: string; label: string; placeholder: string };
const flowOptions: FlowOption[] = [
  { key: "general", label: "General", placeholder: "Ask or fill..." },
  { key: "inventory", label: "Inventory", placeholder: "Ask about inventory, stock, or adjustments..." },
  { key: "mealplan", label: "Meal Plan", placeholder: "Plan meals or ask for ideas..." },
  { key: "prefs", label: "Preferences", placeholder: "Update dislikes, allergies, or servings..." },
];

type InventorySummaryItem = { item_name: string; quantity: number; unit: string; approx?: boolean };
type LowStockItem = { item_name: string; quantity: number; unit: string; threshold: number; reason?: string };

const duetState = {
  threadId: null as string | null,
  history: [] as HistoryItem[],
  drawerOpen: false,
  drawerProgress: 0,
};
let lastServerMode = "ASK";

function currentModeLower() {
  return (lastServerMode || "ASK").toLowerCase();
}

let historyOverlay: HTMLDivElement | null = null;
let historyToggle: HTMLButtonElement | null = null;
let historyBadgeCount = 0;
let historyBadgeEl: HTMLSpanElement | null = null;
let userBubbleEllipsisActive = false;
let currentFlowKey = flowOptions[0].key;
let composerBusy = false;
let flowMenuContainer: HTMLDivElement | null = null;
let flowMenuDropdown: HTMLDivElement | null = null;
let flowMenuButton: HTMLButtonElement | null = null;
let flowMenuOpen = false;
let flowMenuListenersBound = false;
let devPanelVisible = false;
let inventoryOverlay: HTMLDivElement | null = null;
let inventoryStatusEl: HTMLElement | null = null;
let inventoryLowList: HTMLUListElement | null = null;
let inventorySummaryList: HTMLUListElement | null = null;
let inventoryLoading = false;
let inventoryHasLoaded = false;
let prefsOverlay: HTMLDivElement | null = null;
let prefsOverlayStatusEl: HTMLElement | null = null;
let prefsOverlaySummaryEl: HTMLElement | null = null;
let prefsOverlayDetails: HTMLDivElement | null = null;
let prefsOverlayLoading = false;
let prefsOverlayHasLoaded = false;
let onboardMenu: HTMLDivElement | null = null;
const OVERLAY_ROOT_ID = "duet-overlay-root";
const OVERLAY_ROOT_Z_INDEX = 2147483640;
const ONBOARD_MENU_EDGE_MARGIN = 8;
const USER_BUBBLE_SENT_TEXT = "Sent";
const HISTORY_BADGE_DISPLAY_MAX = 99;
const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
let overlayRoot: HTMLDivElement | null = null;
let onboardPressTimer: number | null = null;
let onboardPressStart: { x: number; y: number } | null = null;
let onboardPointerId: number | null = null;
let onboardMenuActive = false;
let onboardActiveItem: HTMLElement | null = null;
let onboardIgnoreDocClickUntilMs = 0;
let onboardDragActive = false;
const COMPOSER_TRIPLE_TAP_WINDOW_MS = 450;
let composerVisible = false;
let stageTripleTapCount = 0;
let stageTripleTapResetTimer: number | null = null;

function headers() {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const raw = state.token?.trim();
  if (raw) {
    const tokenOnly = raw.replace(/^bearer\s+/i, "").replace(/\s+/g, "");
    if (tokenOnly) {
      h["Authorization"] = `Bearer ${tokenOnly}`;
    }
  }
  return h;
}

function setModeFromResponse(json: any) {
  if (json && typeof json.mode === "string") {
    lastServerMode = json.mode.toUpperCase();
    updateThreadLabel();
  }
}

function setText(id: string, value: any) {
  const el = document.getElementById(id);
  if (el) el.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function hide(id: string) {
  document.getElementById(id)?.classList.add("hidden");
}

function show(id: string) {
  document.getElementById(id)?.classList.remove("hidden");
}

function moveGroupIntoDevPanel(ids: string[], panel: HTMLElement, moved: Set<HTMLElement>) {
  const scopes = ["section", "fieldset", ".panel", ".card", ".debug", "div"];
  let target: HTMLElement | null = null;
  for (const id of ids) {
    const el = document.getElementById(id);
    if (!el) continue;
    for (const scope of scopes) {
      const candidate = el.closest(scope) as HTMLElement | null;
      if (!candidate) continue;
      const tag = candidate.tagName.toLowerCase();
      if (tag === "body" || tag === "main") continue;
      if (candidate.id === "duet-shell") continue;
      target = candidate;
      break;
    }
    if (target) break;
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
  if (!host || document.getElementById("dev-panel")) return;

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

  const moved = new Set<HTMLElement>();
  const groups: string[][] = [
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
  const card = document.querySelector("section.card.legacy-card") as HTMLElement | null;
  if (!card) return;
  if (getRememberCheckbox()) return;

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
  if (authOut?.parentElement) {
    authOut.parentElement.insertBefore(row, authOut);
  } else {
    card.appendChild(row);
  }
}

function applyRememberedJwtInput(jwtInput: HTMLInputElement | null) {
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
      durationSelect.value = has ? desired : durationSelect.options[0]?.value ?? desired;
    }
  } else {
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
  if (!container || !textEl) return;
  if (!state.proposalId || !state.proposedActions.length) {
    container.classList.add("hidden");
    textEl.textContent = "";
    return;
  }
  const summaries = state.proposedActions.map((action: any) => {
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

function detectProposalCommand(message: string): "confirm" | "deny" | null {
  const normalized = message.trim().toLowerCase();
  if (!normalized) return null;
  if (PROPOSAL_CONFIRM_COMMANDS.has(normalized)) return "confirm";
  if (PROPOSAL_DENY_COMMANDS.has(normalized)) return "deny";
  return null;
}

async function submitProposalDecision(confirm: boolean, thinkingIndex?: number) {
  if (!state.proposalId) return;
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
        ? response.json?.applied
          ? "Preferences confirmed."
          : "No pending preferences added."
        : "Confirmation failed."
      : success
      ? "Preferences update cancelled."
      : "Cancellation failed.";
    if (typeof thinkingIndex === "number") {
      updateHistory(thinkingIndex, assistantText);
    } else {
      addHistory("assistant", assistantText);
    }
    state.chatReply = response;
    setText("chat-reply", { status: response.status, json: response.json });
    setDuetStatus(success ? "Reply received." : "Confirmation failed.");
    if (success) {
      const confirmedPrefs =
        response.json?.applied &&
        state.proposedActions.some((action: any) => action.action_type === "upsert_prefs");
      if (confirmedPrefs) {
        state.onboarded = true;
        renderOnboardMenuButtons();
        updatePrefsOverlayVisibility();
      }
      clearProposal();
    }
  } catch (err) {
    console.error(err);
    setChatError("Network error. Try again.");
    setDuetStatus("Confirmation failed.");
  } finally {
    setComposerBusy(false);
  }
}

function setChatError(msg: string) {
  state.chatError = msg;
  const el = document.getElementById("chat-error");
  if (el) el.textContent = msg;
}

function setDuetStatus(msg: string, isError = false) {
  const el = document.getElementById("duet-status");
  if (!el) return;
  el.textContent = msg;
  el.classList.toggle("error", isError);
}

function setComposerPlaceholder() {
  const input = document.getElementById("duet-input") as HTMLInputElement | null;
  if (!input) return;
  const flow = flowOptions.find((f) => f.key === currentFlowKey) ?? flowOptions[0];
  input.placeholder = flow.placeholder;
}

function flowDisplayLabel(key: string) {
  const flow = flowOptions.find((f) => f.key === key);
  if (!flow) return "Unknown";
  return flow.key === "general" ? "Home" : flow.label;
}

function flowMenuCandidates(): FlowOption[] {
  if (currentFlowKey === "general") {
    return flowOptions.filter((f) => f.key !== "general");
  }
  return flowOptions.filter((f) => f.key !== currentFlowKey).map((f) => (f.key === "general" ? { ...f, label: "Home" } : f));
}

function setFlowMenuOpen(open: boolean) {
  flowMenuOpen = open;
  if (flowMenuDropdown) {
    flowMenuDropdown.style.display = open ? "grid" : "none";
    flowMenuDropdown.classList.toggle("open", open);
    if (open) {
      positionFlowMenuDropdown();
    }
  }
  flowMenuButton?.setAttribute("aria-expanded", open ? "true" : "false");
}

function renderFlowMenu() {
  const dropdown = flowMenuDropdown;
  const trigger = flowMenuButton;
  if (!dropdown || !trigger) return;
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
  const panel = document.getElementById("dev-panel") as HTMLDetailsElement | null;
  if (!panel) return;
  devPanelVisible = !devPanelVisible;
  panel.classList.toggle("hidden", !devPanelVisible);
  panel.open = devPanelVisible;
}

function updateThreadLabel() {
  const label = document.getElementById("duet-thread-label");
  if (!label) return;
  label.textContent = `Thread: ${duetState.threadId ?? "-"} | Mode: ${lastServerMode}`;
}

function syncHistoryUi() {
  const open = duetState.drawerOpen;
  document.body.classList.toggle("history-open", open);
  historyOverlay?.classList.toggle("open", open);
  historyOverlay?.setAttribute("aria-hidden", open ? "false" : "true");
  if (historyToggle) {
    historyToggle.setAttribute("aria-expanded", open ? "true" : "false");
    historyToggle.classList.toggle("active", open);
  }
}

function renderDuetHistory() {
  const list = document.getElementById("duet-history-list");
  const empty = document.getElementById("duet-history-empty");
  if (!list || !empty) return;
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

function setBubbleText(element: HTMLElement | null, text: string | null | undefined) {
  if (!element) return;
  element.innerHTML = "";
  if (!text) return;
  const parts = text.split("\n");
  parts.forEach((line, idx) => {
    element.append(document.createTextNode(line));
    if (idx < parts.length - 1) {
      element.append(document.createElement("br"));
    }
  });
}

function updateDuetBubbles() {
  const assistant = document.getElementById("duet-assistant-text");
  const user = document.getElementById("duet-user-text");
  const lastAssistant = [...duetState.history].reverse().find((h) => h.role === "assistant");
  const lastUser = [...duetState.history].reverse().find((h) => h.role === "user");
  const assistantFallback =
    "Welcome — I’m Little Chef. To start onboarding, please fill out your preferences (allergies, likes/dislikes, servings, days).";
  const userFallback = "Press and hold to start onboarding with preferences.";
  setBubbleText(assistant, lastAssistant?.text ?? assistantFallback);
  const showSentText = userBubbleEllipsisActive && isNormalChatFlow();
  const fallbackText = isNormalChatFlow() ? userFallback : lastUser?.text ?? userFallback;
  setBubbleText(user, showSentText ? USER_BUBBLE_SENT_TEXT : fallbackText);
}

function isNormalChatFlow() {
  return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
}

function setUserBubbleEllipsis(enabled: boolean) {
  if (userBubbleEllipsisActive === enabled) {
    return;
  }
  userBubbleEllipsisActive = enabled;
  if (!enabled) {
    updateDuetBubbles();
  }
}

function applyDrawerProgress(progress: number, opts?: { dragging?: boolean; commit?: boolean }) {
  const history = document.getElementById("duet-history");
  const stage = document.querySelector(".duet-stage") as HTMLElement | null;
  const userBubble = document.getElementById("duet-user-bubble");
  if (!history || !stage || !userBubble) return;
  ensureHistoryClosedOffset(history);
  const clamped = Math.max(0, Math.min(1, progress));
  duetState.drawerProgress = clamped;
  history.style.setProperty("--drawer-progress", clamped.toString());
  const shouldShow = (opts?.dragging ?? false) || clamped > 0;
  history.style.display = shouldShow ? "grid" : "none";
  history.style.pointerEvents = shouldShow ? "auto" : "none";
  history.classList.toggle("dragging", !!opts?.dragging);
  stage.classList.toggle("history-open", shouldShow);
  if (opts?.commit) {
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
  if (!userBubble) return;
  let dragging = false;
  let startY = 0;
  let pointerId: number | null = null;

  const endDrag = () => {
    if (!dragging) return;
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
    if (!dragging || (pointerId !== null && ev.pointerId !== pointerId)) return;
    const dy = startY - ev.clientY;
    const progress = dy <= 0 ? 0 : Math.min(dy / 120, 1);
    applyDrawerProgress(progress, { dragging: true });
  });

  const cancel = () => {
    if (!dragging) return;
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

function setDrawerOpen(open: boolean) {
  applyDrawerProgress(open ? 1 : 0, { commit: true });
}

function ensureHistoryClosedOffset(historyEl: HTMLElement) {
  const stage = document.querySelector(".duet-stage") as HTMLElement | null;
  const stageHeight = stage?.offsetHeight ?? 0;
  const historyHeight = historyEl.offsetHeight || 0;
  const offset = Math.max(historyHeight, stageHeight) + 200; // larger buffer to force fully off-screen
  historyEl.style.setProperty("--history-closed-offset", `${offset}px`);
}

function bindResizeForHistoryOffset() {
  const history = document.getElementById("duet-history") as HTMLElement | null;
  if (!history) return;
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

function addHistory(role: HistoryItem["role"], text: string) {
  duetState.history.push({ role, text });
  renderDuetHistory();
  updateDuetBubbles();
  return duetState.history.length - 1;
}

function updateHistory(index: number, text: string) {
  if (index < 0 || index >= duetState.history.length) return;
  duetState.history[index] = { ...duetState.history[index], text };
  renderDuetHistory();
  updateDuetBubbles();
}

function setupHistoryDrawerUi() {
  const shell = document.getElementById("duet-shell");
  const stage = document.querySelector(".duet-stage");
  if (!shell || !stage) return;

  const historyPanel = document.getElementById("duet-history");
  const historyHeader = historyPanel?.querySelector(".history-header");
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
    historyOverlay.addEventListener(
      "touchmove",
      (ev) => {
        ev.preventDefault();
      },
      { passive: false },
    );
    historyOverlay.addEventListener(
      "wheel",
      (ev) => {
        ev.preventDefault();
      },
      { passive: false },
    );
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
  if (!historyToggle) return null;
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
  if (!badge) return;
  if (historyBadgeCount > 0) {
    badge.textContent =
      historyBadgeCount > HISTORY_BADGE_DISPLAY_MAX
        ? `${HISTORY_BADGE_DISPLAY_MAX}+`
        : historyBadgeCount.toString();
    badge.classList.add("visible");
    badge.setAttribute("aria-hidden", "false");
  } else {
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

function formatQuantity(quantity: number, unit: string, approx?: boolean) {
  const safe = Number.isFinite(quantity) ? quantity : 0;
  const rounded = Math.abs(safe) >= 10 ? safe.toFixed(1) : safe.toString();
  const trimmed = rounded.replace(/\.0+$/, "").replace(/(\.\d*[1-9])0+$/, "$1");
  const prefix = approx ? "~" : "";
  return `${prefix}${trimmed} ${unit}`;
}

function setInventoryStatus(text: string) {
  if (inventoryStatusEl) {
    inventoryStatusEl.textContent = text;
  }
}

function markInventoryOnboarded(hasData: boolean) {
  const already = !!state.inventoryOnboarded;
  state.inventoryOnboarded = !!state.inventoryOnboarded || hasData;
  if (!already && state.inventoryOnboarded) {
    updateInventoryOverlayVisibility();
  }
}

function renderInventoryLists(low: LowStockItem[], summary: InventorySummaryItem[]) {
  const lowList = inventoryLowList;
  if (lowList) {
    lowList.innerHTML = "";
    if (!low || !low.length) {
      const li = document.createElement("li");
      li.className = "inventory-empty";
      li.textContent = "No low stock items.";
      lowList.appendChild(li);
    } else {
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
    } else {
      summary.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = `${item.item_name} - ${formatQuantity(item.quantity, item.unit, item.approx)}`;
        summaryList.appendChild(li);
      });
    }
  }
}

async function refreshInventoryOverlay(force = false) {
  if (!inventoryOverlay) return;
  if (inventoryLoading && !force) return;
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
    const summaryItems = Array.isArray(summaryResp.json?.items) ? (summaryResp.json.items as InventorySummaryItem[]) : [];
    const lowItems = Array.isArray(lowResp.json?.items) ? (lowResp.json.items as LowStockItem[]) : [];
    renderInventoryLists(lowItems, summaryItems);
    const hasAny = lowItems.length > 0 || summaryItems.length > 0;
    setInventoryStatus(hasAny ? "Read-only snapshot" : "No items yet.");
    markInventoryOnboarded(hasAny);
    inventoryHasLoaded = true;
  } catch (err) {
    setInventoryStatus("Network error. Try refresh.");
    renderInventoryLists([], []);
    console.error(err);
  } finally {
    inventoryLoading = false;
  }
}

function updateInventoryOverlayVisibility() {
  if (!inventoryOverlay) return;
  const wantsInventory = currentFlowKey === "inventory";
  const canShowInventory = !!state.inventoryOnboarded;
  const visible = wantsInventory && canShowInventory;
  inventoryOverlay.classList.toggle("hidden", !visible);
  inventoryOverlay.style.display = visible ? "flex" : "none";
  if (wantsInventory) {
    if (!canShowInventory) {
      refreshInventoryOverlay(true);
    } else if (visible && (!inventoryHasLoaded || !inventoryLowList?.childElementCount)) {
      refreshInventoryOverlay();
    }
  }
}

function setupInventoryGhostOverlay() {
  const shell = document.getElementById("duet-shell");
  const stage = shell?.querySelector(".duet-stage");
  if (!shell || !stage || document.getElementById("inventory-ghost")) return;

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

function setPrefsOverlayStatus(text: string) {
  if (prefsOverlayStatusEl) {
    prefsOverlayStatusEl.textContent = text;
  }
}

function renderPrefsOverlay(prefs: any | null) {
  const details = prefsOverlayDetails;
  const summaryEl = prefsOverlaySummaryEl;
  if (!details || !summaryEl) return;
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
  summaryEl.textContent = `${servings} servings · ${meals} meals/day`;

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
    } else {
      section.items.forEach((item: string) => {
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
  if (!prefsOverlay) return;
  if (prefsOverlayLoading && !force) return;
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
  } catch (err) {
    setPrefsOverlayStatus("Network error. Try refresh.");
    renderPrefsOverlay(null);
    console.error(err);
  } finally {
    prefsOverlayLoading = false;
  }
}

function updatePrefsOverlayVisibility() {
  if (!prefsOverlay) return;
  const visible = currentFlowKey === "prefs" && !!state.onboarded;
  prefsOverlay.classList.toggle("hidden", !visible);
  prefsOverlay.style.display = visible ? "flex" : "none";
  if (visible && (!prefsOverlayHasLoaded || !prefsOverlayDetails?.childElementCount)) {
    refreshPrefsOverlay();
  }
}

function setupPrefsOverlay() {
  const shell = document.getElementById("duet-shell");
  const stage = shell?.querySelector(".duet-stage");
  if (!shell || !stage || document.getElementById("prefs-ghost")) return;

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

async function doGet(path: string) {
  const res = await fetch(path, { headers: headers() });
  return { status: res.status, json: await res.json().catch(() => null) };
}

async function doPost(path: string, body: any) {
  const res = await fetch(path, { method: "POST", headers: headers(), body: JSON.stringify(body) });
  return { status: res.status, json: await res.json().catch(() => null) };
}

function shellOnlyDuetReply(userText: string) {
  const thread = duetState.threadId ?? crypto.randomUUID();
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

async function sendAsk(message: string, opts?: { flowLabel?: string; updateChatPanel?: boolean }) {
  const ensureThread = () => {
    if (!duetState.threadId) {
      duetState.threadId = crypto.randomUUID();
      updateThreadLabel();
    }
    return duetState.threadId;
  };

  const normalizedMessage = message.trim();
  const flowLabel = opts?.flowLabel;
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
    } finally {
      setComposerBusy(false);
    }
    return { userIndex, thinkingIndex };
  }

  setDuetStatus("Contacting backend...");
  setComposerBusy(true);
  try {
    const threadId = ensureThread();
    const endpoint = currentFlowKey === "inventory" ? "/chat/inventory" : "/chat";
    const mode = currentFlowKey === "inventory" ? "fill" : currentModeLower();
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
      throw new Error(json?.message || `ASK failed (status ${res.status})`);
    }
    setModeFromResponse(json);
    const proposalSummary = formatProposalSummary(json);
    const replyText = json.reply_text;
    const replyBase = proposalSummary ? stripProposalPrefix(replyText) ?? replyText : replyText;
    const assistantText = proposalSummary ? `${proposalSummary}\n\n${replyBase}` : replyBase;
    updateHistory(thinkingIndex, assistantText);
    state.proposalId = json.proposal_id ?? null;
    state.proposedActions = Array.isArray(json.proposed_actions) ? json.proposed_actions : [];
    renderProposal();
    if (opts?.updateChatPanel) {
      setText("chat-reply", { status: res.status, json });
    }
    setDuetStatus("Reply received.");
  } catch (err) {
    updateHistory(thinkingIndex, "Network error. Try again.");
    if (opts?.updateChatPanel) {
      setChatError("Network error. Try again.");
    }
    console.error(err);
  } finally {
    setComposerBusy(false);
  }
  return { userIndex, thinkingIndex };
}

function setComposerBusy(busy: boolean) {
  composerBusy = busy;
  const input = document.getElementById("duet-input") as HTMLInputElement | null;
  const sendBtn = document.getElementById("duet-send") as HTMLButtonElement | null;
  if (sendBtn) sendBtn.disabled = busy || !!(input && input.value.trim().length === 0);
  if (input) input.readOnly = busy;
}

async function silentGreetOnce() {
  if (!state.token?.trim()) return;
  const key = "lc_silent_greet_done";
  if (sessionStorage.getItem(key) === "1") return;
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
  } catch (_err) {
    // Silent failure by design
  }
}

function wire() {
  enforceViewportLock();
  const jwtInput = document.getElementById("jwt") as HTMLInputElement;
  document.getElementById("btn-auth")?.addEventListener("click", async () => {
    state.token = jwtInput.value.trim();
    const rememberCheckbox = getRememberCheckbox();
    const rememberSelect = getRememberDurationSelect();
    if (state.token && rememberCheckbox?.checked) {
      const desired = Number(rememberSelect?.value ?? DEV_JWT_DEFAULT_TTL_MS);
      const ttl = Number.isFinite(desired) && desired > 0 ? desired : DEV_JWT_DEFAULT_TTL_MS;
      saveRememberedJwt(state.token, ttl);
    } else {
      clearRememberedJwt();
    }
    clearProposal();
    const result = await doGet("/auth/me");
    setText("auth-out", result);
    state.onboarded = !!result.json?.onboarded;
    state.inventoryOnboarded = !!result.json?.inventory_onboarded;
    renderOnboardMenuButtons();
    updatePrefsOverlayVisibility();
    updateInventoryOverlayVisibility();
    await silentGreetOnce();
    inventoryHasLoaded = false;
    if (currentFlowKey === "inventory") {
      refreshInventoryOverlay(true);
    }
  });

  document.getElementById("btn-chat")?.addEventListener("click", async () => {
    const msg = (document.getElementById("chat-input") as HTMLTextAreaElement).value;
    clearProposal();
    setChatError("");
    if (msg?.trim()) {
      const flow = flowOptions.find((f) => f.key === currentFlowKey) ?? flowOptions[0];
      await sendAsk(msg.trim(), { flowLabel: flow.label, updateChatPanel: true });
    } else {
      setChatError("Enter a message to send.");
    }
  });

  document.getElementById("btn-prefs-get")?.addEventListener("click", async () => {
    const resp = await doGet("/prefs");
    setText("prefs-out", resp);
  });

  document.getElementById("btn-prefs-put")?.addEventListener("click", async () => {
    const servings = Number((document.getElementById("prefs-servings") as HTMLInputElement).value);
    const meals = Number((document.getElementById("prefs-meals") as HTMLInputElement).value);
    const resp = await fetch("/prefs", {
      method: "PUT",
      headers: headers(),
      body: JSON.stringify({ prefs: { servings, meals_per_day: meals } }),
    });
    const json = await resp.json().catch(() => null);
    setText("prefs-out", { status: resp.status, json });
  });

  document.getElementById("btn-plan-gen")?.addEventListener("click", async () => {
    const resp = await doPost("/mealplan/generate", { days: 2, meals_per_day: 3 });
    state.lastPlan = resp.json;
    setText("plan-out", resp);
  });

  document.getElementById("btn-shopping")?.addEventListener("click", async () => {
    if (!state.lastPlan) {
      setText("shopping-out", "No plan yet. Generate a plan first.");
      return;
    }
    const resp = await doPost("/shopping/diff", { plan: state.lastPlan });
    setText("shopping-out", resp);
  });

  document.getElementById("btn-confirm")?.addEventListener("click", async () => {
    if (!state.proposalId) return;
    setChatError("");
    setChatError("Shell-only: confirmations land in Phase 7.4.");
    setDuetStatus("Shell-only: confirmations deferred to Phase 7.4.");
    setText("chat-reply", { status: 0, json: { message: "Shell-only confirmation stub (Phase 7.4 wires backend)" } });
    clearProposal();
  });

  document.getElementById("btn-cancel")?.addEventListener("click", async () => {
    if (!state.proposalId) return;
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
  wireFloatingComposerTrigger(document.querySelector(".duet-stage") as HTMLElement | null);
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
}

document.addEventListener("DOMContentLoaded", wire);

function wireDuetComposer() {
  const input = document.getElementById("duet-input") as HTMLInputElement | null;
  const sendBtn = document.getElementById("duet-send") as HTMLButtonElement | null;
  const micBtn = document.getElementById("duet-mic");
  if (!input || !sendBtn) return;

  hideFloatingComposer();

  const syncButtons = () => {
    sendBtn.disabled = composerBusy || input.value.trim().length === 0;
  };

  const send = () => {
    const text = input.value.trim();
    if (!text || composerBusy) return;
    setChatError("");
    const flow = flowOptions.find((f) => f.key === currentFlowKey) ?? flowOptions[0];
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

  micBtn?.addEventListener("click", () => {
    setDuetStatus("Voice uses client-side transcription; mic will feed text here.", false);
    input.focus();
  });

  setComposerPlaceholder();
}

function showFloatingComposer() {
  const composer = document.getElementById("duet-composer") as HTMLElement | null;
  if (!composer || composerVisible) return;
  composer.classList.add("visible");
  composer.setAttribute("aria-hidden", "false");
  composerVisible = true;
  syncFlowMenuVisibility();
  setFlowMenuOpen(false);
  const input = document.getElementById("duet-input") as HTMLInputElement | null;
  setComposerPlaceholder();
  window.requestAnimationFrame(() => input?.focus());
}

function hideFloatingComposer() {
  const composer = document.getElementById("duet-composer") as HTMLElement | null;
  if (!composer) return;
  composer.classList.remove("visible");
  composer.setAttribute("aria-hidden", "true");
  composerVisible = false;
  syncFlowMenuVisibility();
  const input = document.getElementById("duet-input") as HTMLInputElement | null;
  input?.blur();
}

function wireFloatingComposerTrigger(stage: HTMLElement | null) {
  if (!stage) return;
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
  if (!flowMenuContainer) return;
  flowMenuContainer.classList.toggle("hidden", composerVisible);
}

function setupFlowChips() {
  const shell = document.getElementById("duet-shell");
  const composer = document.getElementById("duet-composer");
  const stage = shell?.querySelector(".duet-stage") as HTMLElement | null;
  if (!shell || !composer) return;

  if (!flowMenuContainer) {
    flowMenuContainer = document.createElement("div");
    flowMenuContainer.id = "flow-chips";
    flowMenuContainer.className = "flow-menu";
  } else {
    flowMenuContainer.innerHTML = "";
    flowMenuContainer.className = "flow-menu";
  }

  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.id = "flow-menu-trigger";
  trigger.className = "flow-menu-toggle";
  trigger.setAttribute("aria-haspopup", "true");
  trigger.setAttribute("aria-expanded", "false");
  trigger.addEventListener("click", () => setFlowMenuOpen(!flowMenuOpen));

  const dropdown = document.createElement("div");
  dropdown.className = "flow-menu-dropdown";
  dropdown.setAttribute("role", "menu");
  dropdown.style.display = "none";
  dropdown.style.position = "absolute";
  dropdown.style.top = "calc(100% + 6px)";

  flowMenuContainer.appendChild(trigger);
  flowMenuContainer.appendChild(dropdown);

  flowMenuButton = trigger;
  flowMenuDropdown = dropdown;
  setFlowMenuOpen(false);
  renderFlowMenu();

  const menuHost = stage ?? shell;
  if (flowMenuContainer && menuHost && flowMenuContainer.parentElement !== menuHost) {
    menuHost.appendChild(flowMenuContainer);
  }

  if (!flowMenuListenersBound) {
    document.addEventListener("click", (ev) => {
      if (!flowMenuOpen || !flowMenuContainer) return;
      if (ev.target instanceof Node && flowMenuContainer.contains(ev.target)) return;
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
  const main = document.querySelector("main.container") as HTMLElement | null;
  const shell = document.getElementById("duet-shell") as HTMLElement | null;
  const stage = shell?.querySelector(".duet-stage") as HTMLElement | null;
  const composer = document.getElementById("duet-composer") as HTMLElement | null;
  const trigger = document.getElementById("flow-menu-trigger") as HTMLElement | null;
  const dock = document.getElementById("duet-dock") as HTMLElement | null;
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

function selectFlow(key: string) {
  if (!flowOptions.find((f) => f.key === key)) return;
  currentFlowKey = key;
  renderFlowMenu();
  setFlowMenuOpen(false);
  setComposerPlaceholder();
  updateInventoryOverlayVisibility();
  updatePrefsOverlayVisibility();
  if (currentFlowKey === "inventory") {
    refreshInventoryOverlay(true);
  }
  if (currentFlowKey === "prefs") {
    refreshPrefsOverlay(true);
  }
}

function ensureOverlayRoot() {
  if (overlayRoot && overlayRoot.isConnected) {
    return overlayRoot;
  }
  const existing = document.getElementById(OVERLAY_ROOT_ID) as HTMLDivElement | null;
  if (existing) {
    overlayRoot = existing;
    return overlayRoot;
  }
  const rootHost = document.body ?? document.documentElement;
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
  if (!onboardMenu) return;
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
}

function clampNumber(value: number, min: number, max: number): number {
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

function showOnboardMenu(x: number, y: number) {
  const menu = ensureOnboardMenu();
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
  if (assistant) assistant.textContent = assistantText;
  if (user) user.textContent = userText;
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
  if (!userBubble) return;

  const clearTimer = () => {
    if (onboardPressTimer !== null) {
      window.clearTimeout(onboardPressTimer);
      onboardPressTimer = null;
    }
  };

  const cancel = (opts?: { hideMenu?: boolean }) => {
    clearTimer();
    onboardPressStart = null;
    onboardPointerId = null;
    if (opts?.hideMenu ?? true) {
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
      } catch (_err) {
        // ignore if capture not supported
      }
    }, 500);
  });

  userBubble.addEventListener("pointermove", (ev) => {
    if (onboardMenuActive) {
      const el = document.elementFromPoint(ev.clientX, ev.clientY) as HTMLElement | null;
      const item = el?.closest("[data-onboard-item]") as HTMLElement | null;
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
    if (!onboardPressStart || onboardPressTimer === null) return;
    const dx = Math.abs(ev.clientX - onboardPressStart.x);
    const dy = Math.abs(ev.clientY - onboardPressStart.y);
    if (dx > 6 || dy > 6) {
      cancel();
    }
  });

  userBubble.addEventListener("pointerup", (ev) => {
    if (onboardMenuActive) {
      const startHovered = onboardActiveItem?.dataset.onboardItem === "start";
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
    } else {
      cancel();
    }
  });
  document.addEventListener("click", (ev) => {
    if (!onboardMenu || onboardMenu.style.display === "none") return;
    if (Date.now() < onboardIgnoreDocClickUntilMs) return;
    if (onboardDragActive) return;
    if (ev.target instanceof Node && onboardMenu.contains(ev.target)) return;
    hideOnboardMenu();
  });
}

function positionFlowMenuDropdown() {
  const dropdown = flowMenuDropdown;
  const trigger = flowMenuButton;
  if (!dropdown || !trigger) return;

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
  } else if (spaceAbove >= dropdownHeight + 8) {
    dropdown.style.bottom = `${trigger.offsetHeight + 6}px`;
  } else if (spaceBelow >= spaceAbove) {
    dropdown.style.top = `${Math.max(6, spaceBelow - 2)}px`;
  } else {
    dropdown.style.bottom = `${Math.max(6, spaceAbove - 2)}px`;
  }

  dropdown.style.display = prevDisplay;
  dropdown.style.visibility = prevVisibility;
}
