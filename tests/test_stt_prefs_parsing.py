"""
Golden STT (speech-to-text) paragraph tests for preference parsing.

These test the regex fallback path (LLM disabled) with representative
unpunctuated STT input.  When the LLM is available it will supersede
the regex parser, but these tests ensure the fallback is still sane
for structured-ish input.
"""

import pytest

from app.services.prefs_service import get_prefs_service
from app.repos.prefs_repo import DbPrefsRepository


class FakeDbPrefsRepository(DbPrefsRepository):
    """In-memory prefs repo for testing (no real DB needed)."""
    def __init__(self):
        self._store: dict[str, object] = {}

    def get_prefs(self, user_id: str):
        return self._store.get(user_id)

    def upsert_prefs(self, user_id, provider_subject, email, prefs, applied_event_id=None):
        self._store[user_id] = prefs
        return prefs


def _post_chat(client, message, thread):
    return client.post(
        "/chat",
        json={"mode": "fill", "message": message, "thread_id": thread},
    )


# ---------------------------------------------------------------------------
# 1) Structured paragraph — labeled fields, punctuated
# ---------------------------------------------------------------------------

def test_stt_structured_paragraph(authed_client):
    """Standard labeled paragraph with punctuation — baseline regression."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-stt-structured"

    resp = _post_chat(
        authed_client,
        "Allergies: peanuts. Dislikes: mushrooms, olives. I like chicken and pasta. Servings: 2. 5 days. 2 meals per day.",
        thread,
    )
    body = resp.json()
    assert body["confirmation_required"] is True
    prefs = body["proposed_actions"][0]["prefs"]

    # Correct classification
    assert "peanuts" in prefs["allergies"]
    assert "mushrooms" in prefs["dislikes"]
    assert "olives" in prefs["dislikes"]
    assert prefs["servings"] == 2
    assert prefs["meals_per_day"] == 2

    # No cross-contamination
    assert "mushrooms" not in prefs["allergies"]
    assert "peanuts" not in prefs["dislikes"]
    assert "chicken" not in prefs["allergies"]
    assert "chicken" not in prefs["dislikes"]


# ---------------------------------------------------------------------------
# 2) Semi-structured STT — some labels, no full stops
# ---------------------------------------------------------------------------

def test_stt_semi_structured(authed_client):
    """Labels present but minimal punctuation — common STT output."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-stt-semi"

    resp = _post_chat(
        authed_client,
        "Allergies: none. Dislikes: none. Likes: mexican and indian food. 4 servings, 3 meals per day",
        thread,
    )
    body = resp.json()
    assert body["confirmation_required"] is True
    prefs = body["proposed_actions"][0]["prefs"]
    assert prefs["allergies"] == []
    assert prefs["servings"] == 4
    assert prefs["meals_per_day"] == 3


# ---------------------------------------------------------------------------
# 3) Cross-contamination check: dislikes must not bleed into allergies
# ---------------------------------------------------------------------------

def test_stt_no_cross_contamination(authed_client):
    """Items from one category must not appear in another."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-stt-cross"

    resp = _post_chat(
        authed_client,
        "I'm allergic to peanuts. I don't like mushrooms and olives. I like chicken and salmon. 2 servings 5 days 2 meals per day.",
        thread,
    )
    body = resp.json()
    assert body["confirmation_required"] is True
    prefs = body["proposed_actions"][0]["prefs"]

    # Allergies: only peanuts
    assert "peanuts" in prefs["allergies"]
    assert len(prefs["allergies"]) <= 2  # might include "peanuts" only

    # Dislikes: mushrooms, olives
    for item in prefs["dislikes"]:
        assert item.lower() not in ("peanuts", "chicken", "salmon")

    # Likes: should NOT contain allergy or dislike items
    for item in prefs["cuisine_likes"]:
        assert item.lower() not in ("peanuts", "mushrooms", "olives")


# ---------------------------------------------------------------------------
# 4) Schema new fields present in response (even when empty)
# ---------------------------------------------------------------------------

def test_stt_new_fields_in_schema(authed_client):
    """cook_time_weekday_mins, cook_time_weekend_mins, diet_goals should appear in prefs."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-stt-schema"

    resp = _post_chat(
        authed_client,
        "Allergies: none. Dislikes: none. Likes: italian. 2 servings, 2 meals per day.",
        thread,
    )
    body = resp.json()
    assert body["confirmation_required"] is True
    prefs = body["proposed_actions"][0]["prefs"]

    # New fields should be present with defaults
    assert "cook_time_weekday_mins" in prefs
    assert "cook_time_weekend_mins" in prefs
    assert "diet_goals" in prefs
    assert prefs["diet_goals"] == []


# ---------------------------------------------------------------------------
# 5) LLM path: verify prefs are correctly parsed from LLM structured reply
# ---------------------------------------------------------------------------

def test_llm_prefs_path(authed_client, monkeypatch):
    """When LLM is enabled, generate_structured_reply returns a dict that
    prefs_parse_service converts into UserPrefs.  Verify the full integration."""
    get_prefs_service().repo = FakeDbPrefsRepository()
    thread = "t-llm-prefs-path"

    fake_llm_response = {
        "allergies": ["peanuts", "dairy"],
        "dislikes": ["mushrooms"],
        "cuisine_likes": ["italian", "mexican"],
        "servings": 4,
        "meals_per_day": 3,
        "plan_days": 7,
        "cook_time_weekday_mins": 30,
        "cook_time_weekend_mins": 60,
        "diet_goals": ["high protein", "low carb"],
        "notes": "prefers one-pot meals",
    }

    import app.services.llm_client as llm_client
    monkeypatch.setattr(
        llm_client.LlmClient,
        "generate_structured_reply",
        lambda self, text, kind: fake_llm_response if kind == "prefs" else None,
    )

    resp = _post_chat(
        authed_client,
        "this wont matter since LLM is mocked",
        thread,
    )
    body = resp.json()
    assert body["confirmation_required"] is True
    prefs = body["proposed_actions"][0]["prefs"]

    assert prefs["allergies"] == ["peanuts", "dairy"]
    assert prefs["dislikes"] == ["mushrooms"]
    assert prefs["cuisine_likes"] == ["italian", "mexican"]
    assert prefs["servings"] == 4
    assert prefs["meals_per_day"] == 3
    assert prefs["plan_days"] == 7
    assert prefs["cook_time_weekday_mins"] == 30
    assert prefs["cook_time_weekend_mins"] == 60
    assert prefs["diet_goals"] == ["high protein", "low carb"]
    assert prefs["notes"] == "prefers one-pot meals"
