from functools import lru_cache
from typing import Dict, Tuple, List

from app.schemas import (
    MealPlanResponse,
    ShoppingDiffResponse,
    ShoppingListItem,
    RecipeSource,
)
from app.services.inventory_service import InventoryService, get_inventory_service


class ShoppingService:
    def __init__(self, inventory_service: InventoryService) -> None:
        self.inventory_service = inventory_service

    def diff(self, user_id: str, plan: MealPlanResponse) -> ShoppingDiffResponse:
        required: Dict[Tuple[str, str], float] = {}
        citations_by_key: Dict[Tuple[str, str], List[RecipeSource]] = {}
        for day in plan.days:
            for meal in day.meals:
                meal_citations = list(meal.citations) if getattr(meal, "citations", None) else [meal.source]
                for ing in meal.ingredients:
                    key = (self._normalize(ing.item_name), ing.unit)
                    required[key] = required.get(key, 0.0) + ing.quantity
                    bucket = citations_by_key.setdefault(key, [])
                    if meal_citations:
                        bucket.append(meal_citations[0])

        summary = self.inventory_service.summary(user_id)
        available: Dict[Tuple[str, str], float] = {}
        for item in summary.items:
            key = (self._normalize(item.item_name), item.unit or "count")
            available[key] = available.get(key, 0.0) + (item.quantity or 0)

        missing_items: list[ShoppingListItem] = []
        for (name, unit), needed in required.items():
            have = available.get((name, unit), 0.0)
            delta = needed - have
            if delta > 0:
                citations = citations_by_key.get((name, unit), [])
                if not citations:
                    citations = [
                        RecipeSource(
                            source_type="built_in",
                            built_in_recipe_id=None,
                            file_id=None,
                            book_id=None,
                            excerpt=None,
                        )
                    ]
                missing_items.append(
                    ShoppingListItem(
                        item_name=name,
                        quantity=delta,
                        unit=unit,
                        reason="missing for meal plan",
                        citations=citations,
                    )
                )

        return ShoppingDiffResponse(missing_items=missing_items)

    def _normalize(self, name: str) -> str:
        return name.strip().lower()


@lru_cache(maxsize=1)
def get_shopping_service() -> ShoppingService:
    return ShoppingService(get_inventory_service())


def reset_shopping_service_cache() -> None:
    get_shopping_service.cache_clear()
