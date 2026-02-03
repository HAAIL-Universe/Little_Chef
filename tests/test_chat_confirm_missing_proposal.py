def test_chat_confirm_missing_proposal_returns_400(authed_client):
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": "missing-id", "confirm": True},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert "detail" not in body
    assert body["error"] == "bad_request"
