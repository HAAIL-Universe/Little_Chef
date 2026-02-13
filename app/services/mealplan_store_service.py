from __future__ import annotations

from functools import lru_cache

from app.repos.mealplan_repo import get_mealplan_repository
from app.schemas import MealPlanResponse


class MealPlanStoreService:
    def __init__(self, repo) -> None:
        self.repo = repo

    def save_confirmed_plan(
        self,
        user_id: str,
        provider_subject: str,
        email: str | None,
        thread_id: str,
        proposal_id: str,
        plan: MealPlanResponse,
    ) -> MealPlanResponse:
        try:
            return self.repo.save_plan(
                user_id,
                provider_subject,
                email,
                thread_id,
                proposal_id,
                plan,
            )
        except TypeError:
            # In-memory repo signature does not require auth identity fields.
            return self.repo.save_plan(user_id, thread_id, proposal_id, plan)

    def get_latest_plan(self, user_id: str) -> MealPlanResponse | None:
        return self.repo.get_latest_plan(user_id)

    def clear(self) -> None:
        if hasattr(self.repo, "clear"):
            self.repo.clear()


@lru_cache(maxsize=1)
def get_mealplan_store_service() -> MealPlanStoreService:
    return MealPlanStoreService(get_mealplan_repository())


def reset_mealplan_store_service_cache() -> None:
    get_mealplan_store_service.cache_clear()
