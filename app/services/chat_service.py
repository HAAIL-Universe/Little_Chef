import re
import uuid
from typing import List

from app.schemas import (
    ChatRequest,
    ChatResponse,
    ProposedUpsertPrefsAction,
    UserPrefs,
)
from app.services.prefs_service import PrefsService
from app.services.proposal_store import ProposalStore


class ChatService:
    def __init__(self, prefs_service: PrefsService, proposal_store: ProposalStore) -> None:
        self.prefs_service = prefs_service
        self.proposal_store = proposal_store

    def handle_chat(self, user_id: str, request: ChatRequest) -> ChatResponse:
        mode = request.mode
        message = request.message.lower()

        if mode == "ask":
            if "pref" in message or "preference" in message:
                prefs = self.prefs_service.get_prefs(user_id)
                reply = self._format_prefs(prefs)
                return ChatResponse(
                    reply_text=reply,
                    confirmation_required=False,
                    proposal_id=None,
                    proposed_actions=[],
                    suggested_next_questions=[],
                )
            return ChatResponse(
                reply_text="I can help set your preferences. Try FILL mode and tell me servings and meals per day.",
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
            )

        if mode == "fill":
            parsed = self._parse_prefs_from_message(message)
            missing_questions = self._collect_missing_questions(parsed)
            if missing_questions:
                return ChatResponse(
                    reply_text="I need a bit more info to propose your prefs.",
                    confirmation_required=False,
                    proposal_id=None,
                    proposed_actions=[],
                    suggested_next_questions=missing_questions,
                )

            prefs = self._merge_with_defaults(user_id, parsed)
            proposal_id = str(uuid.uuid4())
            action = ProposedUpsertPrefsAction(prefs=prefs)
            self.proposal_store.save(user_id, proposal_id, action)

            return ChatResponse(
                reply_text="I prepared a prefs update. Please confirm to apply.",
                confirmation_required=True,
                proposal_id=proposal_id,
                proposed_actions=[action],
                suggested_next_questions=[],
            )

        return ChatResponse(
            reply_text="Unsupported mode. Use ask or fill.",
            confirmation_required=False,
            proposal_id=None,
            proposed_actions=[],
            suggested_next_questions=[],
        )

    def confirm(self, user_id: str, proposal_id: str, confirm: bool) -> bool:
        action = self.proposal_store.pop(user_id, proposal_id)
        if not action:
            return False
        if not confirm:
            return False
        self.prefs_service.upsert_prefs(user_id, action.prefs)
        return True

    def _merge_with_defaults(self, user_id: str, parsed: UserPrefs) -> UserPrefs:
        existing = self.prefs_service.get_prefs(user_id)
        merged = existing.model_copy()
        if parsed.servings and parsed.servings > 0:
            merged.servings = parsed.servings
        if parsed.meals_per_day and parsed.meals_per_day > 0:
            merged.meals_per_day = parsed.meals_per_day
        if parsed.allergies:
            merged.allergies = parsed.allergies
        if parsed.dislikes:
            merged.dislikes = parsed.dislikes
        if parsed.cuisine_likes:
            merged.cuisine_likes = parsed.cuisine_likes
        if parsed.notes:
            merged.notes = parsed.notes
        return merged

    def _parse_prefs_from_message(self, message: str) -> UserPrefs:
        servings = self._extract_first_int(message, ["serving", "servings"])
        meals_per_day = self._extract_first_int(message, ["meal per day", "meals per day", "meals"])

        def extract_list(keyword: str) -> List[str]:
            if keyword not in message:
                return []
            after = message.split(keyword, 1)[1]
            parts = re.split(r"[,.]", after)
            return [p.strip() for p in parts[0].split(" and ") if p.strip()]

        allergies = extract_list("allerg")
        dislikes = extract_list("dislike")
        cuisine_likes = extract_list("cuisine")

        return UserPrefs(
            allergies=allergies,
            dislikes=dislikes,
            cuisine_likes=cuisine_likes,
            servings=servings or 0,
            meals_per_day=meals_per_day or 0,
            notes="",
        )

    def _collect_missing_questions(self, prefs: UserPrefs) -> List[str]:
        questions: List[str] = []
        if prefs.servings < 1:
            questions.append("How many servings should I plan for?")
        if prefs.meals_per_day < 1:
            questions.append("How many meals per day do you want?")
        return questions

    def _extract_first_int(self, text: str, keywords: List[str]) -> int | None:
        for kw in keywords:
            pattern = rf"{kw}[^0-9]*(\d+)"
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None

    def _format_prefs(self, prefs: UserPrefs) -> str:
        return (
            f"Servings: {prefs.servings}, meals/day: {prefs.meals_per_day}. "
            f"Allergies: {', '.join(prefs.allergies) or 'none'}. "
            f"Dislikes: {', '.join(prefs.dislikes) or 'none'}. "
            f"Cuisine likes: {', '.join(prefs.cuisine_likes) or 'none'}."
        )
