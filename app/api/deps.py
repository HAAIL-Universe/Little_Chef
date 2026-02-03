from fastapi import Header

from app.schemas import UserMe
from app.services.auth_service import get_auth_service
from app.auth.jwt_verifier import JWTVerificationError, JWTConfigurationError
from app.errors import UnauthorizedError


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid Authorization header")
    return parts[1]


def get_current_user(
    authorization: str | None = Header(None, convert_underscores=False, alias="Authorization"),
) -> UserMe:
    token = _extract_bearer_token(authorization)
    service = get_auth_service()
    try:
        return service.resolve_user(token)
    except (JWTVerificationError, JWTConfigurationError) as exc:
        raise UnauthorizedError(str(exc)) from exc
