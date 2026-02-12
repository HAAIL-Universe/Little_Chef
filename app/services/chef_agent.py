import re
import uuid
from typing import Dict, List, Optional, Tuple

from app.schemas import (
    ChatRequest,
    ChatResponse,
    MealPlanGenerateRequest,
    ProposedGenerateMealPlanAction,
    UserMe,
)
from app.services.mealplan_service import MealPlanService, _INGREDIENTS_BY_RECIPE
from app.services.proposal_store import ProposalStore
from app.services.llm_client import LlmClient
from app.services.prefs_service import PrefsService
from app.services.recipe_service import BUILT_IN_RECIPES

_DAYS_RE = re.compile(r"(\d+)\s*days?", re.IGNORECASE)
_MEALS_RE = re.compile(r"(\d+)\s*meals?\s*(?:per\s*day|a\s*day)?", re.IGNORECASE)


class ChefAgent:
    def __init__(
        self,
        mealplan_service: MealPlanService,
        proposal_store: ProposalStore,
        llm_client: Optional[LlmClient] = None,
        prefs_service: Optional[PrefsService] = None,
        inventory_service=None,
        recipe_service=None,
    ) -> None:
        self.mealplan_service = mealplan_service
        self.proposal_store = proposal_store
        self.llm_client = llm_client
        self.prefs_service = prefs_service
        self.inventory_service = inventory_service
        self.recipe_service = recipe_service
        self._pending: Dict[Tuple[str, str], str] = {}  # (user_id, thread_id) -> proposal_id
        self._proposal_threads: Dict[str, Tuple[str, str]] = {}  # proposal_id -> (user_id, thread_id)

    def handle_fill(self, user: UserMe, request: ChatRequest) -> ChatResponse:
        thread_id = request.thread_id
        if not thread_id:
            return ChatResponse(
                reply_text="Thread id is required for meal plan generation.",
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
                mode=request.mode or "fill",
            )

        message = request.message
        days = self._parse_days(message)
        meals_per_day = self._parse_meals_per_day(message)

        # MVP: detect multi-day request before capping
        requested_multi = days is not None and days > 1

        # Fall back to user prefs if available
        prefs = None
        if self.prefs_service:
            try:
                prefs = self.prefs_service.get_prefs(user.user_id)
                if prefs:
                    if meals_per_day is None and hasattr(prefs, "meals_per_day") and prefs.meals_per_day:
                        meals_per_day = prefs.meals_per_day
            except Exception:
                pass

        # Final defaults
        if meals_per_day is None:
            meals_per_day = 3

        # MVP: always 1-day plan
        days = 1

        # Prefs-first filtering: exclude recipes matching allergies/dislikes
        pack_recipes = self._build_pack_catalog(user.user_id)
        excluded_ids = self._excluded_recipe_ids(prefs, pack_recipes)

        gen_request = MealPlanGenerateRequest(
            days=days,
            meals_per_day=meals_per_day,
            include_user_library=request.include_user_library,
            notes="",
        )
        plan = self.mealplan_service.generate(gen_request, excluded_recipe_ids=excluded_ids, pack_recipes=pack_recipes)

        # If all recipes were excluded, return a helpful message
        total_meals = sum(len(d.meals) for d in plan.days)
        if total_meals == 0:
            return ChatResponse(
                reply_text="All available recipes conflict with your allergies/dislikes. Try adjusting your preferences.",
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
                mode=request.mode or "fill",
            )

        # Inventory notes (informational)
        plan = self._annotate_inventory_notes(plan, user.user_id)

        action = ProposedGenerateMealPlanAction(mealplan=plan)
        proposal_id = str(uuid.uuid4())
        key = (user.user_id, thread_id)

        self._bind_proposal(user.user_id, thread_id, proposal_id)
        self._pending[key] = proposal_id
        self.proposal_store.save(user.user_id, proposal_id, [action])

        day_count = len(plan.days)
        meal_count = sum(len(d.meals) for d in plan.days)
        reply = (
            f"I've prepared a {day_count}-day meal plan with {meal_count} meals. "
            f"Please confirm to apply."
        )
        if requested_multi:
            reply = (
                "MVP supports 1-day plans. Here's your plan for today "
                "— multi-day planning is coming soon!\n\n" + reply
            )

        return ChatResponse(
            reply_text=reply,
            confirmation_required=True,
            proposal_id=proposal_id,
            proposed_actions=[action],
            suggested_next_questions=[],
            mode=request.mode or "fill",
        )

    def confirm(
        self,
        user: UserMe,
        proposal_id: str,
        confirm: bool,
        thread_id: Optional[str] = None,
    ) -> Tuple[bool, List[str], Optional[str]]:
        if not self.handles_proposal(user.user_id, proposal_id, thread_id):
            return False, [], None
        if not thread_id:
            return False, [], None

        key = (user.user_id, thread_id)

        if not confirm:
            self._clear_proposal(user.user_id, proposal_id, key)
            return False, [], None

        actions = self.proposal_store.peek(user.user_id, proposal_id)
        if actions is None:
            return False, [], None

        action_list = actions if isinstance(actions, list) else [actions]
        applied_ids: List[str] = []
        for act in action_list:
            if isinstance(act, ProposedGenerateMealPlanAction):
                applied_ids.append(act.mealplan.plan_id)

        self._clear_proposal(user.user_id, proposal_id, key)
        return True, applied_ids, None

    def handles_proposal(
        self, user_id: str, proposal_id: str, thread_id: Optional[str] = None
    ) -> bool:
        mapping = self._proposal_threads.get(proposal_id)
        if not mapping or mapping[0] != user_id:
            return False
        if thread_id is not None and mapping[1] != thread_id:
            return False
        return True

    def _bind_proposal(self, user_id: str, thread_id: str, proposal_id: str) -> None:
        self._proposal_threads[proposal_id] = (user_id, thread_id)

    def _clear_proposal(
        self, user_id: str, proposal_id: str, key: Tuple[str, str]
    ) -> None:
        self.proposal_store.pop(user_id, proposal_id)
        self._pending.pop(key, None)
        self._proposal_threads.pop(proposal_id, None)

    @staticmethod
    def _excluded_recipe_ids(prefs, pack_recipes: list | None = None) -> list:
        """Return recipe IDs (built-in + pack) that conflict with user allergies/dislikes."""
        if not prefs:
            return []
        keywords: set[str] = set()
        for a in getattr(prefs, "allergies", []) or []:
            keywords.add(a.lower())
        for d in getattr(prefs, "dislikes", []) or []:
            keywords.add(d.lower())
        if not keywords:
            return []
        excluded: list[str] = []
        # Built-in recipes
        for recipe in BUILT_IN_RECIPES:
            rid = recipe["id"]
            title = recipe.get("title", "").lower()
            if any(kw in title for kw in keywords):
                excluded.append(rid)
                continue
            ingredients = _INGREDIENTS_BY_RECIPE.get(rid, [])
            if any(any(kw in ing.item_name.lower() for kw in keywords) for ing in ingredients):
                excluded.append(rid)
        # Pack recipes
        if pack_recipes:
            for recipe in pack_recipes:
                rid = recipe["id"]
                title = recipe.get("title", "").lower()
                if any(kw in title for kw in keywords):
                    excluded.append(rid)
                    continue
                ingredients = recipe.get("ingredients", [])
                if any(any(kw in ing.item_name.lower() for kw in keywords) for ing in ingredients):
                    excluded.append(rid)
        return excluded

    def _build_pack_catalog(self, user_id: str) -> list[dict]:
        """Query installed pack books and extract ingredients for meal planning."""
        if not self.recipe_service:
            return []
        from app.services.recipe_service import extract_ingredients_from_markdown
        try:
            resp = self.recipe_service.list_books(user_id)
        except Exception:
            return []
        catalog: list[dict] = []
        for book in resp.books:
            if not book.pack_id or not book.text_content:
                continue
            ingredients = extract_ingredients_from_markdown(book.text_content)
            if not ingredients:  # Hardness #2: skip ingredientless recipes
                continue
            catalog.append({
                "id": book.book_id,
                "title": book.title or book.filename,
                "ingredients": ingredients,
                "source_type": "user_library",
            })
        return catalog

    def _annotate_inventory_notes(self, plan, user_id: str):
        """Add informational notes about ingredient stock to the plan."""
        if not self.inventory_service:
            return plan
        try:
            inv = self.inventory_service.summary(user_id)
        except Exception:
            return plan
        if not inv.items:
            return plan
        stock_names = {item.item_name.lower() for item in inv.items}
        needed: set[str] = set()
        for day in plan.days:
            for meal in day.meals:
                for ing in meal.ingredients:
                    needed.add(ing.item_name.lower())
        in_stock = sorted(needed & stock_names)
        need_to_buy = sorted(needed - stock_names)
        parts: list[str] = []
        if in_stock:
            parts.append(f"In stock: {', '.join(in_stock)}")
        if need_to_buy:
            parts.append(f"Need to buy: {', '.join(need_to_buy)}")
        if parts:
            plan.notes = ". ".join(parts) + "."
        return plan

    @staticmethod
    def _parse_days(message: str) -> Optional[int]:
        m = _DAYS_RE.search(message)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 31:
                return val
        return None

    @staticmethod
    def _parse_meals_per_day(message: str) -> Optional[int]:
        m = _MEALS_RE.search(message)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 6:
                return val
        return None
