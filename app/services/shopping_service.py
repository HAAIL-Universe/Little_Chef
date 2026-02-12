from functools import lru_cache
from typing import Dict, Tuple, List

from app.schemas import (
    MealPlanResponse,
    ShoppingDiffResponse,
    ShoppingListItem,
    RecipeSource,
    StapleItem,
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
                        reason="needed for plan",
                        citations=citations,
                    )
                )

        # Staple items that are low/out of stock
        staple_items = self._staple_shortfall(user_id, available, required)

        return ShoppingDiffResponse(missing_items=missing_items, staple_items=staple_items)

    def _staple_shortfall(
        self,
        user_id: str,
        available: Dict[Tuple[str, str], float],
        already_listed: Dict[Tuple[str, str], float],
    ) -> list[ShoppingListItem]:
        """Return shopping items for staples that are low/out of stock."""
        from app.services.inventory_service import THRESHOLDS

        staples = self.inventory_service.list_staples(user_id)
        items: list[ShoppingListItem] = []
        for s in staples:
            key = (self._normalize(s.item_name), s.unit)
            # Skip if already covered by plan-based missing items
            if key in already_listed:
                continue
            have = available.get(key, 0.0)
            threshold = THRESHOLDS.get(s.unit, 0)
            if have <= threshold:
                # Suggest restocking to a reasonable amount above threshold
                restock_qty = max(threshold - have, 1) if threshold > 0 else 1
                citation = RecipeSource(
                    source_type="built_in",
                    built_in_recipe_id=None,
                    file_id=None,
                    book_id=None,
                    excerpt=None,
                )
                items.append(
                    ShoppingListItem(
                        item_name=s.item_name,
                        quantity=restock_qty,
                        unit=s.unit,
                        reason="auto-added: staple low/out of stock",
                        citations=[citation],
                    )
                )
        return items

    def _normalize(self, name: str) -> str:
        return name.strip().lower()


@lru_cache(maxsize=1)
def get_shopping_service() -> ShoppingService:
    return ShoppingService(get_inventory_service())


def reset_shopping_service_cache() -> None:
    get_shopping_service.cache_clear()
