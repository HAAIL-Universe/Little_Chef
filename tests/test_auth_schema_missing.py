import os
import psycopg
from fastapi.testclient import TestClient

from app.main import create_app


def _make_client():
    app = create_app()
    return TestClient(app)


def test_auth_me_schema_missing_returns_503(monkeypatch):
    # ensure JWT verifier bypass: provide dummy verifier output by patching JWTVerifier.verify
    monkeypatch.setenv("LC_DEBUG_AUTH", "0")
    from app.auth import jwt_verifier

    def fake_verify(_token):
        return {"sub": "user-sub"}

    monkeypatch.setattr(jwt_verifier.JWTVerifier, "verify", staticmethod(fake_verify))
    # patch ensure_user to raise UndefinedTable
    import app.repos.user_repo as user_repo

    def boom(*args, **kwargs):
        raise psycopg.errors.UndefinedTable("missing users")

    monkeypatch.setattr(user_repo, "ensure_user", boom)

    with _make_client() as client:
        resp = client.get("/auth/me", headers={"Authorization": "Bearer dummy"})
    assert resp.status_code == 503
    body = resp.json()
    assert body["error"] == "service_unavailable"
    assert "schema" in body["message"].lower() or "missing table" in body["message"].lower()
    details = body.get("details")
    assert isinstance(details, dict)
    assert details.get("missing_table") == "users"


def test_auth_me_invalid_scheme_still_401(monkeypatch):
    monkeypatch.delenv("LC_DEBUG_AUTH", raising=False)
    with _make_client() as client:
        resp = client.get("/auth/me", headers={"Authorization": "Token abc"})
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"] == "unauthorized"
