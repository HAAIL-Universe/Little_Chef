def test_chat_inventory_fill_propose_confirm(authed_client):
    thread = "t-inv-fill"
    resp = authed_client.post("/chat", json={"mode": "fill", "message": "bought 2 eggs", "thread_id": thread, "location": "pantry"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    proposal_id = body["proposal_id"]
    action = body["proposed_actions"][0]
    assert action["action_type"] == "create_inventory_event"
    assert action["event"]["item_name"]

    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert resp.status_code == 200
    assert resp.json()["applied"] is True
    assert resp.json()["applied_event_ids"]
