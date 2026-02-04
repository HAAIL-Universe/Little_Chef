const state = {
  token: "",
  lastPlan: null as any,
  proposalId: null as string | null,
  proposedActions: [] as any[],
  chatReply: null as any,
  chatError: "",
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

async function doGet(path: string) {
  const res = await fetch(path, { headers: headers() });
  return { status: res.status, json: await res.json().catch(() => null) };
}

async function doPost(path: string, body: any) {
  const res = await fetch(path, { method: "POST", headers: headers(), body: JSON.stringify(body) });
  return { status: res.status, json: await res.json().catch(() => null) };
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
    try {
      const resp = await doPost("/chat", { mode: "ask", message: msg, include_user_library: true });
      state.chatReply = resp;
      setText("chat-reply", resp);
      if (resp.json?.confirmation_required && resp.json?.proposal_id) {
        state.proposalId = resp.json.proposal_id;
        state.proposedActions = resp.json.proposed_actions || [];
        renderProposal();
      }
      if (resp.status >= 400) {
        setChatError(`Chat failed (${resp.status}): ${resp.json?.message || "error"}`);
      }
    } catch (e: any) {
      setChatError(`Chat error: ${e?.message || e}`);
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
    const resp = await doPost("/chat/confirm", { proposal_id: state.proposalId, confirm: true });
    setText("chat-reply", resp);
    if (resp.status >= 400) {
      setChatError(`Confirm failed (${resp.status}): ${resp.json?.message || ""}`);
    }
    clearProposal();
  });

  document.getElementById("btn-cancel")?.addEventListener("click", async () => {
    if (!state.proposalId) return;
    setChatError("");
    const resp = await doPost("/chat/confirm", { proposal_id: state.proposalId, confirm: false });
    setText("chat-reply", resp);
    if (resp.status >= 400) {
      setChatError(`Cancel failed (${resp.status}): ${resp.json?.message || ""}`);
    }
    clearProposal();
  });
}

document.addEventListener("DOMContentLoaded", wire);
