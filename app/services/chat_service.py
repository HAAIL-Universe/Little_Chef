import re
import uuid
from typing import List, Optional

from app.schemas import (
    ChatRequest,
    ChatResponse,
    ProposedUpsertPrefsAction,
    ProposedInventoryEventAction,
    UserPrefs,
    InventoryEventCreateRequest,
    UserMe,
)
from app.services.prefs_service import PrefsService
from app.services.proposal_store import ProposalStore
from app.services.inventory_service import InventoryService
from app.services.llm_client import LlmClient, set_runtime_enabled, set_runtime_model


class ChatService:
    def __init__(
        self,
        prefs_service: PrefsService,
        inventory_service: InventoryService,
        proposal_store: ProposalStore,
        llm_client: LlmClient | None = None,
    ) -> None:
        self.prefs_service = prefs_service
        self.inventory_service = inventory_service
        self.proposal_store = proposal_store
        self.llm_client = llm_client

    @property
    def _system_prompt(self) -> str:
        return (
            "You are Little Chef, a concise culinary assistant. "
            "Answer briefly (1-3 sentences) and stay helpful about cooking, ingredients, or meals. "
            "Do not ask the user to confirm actions; just provide guidance."
        )

    def handle_chat(self, user: UserMe, request: ChatRequest) -> ChatResponse:
        mode = request.mode
        message = request.message.lower()
        user_id = user.user_id

        if message.startswith("/llm"):
            parts = message.split()
            action = parts[1] if len(parts) > 1 else ""
            reply = "LLM status: use /llm on, /llm off, or /llm model <name>."
            if action in {"on", "enable"}:
                set_runtime_enabled(True)
                reply = "LLM enabled (requires OPENAI_MODEL=gpt-5*-mini or gpt-5*-nano)."
            elif action in {"off", "disable"}:
                set_runtime_enabled(False)
                reply = "LLM disabled for this session."
            elif action == "model" and len(parts) > 2:
                model_name = parts[2]
                set_runtime_model(model_name)
                reply = f"LLM model set to {model_name} for this session."
            return ChatResponse(
                reply_text=reply,
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
            )

        if mode == "ask":
            ask_reply = self._handle_ask(user_id, message)
            if ask_reply:
                return ask_reply
            reply_text = "I can help set preferences or inventory. Try FILL mode with details."
            if self.llm_client:
                llm_text = self.llm_client.generate_reply(self._system_prompt, request.message)
                if llm_text:
                    reply_text = llm_text
            return ChatResponse(
                reply_text=reply_text,
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
            )

        if mode == "fill":
            inv_action = self._parse_inventory_action(message)
            if inv_action:
                proposal_id = str(uuid.uuid4())
                self.proposal_store.save(user_id, proposal_id, inv_action)
                return ChatResponse(
                    reply_text="I prepared an inventory update. Please confirm to apply.",
                    confirmation_required=True,
                    proposal_id=proposal_id,
                    proposed_actions=[inv_action],
                    suggested_next_questions=[],
                )

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

    def confirm(self, user: UserMe, proposal_id: str, confirm: bool) -> tuple[bool, List[str]]:
        action = self.proposal_store.pop(user.user_id, proposal_id)
        if not action:
            return False, []
        if not confirm:
            return False, []

        applied_event_ids: List[str] = []
        if isinstance(action, ProposedUpsertPrefsAction):
            self.prefs_service.upsert_prefs(user.user_id, user.provider_subject, user.email, action.prefs)
            return True, applied_event_ids
        if isinstance(action, ProposedInventoryEventAction):
            ev = self.inventory_service.create_event(
                user.user_id,
                user.provider_subject,
                user.email,
                action.event,
            )
            applied_event_ids.append(ev.event_id)
            return True, applied_event_ids
        return False, []

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

    def _handle_ask(self, user_id: str, message: str) -> Optional[ChatResponse]:
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
        if any(k in message for k in ["low on", "running out", "low stock"]):
            low = self.inventory_service.low_stock(user_id)
            if not low.items:
                reply = "You are not low on any tracked items."
            else:
                summary = ", ".join(f"{i.item_name} ({i.quantity}{i.unit})" for i in low.items)
                reply = f"Low stock: {summary}"
            return ChatResponse(
                reply_text=reply,
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
            )
        if any(k in message for k in ["what do i have", "inventory", "in stock"]):
            summary = self.inventory_service.summary(user_id)
            if not summary.items:
                reply = "Inventory is empty."
            else:
                content = ", ".join(f"{i.item_name} ({i.quantity}{i.unit})" for i in summary.items)
                reply = f"Inventory: {content}"
            return ChatResponse(
                reply_text=reply,
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
            )
        return None

    def _parse_inventory_action(self, message: str) -> Optional[ProposedInventoryEventAction]:
        lower = message.lower()
        event_type = self._infer_event_type(lower)
        if not event_type:
            return None
        parsed = self._extract_item_quantity_unit(lower)
        if not parsed:
            return None
        item_name, quantity, unit = parsed
        if item_name in {"servings", "meal", "meals", "serving"}:
            return None
        req = InventoryEventCreateRequest(
            event_type=event_type,
            item_name=item_name,
            quantity=quantity,
            unit=unit,
            note="",
            source="chat",
        )
        return ProposedInventoryEventAction(event=req)

    def _infer_event_type(self, text: str) -> Optional[str]:
        if any(k in text for k in ["bought", "added", "got", "picked up", "stocked"]):
            return "add"
        if any(k in text for k in ["cooked", "made", "meal"]):
            return "consume_cooked"
        if any(k in text for k in ["used", "used up", "for recipe"]):
            return "consume_used_separately"
        if any(k in text for k in ["threw", "binned", "expired", "gone off"]):
            return "consume_thrown_away"
        if any(k in text for k in ["set", "correct", "actually have"]):
            if "serving" in text or "meal" in text:
                return None
            return "adjust"
        return None

    def _extract_item_quantity_unit(self, text: str) -> Optional[tuple[str, float, str]]:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(g|gram|grams|ml|milliliter|milliliters|l|liter|liters)", text)
        if match:
            qty = float(match.group(1))
            raw_unit = match.group(2)
            unit = "g" if "g" in raw_unit else "ml"
            name_part = text[match.end():].strip()
            if not name_part:
                name_part = "item"
            return name_part, qty, unit
        match = re.search(r"(\d+)", text)
        if match:
            qty = float(match.group(1))
            words = text.split()
            unit = "count"
            # naive item name: last word
            item_name = words[-1] if words else "item"
            if item_name.isdigit():
                return None
            return item_name, qty, unit
        return None
