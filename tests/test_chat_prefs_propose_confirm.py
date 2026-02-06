from app.repos.prefs_repo import DbPrefsRepository
from app.services.prefs_service import PrefsPersistenceError, get_prefs_service


class FakeDbPrefsRepository(DbPrefsRepository):
    def __init__(self):
        self._store: dict[str, object] = {}

    def get_prefs(self, user_id: str):
        return self._store.get(user_id)

    def upsert_prefs(self, user_id: str, provider_subject, email, prefs, applied_event_id=None):
        self._store[user_id] = prefs
        return prefs


def test_chat_prefs_propose_confirm_flow(authed_client):
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-prefs-confirm"
    # propose
    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "set servings 4 meals per day 2", "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    assert body["proposal_id"]
    assert body["proposed_actions"]
    action = body["proposed_actions"][0]
    assert action["action_type"] == "upsert_prefs"
    assert action["prefs"]["servings"] == 4
    assert action["prefs"]["meals_per_day"] == 2

    # confirm
    proposal_id = body["proposal_id"]
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert resp.status_code == 200
    confirm_body = resp.json()
    assert confirm_body["applied"] is True
    assert confirm_body["reason"] is None
    applied_ids = confirm_body["applied_event_ids"]
    assert applied_ids
    assert applied_ids[0].startswith("prefs-")
    repo = get_prefs_service().repo
    if hasattr(repo, "get_applied_event_id"):
        assert repo.get_applied_event_id("test-user") == applied_ids[0]

    # prefs reflect change
    resp = authed_client.get("/prefs")
    assert resp.status_code == 200
    prefs = resp.json()
    assert prefs["servings"] == 4
    assert prefs["meals_per_day"] == 2


def test_fill_word_servings_detected(authed_client):
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-prefs-word"
    paragraph = (
        "Okay, so for allergies: I'm allergic to peanuts and I can't have shellfish. "
        "I like chicken, salmon, rice, pasta, potatoes, tomatoes, spinach, peppers, cheese, "
        "and anything spicy. I don't like mushrooms, olives, blue cheese, or really sweet sauces. "
        "It's for two servings, and I want meals for Monday to Friday this week."
    )
    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": paragraph, "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    assert body["proposed_actions"]
    action = body["proposed_actions"][0]
    assert action["action_type"] == "upsert_prefs"
    assert action["prefs"]["servings"] == 2
    prefs = action["prefs"]
    assert set(prefs["allergies"]) == {"peanuts", "shellfish"}
    assert set(prefs["dislikes"]) >= {"mushrooms", "olives", "blue cheese", "really sweet sauces"}
    assert set(prefs["cuisine_likes"]) >= {"chicken", "salmon", "rice", "pasta", "potatoes", "tomatoes", "spinach", "peppers", "cheese", "anything spicy"}


def test_chat_prefs_confirm_paragraph_persists(authed_client):
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-prefs-paragraph-confirm"
    paragraph = (
        "Okay, so for allergies: I'm allergic to peanuts and I can't have shellfish. "
        "I like chicken, salmon, rice, pasta, potatoes, tomatoes, spinach, peppers, cheese, "
        "and anything spicy. I don't like mushrooms, olives, blue cheese, or really sweet sauces. "
        "It's for two servings, and I want meals for Monday to Friday this week."
    )

    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": paragraph, "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    proposal_id = body["proposal_id"]
    assert proposal_id

    confirm_resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert confirm_resp.status_code == 200
    confirm_body = confirm_resp.json()
    assert confirm_body["applied"] is True
    assert "confirmation_required" not in confirm_body
    assert "proposal_id" not in confirm_body
    applied_ids = confirm_body["applied_event_ids"]
    assert applied_ids
    assert applied_ids[0].startswith("prefs-")

    prefs_resp = authed_client.get("/prefs")
    assert prefs_resp.status_code == 200
    prefs_body = prefs_resp.json()
    assert prefs_body["servings"] == 2
    assert set(prefs_body["allergies"]) >= {"peanuts", "shellfish"}


def test_chat_prefs_confirm_failure_is_retriable(authed_client, monkeypatch):
    thread = "t-prefs-confirm-fail"
    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "set servings 3 meals per day 2", "thread_id": thread},
    )
    assert resp.status_code == 200
    proposal_id = resp.json()["proposal_id"]
    service = get_prefs_service()
    state: dict[str, int] = {"attempts": 0}

    def flaky_upsert(user_id, provider_subject, email, prefs, applied_event_id=None, require_db=False):
        state["attempts"] += 1
        if state["attempts"] == 1:
            raise PrefsPersistenceError("simulated db outage")
        return prefs

    monkeypatch.setattr(service, "upsert_prefs", flaky_upsert)

    confirm_resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert confirm_resp.status_code == 200
    body = confirm_resp.json()
    assert body["applied"] is False
    assert body["applied_event_ids"] == []
    assert body["reason"] == "prefs_persist_failed"

    confirm_resp2 = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert confirm_resp2.status_code == 200
    body2 = confirm_resp2.json()
    assert body2["applied"] is True
    assert body2["reason"] is None
    assert body2["applied_event_ids"]
    assert body2["applied_event_ids"][0].startswith("prefs-")
