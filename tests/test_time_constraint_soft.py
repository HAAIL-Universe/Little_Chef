"""Phase 10.8 — Time constraints as a soft constraint

Tests that:
- MATCH reply includes cook-time note when prefs have cook_time fields
- CHECK reply includes cook-time note when prefs have cook_time fields
- FILL plan notes include cook-time note when prefs have cook_time fields
- No cook-time note appears when prefs have no cook_time fields
- Behavior is unchanged when no time constraints are set
"""

import pytest

from app.services.inventory_service import get_inventory_service
from app.services.mealplan_service import MealPlanService
from app.services.chef_agent import ChefAgent
from app.services.proposal_store import ProposalStore
from app.services.prefs_service import PrefsService, get_prefs_service
from app.schemas import (
    ChatRequest,
    MealPlanGenerateRequest,
    UserMe,
    UserPrefs,
)


@pytest.fixture(autouse=True)
def _reset_inventory_cache(_clear_db_env):
    """Ensure inventory service uses in-memory repo."""
    get_inventory_service.cache_clear()
    get_prefs_service.cache_clear()
    yield
    get_inventory_service.cache_clear()
    get_prefs_service.cache_clear()


USER = UserMe(user_id="user-108", provider_subject="sub", email=None)


def _make_agent(prefs_service=None):
    from app.services.shopping_service import ShoppingService
    inv_svc = get_inventory_service()
    return ChefAgent(
        mealplan_service=MealPlanService(),
        proposal_store=ProposalStore(),
        prefs_service=prefs_service,
        inventory_service=inv_svc,
        shopping_service=ShoppingService(inv_svc),
    )


def _prefs(**overrides) -> UserPrefs:
    """Build a UserPrefs with required defaults plus overrides."""
    fields = {"servings": 2, "meals_per_day": 3}
    fields.update(overrides)
    return UserPrefs(**fields)


# ── Unit: _format_time_note ──────────────────────────────────────────────


def test_format_time_note_both():
    """When both weekday and weekend cook times are set, note contains both."""
    prefs = _prefs(cook_time_weekday_mins=30, cook_time_weekend_mins=60)
    note = ChefAgent._format_time_note(prefs)
    assert "weekday" in note
    assert "30" in note
    assert "weekend" in note
    assert "60" in note


def test_format_time_note_weekday_only():
    """When only weekday cook time is set."""
    prefs = _prefs(cook_time_weekday_mins=20)
    note = ChefAgent._format_time_note(prefs)
    assert "weekday" in note
    assert "20" in note
    assert "weekend" not in note


def test_format_time_note_none():
    """When no cook time prefs are set, returns empty string."""
    prefs = _prefs()
    note = ChefAgent._format_time_note(prefs)
    assert note == ""


def test_format_time_note_no_prefs():
    """When prefs is None, returns empty string."""
    note = ChefAgent._format_time_note(None)
    assert note == ""


# ── MATCH: cook-time note appears when prefs set ─────────────────────────


def test_match_includes_time_note():
    """MATCH reply includes cook-time note when prefs have cook_time fields."""
    prefs_svc = get_prefs_service()
    prefs_svc.upsert_prefs(USER.user_id, "sub", None, _prefs(cook_time_weekday_mins=30))
    agent = _make_agent(prefs_service=prefs_svc)

    request = ChatRequest(mode="ask", message="What can I make?")
    response = agent.handle_match(USER, request)
    assert "Cook time prefs" in response.reply_text
    assert "weekday" in response.reply_text
    assert "30" in response.reply_text


def test_match_no_time_note_without_prefs():
    """MATCH reply omits cook-time note when no time prefs set."""
    prefs_svc = get_prefs_service()
    prefs_svc.upsert_prefs(USER.user_id, "sub", None, _prefs())
    agent = _make_agent(prefs_service=prefs_svc)

    request = ChatRequest(mode="ask", message="What can I make?")
    response = agent.handle_match(USER, request)
    assert "Cook time" not in response.reply_text


# ── CHECK: cook-time note appears when prefs set ─────────────────────────


def test_check_includes_time_note():
    """CHECK reply includes cook-time note when prefs have cook_time fields."""
    prefs_svc = get_prefs_service()
    prefs_svc.upsert_prefs(USER.user_id, "sub", None, _prefs(cook_time_weekend_mins=45))
    agent = _make_agent(prefs_service=prefs_svc)

    request = ChatRequest(mode="ask", message="Can I cook Tomato Pasta?")
    response = agent.handle_check(USER, request)
    assert "Cook time prefs" in response.reply_text
    assert "weekend" in response.reply_text
    assert "45" in response.reply_text


def test_check_no_time_note_without_prefs():
    """CHECK reply omits cook-time note when no time prefs set."""
    prefs_svc = get_prefs_service()
    prefs_svc.upsert_prefs(USER.user_id, "sub", None, _prefs())
    agent = _make_agent(prefs_service=prefs_svc)

    request = ChatRequest(mode="ask", message="Can I cook Tomato Pasta?")
    response = agent.handle_check(USER, request)
    assert "Cook time" not in response.reply_text


# ── FILL/PLAN: cook-time note in plan notes ──────────────────────────────


def test_fill_plan_includes_time_note():
    """FILL plan notes include cook-time note when prefs have cook_time fields."""
    prefs_svc = get_prefs_service()
    prefs_svc.upsert_prefs(USER.user_id, "sub", None, _prefs(cook_time_weekday_mins=25, cook_time_weekend_mins=90))
    agent = _make_agent(prefs_service=prefs_svc)

    request = ChatRequest(mode="fill", message="plan meals", thread_id="t-108-fill")
    response = agent.handle_fill(USER, request)
    assert response.confirmation_required is True
    plan = response.proposed_actions[0].mealplan
    assert "Cook time prefs" in plan.notes
    assert "weekday" in plan.notes
    assert "25" in plan.notes
    assert "weekend" in plan.notes
    assert "90" in plan.notes


def test_fill_plan_no_time_note_without_prefs():
    """FILL plan notes omit cook-time note when no time prefs set."""
    prefs_svc = get_prefs_service()
    prefs_svc.upsert_prefs(USER.user_id, "sub", None, _prefs())
    agent = _make_agent(prefs_service=prefs_svc)

    request = ChatRequest(mode="fill", message="plan meals", thread_id="t-108-no-time")
    response = agent.handle_fill(USER, request)
    assert response.confirmation_required is True
    plan = response.proposed_actions[0].mealplan
    assert "Cook time" not in (plan.notes or "")
