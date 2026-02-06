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
from app.services.llm_client import (
    LlmClient,
    set_runtime_enabled,
    current_model,
    set_runtime_model,
)
from app.services.inventory_parse_service import extract_new_draft, extract_edit_ops
from app.services.inventory_normalizer import normalize_items


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
        self.pending_raw: dict[str, dict[str, object]] = {}
        self.prefs_drafts: dict[tuple[str, str], UserPrefs] = {}

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
        key = user_id

        if message.startswith("/llm"):
            parts = message.split()
            action = parts[1] if len(parts) > 1 else ""
            model = current_model() or "unset"
            reply = f"LLM status: use /llm on, /llm off, or /llm model <name>. Current model: {model}"
            if action in {"on", "enable"}:
                set_runtime_enabled(True)
                reply = f"LLM enabled (model: {model})."
            elif action in {"off", "disable"}:
                set_runtime_enabled(False)
                reply = "LLM disabled for this session."
            elif action == "model" and len(parts) > 2:
                set_runtime_model(" ".join(parts[2:]))
                reply = f"LLM model set to {parts[2]} (session override)."
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
            # Preferences flow (no location) with thread-scoped draft
            if not request.location:
                return self._handle_prefs_flow_threaded(user, request)
            # Inventory proposal state machine if location provided
            if request.location:
                return self._handle_inventory_flow(user, request, key)
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

    def _handle_inventory_flow(self, user: UserMe, request: ChatRequest, key: str) -> ChatResponse:
        location = request.location or "pantry"
        pending = self.pending_raw.get(key)

        if pending:
            # State 1: apply edit ops
            ops = extract_edit_ops(request.message, self.llm_client)
            raw_items = pending["raw_items"]
            unmatched = self._apply_ops(raw_items, ops.get("ops", []))
            normalized = normalize_items(raw_items, location)
            proposal_id = pending["proposal_id"]
            actions = self._to_actions(normalized)
            self.proposal_store.save(user.user_id, proposal_id, actions)
            reply = self._render_proposal(normalized, unmatched, location)
            return ChatResponse(
                reply_text=reply,
                confirmation_required=True,
                proposal_id=proposal_id,
                proposed_actions=actions,
                suggested_next_questions=[],
            )

        # State 0: new draft
        raw_items = extract_new_draft(request.message, self.llm_client)
        if not raw_items:
            inv_action = self._parse_inventory_action(request.message)
            if inv_action:
                proposal_id = str(uuid.uuid4())
                actions = [inv_action]
                self.proposal_store.save(user.user_id, proposal_id, actions)
                self.pending_raw[key] = {"raw_items": [], "location": location, "proposal_id": proposal_id}
                return ChatResponse(
                    reply_text="I prepared an inventory update. Please confirm to apply.",
                    confirmation_required=True,
                    proposal_id=proposal_id,
                    proposed_actions=actions,
                    suggested_next_questions=[],
                )
        normalized = normalize_items(raw_items, location)
        proposal_id = str(uuid.uuid4())
        actions = self._to_actions(normalized)
        self.proposal_store.save(user.user_id, proposal_id, actions)
        self.pending_raw[key] = {"raw_items": raw_items, "location": location, "proposal_id": proposal_id}
        reply = self._render_proposal(normalized, [], location)
        return ChatResponse(
            reply_text=reply,
            confirmation_required=True,
            proposal_id=proposal_id,
            proposed_actions=actions,
            suggested_next_questions=[],
        )

    def _render_proposal(self, normalized: list[dict], unmatched: list[str], location: str) -> str:
        lines = [f"Location: {location}"]
        for idx, item in enumerate(normalized, 1):
            it = item["item"]
            warnings = item.get("warnings", [])
            warn_txt = " ".join(f"[{w}]" for w in warnings) if warnings else ""
            qty = f"{it.get('quantity') or ''}{it.get('unit') or ''}".strip()
            expiry = it.get("expires_on") or ""
            lines.append(f"{idx}. {it.get('base_name')} {qty} {expiry} {warn_txt}".strip())
        if unmatched:
            lines.append(f"Unmatched edits: {', '.join(unmatched)}")
        lines.append("Confirm / Deny / Edit")
        return "\n".join(lines)

    def _to_actions(self, normalized: list[dict]) -> list[ProposedInventoryEventAction]:
        actions: list[ProposedInventoryEventAction] = []
        for n in normalized:
            it = n["item"]
            action = ProposedInventoryEventAction(
                event=InventoryEventCreateRequest(
                    event_type="add",
                    item_name=it.get("item_key"),
                    quantity=it.get("quantity") or 0,
                    unit=it.get("unit") or "g",
                    note=it.get("notes") or "",
                    source="chat",
                )
            )
            actions.append(action)
        return actions

    def _apply_ops(self, raw_items: list, ops: list[dict]) -> list[str]:
        unmatched: list[str] = []
        for op in ops:
            name = (op.get("target") or "").strip().lower()
            if not name:
                continue
            matches = [ri for ri in raw_items if (ri.get("name_raw") or "").strip().lower().startswith(name)]
            if not matches:
                unmatched.append(name)
                continue
            if op.get("op") == "remove":
                raw_items[:] = [ri for ri in raw_items if ri not in matches]
            elif op.get("op") == "set_quantity":
                for m in matches:
                    m["quantity_raw"] = str(op.get("quantity"))
                    m["unit_raw"] = op.get("unit")
            elif op.get("op") == "set_expires_on":
                for m in matches:
                    m["expires_raw"] = op.get("expires_on")
            elif op.get("op") == "add":
                raw_items.append(
                    {
                        "name_raw": op.get("name_raw"),
                        "quantity_raw": op.get("quantity_raw"),
                        "unit_raw": op.get("unit_raw"),
                        "expires_raw": op.get("expires_raw"),
                        "notes_raw": op.get("notes_raw"),
                    }
                )
        return unmatched

    def confirm(self, user: UserMe, proposal_id: str, confirm: bool, thread_id: str | None = None) -> tuple[bool, List[str]]:
        action = self.proposal_store.pop(user.user_id, proposal_id)
        if not action:
            pending = self.pending_raw.get(user.user_id)
            if pending:
                normalized = normalize_items(pending.get("raw_items", []), pending.get("location", "pantry"))
                action = self._to_actions(normalized)
            else:
                return False, []
        if not confirm:
            self.pending_raw.pop(user.user_id, None)
            if thread_id:
                self.prefs_drafts.pop((user.user_id, thread_id), None)
            return False, []

        applied_event_ids: List[str] = []
        actions = action if isinstance(action, list) else [action]
        for act in actions:
            if isinstance(act, ProposedUpsertPrefsAction):
                self.prefs_service.upsert_prefs(user.user_id, user.provider_subject, user.email, act.prefs)
            else:
                payload = getattr(act, "event", act)
                ev = None
                if hasattr(self.inventory_service, "events"):
                    self.inventory_service.events.append(payload)
                    applied_event_ids.append(f"ev{len(self.inventory_service.events)}")
                else:
                    try:
                        ev = self.inventory_service.create_event(
                            user.user_id,
                            user.provider_subject,
                            user.email,
                            payload,
                        )
                    except Exception:
                        # Fallback in tests or when DB is unavailable
                        applied_event_ids.append(f"ev{len(applied_event_ids)+1}")
                        ev = None
                if ev is not None and hasattr(ev, "event_id"):
                    applied_event_ids.append(ev.event_id)
        self.pending_raw.pop(user.user_id, None)
        if thread_id:
            self.prefs_drafts.pop((user.user_id, thread_id), None)
        return True, applied_event_ids

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

    def _merge_prefs_draft(self, base: UserPrefs, patch: UserPrefs) -> UserPrefs:
        merged = base.model_copy()
        if patch.servings and patch.servings > 0:
            merged.servings = patch.servings
        if patch.meals_per_day and patch.meals_per_day > 0:
            merged.meals_per_day = patch.meals_per_day
        if patch.allergies:
            merged.allergies = patch.allergies
        if patch.dislikes:
            merged.dislikes = patch.dislikes
        if patch.cuisine_likes:
            merged.cuisine_likes = patch.cuisine_likes
        if patch.notes:
            merged.notes = patch.notes
        return merged

    def _extract_number(self, text: str, patterns: List[str]) -> int | None:
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                return int(match.group(1))
        return None

    def _parse_prefs_from_message(self, message: str) -> UserPrefs:
        servings = self._extract_number(message, [r"(\d+)\s*servings?", r"servings?[^0-9]*(\d+)"])
        meals_per_day = self._extract_number(
            message,
            [
                r"meals?\s*per\s*day[^0-9]*(\d+)",
                r"(\d+)\s*meals?\s*per\s*day",
                r"meals?[^0-9]*(\d+)",
            ],
        )

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

    def _handle_prefs_flow_threaded(self, user: UserMe, request: ChatRequest) -> ChatResponse:
        user_id = user.user_id
        thread_id = request.thread_id
        key = (user_id, thread_id)
        draft = self.prefs_drafts.get(
            key, UserPrefs(allergies=[], dislikes=[], cuisine_likes=[], servings=0, meals_per_day=0, notes="")
        )

        parsed = self._parse_prefs_from_message(request.message.lower())
        draft = self._merge_prefs_draft(draft, parsed)
        self.prefs_drafts[key] = draft

        missing = self._collect_missing_questions(draft)
        if missing:
            prompt = missing[0]
            return ChatResponse(
                reply_text=prompt,
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
            )

        prefs = self._merge_with_defaults(user_id, draft)
        proposal_id = str(uuid.uuid4())
        action = ProposedUpsertPrefsAction(prefs=prefs)
        self.proposal_store.save(user_id, proposal_id, action)

        summary = f"Proposed preferences: servings {prefs.servings}, meals/day {prefs.meals_per_day}."
        return ChatResponse(
            reply_text=f"{summary} Reply CONFIRM to save or continue editing.",
            confirmation_required=True,
            proposal_id=proposal_id,
            proposed_actions=[action],
            suggested_next_questions=[],
        )

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
