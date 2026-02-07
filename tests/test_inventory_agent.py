from app.services.inventory_agent import InventoryAgent
from app.services.proposal_store import ProposalStore


def _inventory_events(client):
    resp = client.get("/inventory/events")
    assert resp.status_code == 200
    return resp.json()["events"]


class _DummyInventoryService:
    def __init__(self):
        self.events = []

    def create_event(self, user_id, provider_subject, email, event):
        class E:
            def __init__(self, eid):
                self.event_id = eid

        eid = f"ev{len(self.events) + 1}"
        self.events.append(event)
        return E(eid)


def _make_agent():
    inv = _DummyInventoryService()
    agent = InventoryAgent(inv, ProposalStore())
    return agent, inv


def test_inventory_agent_allowlist_and_isolation(authed_client):
    thread = "inv-allowlist"
    resp = authed_client.post(
        "/chat/inventory",
        json={"mode": "fill", "message": "added 3 tomatoes", "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    actions = body["proposed_actions"]
    assert actions
    assert all(action["action_type"] == "create_inventory_event" for action in actions)
    assert not any(action["action_type"] == "upsert_prefs" for action in actions)
    assert all(action["event"]["event_type"] == "add" for action in actions)


def test_inventory_fallback_parses_multiple_items(authed_client):
    thread = "inv-fallback-list"
    resp = authed_client.post(
        "/chat/inventory",
        json={
            "mode": "fill",
            "message": "cheddar 300 grams, milk 2 litres, eggs 6",
            "thread_id": thread,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    actions = body["proposed_actions"]
    assert len(actions) >= 3
    assert all(action["action_type"] == "create_inventory_event" for action in actions)
    assert all(action["event"]["event_type"] == "add" for action in actions)
    assert any(
        action["event"]["quantity"] == 300 and action["event"]["unit"] == "g"
        for action in actions
    )
    assert all(len(action["event"]["item_name"]) < 80 for action in actions)


def test_inventory_agent_mode_rejects_non_fill(authed_client):
    resp = authed_client.post(
        "/chat/inventory",
        json={"mode": "ask", "message": "what do I have", "thread_id": "inv-mode"},
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "inventory supports fill only in Phase 8 (use mode='fill')."


def test_inventory_agent_parse_coerces_event_type():
    agent, _ = _make_agent()
    action, warnings = agent._parse_inventory_action("used 2 apples")
    assert action is not None
    assert action.event.event_type == "add"
    assert "Note: treated as add in Phase 8." in warnings


def test_inventory_agent_parses_number_words():
    agent, _ = _make_agent()
    action, _ = agent._parse_inventory_action("added three onions")
    assert action is not None
    assert action.event.quantity == 3


def test_inventory_agent_confirm_before_write(authed_client):
    thread = "inv-confirm"
    before = len(_inventory_events(authed_client))
    resp = authed_client.post(
        "/chat/inventory",
        json={"mode": "fill", "message": "bought 1 loaf", "thread_id": thread},
    )
    proposal_id = resp.json()["proposal_id"]
    assert len(_inventory_events(authed_client)) == before

    confirm = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert confirm.status_code == 200
    assert confirm.json()["applied"] is True
    assert len(_inventory_events(authed_client)) == before + len(resp.json()["proposed_actions"])


def test_inventory_agent_deny_is_non_destructive(authed_client):
    thread = "inv-deny"
    before = len(_inventory_events(authed_client))
    resp = authed_client.post(
        "/chat/inventory",
        json={"mode": "fill", "message": "added 2 carrots", "thread_id": thread},
    )
    proposal_id = resp.json()["proposal_id"]

    deny = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": False, "thread_id": thread},
    )
    assert deny.status_code == 200
    assert deny.json()["applied"] is False
    assert len(_inventory_events(authed_client)) == before


def test_inventory_agent_thread_scope(authed_client):
    thread_a = "inv-thread-a"
    thread_b = "inv-thread-b"
    resp = authed_client.post(
        "/chat/inventory",
        json={"mode": "fill", "message": "bought 4 apples", "thread_id": thread_a},
    )
    proposal_id = resp.json()["proposal_id"]
    wrong_thread = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread_b},
    )
    assert wrong_thread.status_code == 400
    assert len(_inventory_events(authed_client)) == 0

    ok = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread_a},
    )
    assert ok.status_code == 200
    assert ok.json()["applied"] is True
