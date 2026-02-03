from functools import lru_cache
from typing import Dict, Tuple

from app.schemas import (
    MealPlanResponse,
    ShoppingDiffResponse,
    ShoppingListItem,
)
from app.services.inventory_service import InventoryService, get_inventory_service


class ShoppingService:
    def __init__(self, inventory_service: InventoryService) -> None:
        self.inventory_service = inventory_service

    def diff(self, user_id: str, plan: MealPlanResponse) -> ShoppingDiffResponse:
        required: Dict[Tuple[str, str], float] = {}
        for day in plan.days:
            for meal in day.meals:
                for ing in meal.ingredients:
                    key = (self._normalize(ing.item_name), ing.unit)
                    required[key] = required.get(key, 0.0) + ing.quantity

        summary = self.inventory_service.summary(user_id)
        available: Dict[Tuple[str, str], float] = {}
        for item in summary.items:
            key = (self._normalize(item.item_name), item.unit)
            available[key] = available.get(key, 0.0) + item.quantity

        missing_items: list[ShoppingListItem] = []
        for (name, unit), needed in required.items():
            have = available.get((name, unit), 0.0)
            delta = needed - have
            if delta > 0:
                missing_items.append(
                    ShoppingListItem(
                        item_name=name,
                        quantity=delta,
                        unit=unit,
                        reason="",
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
