def test_inventory_events_create_and_list(authed_client):
    body = {
        "event_type": "add",
        "item_name": "eggs",
        "quantity": 2,
        "unit": "count",
    }
    resp = authed_client.post("/inventory/events", json=body)
    assert resp.status_code == 201
    created = resp.json()
    assert created["event_id"]
    assert created["event_type"] == "add"

    resp = authed_client.get("/inventory/events")
    assert resp.status_code == 200
    events = resp.json()["events"]
    assert len(events) == 1
    assert events[0]["event_id"] == created["event_id"]
