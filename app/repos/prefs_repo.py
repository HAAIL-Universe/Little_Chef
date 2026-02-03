from typing import Dict, Optional
import json

from app.schemas import UserPrefs
from app.db.conn import get_database_url, connect
from app.repos.user_repo import ensure_user


class PrefsRepository:
    """
    Phase 2 temporary in-memory prefs store.
    Replace with persistent store (DB) in a later phase.
    """

    def __init__(self) -> None:
        self._prefs_by_user: Dict[str, UserPrefs] = {}

    def get_prefs(self, user_id: str) -> Optional[UserPrefs]:
        return self._prefs_by_user.get(user_id)

    def upsert_prefs(self, user_id: str, prefs: UserPrefs) -> UserPrefs:
        self._prefs_by_user[user_id] = prefs
        return prefs

    def clear(self) -> None:
        self._prefs_by_user.clear()


class DbPrefsRepository:
    def get_prefs(self, user_id: str) -> Optional[UserPrefs]:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT prefs FROM prefs WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                return None
            return UserPrefs.model_validate(row[0])

    def upsert_prefs(self, user_id: str, provider_subject: str, email: str | None, prefs: UserPrefs) -> UserPrefs:
        with connect() as conn, conn.cursor() as cur:
            ensure_user(cur, user_id, provider_subject, email)
            cur.execute(
                """
                INSERT INTO prefs (user_id, prefs, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (user_id) DO UPDATE SET prefs = EXCLUDED.prefs, updated_at = now()
                """,
                (user_id, json.loads(prefs.model_dump_json()),),
            )
            conn.commit()
        return prefs


def get_prefs_repository():
    if get_database_url():
        return DbPrefsRepository()
    return PrefsRepository()
