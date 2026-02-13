"""Phase 10.6 — Inventory-aware scoring and ranking

Tests that:
- PLAN meal selection prefers recipes with higher inventory completion %
- MATCH ranking is deterministic (already tested in test_match_decision_mode)
- Scoring model: completion_pct = have_count / total_count (name-only)
- Ranking remains deterministic (no random when stock_names provided)
"""

import pytest

from app.services.inventory_service import get_inventory_service
from app.services.recipe_service import get_recipe_service
from app.services.mealplan_service import MealPlanService, _INGREDIENTS_BY_RECIPE
from app.schemas import MealPlanGenerateRequest, IngredientLine


@pytest.fixture(autouse=True)
def _reset_inventory_cache(_clear_db_env):
    """Ensure inventory service uses in-memory repo after _clear_db_env sets DATABASE_URL=''."""
    get_inventory_service.cache_clear()
    yield
    get_inventory_service.cache_clear()


# ── Unit: MealPlanService.generate() with stock_names ────────────────────

def test_generate_prefers_stocked_recipe():
    """When inventory has ingredients for a recipe, that recipe appears first."""
    svc = MealPlanService()
    req = MealPlanGenerateRequest(days=1, meals_per_day=1)
    # Simple Tomato Pasta needs: tomato, pasta
    stock_names = {"tomato", "pasta"}
    plan = svc.generate(req, stock_names=stock_names)
    assert len(plan.days) == 1
    assert len(plan.days[0].meals) == 1
    # Tomato Pasta should rank first (100% match, vs 0% for others)
    assert plan.days[0].meals[0].name == "Simple Tomato Pasta"


def test_generate_without_stock_names_uses_shuffle():
    """Without stock_names, generate uses random seeded shuffle (existing behavior)."""
    svc = MealPlanService()
    req = MealPlanGenerateRequest(days=1, meals_per_day=3)
    plan = svc.generate(req, stock_names=None)
    # Should produce a valid plan with 3 meals
    assert len(plan.days) == 1
    assert len(plan.days[0].meals) == 3


def test_generate_ranking_is_deterministic():
    """Same stock_names produces same ordering across calls."""
    svc = MealPlanService()
    req = MealPlanGenerateRequest(days=1, meals_per_day=3)
    stock_names = {"tomato", "pasta"}

    plan1 = svc.generate(req, stock_names=stock_names)
    plan2 = svc.generate(req, stock_names=stock_names)

    names1 = [m.name for m in plan1.days[0].meals]
    names2 = [m.name for m in plan2.days[0].meals]
    assert names1 == names2


def test_generate_partial_stock_ranks_correctly():
    """Partial inventory completion ranks higher than zero."""
    svc = MealPlanService()
    req = MealPlanGenerateRequest(days=1, meals_per_day=3)
    # Only 'tomato' — Simple Tomato Pasta gets 50%, others get 0%
    stock_names = {"tomato"}

    plan = svc.generate(req, stock_names=stock_names)
    assert plan.days[0].meals[0].name == "Simple Tomato Pasta"


def test_generate_adventurous_diverges_from_inventory_first_without_expiry():
    """Adventurous mode should not open with the top inventory-ranked recipe."""
    svc = MealPlanService()
    req = MealPlanGenerateRequest(days=1, meals_per_day=1)
    stock_names = {"tomato", "pasta"}

    inventory_plan = svc.generate(
        req,
        stock_names=stock_names,
        planning_mode="inventory_first",
    )
    adventurous_plan = svc.generate(
        req,
        stock_names=stock_names,
        planning_mode="adventurous",
        expiry_priority=None,
    )

    inventory_first_meal = inventory_plan.days[0].meals[0].name
    adventurous_first_meal = adventurous_plan.days[0].meals[0].name

    assert inventory_first_meal == "Simple Tomato Pasta"
    assert adventurous_first_meal != inventory_first_meal


def test_generate_small_catalog_modes_diverge_visibly():
    """With only built-ins available, modes should still produce different ordering."""
    svc = MealPlanService()
    req = MealPlanGenerateRequest(days=2, meals_per_day=3)
    stock_names: set[str] = set()

    inventory_plan = svc.generate(req, stock_names=stock_names, planning_mode="inventory_first")
    balanced_plan = svc.generate(req, stock_names=stock_names, planning_mode="balanced")
    adventurous_plan = svc.generate(req, stock_names=stock_names, planning_mode="adventurous")

    inv_names = [m.name for d in inventory_plan.days for m in d.meals]
    bal_names = [m.name for d in balanced_plan.days for m in d.meals]
    adv_names = [m.name for d in adventurous_plan.days for m in d.meals]

    assert inv_names != bal_names
    assert inv_names != adv_names


def test_generate_empty_stock_ranks_alphabetically():
    """With empty inventory, recipes are sorted alphabetically (deterministic)."""
    svc = MealPlanService()
    req = MealPlanGenerateRequest(days=1, meals_per_day=3)
    stock_names: set[str] = set()

    plan = svc.generate(req, stock_names=stock_names)
    names = [m.name for m in plan.days[0].meals]
    # All at 0% → sorted by title alphabetically
    assert names == sorted(names, key=str.lower)


# ── Integration: PLAN via POST /chat/mealplan ────────────────────────────

def test_plan_prefers_stocked_recipes_via_api(authed_client):
    """Meal plan generated via API prefers recipes matching inventory."""
    # Seed inventory with Simple Tomato Pasta ingredients
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "tomato", "quantity": 5, "unit": "count",
    })
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "pasta", "quantity": 500, "unit": "g",
    })

    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan 1 meal", "thread_id": "t-rank-1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # The plan should list Simple Tomato Pasta first (100% match)
    actions = body.get("proposed_actions", [])
    assert len(actions) > 0
    plan = actions[0].get("mealplan", {})
    first_meal = plan["days"][0]["meals"][0]
    assert first_meal["name"] == "Simple Tomato Pasta"


def test_plan_without_inventory_still_works(authed_client):
    """Plan generation works without any inventory events."""
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan meals", "thread_id": "t-rank-2"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    assert body["proposal_id"] is not None
