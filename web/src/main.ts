const state = {
  token: "",
  lastPlan: null as any,
  proposalId: null as string | null,
  proposedActions: [] as any[],
  chatReply: null as any,
  chatError: "",
};

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

let historyOverlay: HTMLDivElement | null = null;
let historyToggle: HTMLButtonElement | null = null;
let currentFlowKey = flowOptions[0].key;
let composerBusy = false;
let flowMenuContainer: HTMLDivElement | null = null;
let flowMenuDropdown: HTMLDivElement | null = null;
let flowMenuButton: HTMLButtonElement | null = null;
let flowMenuOpen = false;
let flowMenuListenersBound = false;
let inventoryOverlay: HTMLDivElement | null = null;
let inventoryStatusEl: HTMLElement | null = null;
let inventoryLowList: HTMLUListElement | null = null;
let inventorySummaryList: HTMLUListElement | null = null;
let inventoryLoading = false;
let inventoryHasLoaded = false;

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
  flowMenuDropdown?.classList.toggle("open", open);
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

function updateThreadLabel() {
  const label = document.getElementById("duet-thread-label");
  if (!label) return;
  label.textContent = `Thread: ${duetState.threadId ?? "-"}`;
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

function updateDuetBubbles() {
  const assistant = document.getElementById("duet-assistant-text");
  const user = document.getElementById("duet-user-text");
  const lastAssistant = [...duetState.history].reverse().find((h) => h.role === "assistant");
  const lastUser = [...duetState.history].reverse().find((h) => h.role === "user");
  if (assistant) assistant.textContent = lastAssistant?.text ?? "Hi - how can I help?";
  if (user) user.textContent = lastUser?.text ?? "Tap mic or type to start";
}

function applyDrawerProgress(progress: number, opts?: { dragging?: boolean; commit?: boolean }) {
  const history = document.getElementById("duet-history");
  const userBubble = document.getElementById("duet-user-bubble");
  if (!history || !userBubble) return;
  const clamped = Math.max(0, Math.min(1, progress));
  duetState.drawerProgress = clamped;
  history.style.setProperty("--drawer-progress", clamped.toString());
  history.classList.toggle("dragging", !!opts?.dragging);
  if (opts?.commit) {
    duetState.drawerOpen = clamped > 0.35;
    history.classList.toggle("open", duetState.drawerOpen);
    syncHistoryUi();
  }
  const offset = clamped * 70;
  userBubble.style.transform = `translateY(-${offset}px)`;
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

function setDrawerOpen(open: boolean) {
  applyDrawerProgress(open ? 1 : 0, { commit: true });
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
  const visible = currentFlowKey === "inventory";
  inventoryOverlay.classList.toggle("hidden", !visible);
  if (visible && (!inventoryHasLoaded || !inventoryLowList?.childElementCount)) {
    refreshInventoryOverlay();
  }
}

function setupInventoryGhostOverlay() {
  const shell = document.getElementById("duet-shell");
  const stage = shell?.querySelector(".duet-stage");
  if (!shell || !stage || document.getElementById("inventory-ghost")) return;

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

async function doGet(path: string) {
  const res = await fetch(path, { headers: headers() });
  return { status: res.status, json: await res.json().catch(() => null) };
}

async function doPost(path: string, body: any) {
  const res = await fetch(path, { method: "POST", headers: headers(), body: JSON.stringify(body) });
  return { status: res.status, json: await res.json().catch(() => null) };
}

function shellOnlyDuetReply(userText: string) {
  const thread = duetState.threadId ?? "shell-local";
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
  const flowLabel = opts?.flowLabel;
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
      throw new Error(json?.message || `ASK failed (status ${res.status})`);
    }
    updateHistory(thinkingIndex, json.reply_text);
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

function wire() {
  const jwtInput = document.getElementById("jwt") as HTMLInputElement;
  document.getElementById("btn-auth")?.addEventListener("click", async () => {
    state.token = jwtInput.value.trim();
    clearProposal();
    const result = await doGet("/auth/me");
    setText("auth-out", result);
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
  const input = document.getElementById("duet-input") as HTMLInputElement | null;
  const sendBtn = document.getElementById("duet-send") as HTMLButtonElement | null;
  const micBtn = document.getElementById("duet-mic");
  if (!input || !sendBtn) return;

  const syncButtons = () => {
    sendBtn.disabled = composerBusy || input.value.trim().length === 0;
  };

  const send = () => {
    const text = input.value.trim();
    if (!text || composerBusy) return;
    clearProposal();
    setChatError("");
    const flow = flowOptions.find((f) => f.key === currentFlowKey) ?? flowOptions[0];
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

  micBtn?.addEventListener("click", () => {
    setDuetStatus("Voice uses client-side transcription; mic will feed text here.", false);
    input.focus();
  });

  setComposerPlaceholder();
}

function setupFlowChips() {
  const shell = document.getElementById("duet-shell");
  const composer = document.getElementById("duet-composer");
  if (!shell || !composer) return;

  if (!flowMenuContainer) {
    flowMenuContainer = document.createElement("div");
    flowMenuContainer.id = "flow-chips";
    flowMenuContainer.className = "flow-menu";
    shell.insertBefore(flowMenuContainer, composer);
  } else {
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

  flowMenuContainer.appendChild(trigger);
  flowMenuContainer.appendChild(dropdown);

  flowMenuButton = trigger;
  flowMenuDropdown = dropdown;
  setFlowMenuOpen(false);
  renderFlowMenu();

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

function selectFlow(key: string) {
  if (!flowOptions.find((f) => f.key === key)) return;
  currentFlowKey = key;
  renderFlowMenu();
  setFlowMenuOpen(false);
  setComposerPlaceholder();
  updateInventoryOverlayVisibility();
  if (currentFlowKey === "inventory") {
    refreshInventoryOverlay(true);
  }
}


