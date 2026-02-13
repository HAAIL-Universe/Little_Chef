import random
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
from app.services.recipe_service import BUILT_IN_RECIPES, scale_ingredients


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

_INSTRUCTIONS_BY_RECIPE = {
    "builtin_1": [
        "Boil pasta according to package directions.",
        "Dice tomatoes and simmer in a pan with olive oil for 5 minutes.",
        "Drain pasta, toss with tomato sauce, and serve.",
    ],
    "builtin_2": [
        "Season chicken breast with salt and pepper.",
        "Melt butter in a pan over medium-high heat.",
        "Cook chicken 6-7 minutes per side until golden and cooked through.",
        "Rest for 2 minutes before slicing. Serve.",
    ],
    "builtin_3": [
        "Heat oil in a wok or large pan over high heat.",
        "Add mixed veggies and stir-fry for 3-4 minutes.",
        "Add soy sauce, toss to coat, and serve immediately.",
    ],
}


class MealPlanService:
    def generate(
        self,
        request: MealPlanGenerateRequest,
        *,
        excluded_recipe_ids: list | None = None,
        pack_recipes: list[dict] | None = None,
        stock_names: set[str] | None = None,
        target_servings: int = 0,
        planning_mode: str = "inventory_first",
        expiry_priority: dict[str, float] | None = None,
    ) -> MealPlanResponse:
        days = request.days
        meals_per_day = request.meals_per_day or 3
        created_at = datetime.now(timezone.utc).isoformat()
        plan_id = f"plan-{uuid4()}"

        # Build catalog: pack recipes first (primary), built-ins as fallback
        if request.include_user_library and pack_recipes:
            meals_catalog: List[dict] = list(pack_recipes) + list(BUILT_IN_RECIPES)
        else:
            meals_catalog = list(BUILT_IN_RECIPES)

        if excluded_recipe_ids:
            meals_catalog = [r for r in meals_catalog if r["id"] not in excluded_recipe_ids]
        if not meals_catalog:
            return MealPlanResponse(plan_id=plan_id, created_at=created_at, days=[], notes=request.notes or "")

        mode = (planning_mode or "inventory_first").lower()
        if mode not in {"inventory_first", "balanced", "adventurous"}:
            mode = "inventory_first"

        # Inventory-aware scoring with optional expiry bias.
        if stock_names is not None:
            has_expiry_bias = bool(expiry_priority)
            scored = []
            for r in meals_catalog:
                ingredients = r.get("ingredients") or _INGREDIENTS_BY_RECIPE.get(r["id"], [])
                total = len(ingredients) if ingredients else 0
                have = 0
                expiry_boost = 0.0
                if total > 0:
                    for ing in ingredients:
                        name = ing.item_name.lower() if hasattr(ing, "item_name") else str(ing).lower()
                        if name in stock_names:
                            have += 1
                        if expiry_priority:
                            expiry_boost += float(expiry_priority.get(name, 0.0))
                pct = have / total if total else 0.0

                if mode == "inventory_first":
                    mode_score = pct + (expiry_boost * 3.0 if has_expiry_bias else 0.0)
                elif mode == "balanced":
                    mode_score = pct + (expiry_boost * 2.0 if has_expiry_bias else 0.0)
                else:  # adventurous
                    mode_score = (expiry_boost * 4.0 + pct * 0.25) if has_expiry_bias else 0.0

                scored.append((mode_score, pct, expiry_boost, r))

            # Deterministic ordering by selected strategy.
            scored.sort(key=lambda x: (-x[0], -x[2], -x[1], x[3]["title"].lower()))
            ordered = [r for _, _, _, r in scored]
            meals_needed = max(1, days * meals_per_day)

            if len(ordered) <= 6:
                # Small catalog safeguard: force visibly different ordering per mode.
                # This prevents "looks the same" behavior when only fallback recipes exist.
                if mode == "balanced":
                    shuffled = list(ordered[1:]) + list(ordered[:1]) if len(ordered) > 1 else list(ordered)
                elif mode == "adventurous":
                    shuffled = list(reversed(ordered))
                else:
                    shuffled = list(ordered)
            else:
                if mode == "balanced":
                    top_window = min(len(ordered), max(meals_needed * 4, 12))
                    rng = random.Random(f"{plan_id}:balanced")
                    head = list(ordered[:top_window])
                    tail = list(ordered[top_window:])
                    rng.shuffle(head)
                    shuffled = head + tail
                elif mode == "adventurous":
                    if has_expiry_bias:
                        # Keep strong expiry bias while still introducing variety.
                        top_window = min(len(ordered), max(meals_needed * 5, 15))
                        rng = random.Random(f"{plan_id}:adventurous_expiry")
                        head = list(ordered[:top_window])
                        tail = list(ordered[top_window:])
                        rng.shuffle(head)
                        shuffled = head + tail
                    else:
                        # Exploratory mode should visibly diverge from inventory-first:
                        # pick from the lower-ranked inventory matches first.
                        split_idx = min(max(len(ordered) // 3, 1), len(ordered) - 1)
                        exploratory = list(ordered[split_idx:])
                        high_match_tail = list(ordered[:split_idx])
                        rng = random.Random(f"{plan_id}:adventurous")
                        rng.shuffle(exploratory)
                        shuffled = exploratory + high_match_tail
                else:
                    shuffled = ordered
        else:
            # Adventurous mode (or no inventory context): deterministic-per-plan shuffle.
            rng = random.Random(plan_id)
            shuffled = list(meals_catalog)
            rng.shuffle(shuffled)

        meals: List[MealPlanDay] = []
        for day_index in range(1, days + 1):
            day_meals: List[PlannedMeal] = []
            for meal_idx in range(meals_per_day):
                # Add a day stride so small catalogs (e.g. 3 fallback recipes with 3 meals/day)
                # do not render identical day blocks.
                catalog_idx = ((day_index - 1) * (meals_per_day + 1) + meal_idx) % len(shuffled)
                recipe = shuffled[catalog_idx]
                recipe_id = recipe["id"]
                # Inline ingredients (pack recipes) take priority over built-in lookup
                ingredients = recipe.get("ingredients") or _INGREDIENTS_BY_RECIPE.get(recipe_id, [])
                instructions = recipe.get("instructions") or _INSTRUCTIONS_BY_RECIPE.get(recipe_id, [])
                # Scale ingredients if target_servings differs from recipe default (assumed 2)
                if target_servings > 0 and ingredients:
                    original = recipe.get("servings", 2)
                    if original != target_servings:
                        ingredients = scale_ingredients(ingredients, original, target_servings)
                source_type = recipe.get("source_type", "built_in")
                src = RecipeSource(
                    source_type=source_type,
                    built_in_recipe_id=recipe_id if source_type == "built_in" else None,
                    file_id=None,
                    book_id=recipe_id if source_type == "user_library" else None,
                    excerpt=None,
                )
                day_meals.append(
                    PlannedMeal(
                        name=recipe["title"],
                        slot=self._slot_for_index(meal_idx),
                        ingredients=ingredients,
                        instructions=instructions,
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
