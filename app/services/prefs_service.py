from functools import lru_cache
from typing import Optional

from app.schemas import UserPrefs
from app.repos.prefs_repo import PrefsRepository, DbPrefsRepository, get_prefs_repository


DEFAULT_PREFS = UserPrefs(
    allergies=[],
    dislikes=[],
    cuisine_likes=[],
    servings=2,
    meals_per_day=3,
    notes="",
)


class PrefsService:
    def __init__(self, repo) -> None:
        self.repo = repo

    def get_prefs(self, user_id: str) -> UserPrefs:
        stored: Optional[UserPrefs] = self.repo.get_prefs(user_id)
        if stored:
            return stored
        return DEFAULT_PREFS.model_copy()

    def upsert_prefs(self, user_id: str, provider_subject: str, email: str | None, prefs: UserPrefs) -> UserPrefs:
        if isinstance(self.repo, DbPrefsRepository):
            return self.repo.upsert_prefs(user_id, provider_subject, email, prefs)
        return self.repo.upsert_prefs(user_id, prefs)

    def clear(self) -> None:
        if hasattr(self.repo, "clear"):
            self.repo.clear()


@lru_cache(maxsize=1)
def get_prefs_service() -> PrefsService:
    repo = get_prefs_repository()
    return PrefsService(repo)
