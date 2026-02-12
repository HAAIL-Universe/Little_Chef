"""Phase 10.9 — Maintain propose → confirm → apply semantics

Validates that after all Phase 10 changes:
- Meal plan generation remains proposal-based (confirmation_required=True)
- Confirm returns plan_id and is deterministic
- Thread isolation is preserved
- Decline path works
"""

import pytest

from app.services.inventory_service import get_inventory_service


@pytest.fixture(autouse=True)
def _reset_inventory_cache(_clear_db_env):
    get_inventory_service.cache_clear()
    yield
    get_inventory_service.cache_clear()


def test_propose_confirm_returns_plan_id(authed_client):
    """Confirm returns the plan_id deterministically."""
    resp = authed_client.post("/chat/mealplan", json={
        "mode": "fill", "message": "plan meals", "thread_id": "t-109-a",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    pid = body["proposal_id"]
    plan_id = body["proposed_actions"][0]["mealplan"]["plan_id"]
    assert plan_id  # non-empty

    conf = authed_client.post("/chat/confirm", json={
        "proposal_id": pid, "confirm": True, "thread_id": "t-109-a",
    })
    assert conf.status_code == 200
    cb = conf.json()
    assert cb["applied"] is True
    assert plan_id in cb["applied_event_ids"]


def test_decline_does_not_apply(authed_client):
    """Declining a proposal returns applied=False, no event ids."""
    resp = authed_client.post("/chat/mealplan", json={
        "mode": "fill", "message": "plan meals", "thread_id": "t-109-b",
    })
    pid = resp.json()["proposal_id"]

    conf = authed_client.post("/chat/confirm", json={
        "proposal_id": pid, "confirm": False, "thread_id": "t-109-b",
    })
    assert conf.status_code == 200
    assert conf.json()["applied"] is False
    assert conf.json()["applied_event_ids"] == []


def test_thread_isolation_cross_confirm_rejected(authed_client):
    """Confirming a proposal on the wrong thread is rejected."""
    resp = authed_client.post("/chat/mealplan", json={
        "mode": "fill", "message": "plan meals", "thread_id": "t-109-c",
    })
    pid = resp.json()["proposal_id"]

    # Attempt confirm on wrong thread
    conf = authed_client.post("/chat/confirm", json={
        "proposal_id": pid, "confirm": True, "thread_id": "t-109-wrong",
    })
    assert conf.status_code == 400


def test_double_confirm_rejected(authed_client):
    """Confirming the same proposal twice is rejected."""
    resp = authed_client.post("/chat/mealplan", json={
        "mode": "fill", "message": "plan meals", "thread_id": "t-109-d",
    })
    pid = resp.json()["proposal_id"]

    # First confirm succeeds
    conf1 = authed_client.post("/chat/confirm", json={
        "proposal_id": pid, "confirm": True, "thread_id": "t-109-d",
    })
    assert conf1.status_code == 200
    assert conf1.json()["applied"] is True

    # Second confirm on same proposal should fail (already consumed)
    conf2 = authed_client.post("/chat/confirm", json={
        "proposal_id": pid, "confirm": True, "thread_id": "t-109-d",
    })
    assert conf2.status_code == 400
