from functools import lru_cache
from uuid import uuid5, NAMESPACE_URL
from typing import Optional

from app.auth.jwt_verifier import JWTVerifier, JWTVerificationError
from app.schemas import UserMe
from app.db.conn import get_database_url, connect
from app.repos.user_repo import ensure_user


def _deterministic_user_id(provider_subject: str) -> str:
    """
    Temporary mapping for Phase 1: derive an internal user id deterministically
    from the provider subject. Phase 2 should persist real user records.
    """
    return str(uuid5(NAMESPACE_URL, f"littlechef:{provider_subject}"))


class AuthService:
    def __init__(self, verifier: JWTVerifier):
        self.verifier = verifier

    def resolve_user(self, token: str) -> UserMe:
        claims = self.verifier.verify(token)
        provider_subject: Optional[str] = claims.get("sub")
        if not provider_subject:
            raise JWTVerificationError("Missing sub claim")

        email = claims.get("email")
        user_id = _deterministic_user_id(provider_subject)

        if get_database_url():
            with connect() as conn, conn.cursor() as cur:
                ensure_user(cur, user_id, provider_subject, email)
                conn.commit()

        return UserMe(
            user_id=user_id,
            provider_subject=provider_subject,
            email=email,
        )


@lru_cache(maxsize=1)
def get_auth_service() -> AuthService:
    verifier = JWTVerifier.from_env()
    return AuthService(verifier=verifier)
