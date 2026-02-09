"""Deterministic tests for prefs proposal edit-apply semantics.

Validates that non-confirm messages while a prefs proposal is pending
mutate the proposal in-place (same proposal_id) instead of no-oping.
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
# 1) Core regression: edit applies to pending prefs proposal
# ---------------------------------------------------------------------------

def test_prefs_edit_removes_allergy_and_moves_dislike_to_like(authed_client):
    """
    Regression for reported bug:
    - Initial paragraph: allergies [milk, peanuts], dislikes [mushrooms, olives, tuna],
      likes [chicken, salmon, rice, pasta, ...]
    - Edit message: "I actually like tuna. I'm not allergic to milk."
    - Expected: tuna removed from dislikes + added to likes, milk removed from allergies.
    - proposal_id must stay the same, confirmation_required still True.
    """
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-edit-apply-regression"

    # Step 1: create proposal with paragraph
    paragraph = (
        "Allergies: milk and peanuts. "
        "I like chicken, salmon, rice and pasta. "
        "I don't like mushrooms, olives, tuna. "
        "Servings: 2. Days: 5."
    )
    resp1 = authed_client.post(
        "/chat", json={"mode": "fill", "message": paragraph, "thread_id": thread}
    )
    assert resp1.status_code == 200
    body1 = resp1.json()
    assert body1["confirmation_required"] is True
    pid = body1["proposal_id"]
    prefs1 = body1["proposed_actions"][0]["prefs"]
    assert "milk" in prefs1["allergies"]
    assert "peanuts" in prefs1["allergies"]
    assert "tuna" in prefs1["dislikes"]

    # Step 2: send edit instruction
    resp2 = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "I actually like tuna. I'm not allergic to milk.", "thread_id": thread},
    )
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["confirmation_required"] is True
    prefs2 = body2["proposed_actions"][0]["prefs"]

    # proposal_id must be unchanged
    assert body2["proposal_id"] == pid

    # milk removed from allergies
    assert "milk" not in prefs2["allergies"]
    # peanuts still present
    assert "peanuts" in prefs2["allergies"]

    # tuna removed from dislikes
    assert "tuna" not in prefs2["dislikes"]
    # tuna added to likes
    assert "tuna" in prefs2["cuisine_likes"]

    # mushrooms and olives still disliked
    assert "mushrooms" in prefs2["dislikes"]
    assert "olives" in prefs2["dislikes"]

    # original likes preserved
    assert "chicken" in prefs2["cuisine_likes"]
    assert "salmon" in prefs2["cuisine_likes"]


def test_prefs_edit_adds_allergy(authed_client):
    """Edit adds new allergy to existing proposal."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-edit-add-allergy"

    resp1 = authed_client.post(
        "/chat", json={"mode": "fill", "message": "servings 2 meals per day 3", "thread_id": thread}
    )
    body1 = resp1.json()
    pid = body1["proposal_id"]
    assert body1["proposed_actions"][0]["prefs"]["allergies"] == []

    resp2 = authed_client.post(
        "/chat", json={"mode": "fill", "message": "I'm allergic to shellfish", "thread_id": thread}
    )
    body2 = resp2.json()
    assert body2["proposal_id"] == pid
    assert "shellfish" in body2["proposed_actions"][0]["prefs"]["allergies"]


def test_prefs_edit_adds_dislike(authed_client):
    """Edit adds new dislike and removes from likes."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-edit-add-dislike"

    resp1 = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "I like chicken and rice. servings 2. days 3.", "thread_id": thread},
    )
    body1 = resp1.json()
    pid = body1["proposal_id"]
    prefs1 = body1["proposed_actions"][0]["prefs"]
    assert "chicken" in prefs1["cuisine_likes"]

    resp2 = authed_client.post(
        "/chat", json={"mode": "fill", "message": "I don't like chicken", "thread_id": thread}
    )
    body2 = resp2.json()
    assert body2["proposal_id"] == pid
    prefs2 = body2["proposed_actions"][0]["prefs"]
    assert "chicken" in prefs2["dislikes"]
    assert "chicken" not in prefs2["cuisine_likes"]
    # rice still liked
    assert "rice" in prefs2["cuisine_likes"]


def test_prefs_edit_dislike_verb_removes_from_likes(authed_client):
    """'I dislike eggs' (using 'dislike' verb) removes eggs from likes."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-edit-dislike-verb"

    resp1 = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "I like chicken, eggs and rice. Servings 2. Days 3.", "thread_id": thread},
    )
    body1 = resp1.json()
    pid = body1["proposal_id"]
    assert "eggs" in body1["proposed_actions"][0]["prefs"]["cuisine_likes"]

    resp2 = authed_client.post(
        "/chat", json={"mode": "fill", "message": "I dislike eggs", "thread_id": thread}
    )
    body2 = resp2.json()
    assert body2["proposal_id"] == pid
    prefs2 = body2["proposed_actions"][0]["prefs"]
    assert "eggs" in prefs2["dislikes"]
    assert "eggs" not in prefs2["cuisine_likes"]
    # other likes preserved
    assert "chicken" in prefs2["cuisine_likes"]
    assert "rice" in prefs2["cuisine_likes"]


def test_prefs_edit_comma_separated_clauses(authed_client):
    """'I don't like eggs, I'm not allergic to milk' must NOT treat
    'I'm not allergic to milk' as a dislike — each clause is independent."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-clause-sep"

    resp1 = authed_client.post(
        "/chat",
        json={
            "mode": "fill",
            "message": "Allergies: milk, peanuts. I like chicken, eggs and rice. "
                       "I don't like mushrooms, olives, tuna. Servings 2. Days 2.",
            "thread_id": thread,
        },
    )
    body1 = resp1.json()
    pid = body1["proposal_id"]
    prefs1 = body1["proposed_actions"][0]["prefs"]
    assert "eggs" in prefs1["cuisine_likes"]
    assert "milk" in prefs1["allergies"]

    # Combined edit: dislike eggs + remove milk allergy
    resp2 = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "I don't like eggs, I'm not allergic to milk", "thread_id": thread},
    )
    body2 = resp2.json()
    assert body2["proposal_id"] == pid
    prefs2 = body2["proposed_actions"][0]["prefs"]

    # eggs moved to dislikes
    assert "eggs" in prefs2["dislikes"]
    assert "eggs" not in prefs2["cuisine_likes"]

    # milk removed from allergies — NOT added to dislikes
    assert "milk" not in prefs2["allergies"]
    assert "milk" not in prefs2["dislikes"]

    # peanuts still in allergies
    assert "peanuts" in prefs2["allergies"]
    # original likes preserved (minus eggs)
    assert "chicken" in prefs2["cuisine_likes"]


def test_prefs_edit_stacks_multiple_edits(authed_client):
    """Multiple sequential edits compound on the same proposal."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-edit-stacking"

    resp1 = authed_client.post(
        "/chat", json={"mode": "fill", "message": "Servings: 2. Days: 5.", "thread_id": thread}
    )
    pid = resp1.json()["proposal_id"]

    # Edit 1: add allergy
    resp2 = authed_client.post(
        "/chat", json={"mode": "fill", "message": "I'm allergic to gluten", "thread_id": thread}
    )
    assert resp2.json()["proposal_id"] == pid
    assert "gluten" in resp2.json()["proposed_actions"][0]["prefs"]["allergies"]

    # Edit 2: add like
    resp3 = authed_client.post(
        "/chat", json={"mode": "fill", "message": "I like sushi", "thread_id": thread}
    )
    assert resp3.json()["proposal_id"] == pid
    prefs3 = resp3.json()["proposed_actions"][0]["prefs"]
    # Both edits persisted
    assert "gluten" in prefs3["allergies"]
    assert "sushi" in prefs3["cuisine_likes"]


# ---------------------------------------------------------------------------
# 2) Confirm still works correctly after edits
# ---------------------------------------------------------------------------

def test_prefs_confirm_persists_edited_proposal(authed_client):
    """Confirm after edit persists the edited prefs, not the original."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-edit-then-confirm"

    # Create proposal
    resp1 = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "Allergies: milk. Servings: 2. Days: 3.", "thread_id": thread},
    )
    pid = resp1.json()["proposal_id"]
    assert "milk" in resp1.json()["proposed_actions"][0]["prefs"]["allergies"]

    # Edit: remove milk allergy
    resp2 = authed_client.post(
        "/chat", json={"mode": "fill", "message": "I'm not allergic to milk", "thread_id": thread}
    )
    assert resp2.json()["proposal_id"] == pid
    assert "milk" not in resp2.json()["proposed_actions"][0]["prefs"]["allergies"]

    # Confirm
    resp3 = authed_client.post(
        "/chat/confirm", json={"proposal_id": pid, "confirm": True, "thread_id": thread}
    )
    assert resp3.status_code == 200
    assert resp3.json()["applied"] is True

    # Verify persisted prefs reflect the edit
    prefs = authed_client.get("/prefs").json()
    assert "milk" not in prefs["allergies"]
    assert prefs["servings"] == 2


def test_prefs_confirm_clears_proposal_after_edit(authed_client):
    """After confirm, the proposal_id is no longer valid."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-edit-confirm-clear"

    resp1 = authed_client.post(
        "/chat", json={"mode": "fill", "message": "Servings: 2. Days: 5.", "thread_id": thread}
    )
    pid = resp1.json()["proposal_id"]

    # Edit
    authed_client.post(
        "/chat", json={"mode": "fill", "message": "I like pasta", "thread_id": thread}
    )

    # Confirm
    resp3 = authed_client.post(
        "/chat/confirm", json={"proposal_id": pid, "confirm": True, "thread_id": thread}
    )
    assert resp3.json()["applied"] is True

    # Re-confirm should fail
    resp4 = authed_client.post(
        "/chat/confirm", json={"proposal_id": pid, "confirm": True, "thread_id": thread}
    )
    assert resp4.status_code == 400


# ---------------------------------------------------------------------------
# 3) Unit-level test of _apply_prefs_edit_text
# ---------------------------------------------------------------------------

def test_apply_prefs_edit_text_add_allergy_does_not_conflict_with_remove():
    """'Not allergic to X' must not also trigger 'allergic to X' add."""
    from app.services.chat_service import ChatService
    from app.services.prefs_service import PrefsService
    from app.services.inventory_service import InventoryService
    from app.services.proposal_store import ProposalStore
    from app.schemas import UserPrefs

    svc = ChatService(
        PrefsService.__new__(PrefsService),
        InventoryService.__new__(InventoryService),
        ProposalStore(),
    )

    prefs = UserPrefs(
        allergies=["milk"], dislikes=[], cuisine_likes=[],
        servings=2, meals_per_day=3, notes="",
    )

    edited = svc._apply_prefs_edit_text(prefs, "I'm not allergic to milk.")
    assert "milk" not in edited.allergies


# ---------------------------------------------------------------------------
# 4) Generic "remove X" tests
# ---------------------------------------------------------------------------

def _make_svc_and_prefs(**overrides):
    """Helper to build ChatService + UserPrefs for unit tests."""
    from app.services.chat_service import ChatService
    from app.services.prefs_service import PrefsService
    from app.services.inventory_service import InventoryService
    from app.services.proposal_store import ProposalStore
    from app.schemas import UserPrefs

    svc = ChatService(
        PrefsService.__new__(PrefsService),
        InventoryService.__new__(InventoryService),
        ProposalStore(),
    )
    defaults = dict(allergies=[], dislikes=[], cuisine_likes=[],
                    servings=2, meals_per_day=3, notes="")
    defaults.update(overrides)
    prefs = UserPrefs(**defaults)
    return svc, prefs


def test_generic_remove_from_likes():
    svc, prefs = _make_svc_and_prefs(cuisine_likes=["chicken", "salmon"])
    edited = svc._apply_prefs_edit_text(prefs, "remove chicken")
    assert "chicken" not in edited.cuisine_likes
    assert "salmon" in edited.cuisine_likes


def test_generic_remove_from_allergies():
    svc, prefs = _make_svc_and_prefs(allergies=["milk", "peanuts"])
    edited = svc._apply_prefs_edit_text(prefs, "remove milk")
    assert "milk" not in edited.allergies
    assert "peanuts" in edited.allergies


def test_generic_remove_from_dislikes():
    svc, prefs = _make_svc_and_prefs(dislikes=["mushrooms", "olives"])
    edited = svc._apply_prefs_edit_text(prefs, "remove mushrooms from the list")
    assert "mushrooms" not in edited.dislikes
    assert "olives" in edited.dislikes


def test_generic_remove_multiple_items():
    svc, prefs = _make_svc_and_prefs(
        allergies=["milk"], cuisine_likes=["chicken"], dislikes=["tuna"]
    )
    edited = svc._apply_prefs_edit_text(prefs, "remove milk, chicken and tuna")
    assert "milk" not in edited.allergies
    assert "chicken" not in edited.cuisine_likes
    assert "tuna" not in edited.dislikes


def test_generic_remove_does_not_readd():
    """'remove chicken' must not trigger like/dislike patterns to re-add."""
    svc, prefs = _make_svc_and_prefs(cuisine_likes=["chicken", "salmon"])
    edited = svc._apply_prefs_edit_text(prefs, "remove chicken")
    assert "chicken" not in edited.cuisine_likes
    assert "chicken" not in edited.dislikes
    assert "chicken" not in edited.allergies


def test_take_off_variant():
    svc, prefs = _make_svc_and_prefs(cuisine_likes=["sushi"])
    edited = svc._apply_prefs_edit_text(prefs, "take off sushi")
    assert "sushi" not in edited.cuisine_likes


def test_delete_variant():
    svc, prefs = _make_svc_and_prefs(dislikes=["broccoli"])
    edited = svc._apply_prefs_edit_text(prefs, "delete broccoli from dislikes")
    assert "broccoli" not in edited.dislikes


# ---------------------------------------------------------------------------
# 5) Smart-apostrophe (U+2019) tests
# ---------------------------------------------------------------------------

def test_smart_apostrophe_not_allergic():
    svc, prefs = _make_svc_and_prefs(allergies=["milk"])
    edited = svc._apply_prefs_edit_text(prefs, "I\u2019m not allergic to milk")
    assert "milk" not in edited.allergies


def test_smart_apostrophe_allergic():
    svc, prefs = _make_svc_and_prefs()
    edited = svc._apply_prefs_edit_text(prefs, "I\u2019m allergic to shellfish")
    assert "shellfish" in edited.allergies


def test_smart_apostrophe_dont_like():
    svc, prefs = _make_svc_and_prefs(cuisine_likes=["olives"])
    edited = svc._apply_prefs_edit_text(prefs, "I don\u2019t like olives")
    assert "olives" in edited.dislikes
    assert "olives" not in edited.cuisine_likes


def test_smart_apostrophe_cant_have():
    svc, prefs = _make_svc_and_prefs()
    edited = svc._apply_prefs_edit_text(prefs, "I can\u2019t have dairy")
    assert "dairy" in edited.allergies


# ---------------------------------------------------------------------------
# 6) Clause-boundary normalization
# ---------------------------------------------------------------------------

def test_clause_boundary_combo_dislike_and_remove_allergy():
    """'I don't like eggs, I'm not allergic to milk' must handle both clauses."""
    svc, prefs = _make_svc_and_prefs(
        allergies=["milk", "peanuts"], cuisine_likes=["eggs", "chicken"]
    )
    edited = svc._apply_prefs_edit_text(
        prefs, "I don't like eggs, I'm not allergic to milk"
    )
    assert "eggs" in edited.dislikes
    assert "eggs" not in edited.cuisine_likes
    assert "milk" not in edited.allergies
    assert "milk" not in edited.dislikes  # must NOT leak into dislikes
    assert "peanuts" in edited.allergies
    assert "chicken" in edited.cuisine_likes


def test_clause_boundary_preserves_list_commas():
    """Commas between list items (not before 'I') must NOT be split."""
    svc, prefs = _make_svc_and_prefs()
    edited = svc._apply_prefs_edit_text(prefs, "I like chicken, rice and pasta")
    assert "chicken" in edited.cuisine_likes
    assert "rice" in edited.cuisine_likes
    assert "pasta" in edited.cuisine_likes


def test_clause_boundary_smart_apostrophe():
    """Smart-apostrophe clause: ', I\u2019m not allergic'."""
    svc, prefs = _make_svc_and_prefs(
        allergies=["milk"], cuisine_likes=["tuna"], dislikes=["olives"]
    )
    edited = svc._apply_prefs_edit_text(
        prefs, "I like olives, I\u2019m not allergic to milk"
    )
    assert "olives" in edited.cuisine_likes
    assert "olives" not in edited.dislikes
    assert "milk" not in edited.allergies
    assert "milk" not in edited.dislikes


# ---------------------------------------------------------------------------
# 7) Initial parse regression: STT paragraph (reported 2026-02-09)
# ---------------------------------------------------------------------------

def test_initial_parse_stt_paragraph():
    """Full STT paragraph must parse correctly: milk allergy, no duplicates,
    no filler in dislikes, no prefix in likes, correct servings + days."""
    svc, _ = _make_svc_and_prefs()

    text = (
        "I've got a milk allergy and I'm also allergic to peanuts. "
        "I really like Italian food and Mexican food, and I'm happy with most "
        "chicken meals and pasta dishes. I don't like mushrooms, olives, or "
        "tuna, so please avoid those. I'm cooking for two servings each time. "
        "I want to plan for five days this week."
    )
    result = svc._parse_prefs_from_message(text.lower())

    # Allergies: milk + peanuts, no duplicates, no phrase leaks
    assert "milk" in result.allergies
    assert "peanuts" in result.allergies
    assert len(result.allergies) == 2

    # Likes: clean items, no "i'm happy with most" prefix
    assert "italian food" in result.cuisine_likes
    assert "mexican food" in result.cuisine_likes
    assert "chicken meals" in result.cuisine_likes or "chicken" in result.cuisine_likes
    assert "pasta dishes" in result.cuisine_likes or "pasta" in result.cuisine_likes
    assert not any("happy" in item for item in result.cuisine_likes)

    # Dislikes: clean, no "so please avoid those"
    assert "mushrooms" in result.dislikes
    assert "olives" in result.dislikes
    assert "tuna" in result.dislikes
    assert not any("please" in item for item in result.dislikes)
    assert not any("avoid" in item for item in result.dislikes)

    # Numbers
    assert result.servings == 2
    assert result.meals_per_day == 5


def test_initial_parse_monday_to_friday_days():
    """'Monday to Friday' should produce meals_per_day=5."""
    svc, _ = _make_svc_and_prefs()
    text = "it's for two servings, and i want meals for monday to friday this week."
    result = svc._parse_prefs_from_message(text)
    assert result.servings == 2
    assert result.meals_per_day == 5


def test_initial_parse_allergy_before_keyword():
    """'got a X allergy' pattern captures item BEFORE the word allergy."""
    svc, _ = _make_svc_and_prefs()
    text = "i've got a dairy allergy"
    result = svc._parse_prefs_from_message(text)
    assert "dairy" in result.allergies
