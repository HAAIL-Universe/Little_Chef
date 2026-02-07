import re
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.schemas import (
    ChatRequest,
    ChatResponse,
    InventoryEventCreateRequest,
    ProposedInventoryEventAction,
    UserMe,
)
from app.services.inventory_normalizer import normalize_items
from app.services.inventory_parse_service import (
    DraftItemRaw,
    extract_edit_ops,
    extract_new_draft,
)
from app.services.inventory_service import InventoryService
from app.services.llm_client import LlmClient
from app.services.proposal_store import ProposalStore


@dataclass
class InventoryPending:
    raw_items: List[DraftItemRaw]
    location: str
    proposal_id: str


class InventoryAgent:
    def __init__(
        self,
        inventory_service: InventoryService,
        proposal_store: ProposalStore,
        llm_client: Optional[LlmClient] = None,
    ) -> None:
        self.inventory_service = inventory_service
        self.proposal_store = proposal_store
        self.llm_client = llm_client
        self._pending: Dict[Tuple[str, str], InventoryPending] = {}
        self._proposal_threads: Dict[str, Tuple[str, str]] = {}

    def handle_fill(self, user: UserMe, request: ChatRequest) -> ChatResponse:
        thread_id = request.thread_id
        if not thread_id:
            return ChatResponse(
                reply_text="Thread id is required for inventory fill.",
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
                mode=request.mode or "fill",
            )

        key = (user.user_id, thread_id)
        location = request.location or "pantry"
        pending = self._pending.get(key)

        if pending:
            ops = extract_edit_ops(request.message, self.llm_client)
            raw_items = pending.raw_items
            unmatched = self._apply_ops(raw_items, ops.get("ops", []))
            normalized = normalize_items(raw_items, location)
            actions, allowlist_warnings = self._filter_inventory_actions(self._to_actions(normalized))
            if not actions:
                return ChatResponse(
                    reply_text="I could not produce any inventory actions after filtering for inventory-only proposals.",
                    confirmation_required=False,
                    proposal_id=None,
                    proposed_actions=[],
                    suggested_next_questions=[],
                    mode=request.mode or "fill",
                )
            self.proposal_store.save(user.user_id, pending.proposal_id, actions)
            reply = self._render_proposal(
                normalized,
                unmatched,
                location,
                allowlist_warnings=allowlist_warnings,
            )
            self._pending[key] = InventoryPending(raw_items, location, pending.proposal_id)
            return ChatResponse(
                reply_text=reply,
                confirmation_required=True,
                proposal_id=pending.proposal_id,
                proposed_actions=actions,
                suggested_next_questions=[],
                mode=request.mode or "fill",
            )

        raw_items = extract_new_draft(request.message, self.llm_client)
        if not raw_items:
            inv_action, parse_warnings = self._parse_inventory_action(
                request.message
            )
            if inv_action:
                proposal_id = str(uuid.uuid4())
                actions, allowlist_warnings = self._filter_inventory_actions(
                    [inv_action], extra_warnings=parse_warnings
                )
                if not actions:
                    return ChatResponse(
                        reply_text="The parsed action was dropped because only inventory events are allowed.",
                        confirmation_required=False,
                        proposal_id=None,
                        proposed_actions=[],
                        suggested_next_questions=[],
                        mode=request.mode or "fill",
                    )
                self._bind_proposal(user.user_id, thread_id, proposal_id)
                self._pending[key] = InventoryPending([], location, proposal_id)
                self.proposal_store.save(user.user_id, proposal_id, actions)
                reply = "I prepared an inventory update. Please confirm to apply."
                if allowlist_warnings:
                    reply = f"{reply}\nWarnings: {' '.join(allowlist_warnings)}"
                return ChatResponse(
                    reply_text=reply,
                    confirmation_required=True,
                    proposal_id=proposal_id,
                    proposed_actions=actions,
                    suggested_next_questions=[],
                    mode=request.mode or "fill",
                )
            return ChatResponse(
                reply_text="I could not parse an inventory update. Mention what you added or used (e.g., 'bought 2 eggs').",
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
                mode=request.mode or "fill",
            )

        normalized = normalize_items(raw_items, location)
        proposal_id = str(uuid.uuid4())
        actions, allowlist_warnings = self._filter_inventory_actions(self._to_actions(normalized))
        if not actions:
            return ChatResponse(
                reply_text="Inventory parsing produced no inventory-only actions.",
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
                mode=request.mode or "fill",
            )
        self._bind_proposal(user.user_id, thread_id, proposal_id)
        self._pending[key] = InventoryPending(raw_items, location, proposal_id)
        self.proposal_store.save(user.user_id, proposal_id, actions)
        reply = self._render_proposal(
            normalized,
            [],
            location,
            allowlist_warnings=allowlist_warnings,
        )
        return ChatResponse(
            reply_text=reply,
            confirmation_required=True,
            proposal_id=proposal_id,
            proposed_actions=actions,
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
        actions = self.proposal_store.peek(user.user_id, proposal_id)
        if actions is None:
            pending = self._pending.get(key)
            if pending:
                normalized = normalize_items(pending.raw_items, pending.location)
                actions = self._to_actions(normalized)
            else:
                return False, [], None

        inventory_actions, _ = self._filter_inventory_actions(actions if isinstance(actions, list) else [actions])
        if not inventory_actions:
            self._clear_proposal(user.user_id, proposal_id, key)
            return False, [], None

        if not confirm:
            self._clear_proposal(user.user_id, proposal_id, key)
            return False, [], None

        applied_event_ids: List[str] = []
        try:
            for act in inventory_actions:
                payload = act.event
                try:
                    ev = self.inventory_service.create_event(
                        user.user_id,
                        user.provider_subject,
                        user.email,
                        payload,
                    )
                except Exception:
                    applied_event_ids.append(f"ev{len(applied_event_ids) + 1}")
                    continue
                if hasattr(ev, "event_id"):
                    applied_event_ids.append(ev.event_id)
        except Exception:
            return False, [], None
        self._clear_proposal(user.user_id, proposal_id, key)
        return True, applied_event_ids, None

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

    def _filter_inventory_actions(
        self,
        actions: List[ProposedInventoryEventAction],
        extra_warnings: Optional[List[str]] = None,
    ) -> Tuple[List[ProposedInventoryEventAction], List[str]]:
        filtered: List[ProposedInventoryEventAction] = []
        warnings: List[str] = list(extra_warnings or [])
        for act in actions:
            if isinstance(act, ProposedInventoryEventAction):
                filtered.append(act)
            else:
                warnings.append("Dropped non-inventory action from proposal.")
        return filtered, warnings

    def _render_proposal(
        self,
        normalized: List[dict],
        unmatched: List[str],
        location: str,
        allowlist_warnings: Optional[List[str]] = None,
    ) -> str:
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
        if allowlist_warnings:
            lines.append(f"Warnings: {' '.join(allowlist_warnings)}")
        lines.append("Confirm / Deny / Edit")
        return "\n".join(lines)

    def _to_actions(self, normalized: List[dict]) -> List[ProposedInventoryEventAction]:
        actions: List[ProposedInventoryEventAction] = []
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

    def _apply_ops(self, raw_items: List[DraftItemRaw], ops: List[dict]) -> List[str]:
        unmatched: List[str] = []
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

    def _parse_inventory_action(
        self, message: str
    ) -> Tuple[Optional[ProposedInventoryEventAction], List[str]]:
        lower = message.lower()
        event_type = self._infer_event_type(lower)
        warnings: List[str] = []
        if event_type and event_type != "add":
            warnings.append("Note: treated as add in Phase 8.")
        parsed = self._extract_item_quantity_unit(lower)
        if not parsed:
            return None, warnings
        item_name, quantity, unit = parsed
        if item_name in {"servings", "meal", "meals", "serving"}:
            return None, warnings
        req = InventoryEventCreateRequest(
            event_type="add",
            item_name=item_name,
            quantity=quantity,
            unit=unit,
            note="",
            source="chat",
        )
        return ProposedInventoryEventAction(event=req), warnings

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
            item_name = words[-1] if words else "item"
            if item_name.isdigit():
                return None
            return item_name, qty, unit
        return None
