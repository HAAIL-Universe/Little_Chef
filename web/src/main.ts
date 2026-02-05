const state = {
  token: "",
  lastPlan: null as any,
  proposalId: null as string | null,
  proposedActions: [] as any[],
  chatReply: null as any,
  chatError: "",
};

type HistoryItem = { role: "user" | "assistant"; text: string };

const duetState = {
  threadId: null as string | null,
  history: [] as HistoryItem[],
  drawerOpen: false,
  drawerProgress: 0,
};

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

function updateThreadLabel() {
  const label = document.getElementById("duet-thread-label");
  if (!label) return;
  label.textContent = `Thread: ${duetState.threadId ?? "—"}`;
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
  duetState.history.forEach((item) => {
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
  if (assistant) assistant.textContent = lastAssistant?.text ?? "Hi — how can I help?";
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

function addHistory(role: HistoryItem["role"], text: string) {
  duetState.history.push({ role, text });
  renderDuetHistory();
  updateDuetBubbles();
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

function wire() {
  const jwtInput = document.getElementById("jwt") as HTMLInputElement;
  document.getElementById("btn-auth")?.addEventListener("click", async () => {
    state.token = jwtInput.value.trim();
    clearProposal();
    const result = await doGet("/auth/me");
    setText("auth-out", result);
  });

  document.getElementById("btn-chat")?.addEventListener("click", async () => {
    const msg = (document.getElementById("chat-input") as HTMLTextAreaElement).value;
    clearProposal();
    setChatError("");
    if (msg?.trim()) {
      addHistory("user", msg.trim());
      shellOnlyDuetReply(msg.trim());
    } else {
      setChatError("Shell-only: enter a message to preview duet shell response.");
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

  wireDuetComposer();
  wireDuetDrag();
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
    sendBtn.disabled = input.value.trim().length === 0;
  };

  const send = () => {
    const text = input.value.trim();
    if (!text) return;
    clearProposal();
    setChatError("");
    addHistory("user", text);
    setDuetStatus("Shell-only: preparing local reply…");
    syncButtons();
    shellOnlyDuetReply(text);
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
}
