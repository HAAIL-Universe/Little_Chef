import logging
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


class PrefsPersistenceError(RuntimeError):
    """Raised when confirmed prefs cannot be persisted to the database."""


logger = logging.getLogger(__name__)


class PrefsService:
    def __init__(self, repo) -> None:
        self.repo = repo

    def get_prefs(self, user_id: str) -> UserPrefs:
        try:
            stored: Optional[UserPrefs] = self.repo.get_prefs(user_id)
        except Exception:
            stored = None
        if stored:
            return stored
        return DEFAULT_PREFS.model_copy()

    def has_prefs(self, user_id: str) -> bool:
        try:
            stored = self.repo.get_prefs(user_id)
        except Exception:
            return False
        return stored is not None

    def upsert_prefs(
        self,
        user_id: str,
        provider_subject: str,
        email: str | None,
        prefs: UserPrefs,
        applied_event_id: str | None = None,
        require_db: bool = False,
    ) -> UserPrefs:
        if require_db and not isinstance(self.repo, DbPrefsRepository):
            raise PrefsPersistenceError("database persistence required but no DB repository configured")
        try:
            return self.repo.upsert_prefs(user_id, provider_subject, email, prefs, applied_event_id)
        except PrefsPersistenceError:
            raise
        except Exception as exc:
            if require_db:
                raise PrefsPersistenceError("database write failed") from exc
            if not isinstance(self.repo, PrefsRepository):
                self.repo = PrefsRepository()
            return self.repo.upsert_prefs(user_id, prefs, applied_event_id)

    def clear(self) -> None:
        if hasattr(self.repo, "clear"):
            self.repo.clear()


@lru_cache(maxsize=1)
def get_prefs_service() -> PrefsService:
    repo = get_prefs_repository()
    kind = "postgres" if isinstance(repo, DbPrefsRepository) else "in-memory"
    logger.info("Prefs repo implementation: %s", kind)
    return PrefsService(repo)
