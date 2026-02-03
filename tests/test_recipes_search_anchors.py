import io


def test_user_library_results_include_anchor(authed_client):
    content = b"# Apple Pie\nSweet apple pie with cinnamon."
    files = {"file": ("apple.md", io.BytesIO(content), "text/markdown")}
    resp = authed_client.post("/recipes/books", files=files, data={"title": "Apple Book"})
    assert resp.status_code == 201
    book_id = resp.json()["book_id"]

    resp = authed_client.post("/recipes/search", json={"query": "apple", "max_results": 5})
    assert resp.status_code == 200
    results = [r for r in resp.json()["results"] if r["source_type"] == "user_library"]
    assert results, "Expected at least one user_library result"
    first = results[0]
    assert first["book_id"] == book_id
    assert first["file_id"] == book_id
    assert first["excerpt"]


def test_pdf_without_text_does_not_return_user_library_results(authed_client):
    content = b"%PDF-1.4 fake pdf\nuniqueonly content"
    files = {"file": ("notes.pdf", io.BytesIO(content), "application/pdf")}
    resp = authed_client.post("/recipes/books", files=files, data={"title": "PDF Book"})
    assert resp.status_code == 201

    resp = authed_client.post("/recipes/search", json={"query": "uniqueonly", "max_results": 5})
    assert resp.status_code == 200
    results = resp.json()["results"]
    user_results = [r for r in results if r["source_type"] == "user_library"]
    assert user_results == []
