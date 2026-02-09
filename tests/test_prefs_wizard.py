"""Tests for the one-question-at-a-time preferences wizard.

Covers:
- Wizard progression (field by field)
- Allergy hard stop (must be answered first)
- Bare answer attribution (none sentinel, bare number, bare list)
- Misroute detection (inventory text in prefs flow, prefs text in inventory flow)
- Backward compat: all-fields-in-one-message produces immediate proposal
- Rolling summary presence
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


def _post_chat(client, message, thread_id="t-wizard"):
    return client.post(
        "/chat",
        json={"mode": "fill", "message": message, "thread_id": thread_id},
    )


# ---------------------------------------------------------------------------
# 1) Wizard progression: field by field
# ---------------------------------------------------------------------------

def test_wizard_asks_allergies_first(authed_client):
    """First message without allergies triggers allergy question."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    resp = _post_chat(authed_client, "2 servings")
    body = resp.json()
    assert resp.status_code == 200
    assert body["confirmation_required"] is False
    assert "allerg" in body["reply_text"].lower()


def test_wizard_full_progression(authed_client):
    """Walk through the full wizard: allergies -> dislikes -> likes -> servings -> days -> proposal."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-wizard-full"

    # Step 1: allergies
    r1 = _post_chat(authed_client, "no allergies", thread)
    b1 = r1.json()
    assert b1["confirmation_required"] is False
    assert "dislike" in b1["reply_text"].lower()

    # Step 2: dislikes
    r2 = _post_chat(authed_client, "none", thread)
    b2 = r2.json()
    assert b2["confirmation_required"] is False
    assert "like" in b2["reply_text"].lower()

    # Step 3: likes
    r3 = _post_chat(authed_client, "italian, mexican", thread)
    b3 = r3.json()
    assert b3["confirmation_required"] is False
    assert "servings" in b3["reply_text"].lower()

    # Step 4: servings
    r4 = _post_chat(authed_client, "4", thread)
    b4 = r4.json()
    assert b4["confirmation_required"] is False
    assert "days" in b4["reply_text"].lower() or "meals" in b4["reply_text"].lower()

    # Step 5: plan_days
    r5 = _post_chat(authed_client, "7", thread)
    b5 = r5.json()
    # Should now produce a proposal
    assert b5["confirmation_required"] is True
    assert b5["proposal_id"] is not None
    assert b5["proposed_actions"]
    prefs = b5["proposed_actions"][0]["prefs"]
    assert prefs["servings"] == 4
    assert prefs["plan_days"] == 7


# ---------------------------------------------------------------------------
# 2) Allergy hard stop
# ---------------------------------------------------------------------------

def test_allergy_hard_stop_blocks_other_fields(authed_client):
    """Even if servings/days are provided, allergies must be answered first."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-allergy-stop"

    resp = _post_chat(authed_client, "4 servings 7 days", thread)
    body = resp.json()
    assert body["confirmation_required"] is False
    # Must ask about allergies, not proceed to proposal
    assert "allerg" in body["reply_text"].lower()


def test_allergy_none_sentinel_progresses(authed_client):
    """Saying 'none' to allergies moves to the next question."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-allergy-none"

    # Start wizard
    r1 = _post_chat(authed_client, "2 servings", thread)
    assert "allerg" in r1.json()["reply_text"].lower()

    # Answer 'none'
    r2 = _post_chat(authed_client, "none", thread)
    b2 = r2.json()
    # Should ask about dislikes, not allergies again
    assert "dislike" in b2["reply_text"].lower()


def test_allergy_explicit_list_progresses(authed_client):
    """Providing explicit allergy list moves to next question."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-allergy-list"

    r1 = _post_chat(authed_client, "allergic to peanuts and shellfish", thread)
    b1 = r1.json()
    assert b1["confirmation_required"] is False
    # Should ask about dislikes, not allergies
    assert "dislike" in b1["reply_text"].lower()
    # Rolling summary should show allergies
    assert "peanuts" in b1["reply_text"].lower()


# ---------------------------------------------------------------------------
# 3) Backward compat: all fields in one message
# ---------------------------------------------------------------------------

def test_all_fields_one_message_produces_proposal(authed_client):
    """A message containing all required fields produces an immediate proposal."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-all-fields"

    resp = _post_chat(
        authed_client,
        "no allergies, dislikes: none, likes: italian, 4 servings, 7 days, 3 meals per day",
        thread,
    )
    body = resp.json()
    assert body["confirmation_required"] is True
    assert body["proposal_id"] is not None
    prefs = body["proposed_actions"][0]["prefs"]
    assert prefs["servings"] == 4
    assert prefs["plan_days"] == 7
    assert prefs["meals_per_day"] == 3


def test_paragraph_with_allergies_produces_proposal(authed_client):
    """Paragraph providing allergies + all numeric fields + likes/dislikes produces proposal."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-para-allergy"

    resp = _post_chat(
        authed_client,
        "I'm allergic to peanuts, I dislike mushrooms, I like pasta, 2 servings, 5 days, 2 meals per day",
        thread,
    )
    body = resp.json()
    assert body["confirmation_required"] is True
    prefs = body["proposed_actions"][0]["prefs"]
    assert "peanuts" in prefs["allergies"]
    assert prefs["servings"] == 2


# ---------------------------------------------------------------------------
# 4) Misroute detection
# ---------------------------------------------------------------------------

def test_inventory_misroute_in_prefs_flow(authed_client):
    """Inventory-like text in prefs flow returns a nudge."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-misroute-inv"

    resp = _post_chat(authed_client, "bought 2kg chicken and picked up 500ml milk", thread)
    body = resp.json()
    assert body["confirmation_required"] is False
    assert "inventory" in body["reply_text"].lower()


def test_prefs_misroute_in_inventory_flow(authed_client):
    """Prefs-like text in inventory flow returns a nudge."""
    resp = authed_client.post(
        "/chat/inventory",
        json={
            "mode": "fill",
            "message": "allergic to peanuts, 4 servings, 3 meals per day",
            "thread_id": "t-misroute-prefs",
        },
    )
    body = resp.json()
    assert body["confirmation_required"] is False
    assert "preferences" in body["reply_text"].lower() or "prefs" in body["reply_text"].lower()


# ---------------------------------------------------------------------------
# 5) Rolling summary
# ---------------------------------------------------------------------------

def test_rolling_summary_shown_during_wizard(authed_client):
    """After answering allergies, the next question shows a summary."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-rolling"

    _post_chat(authed_client, "allergic to dairy", thread)
    r2 = _post_chat(authed_client, "none", thread)  # dislikes: none
    body = r2.json()
    # Should mention dairy in summary and ask about likes
    assert "dairy" in body["reply_text"].lower()
    assert "like" in body["reply_text"].lower()


# ---------------------------------------------------------------------------
# 6) Wizard cleanup on deny
# ---------------------------------------------------------------------------

def test_wizard_state_cleared_on_deny(authed_client):
    """Denying a proposal clears wizard state; next message starts fresh."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-wizard-deny"

    # Walk through full wizard to proposal
    _post_chat(authed_client, "no allergies", thread)
    _post_chat(authed_client, "none", thread)
    _post_chat(authed_client, "none", thread)
    _post_chat(authed_client, "4", thread)
    r5 = _post_chat(authed_client, "7", thread)
    b5 = r5.json()
    assert b5["confirmation_required"] is True
    pid = b5["proposal_id"]

    # Deny
    authed_client.post(
        "/chat/confirm",
        json={"proposal_id": pid, "confirm": False, "thread_id": thread},
    )

    # Next message should start fresh — ask about allergies
    r_fresh = _post_chat(authed_client, "2 servings", thread)
    body = r_fresh.json()
    assert body["confirmation_required"] is False
    assert "allerg" in body["reply_text"].lower()


# ---------------------------------------------------------------------------
# 7) No duplicate summary — single canonical display
# ---------------------------------------------------------------------------

def test_proposal_reply_has_single_summary_no_legacy(authed_client):
    """Wizard proposal reply_text must contain exactly one summary (hyphen format),
    not the legacy bullet (•) or 'Cuisine likes' label."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-no-dup"

    _post_chat(authed_client, "allergic to peanuts", thread)
    _post_chat(authed_client, "mushrooms", thread)  # dislikes
    _post_chat(authed_client, "italian, thai", thread)  # likes
    _post_chat(authed_client, "4", thread)  # servings
    r5 = _post_chat(authed_client, "7", thread)  # plan_days
    b5 = r5.json()

    assert b5["confirmation_required"] is True
    reply = b5["reply_text"]

    # Title present
    assert reply.startswith("Proposed preferences:"), "proposal should start with title"

    # Wizard rolling summary uses "- Field: value" format
    assert "- Allergies:" in reply, "wizard summary should use hyphen format"
    assert "- Likes:" in reply, "wizard summary should include Likes"
    assert "- Servings:" in reply, "wizard summary should include Servings"

    # Legacy describePrefs labels must NOT appear in reply_text
    assert "Cuisine likes" not in reply, "legacy 'Cuisine likes' label must not appear in reply_text"
    assert "\u2022" not in reply, "legacy bullet (•) must not appear in reply_text"

    # Only one summary block — count summary-style lines
    summary_lines = [l for l in reply.splitlines() if l.startswith("- ")]
    assert len(summary_lines) >= 3, "at least 3 summary lines expected"
    # No duplicate: each field label appears at most once
    labels = [l.split(":")[0] for l in summary_lines]
    assert len(labels) == len(set(labels)), f"duplicate labels found in summary: {labels}"


def test_backward_compat_all_fields_single_summary(authed_client):
    """All-fields-in-one-message still produces a single canonical summary."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-compat-dup"

    resp = _post_chat(
        authed_client,
        "Allergies: none. Dislikes: none. Likes: pasta. 2 servings, 5 days.",
        thread,
    )
    body = resp.json()
    assert body["confirmation_required"] is True
    reply = body["reply_text"]

    # Single hyphen-format summary only, with title
    assert reply.startswith("Proposed preferences:"), "proposal should start with title"
    assert "- Allergies:" in reply
    assert "Cuisine likes" not in reply, "legacy label must not appear"
    assert "\u2022" not in reply, "legacy bullet must not appear"