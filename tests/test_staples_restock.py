"""Phase 12 — Restock + staples intelligence tests.

12.1: Always-keep-stocked toggle per item (staples API)
12.2: Low/empty detection improvements (explainable reasons, staple awareness)
12.3: Shopping list refinement (staple_items in shopping diff, distinct reasons)
"""
import pytest


# ---------------------------------------------------------------------------
# 12.1 — Staples API
# ---------------------------------------------------------------------------


def test_staples_list_empty_initially(authed_client):
    resp = authed_client.get("/inventory/staples")
    assert resp.status_code == 200
    assert resp.json()["staples"] == []


def test_staple_set_and_list(authed_client):
    resp = authed_client.post(
        "/inventory/staples",
        json={"item_name": "Milk", "unit": "ml"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_staple"] is True
    assert body["item_name"] == "Milk"
    assert body["unit"] == "ml"

    # List should now contain it
    resp = authed_client.get("/inventory/staples")
    staples = resp.json()["staples"]
    assert len(staples) == 1
    assert staples[0]["item_name"] == "milk"  # normalized


def test_staple_remove(authed_client):
    authed_client.post("/inventory/staples", json={"item_name": "Eggs", "unit": "count"})

    resp = authed_client.request(
        "DELETE",
        "/inventory/staples",
        json={"item_name": "Eggs", "unit": "count"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_staple"] is False

    # List should be empty
    resp = authed_client.get("/inventory/staples")
    assert resp.json()["staples"] == []


def test_staple_idempotent_set(authed_client):
    """Setting the same staple twice should not duplicate."""
    authed_client.post("/inventory/staples", json={"item_name": "Butter", "unit": "g"})
    authed_client.post("/inventory/staples", json={"item_name": "Butter", "unit": "g"})

    resp = authed_client.get("/inventory/staples")
    staples = resp.json()["staples"]
    assert len(staples) == 1


def test_staple_requires_auth(client):
    resp = client.get("/inventory/staples")
    assert resp.status_code == 401


def test_staple_multiple_items(authed_client):
    authed_client.post("/inventory/staples", json={"item_name": "Milk", "unit": "ml"})
    authed_client.post("/inventory/staples", json={"item_name": "Eggs", "unit": "count"})
    authed_client.post("/inventory/staples", json={"item_name": "Butter", "unit": "g"})

    resp = authed_client.get("/inventory/staples")
    staples = resp.json()["staples"]
    assert len(staples) == 3
    names = {s["item_name"] for s in staples}
    assert names == {"milk", "eggs", "butter"}


# ---------------------------------------------------------------------------
# 12.2 — Low/empty detection improvements
# ---------------------------------------------------------------------------


def test_low_stock_reason_below_threshold(authed_client):
    """Non-staple low stock items should have 'below threshold' reason."""
    authed_client.post(
        "/inventory/events",
        json={"event_type": "add", "item_name": "Rice", "quantity": 50, "unit": "g"},
    )
    resp = authed_client.get("/inventory/low-stock")
    assert resp.status_code == 200
    items = resp.json()["items"]
    rice = [i for i in items if i["item_name"] == "rice"]
    assert len(rice) == 1
    assert rice[0]["reason"] == "below threshold"
    assert rice[0]["is_staple"] is False


def test_low_stock_staple_reason(authed_client):
    """Staple items below threshold should have staple-specific reason."""
    authed_client.post("/inventory/staples", json={"item_name": "Milk", "unit": "ml"})
    authed_client.post(
        "/inventory/events",
        json={"event_type": "add", "item_name": "Milk", "quantity": 50, "unit": "ml"},
    )
    resp = authed_client.get("/inventory/low-stock")
    items = resp.json()["items"]
    milk = [i for i in items if i["item_name"] == "milk"]
    assert len(milk) == 1
    assert "staple" in milk[0]["reason"]
    assert milk[0]["is_staple"] is True


def test_low_stock_staple_never_added(authed_client):
    """Staple with zero inventory (never added) should appear in low-stock."""
    authed_client.post("/inventory/staples", json={"item_name": "Butter", "unit": "g"})

    resp = authed_client.get("/inventory/low-stock")
    items = resp.json()["items"]
    butter = [i for i in items if i["item_name"] == "butter"]
    assert len(butter) == 1
    assert butter[0]["quantity"] == 0
    assert "staple" in butter[0]["reason"]
    assert "out of stock" in butter[0]["reason"]
    assert butter[0]["is_staple"] is True


def test_low_stock_staple_fully_stocked_excluded(authed_client):
    """Staple items above threshold should NOT appear in low-stock."""
    authed_client.post("/inventory/staples", json={"item_name": "Milk", "unit": "ml"})
    authed_client.post(
        "/inventory/events",
        json={"event_type": "add", "item_name": "Milk", "quantity": 500, "unit": "ml"},
    )
    resp = authed_client.get("/inventory/low-stock")
    items = resp.json()["items"]
    milk = [i for i in items if i["item_name"] == "milk"]
    assert len(milk) == 0, f"Milk at 500ml should not be low-stock, got {milk}"


def test_low_stock_reasons_explainable(authed_client):
    """All low-stock items should have a non-empty reason."""
    authed_client.post("/inventory/staples", json={"item_name": "Eggs", "unit": "count"})
    authed_client.post(
        "/inventory/events",
        json={"event_type": "add", "item_name": "Rice", "quantity": 50, "unit": "g"},
    )
    resp = authed_client.get("/inventory/low-stock")
    for item in resp.json()["items"]:
        assert item["reason"], f"Item {item['item_name']} has empty reason"


# ---------------------------------------------------------------------------
# 12.3 — Shopping list refinement
# ---------------------------------------------------------------------------


def _make_plan(authed_client):
    """Generate a 1-day plan for shopping diff tests."""
    resp = authed_client.post("/mealplan/generate", json={"days": 1, "meals_per_day": 2})
    assert resp.status_code == 200
    return resp.json()


def test_shopping_diff_plan_items_have_needed_reason(authed_client):
    """Plan-based missing items should have 'needed for plan' reason."""
    plan = _make_plan(authed_client)
    resp = authed_client.post("/shopping/diff", json={"plan": plan})
    assert resp.status_code == 200
    for item in resp.json()["missing_items"]:
        assert item["reason"] == "needed for plan"


def test_shopping_diff_staple_items_separate(authed_client):
    """Staple items NOT in the plan should appear in staple_items."""
    # Use an item that won't be in a plan (flour is not a built-in recipe ingredient)
    authed_client.post("/inventory/staples", json={"item_name": "Flour", "unit": "g"})
    plan = _make_plan(authed_client)
    resp = authed_client.post("/shopping/diff", json={"plan": plan})
    body = resp.json()
    assert "staple_items" in body
    flour_in_staples = [i for i in body["staple_items"] if i["item_name"] == "flour"]
    assert len(flour_in_staples) == 1
    assert "auto-added" in flour_in_staples[0]["reason"]
    assert "staple" in flour_in_staples[0]["reason"]


def test_shopping_diff_staple_not_duplicated_with_plan(authed_client):
    """If a staple item is already needed for the plan, it should only appear in missing_items."""
    # Get plan ingredients so we can mark one as staple
    plan = _make_plan(authed_client)
    plan_ingredients = [
        (ing["item_name"], ing["unit"])
        for day in plan["days"]
        for meal in day["meals"]
        for ing in meal["ingredients"]
    ]
    assert plan_ingredients, "Plan should have ingredients"

    # Mark first plan ingredient as a staple
    name, unit = plan_ingredients[0]
    authed_client.post("/inventory/staples", json={"item_name": name, "unit": unit})

    resp = authed_client.post("/shopping/diff", json={"plan": plan})
    body = resp.json()

    # The item should be in missing_items (needed for plan) not staple_items
    staple_item_names = {i["item_name"].lower() for i in body["staple_items"]}
    assert name.lower() not in staple_item_names, \
        f"{name} should not be in staple_items when already in plan's missing_items"

    # It should still be in missing_items
    missing_names = {i["item_name"].lower() for i in body["missing_items"]}
    assert name.lower() in missing_names


def test_shopping_diff_staple_fully_stocked_excluded(authed_client):
    """Staple items above threshold should not appear in staple_items."""
    authed_client.post("/inventory/staples", json={"item_name": "Flour", "unit": "g"})
    authed_client.post(
        "/inventory/events",
        json={"event_type": "add", "item_name": "Flour", "quantity": 500, "unit": "g"},
    )
    plan = _make_plan(authed_client)
    resp = authed_client.post("/shopping/diff", json={"plan": plan})
    body = resp.json()
    flour = [i for i in body["staple_items"] if i["item_name"] == "flour"]
    assert len(flour) == 0


def test_shopping_diff_multiple_staples(authed_client):
    """Multiple low/out-of-stock staples NOT in the plan should all appear."""
    # Use items not in built-in recipes: flour, sugar, olive oil
    authed_client.post("/inventory/staples", json={"item_name": "Flour", "unit": "g"})
    authed_client.post("/inventory/staples", json={"item_name": "Sugar", "unit": "g"})
    authed_client.post("/inventory/staples", json={"item_name": "Olive Oil", "unit": "ml"})

    plan = _make_plan(authed_client)
    resp = authed_client.post("/shopping/diff", json={"plan": plan})
    body = resp.json()
    staple_names = {i["item_name"] for i in body["staple_items"]}
    assert "flour" in staple_names
    assert "sugar" in staple_names
    assert "olive oil" in staple_names
