"""Regression: MATCH/CHECK must work even when mode=fill is sent.

Root cause: frontend Meal Plan flow inherits stale mode='fill' from the Prefs
flow because lastServerMode leaks across flow switches. This causes handle_chat()
to route into the prefs wizard instead of detecting MATCH/CHECK patterns.

Fix: intercept MATCH/CHECK/CONSUME patterns in fill mode before the prefs wizard.
"""
import pytest
from app.api.routers.chat import reset_chat_state_for_tests
from app.schemas import ChatRequest, UserMe


@pytest.fixture(autouse=True)
def _reset():
    reset_chat_state_for_tests()
    yield
    reset_chat_state_for_tests()


@pytest.fixture()
def chat_service():
    from app.api.routers.chat import _chat_service
    return _chat_service


@pytest.fixture()
def user():
    return UserMe(user_id="fill-mode-test-user")


# ── MATCH in fill mode ──────────────────────────────────────────────────────

class TestMatchInFillMode:
    def test_what_can_i_make_fill_mode(self, chat_service, user):
        """'what can I make' must trigger MATCH even when mode=fill."""
        req = ChatRequest(mode="fill", message="what can I make", thread_id="t1")
        resp = chat_service.handle_chat(user, req)
        # Must NOT be the prefs wizard allergies question
        assert "allerg" not in resp.reply_text.lower(), (
            f"Prefs wizard leaked: {resp.reply_text!r}"
        )
        assert "what you can make" in resp.reply_text.lower() or "inventory" in resp.reply_text.lower() or "make" in resp.reply_text.lower()

    def test_what_can_i_cook_fill_mode(self, chat_service, user):
        """'what can I cook' must trigger MATCH even when mode=fill."""
        req = ChatRequest(mode="fill", message="what can I cook", thread_id="t2")
        resp = chat_service.handle_chat(user, req)
        assert "allerg" not in resp.reply_text.lower()

    def test_suggest_meals_fill_mode(self, chat_service, user):
        """'suggest meals' triggers MATCH in fill mode."""
        req = ChatRequest(mode="fill", message="suggest meals", thread_id="t3")
        resp = chat_service.handle_chat(user, req)
        assert "allerg" not in resp.reply_text.lower()


# ── CHECK in fill mode ──────────────────────────────────────────────────────

class TestCheckInFillMode:
    def test_can_i_cook_recipe_fill_mode(self, chat_service, user):
        """'can I cook tomato pasta?' must trigger CHECK even in fill mode."""
        req = ChatRequest(mode="fill", message="can I cook tomato pasta?", thread_id="t4")
        resp = chat_service.handle_chat(user, req)
        assert "allerg" not in resp.reply_text.lower()
        # Should be a feasibility reply
        assert any(w in resp.reply_text.lower() for w in ["tomato pasta", "feasib", "missing", "not found"])


# ── CONSUME in fill mode ────────────────────────────────────────────────────

class TestConsumeInFillMode:
    def test_i_cooked_fill_mode(self, chat_service, user):
        """'I cooked tomato pasta' must trigger CONSUME even in fill mode."""
        req = ChatRequest(mode="fill", message="I cooked tomato pasta", thread_id="t5")
        resp = chat_service.handle_chat(user, req)
        assert "allerg" not in resp.reply_text.lower()


# ── Prefs wizard still works in fill mode ────────────────────────────────────

class TestPrefsWizardStillWorks:
    def test_plain_prefs_text_still_enters_wizard(self, chat_service, user):
        """A genuine prefs message (not MATCH/CHECK) should still use the wizard."""
        req = ChatRequest(mode="fill", message="I'm allergic to peanuts", thread_id="t6")
        resp = chat_service.handle_chat(user, req)
        # Should be in prefs wizard flow (mentions allergies in summary or asks next question)
        lower = resp.reply_text.lower()
        assert "peanuts" in lower or "dislike" in lower or "servings" in lower
