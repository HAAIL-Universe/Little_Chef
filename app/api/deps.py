from fastapi import Header

from app.schemas import UserMe
from app.services.auth_service import get_auth_service
from app.auth.jwt_verifier import JWTVerificationError, JWTConfigurationError
import os
from app.errors import UnauthorizedError


def _auth_debug_details(authorization: str | None):
    text = authorization or ""
    parts = text.split()
    scheme_lower = parts[0].lower() if parts else None
    return {
        "auth_present": authorization is not None,
        "auth_len": len(text),
        "parts_count": len(parts),
        "scheme_lower": scheme_lower,
        "starts_with_bearer_ci": text.lower().startswith("bearer"),
        "has_newline": "\n" in text,
        "has_tab": "\t" in text,
        "has_comma": "," in text,
    }


def _extract_bearer_token(authorization: str | None) -> str:
    debug = os.environ.get("LC_DEBUG_AUTH") == "1"
    if not authorization:
        details = _auth_debug_details(authorization) if debug else None
        raise UnauthorizedError("Missing Authorization header", details=details)
    parts = authorization.split()
    details = _auth_debug_details(authorization) if debug else None
    if len(parts) < 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid Authorization header", details=details)
    token = "".join(parts[1:])
    if not token:
        raise UnauthorizedError("Invalid Authorization header", details=details)
    return token


def get_current_user(
    authorization: str | None = Header(None, convert_underscores=False, alias="Authorization"),
) -> UserMe:
    token = _extract_bearer_token(authorization)
    service = get_auth_service()
    try:
        return service.resolve_user(token)
    except (JWTVerificationError, JWTConfigurationError) as exc:
        raise UnauthorizedError(str(exc)) from exc
