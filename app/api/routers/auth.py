from fastapi import APIRouter, Header

from app.schemas import UserMe, ErrorResponse
from app.services.auth_service import get_auth_service
from app.auth.jwt_verifier import JWTVerificationError, JWTConfigurationError
from app.errors import UnauthorizedError

router = APIRouter(prefix="", tags=["Auth"])


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid Authorization header")
    return parts[1]


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
    try:
        return service.resolve_user(token)
    except (JWTVerificationError, JWTConfigurationError) as exc:
        raise UnauthorizedError(str(exc)) from exc
