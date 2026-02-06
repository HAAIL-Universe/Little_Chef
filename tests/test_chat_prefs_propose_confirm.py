def test_chat_prefs_propose_confirm_flow(authed_client):
    thread = "t-prefs-confirm"
    # propose
    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "set servings 4 meals per day 2", "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    assert body["proposal_id"]
    assert body["proposed_actions"]
    action = body["proposed_actions"][0]
    assert action["action_type"] == "upsert_prefs"
    assert action["prefs"]["servings"] == 4
    assert action["prefs"]["meals_per_day"] == 2

    # confirm
    proposal_id = body["proposal_id"]
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert resp.status_code == 200
    assert resp.json()["applied"] is True

    # prefs reflect change
    resp = authed_client.get("/prefs")
    assert resp.status_code == 200
    prefs = resp.json()
    assert prefs["servings"] == 4
    assert prefs["meals_per_day"] == 2


def test_fill_word_servings_detected(authed_client):
    thread = "t-prefs-word"
    paragraph = (
        "Okay, so for allergies: I'm allergic to peanuts and I can't have shellfish. "
        "I like chicken, salmon, rice, pasta, potatoes, tomatoes, spinach, peppers, cheese, "
        "and anything spicy. I don't like mushrooms, olives, blue cheese, or really sweet sauces. "
        "It's for two servings, and I want meals for Monday to Friday this week."
    )
    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": paragraph, "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    assert body["proposed_actions"]
    action = body["proposed_actions"][0]
    assert action["action_type"] == "upsert_prefs"
    assert action["prefs"]["servings"] == 2
    prefs = action["prefs"]
    assert set(prefs["allergies"]) == {"peanuts", "shellfish"}
    assert set(prefs["dislikes"]) >= {"mushrooms", "olives", "blue cheese", "really sweet sauces"}
    assert set(prefs["cuisine_likes"]) >= {"chicken", "salmon", "rice", "pasta", "potatoes", "tomatoes", "spinach", "peppers", "cheese", "anything spicy"}
