def test_auth_me_unauthorized_shape(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
    body = resp.json()
    assert "detail" not in body
    assert body["error"] == "unauthorized"
    assert "message" in body
