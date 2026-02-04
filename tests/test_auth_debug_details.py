import os
from fastapi.testclient import TestClient

from app.main import create_app


def _make_client():
    app = create_app()
    return TestClient(app)


def test_auth_me_debug_details_when_enabled(monkeypatch):
    monkeypatch.setenv("LC_DEBUG_AUTH", "1")
    with _make_client() as client:
        resp = client.get("/auth/me", headers={"Authorization": "Bearer part1 part2"})
    assert resp.status_code == 401
    body = resp.json()
    # Parsing should succeed; message now comes from JWT verification path, not parsing
    assert body["message"] != "Invalid Authorization header"
    details = body.get("details")
    if details is not None:
        assert isinstance(details, dict)
        assert details.get("parts_count") == 3
        assert details.get("scheme_lower") == "bearer"
        assert details.get("has_newline") is False
        detail_str = str(details)
        assert "part1" not in detail_str and "part2" not in detail_str


def test_auth_me_debug_details_disabled(monkeypatch):
    monkeypatch.delenv("LC_DEBUG_AUTH", raising=False)
    with _make_client() as client:
        resp = client.get("/auth/me", headers={"Authorization": "Bearer bad token"})
    assert resp.status_code == 401
    body = resp.json()
    # With debug off, details stay null; message comes from JWT verification
    assert body.get("details") is None
    assert isinstance(body.get("message"), str)


def test_auth_me_accepts_space_split_token(monkeypatch):
    # Debug on to allow details if later stages fail; parsing should not fail on split token
    monkeypatch.setenv("LC_DEBUG_AUTH", "1")
    # This token is nonsense but intentionally space-split; parser should stitch and forward to verifier
    header = "Bearer eyJ partA partB partC"
    with _make_client() as client:
        resp = client.get("/auth/me", headers={"Authorization": header})
    assert resp.status_code == 401
    # Parsing should have succeeded; message should no longer be "Invalid Authorization header"
    assert resp.json()["message"] != "Invalid Authorization header"


def test_auth_me_invalid_scheme_debug_details(monkeypatch):
    monkeypatch.setenv("LC_DEBUG_AUTH", "1")
    with _make_client() as client:
        resp = client.get("/auth/me", headers={"Authorization": "Token abc def"})
    assert resp.status_code == 401
    body = resp.json()
    assert body["message"] == "Invalid Authorization header"
    details = body.get("details")
    assert isinstance(details, dict)
    assert details.get("parts_count") == 3
    assert details.get("scheme_lower") == "token"
