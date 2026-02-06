def test_chat_inventory_ask_low_stock(authed_client):
    authed_client.post("/inventory/events", json={"event_type": "add", "item_name": "rice", "quantity": 50, "unit": "g"})
    resp = authed_client.post("/chat", json={"mode": "ask", "message": "what am I low on?", "thread_id": "t-chat-low"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is False
    assert "rice" in body["reply_text"].lower()
