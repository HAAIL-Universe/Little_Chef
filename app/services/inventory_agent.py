import re
import uuid
from dataclasses import dataclass
from typing import Dict, List, Match, Optional, Tuple

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


SEPARATORS = [",", ";", " and ", " plus ", " also ", " then "]
SPLIT_PATTERN = re.compile(r",|;|\band\b|\bplus\b|\balso\b|\bthen\b", re.IGNORECASE)
QUANTITY_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(g|gram|grams|kg|kilogram|kilograms|l|liter|liters|ml|milliliter|milliliters)?",
    re.IGNORECASE,
)
FALLBACK_FILLERS = [
    "i've got",
    "i have",
    "i got",
    "i just got",
    "i just bought",
    "bought",
    "picked up",
    "grabbed",
    "got",
    "just got",
    "the",
    "a",
]
DATE_CONTEXT_PHRASES = ["use by", "sell by", "expires on", "best before", "due by"]
ORDINAL_SUFFIXES = ("st", "nd", "rd", "th")


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
            inv_actions, parse_warnings = self._parse_inventory_actions(request.message)
            if inv_actions:
                proposal_id = str(uuid.uuid4())
                actions, allowlist_warnings = self._filter_inventory_actions(
                    inv_actions, extra_warnings=parse_warnings
                )
                if not actions:
                    return ChatResponse(
                        reply_text="The parsed actions were dropped because only inventory events are allowed.",
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

    def _parse_inventory_actions(
        self, message: str
    ) -> Tuple[List[ProposedInventoryEventAction], List[str]]:
        text = message.strip()
        if not text:
            return [], []
        lower = text.lower()
        actions: List[ProposedInventoryEventAction] = []
        warnings: List[str] = []
        event_type = self._infer_event_type(lower)
        if event_type and event_type != "add":
            self._append_warning(warnings, "Note: treated as add in Phase 8.")

        segments = self._split_segments(text)
        matches = list(QUANTITY_PATTERN.finditer(lower))
        seen: set[str] = set()
        fallback_missing_quantity = False

        if matches:
            for match in matches:
                if self._looks_like_date_quantity(lower, match):
                    continue
                start = self._previous_separator(lower, match.start())
                end = self._next_separator(lower, match.end())
                segment = text[start:end]
                rel_start = match.start() - start
                rel_end = match.end() - start
                name_candidate = self._remove_numeric_from_phrase(segment, rel_start, rel_end)
                item_name = self._clean_segment_text(name_candidate)
                if not item_name:
                    item_name = self._guess_item_name(text, match.start())
                if not item_name:
                    item_name = "item"
                quantity, unit = self._normalize_quantity_and_unit(
                    match.group(1), match.group(2)
                )
                key = item_name.lower()
                if key in seen:
                    continue
                seen.add(key)
                actions.append(
                    ProposedInventoryEventAction(
                        event=InventoryEventCreateRequest(
                            event_type="add",
                            item_name=item_name,
                            quantity=quantity,
                            unit=unit,
                            note="",
                            source="chat",
                        )
                    )
                )
            for segment in segments:
                cleaned = self._clean_segment_text(segment)
                if not cleaned:
                    continue
                if re.search(r"\d", cleaned):
                    continue
                key = cleaned.lower()
                if key in seen:
                    continue
                fallback_missing_quantity = True
                seen.add(key)
                actions.append(
                    ProposedInventoryEventAction(
                        event=InventoryEventCreateRequest(
                            event_type="add",
                            item_name=cleaned,
                            quantity=1.0,
                            unit="count",
                            note="",
                            source="chat",
                        )
                    )
                )
        else:
            for segment in segments:
                cleaned = self._clean_segment_text(segment)
                if not cleaned:
                    continue
                key = cleaned.lower()
                if key in seen:
                    continue
                fallback_missing_quantity = True
                seen.add(key)
                actions.append(
                    ProposedInventoryEventAction(
                        event=InventoryEventCreateRequest(
                            event_type="add",
                            item_name=cleaned,
                            quantity=1.0,
                            unit="count",
                            note="",
                            source="chat",
                        )
                    )
                )

        if fallback_missing_quantity:
            self._append_warning(warnings, "FALLBACK_MISSING_QUANTITY")

        if len(segments) > 1 and len(actions) == 1:
            self._append_warning(warnings, "FALLBACK_MAY_HAVE_COLLAPSED_LIST")

        return actions, warnings

    def _parse_inventory_action(
        self, message: str
    ) -> Tuple[Optional[ProposedInventoryEventAction], List[str]]:
        actions, warnings = self._parse_inventory_actions(message)
        if not actions:
            return None, warnings
        return actions[0], warnings

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

    def _previous_separator(self, lower_text: str, index: int) -> int:
        boundary = 0
        for sep in SEPARATORS:
            pos = lower_text.rfind(sep, 0, index)
            if pos != -1:
                candidate = pos + len(sep)
                if candidate > boundary:
                    boundary = candidate
        return boundary

    def _next_separator(self, lower_text: str, index: int) -> int:
        boundary = len(lower_text)
        for sep in SEPARATORS:
            pos = lower_text.find(sep, index)
            if pos != -1 and pos < boundary:
                boundary = pos
        return boundary

    def _remove_numeric_from_phrase(self, phrase: str, start: int, end: int) -> str:
        before = phrase[:start]
        after = phrase[end:]
        candidate = f"{before} {after}"
        return " ".join(candidate.split())

    def _clean_segment_text(self, segment: str) -> str:
        cleaned = re.sub(r"\s+", " ", segment).strip(" ,;.")
        lowered = cleaned.lower()
        for filler in FALLBACK_FILLERS:
            if lowered.startswith(filler + " ") or lowered == filler:
                cleaned = cleaned[len(filler) :].strip()
                lowered = cleaned.lower()
        return cleaned.strip(" ,;.")

    def _guess_item_name(self, text: str, index: int, limit: int = 5) -> str:
        window = text[max(0, index - 40) : index]
        words = re.findall(r"[\w'-]+", window)
        if not words:
            return ""
        return " ".join(words[-limit:])

    def _normalize_quantity_and_unit(
        self, quantity_str: str, unit_str: Optional[str]
    ) -> Tuple[float, str]:
        qty = float(quantity_str.replace(",", "."))
        raw_unit = (unit_str or "").strip().lower()
        if raw_unit in {"g", "gram", "grams"}:
            return qty, "g"
        if raw_unit in {"kg", "kilogram", "kilograms"}:
            return qty * 1000, "g"
        if raw_unit in {"ml", "milliliter", "milliliters"}:
            return qty, "ml"
        if raw_unit in {"l", "liter", "liters"}:
            return qty * 1000, "ml"
        return qty, "count"

    def _split_segments(self, text: str) -> List[str]:
        return [segment.strip() for segment in SPLIT_PATTERN.split(text) if segment.strip()]

    def _append_warning(self, warnings: List[str], value: str) -> None:
        if value not in warnings:
            warnings.append(value)

    def _looks_like_date_quantity(self, lower_text: str, match: Match[str]) -> bool:
        start, end = match.span()
# skip ordinals directly following the digits (e.g., "10th")
        suffix = lower_text[end:end + 2]
        if any(suffix.startswith(ord_suffix) for ord_suffix in ORDINAL_SUFFIXES):
            return True
        context_start = max(0, start - 30)
        context = lower_text[context_start:start]
        if any(phrase in context for phrase in DATE_CONTEXT_PHRASES):
            return True
        return False
