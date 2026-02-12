"""Phase 11.2 — Aggregated shopping list from multi-day plan

Tests that:
- ShoppingService.diff() aggregates ingredients across all days of a multi-day plan
- Inventory deduction is quantity-aware: partial stock reduces the needed amount
- Items fully in stock are excluded from missing list
- Multi-day plan annotations show correct "You have"/"You need" summary
- POST /shopping/diff works with multi-day MealPlanResponse
"""

import pytest
from datetime import datetime, timezone

from app.services.inventory_service import get_inventory_service
from app.services.shopping_service import ShoppingService
from app.services.mealplan_service import MealPlanService
from app.services.chef_agent import ChefAgent
from app.services.proposal_store import ProposalStore
from app.services.prefs_service import get_prefs_service
from app.schemas import (
    ChatRequest,
    MealPlanGenerateRequest,
    MealPlanResponse,
    MealPlanDay,
    PlannedMeal,
    IngredientLine,
    RecipeSource,
    InventoryEventCreateRequest,
    UserMe,
    UserPrefs,
)


@pytest.fixture(autouse=True)
def _reset_caches(_clear_db_env):
    get_inventory_service.cache_clear()
    get_prefs_service.cache_clear()
    yield
    get_inventory_service.cache_clear()
    get_prefs_service.cache_clear()


USER = UserMe(user_id="user-112", provider_subject="sub", email=None)


def _source():
    return RecipeSource(
        source_type="built_in", built_in_recipe_id="test",
        file_id=None, book_id=None, excerpt=None,
    )


def _plan_2_days() -> MealPlanResponse:
    """A 2-day plan: day 1 uses 200g pasta + 2 tomato; day 2 uses 200g pasta + 250g veggies."""
    return MealPlanResponse(
        plan_id="plan-112",
        created_at=datetime.now(timezone.utc).isoformat(),
        days=[
            MealPlanDay(day_index=1, meals=[
                PlannedMeal(
                    name="Tomato Pasta",
                    slot="dinner",
                    ingredients=[
                        IngredientLine(item_name="pasta", quantity=200.0, unit="g", optional=False),
                        IngredientLine(item_name="tomato", quantity=2.0, unit="count", optional=False),
                    ],
                    instructions=["Cook pasta. Add tomato."],
                    source=_source(), citations=[_source()],
                ),
            ]),
            MealPlanDay(day_index=2, meals=[
                PlannedMeal(
                    name="Veggie Pasta",
                    slot="dinner",
                    ingredients=[
                        IngredientLine(item_name="pasta", quantity=200.0, unit="g", optional=False),
                        IngredientLine(item_name="mixed veggies", quantity=250.0, unit="g", optional=False),
                    ],
                    instructions=["Cook pasta. Add veggies."],
                    source=_source(), citations=[_source()],
                ),
            ]),
        ],
        notes="",
    )


def test_aggregates_across_days_no_inventory():
    """With no inventory, all ingredients across both days are missing."""
    svc = ShoppingService(get_inventory_service())
    plan = _plan_2_days()

    result = svc.diff(USER.user_id, plan)
    items = {i.item_name: i for i in result.missing_items}

    # Pasta: 200g (day 1) + 200g (day 2) = 400g needed
    assert "pasta" in items
    assert items["pasta"].quantity == 400.0
    assert items["pasta"].unit == "g"

    # Tomato: 2 count
    assert "tomato" in items
    assert items["tomato"].quantity == 2.0

    # Veggies: 250g
    assert "mixed veggies" in items
    assert items["mixed veggies"].quantity == 250.0


def test_aggregates_with_partial_inventory():
    """Partial inventory reduces the needed quantity."""
    inv_svc = get_inventory_service()
    # Add 300g pasta (need 400g total across 2 days)
    inv_svc.create_event(USER.user_id, "sub", None, InventoryEventCreateRequest(
        event_type="add", item_name="pasta", quantity=300.0, unit="g",
    ))

    svc = ShoppingService(inv_svc)
    result = svc.diff(USER.user_id, _plan_2_days())
    items = {i.item_name: i for i in result.missing_items}

    # Need 400g - have 300g = 100g missing
    assert "pasta" in items
    assert items["pasta"].quantity == 100.0

    # Tomato and veggies still fully missing
    assert "tomato" in items
    assert "mixed veggies" in items


def test_fully_stocked_items_excluded():
    """Items with enough inventory are excluded from missing list."""
    inv_svc = get_inventory_service()
    # Add enough pasta for both days
    inv_svc.create_event(USER.user_id, "sub", None, InventoryEventCreateRequest(
        event_type="add", item_name="pasta", quantity=500.0, unit="g",
    ))
    # Add enough tomatoes
    inv_svc.create_event(USER.user_id, "sub", None, InventoryEventCreateRequest(
        event_type="add", item_name="tomato", quantity=5.0, unit="count",
    ))

    svc = ShoppingService(inv_svc)
    result = svc.diff(USER.user_id, _plan_2_days())
    items = {i.item_name: i for i in result.missing_items}

    # Pasta and tomato are fully stocked — not in missing
    assert "pasta" not in items
    assert "tomato" not in items

    # Mixed veggies still missing
    assert "mixed veggies" in items
    assert items["mixed veggies"].quantity == 250.0


def test_multiday_plan_annotations():
    """ChefAgent annotates multi-day plan with shopping diff summary."""
    inv_svc = get_inventory_service()
    # Add some pasta
    inv_svc.create_event(USER.user_id, "sub", None, InventoryEventCreateRequest(
        event_type="add", item_name="pasta", quantity=500.0, unit="g",
    ))

    svc = ShoppingService(inv_svc)
    agent = ChefAgent(
        mealplan_service=MealPlanService(),
        proposal_store=ProposalStore(),
        inventory_service=inv_svc,
        shopping_service=svc,
    )

    plan = _plan_2_days()
    annotated = agent._annotate_via_shopping_diff(plan, USER.user_id)

    # Notes should mention what we have and what we need
    assert "pasta" in annotated.notes.lower()
    assert "You have" in annotated.notes or "you have" in annotated.notes.lower()


def test_shopping_diff_api_multiday(authed_client):
    """POST /shopping/diff works with a multi-day plan body."""
    plan = _plan_2_days()
    resp = authed_client.post("/shopping/diff", json={"plan": plan.model_dump()})
    assert resp.status_code == 200
    body = resp.json()
    items = {i["item_name"]: i for i in body["missing_items"]}

    # All ingredients missing (no inventory for authed_client user)
    assert "pasta" in items
    assert items["pasta"]["quantity"] == 400.0
    assert "tomato" in items
    assert "mixed veggies" in items


def test_shopping_diff_multiday_via_mealplan_endpoint(authed_client):
    """Full flow: generate multi-day plan, then diff it."""
    # Generate a 3-day plan
    resp = authed_client.post("/chat/mealplan", json={
        "mode": "fill", "message": "plan 3 days of meals", "thread_id": "t-112-flow",
    })
    assert resp.status_code == 200
    plan = resp.json()["proposed_actions"][0]["mealplan"]
    assert len(plan["days"]) == 3

    # Diff the plan
    diff_resp = authed_client.post("/shopping/diff", json={"plan": plan})
    assert diff_resp.status_code == 200
    body = diff_resp.json()
    # With a 3-day plan, aggregated quantities should be > single day
    assert len(body["missing_items"]) > 0
