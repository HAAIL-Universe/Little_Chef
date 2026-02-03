from functools import lru_cache
from typing import Optional

from app.schemas import UserPrefs
from app.repos.prefs_repo import PrefsRepository


DEFAULT_PREFS = UserPrefs(
    allergies=[],
    dislikes=[],
    cuisine_likes=[],
    servings=2,
    meals_per_day=3,
    notes="",
)


class PrefsService:
    def __init__(self, repo: PrefsRepository) -> None:
        self.repo = repo

    def get_prefs(self, user_id: str) -> UserPrefs:
        stored: Optional[UserPrefs] = self.repo.get_prefs(user_id)
        if stored:
            return stored
        return DEFAULT_PREFS.model_copy()

    def upsert_prefs(self, user_id: str, prefs: UserPrefs) -> UserPrefs:
        return self.repo.upsert_prefs(user_id, prefs)


@lru_cache(maxsize=1)
def get_prefs_service() -> PrefsService:
    repo = PrefsRepository()
    return PrefsService(repo)

