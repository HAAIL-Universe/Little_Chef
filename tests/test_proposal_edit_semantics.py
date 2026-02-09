"""Deterministic tests for proposal edit semantics (Confirm / Edit / Deny).

Validates Architecture A: edits are implicit via the existing endpoints when a
proposal is pending.  No new endpoint.  No LLM dependency.
"""
from app.repos.prefs_repo import DbPrefsRepository
from app.services.prefs_service import get_prefs_service


class FakeDbPrefsRepository(DbPrefsRepository):
    def __init__(self):
        self._store: dict[str, object] = {}

    def get_prefs(self, user_id: str):
        return self._store.get(user_id)

    def upsert_prefs(self, user_id, provider_subject, email, prefs, applied_event_id=None):
        self._store[user_id] = prefs
        return prefs


# ---------------------------------------------------------------------------
# 1) Prefs: create proposal → edit → confirm → deny
# ---------------------------------------------------------------------------

def test_prefs_deny_clears_proposal(authed_client):
    """Deny (confirm=False) clears the pending proposal; re-confirm returns 400."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-edit-deny"

    # Create proposal (include all wizard fields for immediate proposal)
    resp1 = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "Allergies: none. Dislikes: none. Likes: none. servings 2 meals per day 3", "thread_id": thread},
    )
    body1 = resp1.json()
    pid = body1["proposal_id"]
    assert body1["confirmation_required"] is True

    # Deny
    resp2 = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": pid, "confirm": False, "thread_id": thread},
    )
    assert resp2.status_code == 200
    assert resp2.json()["applied"] is False

    # Re-confirm should fail (proposal cleared)
    resp3 = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": pid, "confirm": True, "thread_id": thread},
    )
    assert resp3.status_code == 400


def test_reply_copy_updated(authed_client):
    """Reply copy no longer says 'continue editing' — says 'send changes to edit'."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-edit-copy"
    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "Allergies: none. Dislikes: none. Likes: none. servings 2 meals per day 3", "thread_id": thread},
    )
    body = resp.json()
    assert "continue editing" not in body["reply_text"]
    assert "send changes to edit" in body["reply_text"]


# ---------------------------------------------------------------------------
# 2) Inventory: edit / deny lifecycle (unit-level)
# ---------------------------------------------------------------------------

def test_inventory_deny_clears_server_proposal():
    """Deny on inventory proposal clears server-side proposal store."""
    from app.services.inventory_agent import InventoryAgent
    from app.services.proposal_store import ProposalStore
    from app.schemas import UserMe, ChatRequest
    import app.services.inventory_agent as agent_module

    store = ProposalStore()

    class DummyInv:
        def __init__(self):
            self.events = []
        def create_event(self, uid, sub, email, ev):
            class E:
                event_id = f"ev{len(self.events)+1}"
            self.events.append(ev)
            return E()

    inv = DummyInv()
    agent = InventoryAgent(inv, store, None)

    # Monkey-patch extractors for deterministic behavior
    agent_module_extract_new_draft_orig = agent_module.extract_new_draft
    agent_module_normalize_items_orig = agent_module.normalize_items

    def fake_extract(text, llm):
        return [{"name_raw": "eggs", "quantity_raw": "6", "unit_raw": "count", "expires_raw": None, "notes_raw": None}]
    def fake_normalize(raw, loc):
        return [{"item": {"item_key": "eggs", "quantity": 6, "unit": "count", "notes": None, "expires_on": None, "base_name": "eggs"}, "warnings": []}]

    agent_module.extract_new_draft = fake_extract
    agent_module.normalize_items = fake_normalize

    try:
        user = UserMe(user_id="u1", provider_subject="s", email=None)
        resp = agent.handle_fill(user, ChatRequest(mode="fill", message="6 eggs", thread_id="t1"))
        assert resp.confirmation_required is True
        pid = resp.proposal_id

        # Proposal exists in store
        assert store.peek("u1", pid) is not None

        # Deny
        applied, _, _ = agent.confirm(user, pid, confirm=False, thread_id="t1")
        assert applied is False

        # Proposal cleared
        assert store.peek("u1", pid) is None
        assert len(inv.events) == 0
    finally:
        agent_module.extract_new_draft = agent_module_extract_new_draft_orig
        agent_module.normalize_items = agent_module_normalize_items_orig
