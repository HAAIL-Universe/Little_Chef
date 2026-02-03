const state = {
    token: "",
    lastPlan: null,
};
function headers() {
    const h = { "Content-Type": "application/json" };
    if (state.token)
        h["Authorization"] = `Bearer ${state.token}`;
    return h;
}
function setText(id, value) {
    const el = document.getElementById(id);
    if (el)
        el.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}
async function doGet(path) {
    const res = await fetch(path, { headers: headers() });
    return { status: res.status, json: await res.json().catch(() => null) };
}
async function doPost(path, body) {
    const res = await fetch(path, { method: "POST", headers: headers(), body: JSON.stringify(body) });
    return { status: res.status, json: await res.json().catch(() => null) };
}
function wire() {
    const jwtInput = document.getElementById("jwt");
    document.getElementById("btn-auth")?.addEventListener("click", async () => {
        state.token = jwtInput.value.trim();
        const result = await doGet("/auth/me");
        setText("auth-out", result);
    });
    document.getElementById("btn-chat")?.addEventListener("click", async () => {
        const msg = document.getElementById("chat-input").value;
        const resp = await doPost("/chat", { mode: "ask", message: msg, include_user_library: true });
        setText("chat-reply", resp);
    });
    document.getElementById("btn-prefs-get")?.addEventListener("click", async () => {
        const resp = await doGet("/prefs");
        setText("prefs-out", resp);
    });
    document.getElementById("btn-prefs-put")?.addEventListener("click", async () => {
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
}
document.addEventListener("DOMContentLoaded", wire);
