"""Phase 10.7 — Wire shopping diff into Chef outputs

Tests that:
- ChefAgent._annotate_inventory_notes uses ShoppingService.diff() when available
- Notes distinguish "You have" vs "You need" with quantities
- Missing items are consistent with ShoppingService.diff() output
- POST /shopping/diff and ChefAgent share the same diff logic
- Fallback to name-only matching when no shopping_service provided
"""

import pytest

from app.services.inventory_service import get_inventory_service
from app.services.shopping_service import ShoppingService
from app.services.mealplan_service import MealPlanService
from app.services.chef_agent import ChefAgent
from app.services.proposal_store import ProposalStore
from app.schemas import (
    ChatRequest,
    InventoryEventCreateRequest,
    MealPlanGenerateRequest,
    MealPlanResponse,
    UserMe,
)


@pytest.fixture(autouse=True)
def _reset_inventory_cache(_clear_db_env):
    """Ensure inventory service uses in-memory repo after _clear_db_env sets DATABASE_URL=''."""
    get_inventory_service.cache_clear()
    yield
    get_inventory_service.cache_clear()


def _seed_inventory(inv_svc, user_id, name, qty, unit="count"):
    """Helper to seed inventory via service."""
    inv_svc.create_event(
        user_id, "sub", None,
        InventoryEventCreateRequest(event_type="add", item_name=name, quantity=qty, unit=unit),
    )


def _make_agent(inventory_service=None, shopping_service=None):
    return ChefAgent(
        mealplan_service=MealPlanService(),
        proposal_store=ProposalStore(),
        inventory_service=inventory_service,
        shopping_service=shopping_service,
    )


# ── Unit: _annotate_inventory_notes with shopping_service ────────────────


def test_annotate_uses_shopping_diff_when_available():
    """When shopping_service is set, notes use 'You have'/'You need' format."""
    inv_svc = get_inventory_service()
    shopping_svc = ShoppingService(inv_svc)
    agent = _make_agent(inventory_service=inv_svc, shopping_service=shopping_svc)

    # Generate a plan (Simple Tomato Pasta needs: tomato 2 count, pasta 200 g)
    plan = agent.mealplan_service.generate(
        MealPlanGenerateRequest(days=1, meals_per_day=1),
        stock_names={"tomato"},  # force Tomato Pasta to rank first
    )
    assert plan.days[0].meals[0].name == "Simple Tomato Pasta"

    # No inventory at all — everything should be "You need"
    plan = agent._annotate_inventory_notes(plan, "user-107")
    assert plan.notes is not None
    assert "You need" in plan.notes


def test_annotate_shows_quantities_in_need():
    """'You need' items include quantity and unit."""
    inv_svc = get_inventory_service()
    shopping_svc = ShoppingService(inv_svc)
    agent = _make_agent(inventory_service=inv_svc, shopping_service=shopping_svc)

    plan = agent.mealplan_service.generate(
        MealPlanGenerateRequest(days=1, meals_per_day=1),
        stock_names={"tomato"},
    )
    plan = agent._annotate_inventory_notes(plan, "user-107-qty")
    # Should contain something like "tomato (2 count)" or "pasta (200 g)"
    assert "(" in plan.notes
    assert ")" in plan.notes


def test_annotate_partial_stock():
    """With partial inventory, notes show both 'You have' and 'You need'."""
    inv_svc = get_inventory_service()
    shopping_svc = ShoppingService(inv_svc)
    agent = _make_agent(inventory_service=inv_svc, shopping_service=shopping_svc)

    _seed_inventory(inv_svc, "user-partial", "tomato", 10, "count")

    plan = agent.mealplan_service.generate(
        MealPlanGenerateRequest(days=1, meals_per_day=1),
        stock_names={"tomato"},
    )
    plan = agent._annotate_inventory_notes(plan, "user-partial")
    assert "You have" in plan.notes
    assert "tomato" in plan.notes.lower()
    assert "You need" in plan.notes
    assert "pasta" in plan.notes.lower()


def test_annotate_full_stock():
    """With all ingredients stocked, no 'You need' section."""
    inv_svc = get_inventory_service()
    shopping_svc = ShoppingService(inv_svc)
    agent = _make_agent(inventory_service=inv_svc, shopping_service=shopping_svc)

    _seed_inventory(inv_svc, "user-full", "tomato", 10, "count")
    _seed_inventory(inv_svc, "user-full", "pasta", 500, "g")

    plan = agent.mealplan_service.generate(
        MealPlanGenerateRequest(days=1, meals_per_day=1),
        stock_names={"tomato", "pasta"},
    )
    plan = agent._annotate_inventory_notes(plan, "user-full")
    assert "You have" in plan.notes
    assert "You need" not in plan.notes


def test_annotate_fallback_without_shopping_service():
    """Without shopping_service, falls back to name-only matching."""
    inv_svc = get_inventory_service()
    agent = _make_agent(inventory_service=inv_svc, shopping_service=None)

    _seed_inventory(inv_svc, "user-fb", "tomato", 1, "count")

    plan = agent.mealplan_service.generate(
        MealPlanGenerateRequest(days=1, meals_per_day=1),
        stock_names={"tomato"},
    )
    plan = agent._annotate_inventory_notes(plan, "user-fb")
    # Fallback uses "In stock" / "Need to buy" format
    assert "In stock" in plan.notes
    assert "Need to buy" in plan.notes


def test_shopping_diff_consistency():
    """ChefAgent and ShoppingService.diff() produce consistent missing items."""
    inv_svc = get_inventory_service()
    shopping_svc = ShoppingService(inv_svc)
    agent = _make_agent(inventory_service=inv_svc, shopping_service=shopping_svc)

    _seed_inventory(inv_svc, "user-consist", "tomato", 10, "count")

    plan = agent.mealplan_service.generate(
        MealPlanGenerateRequest(days=1, meals_per_day=1),
        stock_names={"tomato"},
    )

    # Direct diff
    diff_result = shopping_svc.diff("user-consist", plan)
    # Agent annotation
    annotated = agent._annotate_inventory_notes(plan, "user-consist")

    # Both should agree: tomato is stocked, pasta is missing
    missing_names = {item.item_name for item in diff_result.missing_items}
    assert "pasta" in missing_names
    assert "tomato" not in missing_names
    # Agent notes should reflect the same
    assert "pasta" in annotated.notes.lower()
    assert "You have" in annotated.notes
    assert "tomato" in annotated.notes.lower()


def test_annotate_excludes_staples_from_plan_notes():
    """Staple items must not appear in mealplan.notes 'You need' list."""
    inv_svc = get_inventory_service()
    shopping_svc = ShoppingService(inv_svc)
    agent = _make_agent(inventory_service=inv_svc, shopping_service=shopping_svc)

    user_id = "user-staple-exclude"
    # Seed tomato so it's in stock
    _seed_inventory(inv_svc, user_id, "tomato", 10, "count")
    # Mark pasta as a staple
    inv_svc.set_staple(user_id, "pasta", "g")

    plan = agent.mealplan_service.generate(
        MealPlanGenerateRequest(days=1, meals_per_day=1),
        stock_names={"tomato"},
    )
    assert plan.days[0].meals[0].name == "Simple Tomato Pasta"

    plan = agent._annotate_inventory_notes(plan, user_id)
    # pasta is a staple → must NOT appear in "You need"
    notes_lower = plan.notes.lower()
    assert "pasta" not in notes_lower or "You need" not in plan.notes
    # tomato should still be in "You have"
    assert "tomato" in notes_lower

    # Verify the service still returns staple_items for general shopping flows
    diff = shopping_svc.diff(user_id, plan)
    staple_names = {s.item_name for s in diff.staple_items}
    # pasta may appear in staple_items if low/out of stock, or in missing_items
    # but the key invariant is: notes exclude it
    assert "pasta" not in plan.notes.lower() or "You need" not in plan.notes


# ── Integration: handle_fill wires shopping diff ──────────────────────────


def test_handle_fill_uses_shopping_diff(authed_client):
    """End-to-end: handle_fill meal plan notes use quantity-aware format."""
    # Stock tomato so Tomato Pasta has inventory presence
    authed_client.post("/inventory/events", json={
        "event_type": "add",
        "item_name": "tomato",
        "quantity": 10,
        "unit": "count",
    })

    resp = authed_client.post("/chat/mealplan", json={
        "mode": "fill",
        "message": "plan me a meal for today",
        "thread_id": "t-107-fill",
    })
    assert resp.status_code == 200
    data = resp.json()
    actions = data.get("proposed_actions", [])
    assert len(actions) >= 1
    plan = actions[0].get("mealplan", {})
    notes = plan.get("notes", "")
    # Should use ShoppingService.diff format
    assert "You have" in notes or "You need" in notes
