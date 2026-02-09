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


def test_labeled_paragraph_produces_proposal_not_followup(authed_client):
    """Exact paragraph from live bug: system asked follow-up despite all fields supplied."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-prefs-labeled-para"
    paragraph = (
        "Alright Little Chef. Allergies: none. "
        "Likes: chicken, salmon, rice, pasta, eggs, yoghurt, spinach, tomatoes. "
        "Dislikes: mushrooms, olives, tuna. "
        "Servings: 2 people. Days: 5 days."
    )
    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": paragraph, "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    # Must produce a proposal, NOT a follow-up question
    assert body["confirmation_required"] is True, (
        f"Expected proposal but got follow-up: {body['reply_text']}"
    )
    assert body["proposal_id"]
    action = body["proposed_actions"][0]
    prefs = action["prefs"]
    assert prefs["servings"] == 2
    assert prefs["plan_days"] == 5
    # "Allergies: none" must yield empty list, not ["none"]
    assert prefs["allergies"] == []
    # Likes must not include dislike items
    assert set(prefs["cuisine_likes"]) >= {
        "chicken", "salmon", "rice", "pasta", "eggs", "yoghurt", "spinach", "tomatoes",
    }
    assert "mushrooms" not in prefs["cuisine_likes"]
    assert "olives" not in prefs["cuisine_likes"]
    assert "tuna" not in prefs["cuisine_likes"]
    # Dislikes
    assert set(prefs["dislikes"]) >= {"mushrooms", "olives", "tuna"}


def test_labeled_paragraph_persists_after_confirm(authed_client):
    """Full round-trip: paragraph -> proposal -> confirm -> GET /prefs returns correct data."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-prefs-labeled-persist"
    paragraph = (
        "Allergies: none. Likes: chicken, salmon. "
        "Dislikes: mushrooms. Servings: 4. Days: 3."
    )
    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": paragraph, "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    proposal_id = body["proposal_id"]

    confirm_resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["applied"] is True

    prefs_resp = authed_client.get("/prefs")
    assert prefs_resp.status_code == 200
    prefs = prefs_resp.json()
    assert prefs["servings"] == 4
    assert prefs["plan_days"] == 3
    assert prefs["allergies"] == []
    assert "chicken" in prefs["cuisine_likes"]
    assert "mushrooms" in prefs["dislikes"]


def test_plan_days_asked_only_when_truly_missing(authed_client):
    """When servings supplied but days not, must ask. When days supplied, must not."""
    get_prefs_service().repo = FakeDbPrefsRepository()

    # Case 1: only servings -> asks for plan days
    thread1 = "t-prefs-missing-mpd"
    resp1 = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "Servings: 3", "thread_id": thread1},
    )
    assert resp1.status_code == 200
    body1 = resp1.json()
    assert body1["confirmation_required"] is False
    assert "day" in body1["reply_text"].lower()

    # Case 2: servings + days -> proposal (no follow-up)
    thread2 = "t-prefs-has-days"
    resp2 = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "Servings: 3. Days: 7.", "thread_id": thread2},
    )
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["confirmation_required"] is True
    assert body2["proposed_actions"][0]["prefs"]["plan_days"] == 7


def test_none_sentinel_filtered_from_all_list_fields(authed_client):
    """'none' / 'n/a' in allergy, likes, or dislikes must produce empty lists."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-prefs-none-filter"
    resp = authed_client.post(
        "/chat",
        json={
            "mode": "fill",
            "message": "Allergies: none. Likes: n/a. Dislikes: nothing. Servings: 2. Days: 5.",
            "thread_id": thread,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    prefs = body["proposed_actions"][0]["prefs"]
    assert prefs["allergies"] == []
    assert prefs["cuisine_likes"] == []
    assert prefs["dislikes"] == []
