from functools import lru_cache
from uuid import uuid5, NAMESPACE_URL
from typing import Optional

from app.auth.jwt_verifier import JWTVerifier, JWTVerificationError
from app.schemas import UserMe
from app.db.conn import get_database_url, connect
from app.repos.user_repo import ensure_user, delete_user
from app.errors import ServiceUnavailableError
import psycopg


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
                try:
                    ensure_user(cur, user_id, provider_subject, email)
                    conn.commit()
                except psycopg.errors.UndefinedTable as exc:
                    details = {"missing_table": "users"}
                    raise ServiceUnavailableError(
                        "Database schema is not initialized (missing table: users). Apply migrations to the configured DATABASE_URL.",
                        details=details,
                    ) from exc

        return UserMe(
            user_id=user_id,
            provider_subject=provider_subject,
            email=email,
        )

    def delete_account(self, token: str) -> bool:
        """Verify the token, then delete the user and all cascade-linked data."""
        claims = self.verifier.verify(token)
        provider_subject: Optional[str] = claims.get("sub")
        if not provider_subject:
            raise JWTVerificationError("Missing sub claim")
        user_id = _deterministic_user_id(provider_subject)
        if not get_database_url():
            return False
        with connect() as conn, conn.cursor() as cur:
            deleted = delete_user(cur, user_id)
            conn.commit()
        return deleted


@lru_cache(maxsize=1)
def get_auth_service() -> AuthService:
    verifier = JWTVerifier.from_env()
    return AuthService(verifier=verifier)
