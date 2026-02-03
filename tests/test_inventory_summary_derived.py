def test_inventory_summary_and_clamp(authed_client):
    # add 3 eggs
    authed_client.post("/inventory/events", json={"event_type": "add", "item_name": "eggs", "quantity": 3, "unit": "count"})
    # consume 4 eggs -> should clamp to 0 approx true
    authed_client.post("/inventory/events", json={"event_type": "consume_cooked", "item_name": "eggs", "quantity": 4, "unit": "count"})

    resp = authed_client.get("/inventory/summary")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    item = items[0]
    assert item["item_name"] == "eggs"
    assert item["quantity"] == 0
    assert item["approx"] is True
