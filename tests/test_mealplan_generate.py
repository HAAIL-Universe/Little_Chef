def test_mealplan_generate_requires_auth(client):
    resp = client.post("/mealplan/generate", json={"days": 1, "meals_per_day": 2})
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"] == "unauthorized"
    assert "detail" not in body


def test_mealplan_generate_happy_path(authed_client):
    resp = authed_client.post("/mealplan/generate", json={"days": 2, "meals_per_day": 2})
    assert resp.status_code == 200
    plan = resp.json()
    assert plan["plan_id"]
    assert plan["created_at"]
    assert len(plan["days"]) == 2
    for day in plan["days"]:
        assert "day_index" in day
        assert len(day["meals"]) == 2
        for meal in day["meals"]:
            source = meal["source"]
            assert source["source_type"] == "built_in"
            assert source["built_in_recipe_id"]
            assert source["book_id"] is None
            assert source["file_id"] is None
            assert "excerpt" in source
            citations = meal.get("citations", [])
            assert isinstance(citations, list)
            assert len(citations) >= 1
            first = citations[0]
            assert first["source_type"] == "built_in"
            assert first["built_in_recipe_id"]
            assert meal["ingredients"]
            for ing in meal["ingredients"]:
                assert ing["item_name"]
                assert ing["quantity"] >= 0
                assert ing["unit"] in ("g", "ml", "count")
