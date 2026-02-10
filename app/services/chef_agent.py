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
from app.services.mealplan_service import MealPlanService
from app.services.proposal_store import ProposalStore
from app.services.llm_client import LlmClient
from app.services.prefs_service import PrefsService

_DAYS_RE = re.compile(r"(\d+)\s*days?", re.IGNORECASE)
_MEALS_RE = re.compile(r"(\d+)\s*meals?\s*(?:per\s*day|a\s*day)?", re.IGNORECASE)


class ChefAgent:
    def __init__(
        self,
        mealplan_service: MealPlanService,
        proposal_store: ProposalStore,
        llm_client: Optional[LlmClient] = None,
        prefs_service: Optional[PrefsService] = None,
    ) -> None:
        self.mealplan_service = mealplan_service
        self.proposal_store = proposal_store
        self.llm_client = llm_client
        self.prefs_service = prefs_service
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

        # Fall back to user prefs if available
        if self.prefs_service and (days is None or meals_per_day is None):
            try:
                prefs = self.prefs_service.get_prefs(user.user_id)
                if prefs:
                    if days is None and hasattr(prefs, "plan_days") and prefs.plan_days:
                        days = prefs.plan_days
                    if meals_per_day is None and hasattr(prefs, "meals_per_day") and prefs.meals_per_day:
                        meals_per_day = prefs.meals_per_day
            except Exception:
                pass

        # Final defaults
        if days is None:
            days = 3
        if meals_per_day is None:
            meals_per_day = 3

        gen_request = MealPlanGenerateRequest(
            days=days,
            meals_per_day=meals_per_day,
            include_user_library=request.include_user_library,
            notes="",
        )
        plan = self.mealplan_service.generate(gen_request)

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
