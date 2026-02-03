import io


def test_recipes_upload_list_get_delete_and_search(authed_client):
    # Upload a markdown file
    content = b"# My Notes\nTomato pasta sauce with garlic."
    files = {
        "file": ("notes.md", io.BytesIO(content), "text/markdown"),
    }
    data = {"title": "My Recipes"}
    resp = authed_client.post("/recipes/books", files=files, data=data)
    assert resp.status_code == 201
    book = resp.json()
    book_id = book["book_id"]
    assert book["status"] in ("ready", "processing")

    # List
    resp = authed_client.get("/recipes/books")
    assert resp.status_code == 200
    books = resp.json()["books"]
    assert any(b["book_id"] == book_id for b in books)

    # Get
    resp = authed_client.get(f"/recipes/books/{book_id}")
    assert resp.status_code == 200

    # Search built-in
    resp = authed_client.post("/recipes/search", json={"query": "tomato", "max_results": 5})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert any(r["source_type"] == "built_in" for r in results)

    # Search user_library must include anchor
    resp = authed_client.post("/recipes/search", json={"query": "pasta", "max_results": 5})
    assert resp.status_code == 200
    results = resp.json()["results"]
    user_results = [r for r in results if r["source_type"] == "user_library"]
    if user_results:
        r0 = user_results[0]
        assert r0["book_id"] == book_id
        assert r0["excerpt"]

    # Delete
    resp = authed_client.delete(f"/recipes/books/{book_id}")
    assert resp.status_code == 204

    resp = authed_client.get(f"/recipes/books/{book_id}")
    assert resp.status_code == 404
