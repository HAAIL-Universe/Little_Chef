from functools import lru_cache
from uuid import uuid4
from datetime import datetime, timezone
from typing import List

from app.schemas import (
    MealPlanGenerateRequest,
    MealPlanResponse,
    MealPlanDay,
    PlannedMeal,
    IngredientLine,
    RecipeSource,
)
from app.services.recipe_service import BUILT_IN_RECIPES


_INGREDIENTS_BY_RECIPE = {
    "builtin_1": [
        IngredientLine(item_name="tomato", quantity=2, unit="count", optional=False),
        IngredientLine(item_name="pasta", quantity=200, unit="g", optional=False),
    ],
    "builtin_2": [
        IngredientLine(item_name="chicken breast", quantity=300, unit="g", optional=False),
        IngredientLine(item_name="butter", quantity=20, unit="g", optional=False),
    ],
    "builtin_3": [
        IngredientLine(item_name="mixed veggies", quantity=250, unit="g", optional=False),
        IngredientLine(item_name="soy sauce", quantity=30, unit="ml", optional=False),
    ],
}


class MealPlanService:
    def generate(self, request: MealPlanGenerateRequest, *, excluded_recipe_ids: list | None = None) -> MealPlanResponse:
        days = request.days
        meals_per_day = request.meals_per_day or 3
        created_at = datetime.now(timezone.utc).isoformat()
        plan_id = f"plan-{uuid4()}"

        meals_catalog: List[dict] = BUILT_IN_RECIPES
        if excluded_recipe_ids:
            meals_catalog = [r for r in meals_catalog if r["id"] not in excluded_recipe_ids]
        if not meals_catalog:
            return MealPlanResponse(plan_id=plan_id, created_at=created_at, days=[], notes=request.notes or "")
        meals: List[MealPlanDay] = []
        for day_index in range(1, days + 1):
            day_meals: List[PlannedMeal] = []
            for meal_idx in range(meals_per_day):
                recipe = meals_catalog[meal_idx % len(meals_catalog)]
                recipe_id = recipe["id"]
                ingredients = _INGREDIENTS_BY_RECIPE.get(recipe_id, [])
                src = RecipeSource(
                    source_type="built_in",
                    built_in_recipe_id=recipe_id,
                    file_id=None,
                    book_id=None,
                    excerpt=None,
                )
                day_meals.append(
                    PlannedMeal(
                        name=recipe["title"],
                        slot=self._slot_for_index(meal_idx),
                        ingredients=ingredients,
                        instructions=[],
                        source=src,
                        citations=[src],
                    )
                )
            meals.append(MealPlanDay(day_index=day_index, meals=day_meals))

        return MealPlanResponse(plan_id=plan_id, created_at=created_at, days=meals, notes=request.notes or "")

    def _slot_for_index(self, idx: int) -> str:
        order = ["breakfast", "lunch", "dinner", "supper", "snack"]
        return order[idx % len(order)]


@lru_cache(maxsize=1)
def get_mealplan_service() -> MealPlanService:
    return MealPlanService()


def reset_mealplan_service_cache() -> None:
    get_mealplan_service.cache_clear()
