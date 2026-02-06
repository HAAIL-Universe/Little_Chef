from fastapi import APIRouter, Header
import os

from app.schemas import UserMe, ErrorResponse
from app.services.auth_service import get_auth_service
from app.auth.jwt_verifier import JWTVerificationError, JWTConfigurationError
from app.errors import UnauthorizedError

router = APIRouter(prefix="", tags=["Auth"])


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


@router.get(
    "/auth/me",
    response_model=UserMe,
    responses={"401": {"model": ErrorResponse}},
)
def auth_me(
    authorization: str | None = Header(None, convert_underscores=False, alias="Authorization"),
):
    token = _extract_bearer_token(authorization)
    service = get_auth_service()
    from app.services.inventory_service import get_inventory_service
    try:
        user = service.resolve_user(token)
        try:
            inv = get_inventory_service()
            user.onboarded = bool(inv.has_events(user.user_id))
        except Exception:
            user.onboarded = False
        return user
    except (JWTVerificationError, JWTConfigurationError) as exc:
        raise UnauthorizedError(str(exc)) from exc
