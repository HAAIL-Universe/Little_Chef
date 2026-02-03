from fastapi import Header, HTTPException, status

from app.schemas import ErrorResponse, UserMe
from app.services.auth_service import get_auth_service
from app.auth.jwt_verifier import JWTVerificationError, JWTConfigurationError


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(error="unauthorized", message="Missing Authorization header").model_dump(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(error="unauthorized", message="Invalid Authorization header").model_dump(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parts[1]


def get_current_user(
    authorization: str | None = Header(None, convert_underscores=False, alias="Authorization"),
) -> UserMe:
    token = _extract_bearer_token(authorization)
    service = get_auth_service()
    try:
        return service.resolve_user(token)
    except (JWTVerificationError, JWTConfigurationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(error="unauthorized", message=str(exc)).model_dump(),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

