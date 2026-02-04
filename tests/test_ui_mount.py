from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_root_served_or_not_ready():
    resp = client.get("/")
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        assert "text/html" in resp.headers.get("content-type", "")
        html = resp.text
        assert "duet-shell" in html
        assert "duet-assistant-bubble" in html
        assert "duet-user-bubble" in html
        assert "duet-composer" in html
    else:
        body = resp.json()
        assert body["error"] == "ui_not_built"


def test_static_missing_returns_404():
    resp = client.get("/static/does-not-exist.css")
    assert resp.status_code == 404
