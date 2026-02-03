def test_prefs_defaults_and_upsert(authed_client):
    # defaults
    resp = authed_client.get("/prefs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["servings"] >= 1
    assert data["meals_per_day"] >= 1

    # update
    new_prefs = {
        "prefs": {
            "allergies": ["peanuts"],
            "dislikes": ["mushrooms"],
            "cuisine_likes": ["thai"],
            "servings": 3,
            "meals_per_day": 2,
            "notes": "spicy ok",
        }
    }
    resp = authed_client.put("/prefs", json=new_prefs)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["servings"] == 3
    assert updated["meals_per_day"] == 2
    assert updated["allergies"] == ["peanuts"]

    # confirm persisted
    resp = authed_client.get("/prefs")
    assert resp.status_code == 200
    again = resp.json()
    assert again["servings"] == 3
    assert again["meals_per_day"] == 2
