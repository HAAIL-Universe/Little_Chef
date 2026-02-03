import os
from functools import lru_cache
from typing import Optional, Dict, Any

import jwt
import requests
from jwt import PyJWKClient


class JWTConfigurationError(Exception):
    """Raised when verifier configuration is missing or invalid."""


class JWTVerificationError(Exception):
    """Raised when a token fails verification."""


class JWTVerifier:
    """
    Wraps PyJWT + JWKS retrieval.

    Verification steps:
    - Require issuer and audience.
    - Resolve JWKS URL (direct or via OIDC discovery).
    - Fetch signing key via PyJWKClient (caches keys).
    - Decode & verify signature, issuer, audience, and exp.
    """

    def __init__(self, issuer: str, audience: str, jwks_url: str):
        if not issuer or not audience or not jwks_url:
            raise JWTConfigurationError("issuer, audience, and jwks_url are required")
        self.issuer = issuer
        self.audience = audience
        self.jwks_url = jwks_url
        self._jwks_client = PyJWKClient(jwks_url)

    @staticmethod
    def _discover_jwks(discovery_url: str) -> str:
        try:
            resp = requests.get(discovery_url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # pragma: no cover - defensive
            raise JWTConfigurationError(f"Failed to fetch OIDC discovery document: {exc}") from exc

        jwks_uri = data.get("jwks_uri")
        if not jwks_uri:
            raise JWTConfigurationError("OIDC discovery document missing jwks_uri")
        return jwks_uri

    @classmethod
    @lru_cache(maxsize=1)
    def from_env(cls) -> "JWTVerifier":
        issuer = os.getenv("LC_JWT_ISSUER")
        audience = os.getenv("LC_JWT_AUDIENCE")
        discovery_url = os.getenv("LC_OIDC_DISCOVERY_URL")
        jwks_url = os.getenv("LC_JWKS_URL")

        if not issuer or not audience:
            raise JWTConfigurationError("LC_JWT_ISSUER and LC_JWT_AUDIENCE are required")

        resolved_jwks = jwks_url
        if not resolved_jwks and discovery_url:
            resolved_jwks = cls._discover_jwks(discovery_url)

        if not resolved_jwks:
            raise JWTConfigurationError("Provide LC_OIDC_DISCOVERY_URL or LC_JWKS_URL")

        return cls(issuer=issuer, audience=audience, jwks_url=resolved_jwks)

    def verify(self, token: str) -> Dict[str, Any]:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
            return claims
        except jwt.ExpiredSignatureError as exc:
            raise JWTVerificationError("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise JWTVerificationError(str(exc)) from exc
