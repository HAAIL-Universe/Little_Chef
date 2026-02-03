def test_chat_prefs_propose_confirm_flow(authed_client):
    # propose
    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "set servings 4 meals per day 2"},
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
        json={"proposal_id": proposal_id, "confirm": True},
    )
    assert resp.status_code == 200
    assert resp.json()["applied"] is True

    # prefs reflect change
    resp = authed_client.get("/prefs")
    assert resp.status_code == 200
    prefs = resp.json()
    assert prefs["servings"] == 4
    assert prefs["meals_per_day"] == 2
