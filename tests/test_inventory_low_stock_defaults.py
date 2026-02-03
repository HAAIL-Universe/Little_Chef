def test_inventory_low_stock_defaults(authed_client):
    authed_client.post("/inventory/events", json={"event_type": "add", "item_name": "milk", "quantity": 50, "unit": "ml"})
    resp = authed_client.get("/inventory/low-stock")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["item_name"] == "milk" for i in items)
