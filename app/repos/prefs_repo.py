from typing import Dict, Optional

from app.schemas import UserPrefs


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
