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
        self._applied_event_ids: Dict[str, str] = {}

    def get_prefs(self, user_id: str) -> Optional[UserPrefs]:
        return self._prefs_by_user.get(user_id)

    def upsert_prefs(self, user_id: str, prefs: UserPrefs, applied_event_id: str | None = None) -> UserPrefs:
        self._prefs_by_user[user_id] = prefs
        if applied_event_id is not None:
            self._applied_event_ids[user_id] = applied_event_id
        return prefs

    def get_applied_event_id(self, user_id: str) -> Optional[str]:
        return self._applied_event_ids.get(user_id)

    def clear(self) -> None:
        self._prefs_by_user.clear()
        self._applied_event_ids.clear()


class DbPrefsRepository:
    def get_prefs(self, user_id: str) -> Optional[UserPrefs]:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT prefs FROM prefs WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                return None
            return UserPrefs.model_validate(row[0])

    def upsert_prefs(
        self,
        user_id: str,
        provider_subject: str,
        email: str | None,
        prefs: UserPrefs,
        applied_event_id: str | None = None,
    ) -> UserPrefs:
        with connect() as conn, conn.cursor() as cur:
            ensure_user(cur, user_id, provider_subject, email)
            cur.execute(
                """
                INSERT INTO prefs (user_id, prefs, applied_event_id, updated_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (user_id) DO UPDATE SET prefs = EXCLUDED.prefs, applied_event_id = EXCLUDED.applied_event_id, updated_at = now()
                """,
                (user_id, json.dumps(prefs.model_dump()), applied_event_id),
            )
            conn.commit()
        return prefs


def get_prefs_repository():
    if get_database_url():
        return DbPrefsRepository()
    return PrefsRepository()
