import datetime


def _make_plan(ingredients):
    return {
        "plan_id": "plan-1",
        "created_at": "2026-02-03T00:00:00Z",
        "notes": "",
        "days": [
            {
                "day_index": 1,
                "meals": [
                    {
                        "name": "Test Meal",
                        "slot": "dinner",
                        "ingredients": ingredients,
                        "instructions": [],
                        "source": {
                            "source_type": "built_in",
                            "built_in_recipe_id": "builtin_1",
                            "file_id": None,
                            "book_id": None,
                            "excerpt": None,
                        },
                    }
                ],
            }
        ],
    }


def test_shopping_diff_requires_auth(client):
    plan = _make_plan(
        [
            {"item_name": "eggs", "quantity": 4, "unit": "count", "optional": False},
        ]
    )
    resp = client.post("/shopping/diff", json={"plan": plan})
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"] == "unauthorized"
    assert "detail" not in body


def test_shopping_diff_computes_missing_only(authed_client):
    # Existing inventory: 2 eggs, 200 ml milk
    authed_client.post(
        "/inventory/events",
        json={
            "event_type": "add",
            "item_name": "Eggs",
            "quantity": 2,
            "unit": "count",
            "note": "",
            "source": "ui",
        },
    )
    authed_client.post(
        "/inventory/events",
        json={
            "event_type": "add",
            "item_name": "milk",
            "quantity": 200,
            "unit": "ml",
            "note": "",
            "source": "ui",
        },
    )

    plan = _make_plan(
        [
            {"item_name": "Eggs", "quantity": 4, "unit": "count", "optional": False},
            {"item_name": "Milk", "quantity": 500, "unit": "ml", "optional": False},
        ]
    )
    resp = authed_client.post("/shopping/diff", json={"plan": plan})
    assert resp.status_code == 200
    missing = {item["item_name"]: item for item in resp.json()["missing_items"]}
    assert missing["eggs"]["quantity"] == 2
    assert missing["eggs"]["unit"] == "count"
    assert missing["milk"]["quantity"] == 300
    assert missing["milk"]["unit"] == "ml"
