def test_recipes_books_unauthorized_shape(client):
    resp = client.get("/recipes/books")
    assert resp.status_code == 401
    body = resp.json()
    assert "detail" not in body
    assert body["error"] == "unauthorized"
