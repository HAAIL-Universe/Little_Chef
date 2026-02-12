"""Phase 11.3 — Cooked/consumed confirmation tests.

Verifies that:
  - "I cooked X" messages produce consume_cooked proposals
  - Confirming a consume proposal writes inventory events
  - Declining a consume proposal does nothing
  - Unknown recipe names get a helpful rejection
  - thread_id is required for consume tracking
  - Inventory summary reflects consumed items
"""
import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CHAT_URL = "/chat"
CONFIRM_URL = "/chat/confirm"


def _chat(client: TestClient, message: str, thread_id: str = "t-consume-1") -> dict:
    resp = client.post(
        CHAT_URL,
        json={"mode": "ask", "message": message, "thread_id": thread_id},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _confirm(client: TestClient, proposal_id: str, confirm: bool, thread_id: str = "t-consume-1") -> dict:
    resp = client.post(
        CONFIRM_URL,
        json={"proposal_id": proposal_id, "confirm": confirm, "thread_id": thread_id},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_consume_proposal_created(authed_client):
    """'I cooked Simple Tomato Pasta' should propose consume_cooked events."""
    body = _chat(authed_client, "I cooked Simple Tomato Pasta")
    assert body["confirmation_required"] is True
    assert body["proposal_id"] is not None
    actions = body["proposed_actions"]
    assert len(actions) >= 1
    for act in actions:
        assert act["action_type"] == "create_inventory_event"
        assert act["event"]["event_type"] == "consume_cooked"


def test_consume_proposal_lists_ingredients(authed_client):
    """Proposal actions should map to the recipe's known ingredients."""
    body = _chat(authed_client, "I made Tomato Pasta")
    actions = body["proposed_actions"]
    item_names = {a["event"]["item_name"] for a in actions}
    # builtin_1 has tomato + pasta
    assert "tomato" in item_names
    assert "pasta" in item_names


def test_consume_confirm_writes_events(authed_client):
    """Confirming the proposal should write consume_cooked events to inventory."""
    body = _chat(authed_client, "I cooked Simple Tomato Pasta", thread_id="t-consume-confirm")
    proposal_id = body["proposal_id"]
    assert proposal_id is not None

    confirm_body = _confirm(authed_client, proposal_id, True, thread_id="t-consume-confirm")
    assert confirm_body["applied"] is True
    # Should return event IDs for each ingredient
    assert len(confirm_body["applied_event_ids"]) >= 1


def test_consume_decline_no_events(authed_client):
    """Declining the proposal should not write any events."""
    body = _chat(authed_client, "I cooked Garlic Butter Chicken", thread_id="t-consume-decline")
    proposal_id = body["proposal_id"]

    confirm_body = _confirm(authed_client, proposal_id, False, thread_id="t-consume-decline")
    assert confirm_body["applied"] is False

    # Verify inventory summary is empty (no events written)
    resp = authed_client.get("/inventory/summary")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_consume_unknown_recipe_rejected(authed_client):
    """An unrecognised recipe name should respond without a proposal."""
    body = _chat(authed_client, "I cooked Unicorn Surprise")
    assert body["confirmation_required"] is False
    assert body["proposal_id"] is None
    assert "couldn't find" in body["reply_text"].lower()


def test_consume_requires_thread_id(authed_client):
    """Consuming without a thread_id should fail gracefully."""
    resp = authed_client.post(
        CHAT_URL,
        json={"mode": "ask", "message": "I cooked Simple Tomato Pasta"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is False
    assert "thread" in body["reply_text"].lower()


def test_consume_inventory_summary_reflects_events(authed_client):
    """After confirming consumption, inventory summary should contain consume events."""
    # First add some inventory
    authed_client.post(
        CHAT_URL,
        json={
            "mode": "fill",
            "message": "I have 5 count tomato and 500g pasta",
            "thread_id": "t-inv-setup",
        },
    )
    # Confirm inventory addition if proposed
    resp = authed_client.post(
        CHAT_URL,
        json={
            "mode": "fill",
            "message": "I have 5 count tomato and 500g pasta",
            "thread_id": "t-inv-setup2",
        },
    )
    inv_body = resp.json()
    if inv_body.get("proposal_id"):
        _confirm(authed_client, inv_body["proposal_id"], True, thread_id="t-inv-setup2")

    # Now consume
    body = _chat(authed_client, "I cooked Simple Tomato Pasta", thread_id="t-consume-inv")
    assert body["confirmation_required"] is True
    proposal_id = body["proposal_id"]
    _confirm(authed_client, proposal_id, True, thread_id="t-consume-inv")

    # Check inventory events exist
    resp = authed_client.get("/inventory/events")
    assert resp.status_code == 200
    events = resp.json()["events"]
    consume_events = [e for e in events if e["event_type"] == "consume_cooked"]
    assert len(consume_events) >= 2  # tomato + pasta


def test_consume_regex_variations(authed_client):
    """Various consume phrasings should all trigger the consume flow."""
    for msg in [
        "I made Tomato Pasta",
        "We cooked the Tomato Pasta",
        "I prepared Simple Tomato Pasta",
        "We had Garlic Butter Chicken",
    ]:
        body = _chat(authed_client, msg, thread_id=f"t-var-{hash(msg)}")
        assert body["confirmation_required"] is True, f"Failed for: {msg}"
        assert body["proposal_id"] is not None, f"No proposal for: {msg}"


def test_consume_event_has_recipe_note(authed_client):
    """Consume events should have a note referencing the recipe title."""
    body = _chat(authed_client, "I cooked Simple Tomato Pasta", thread_id="t-note")
    actions = body["proposed_actions"]
    for act in actions:
        assert "Cooked:" in act["event"]["note"]
        assert "Simple Tomato Pasta" in act["event"]["note"] or "Tomato Pasta" in act["event"]["note"]


def test_consume_event_quantities_from_recipe(authed_client):
    """Consume events should preserve ingredient quantities from the recipe."""
    body = _chat(authed_client, "I cooked Simple Tomato Pasta", thread_id="t-qty")
    actions = body["proposed_actions"]
    qty_map = {a["event"]["item_name"]: a["event"] for a in actions}
    # builtin_1: tomato 2 count, pasta 200g
    assert qty_map["tomato"]["quantity"] == 2
    assert qty_map["tomato"]["unit"] == "count"
    assert qty_map["pasta"]["quantity"] == 200
    assert qty_map["pasta"]["unit"] == "g"
