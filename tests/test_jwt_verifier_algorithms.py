import types

import pytest

from app.auth.jwt_verifier import JWTVerifier


class DummySigningKey:
    def __init__(self, key: str):
        self.key = key


def test_jwt_decode_called_with_algorithms(monkeypatch):
    verifier = JWTVerifier(issuer="https://example.com/", audience="api://default", jwks_url="https://example.com/.well-known/jwks.json")

    # Stub JWKS client to avoid network and provide a dummy key
    monkeypatch.setattr(verifier, "_jwks_client", types.SimpleNamespace(get_signing_key_from_jwt=lambda token: DummySigningKey("dummy-key")))

    captured = {}

    def fake_decode(token, key, **kwargs):
        captured["token"] = token
        captured["key"] = key
        captured["kwargs"] = kwargs
        return {"sub": "test-sub"}

    monkeypatch.setattr("app.auth.jwt_verifier.jwt.decode", fake_decode)

    claims = verifier.verify("any.token.value")

    assert claims["sub"] == "test-sub"
    assert captured["kwargs"]["algorithms"] == ["RS256"]
    assert captured["kwargs"]["audience"] == "api://default"
    assert captured["kwargs"]["issuer"] == "https://example.com/"
