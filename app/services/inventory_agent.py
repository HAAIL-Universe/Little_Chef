import re
import uuid
from dataclasses import dataclass
from typing import Dict, List, Match, Optional, Set, Tuple

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
    r"(\d+(?:\.\d+)?)(?:\s*(g|gram|grams|kg|kilogram|kilograms|kilo|kilos|l|liter|liters|litre|litres|ml|milliliter|milliliters)\b)?",
    re.IGNORECASE,
)
FALLBACK_FILLERS = [
    "i've got",
    "i ve got",
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
    "half left",
    "about half left",
]
FALLBACK_ATTACHMENT_DROPPED = "FALLBACK_ATTACHMENT_DROPPED"
DATE_CONTEXT_PHRASES = ["use by", "sell by", "expires on", "best before", "due by"]
ATTACHMENT_ONLY_WORDS = {"total", "altogether", "about", "roughly", "around", "approx", "approximately"}
CHATTER_WORDS = {"cheers", "done", "ignore", "yeah"}
CHATTER_DROP_PHRASES = {"ignore that", "cheers", "done"}
UNCERTAINTY_MARKERS = {"not sure", "maybe", "how much", "no idea"}
CHATTER_LEADING_PREFIXES = (
    "i've just",
    "ive just",
    "i ve just",
    "i've got",
    "ive got",
    "i ve got",
    "i have",
    "i just",
    "just got",
    "just bought",
    "finished checking",
    "just checked",
    "alright little chef",
    "okay little chef",
    "hey little chef",
)
DATE_MARKER_PHRASES = {"use by", "use-by", "best before", "bb"}
ORDINAL_SUFFIXES = ("st", "nd", "rd", "th")
ORDINAL_PATTERN = r"\d+(?:st|nd|rd|th)"
MONTH_NAME_PATTERN = r"(?:january|february|march|april|may|june|july|august|september|october|november|december)"
USE_BY_VALUE_PATTERN = re.compile(
    rf"({ORDINAL_PATTERN})\s+(?:on|for)\s+(?:the\s+)?([\w'-]+(?:\s+[\w'-]+)?)",
    re.IGNORECASE,
)
SENTENCE_TERMINATORS = (".", "!", "?")
UNIT_KEYWORDS = {
    "g",
    "gram",
    "grams",
    "kg",
    "kilogram",
    "kilograms",
    "kilo",
    "kilos",
    "ml",
    "milliliter",
    "milliliters",
    "l",
    "liter",
    "liters",
    "litre",
    "litres",
}
CONTEXT_IGNORE_WORDS = {"of", "the", "and", "also", "plus", "with"}
QUANTITY_ADVERBS = {"about", "around", "approx", "approximately"}
FALLBACK_IGNORE_PHRASES = {"i've just been through the cupboard", "no idea how many"}
AFTER_IGNORE_WORDS = CONTEXT_IGNORE_WORDS | QUANTITY_ADVERBS | UNIT_KEYWORDS
BEFORE_IGNORE_WORDS = CONTEXT_IGNORE_WORDS | QUANTITY_ADVERBS
INTRO_LOCATION_WORDS = {"cupboard", "fridge", "pantry"}
CONTAINER_WORDS = {
    "bag",
    "bags",
    "pack",
    "packs",
    "bottle",
    "bottles",
    "jar",
    "jars",
    "can",
    "cans",
    "loaf",
    "loaves",
    "tin",
    "tins",
    "pot",
    "pots",
    "piece",
    "pieces",
    "bulb",
    "slice",
    "slices",
}
BARE_FILLER_WORDS = {
    "unopened",
    "sliced",
    "left",
    "cereal",
    "now",
    "fridge",
    "freezer",
    "stuff",
    "half",
    "third",
    "quarter",
    "both",
}
ITEM_STOP_WORDS = (
    CONTEXT_IGNORE_WORDS
    | CONTAINER_WORDS
    | QUANTITY_ADVERBS
    | UNIT_KEYWORDS
    | ATTACHMENT_ONLY_WORDS
    | CHATTER_WORDS
    | (BARE_FILLER_WORDS - {"cereal"})
)
PARTIAL_KEYWORDS = UNIT_KEYWORDS | CONTAINER_WORDS
NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}
NUMBER_WORD_PATTERN = re.compile(r"\b(" + r"|".join(re.escape(word) for word in NUMBER_WORDS) + r")\b", re.IGNORECASE)

DATE_STRIP_PATTERN = re.compile(
    rf"\b(?:best before|use by|use-by|sell by|expires on|due by)\b[^,;.]*"
    rf"|\bbefore\b[^,;.]*\b{MONTH_NAME_PATTERN}\b[^,;.]*(?:\s*\d{{4}})?",
    re.IGNORECASE,
)
FRACTION_LEFT_PATTERN = re.compile(
    r"^(?:a|about)\s+(?:half|third|quarter)\s+left$", re.IGNORECASE
)
SECTION_TRANSITION_PATTERN = re.compile(
    r"\s+(?=(?:now|and)\s+(?:fridge|freezer|cupboard|pantry)\b)",
    re.IGNORECASE,
)
FRACTION_STATE_PATTERN = re.compile(
    r"\b(half|third|quarter)\s+(left|full)\b",
    re.IGNORECASE,
)
FRACTION_VALUES: Dict[str, float] = {"half": 0.5, "third": 1 / 3, "quarter": 0.25}
LEAD_PREFIXES = (
    "quick stock check",
    "quick pantry scan",
    "quick pantry check",
    "i've got",
    "both unopened",
    "now fridge stuff",
    "freezer",
    "about half left",
    "half left",
    "a third left",
    "third left",
    "a quarter left",
)
CEREAL_TOKENS = ("coco pops", "cornflakes")

CONTAINER_PHRASE_SEPARATORS = [".", ",", ";", " and ", " plus ", " also ", " then "]
CONTAINER_WORD_HINTS = {
    "tin",
    "tins",
    "can",
    "cans",
    "jar",
    "bottle",
    "bottles",
    "bag",
    "bags",
    "pack",
    "packs",
    "box",
    "boxes",
    "pot",
    "pots",
    "piece",
    "pieces",
    "bulb",
    "loaf",
    "loaves",
    "slice",
    "slices",
}
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
        text = self._replace_number_words(text)
        text = SECTION_TRANSITION_PATTERN.sub(". ", text)
        # Strip greeting patterns like "Alright Little Chef" from the start
        text = re.sub(
            r"^(?:alright|okay|hey|hi|hello)\s+little\s+chef\b[,;:\s]*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        if not text:
            return [], []
        lower = text.lower()
        actions: List[ProposedInventoryEventAction] = []
        warnings: List[str] = []
        seen_dedup_keys: Set[str] = set()
        event_type = self._infer_event_type(lower)
        if event_type and event_type != "add":
            self._append_warning(warnings, "Note: treated as add in Phase 8.")

        segments = self._split_segments(text)
        matches = list(QUANTITY_PATTERN.finditer(lower))
        seen: set[Tuple[str, float, str]] = set()
        fallback_missing_quantity = False
        action_index: Dict[str, int] = {}
        clause_action_index: Dict[Tuple[int, int], int] = {}
        dedup_action_index: Dict[str, int] = {}
        use_by_values = self._extract_use_by_values(lower)

        if matches:
            for idx, match in enumerate(matches):
                if self._looks_like_date_quantity(lower, match):
                    continue
                sentence_start = self._previous_sentence_boundary(lower, match.start())
                sentence_end = self._next_sentence_boundary(lower, match.end())
                start = max(
                    self._previous_separator(lower, match.start()),
                    sentence_start,
                )
                end = min(
                    self._next_separator(lower, match.end()),
                    sentence_end,
                )
                if end <= start:
                    continue
                next_match_start = (
                    matches[idx + 1].start() if idx + 1 < len(matches) else sentence_end
                )
                general_use_by_data = self._find_general_use_by_after(
                    lower, match.end(), sentence_end
                )
                general_use_by: Optional[str] = None
                if general_use_by_data:
                    general_use_by, general_use_by_start = general_use_by_data
                    if general_use_by_start >= next_match_start:
                        general_use_by = None
                segment = text[start:end]
                rel_start = max(0, match.start() - start)
                rel_end = max(0, match.end() - start)
                boundary = self._find_segment_boundary(segment.lower(), rel_end)
                if boundary is not None:
                    end = start + boundary
                    segment = text[start:end]
                    rel_end = min(rel_end, len(segment))
                if rel_end <= rel_start:
                    continue
                clause_text = lower[start:end]
                if self._is_chatter_clause(clause_text):
                    continue
                left_segment = text[:start]
                candidate = self._extract_candidate_phrase(segment, rel_start, rel_end)
                if not candidate:
                    candidate = self._remove_numeric_from_phrase(segment, rel_start, rel_end)
                primary_name = self._clean_segment_text(candidate)
                cereal_candidate = self._extract_cereal_candidate(segment)
                if cereal_candidate:
                    primary_name = cereal_candidate
                fallback_left = ""
                if left_segment:
                    fallback_left_clause = self._extract_left_clause(left_segment)
                    if fallback_left_clause:
                        fallback_left_clause = re.sub(r"\d+", " ", fallback_left_clause)
                        fallback_left = self._clean_segment_text(fallback_left_clause)
                guess_cleaned = self._clean_segment_text(
                    self._guess_item_name(text, match.start())
                )
                fallback_override = ""
                if fallback_left and not self._is_container_candidate(fallback_left):
                    fallback_override = fallback_left
                elif guess_cleaned and not self._is_container_candidate(guess_cleaned):
                    fallback_override = guess_cleaned
                if fallback_override and (
                    not primary_name or self._is_container_candidate(primary_name)
                ):
                    primary_name = fallback_override
                if not primary_name:
                    primary_name = self._guess_item_name(text, match.start())
                item_name = primary_name
                if not item_name:
                    item_name = "item"
                if self._is_filler_text(item_name):
                    guess = self._guess_item_name(text, match.start())
                    if guess:
                        item_name = guess
                    else:
                        continue
                if item_name.lower() in ATTACHMENT_ONLY_WORDS or self._contains_date_marker(
                    item_name
                ):
                    guess = self._guess_item_name(text, match.start())
                    if guess:
                        item_name = guess
                    else:
                        continue
                quantity, unit = self._normalize_quantity_and_unit(
                    match.group(1), match.group(2)
                )
                item_name = self._clamp_multi_anchor(item_name, unit)
                normalized_key = self._normalize_item_key(item_name)
                if not normalized_key:
                    normalized_key = item_name.lower()
                if self._is_disallowed_item_name(item_name, normalized_key):
                    continue
                dedup_key = self._dedup_key(normalized_key)
                measurement_note = self._measurement_note_value(unit, quantity)
                existing_index = action_index.get(normalized_key)
                if existing_index is None:
                    existing_index = dedup_action_index.get(dedup_key)
                use_by_key = self._find_use_by_target(item_name, use_by_values)
                use_by_ord = use_by_values.get(use_by_key) if use_by_key else None
                clause_key = (start, end)
                if measurement_note and existing_index is not None:
                    self._add_note_value(actions[existing_index], measurement_note)
                    if use_by_ord:
                        self._add_note_value(
                            actions[existing_index], f"use_by={use_by_ord}"
                        )
                    elif general_use_by:
                        self._add_note_value(
                            actions[existing_index], f"use_by={general_use_by}"
                        )
                    clause_action_index[clause_key] = existing_index
                    continue
                normalized_tokens = [
                    word for word in re.findall(r"[\w'-]+", normalized_key) if word
                ]
                valid_anchor = self._is_valid_candidate(item_name, normalized_tokens)
                if not valid_anchor:
                    target_index = clause_action_index.get(clause_key)
                    attached = False
                    if measurement_note and target_index is not None:
                        self._add_note_value(actions[target_index], measurement_note)
                        attached = True
                    if use_by_ord and target_index is not None:
                        self._add_note_value(
                            actions[target_index], f"use_by={use_by_ord}"
                        )
                    elif general_use_by and target_index is not None:
                        self._add_note_value(
                            actions[target_index], f"use_by={general_use_by}"
                        )
                    attached = True
                    if attached:
                        if target_index is not None:
                            clause_action_index[clause_key] = target_index
                        continue
                    if measurement_note:
                        self._append_warning(warnings, FALLBACK_ATTACHMENT_DROPPED)
                    continue
                key = (normalized_key, round(quantity, 3), unit)
                if dedup_key in seen_dedup_keys:
                    if measurement_note and existing_index is not None:
                        self._add_note_value(actions[existing_index], measurement_note)
                        if use_by_ord:
                            self._add_note_value(
                                actions[existing_index], f"use_by={use_by_ord}"
                            )
                        elif general_use_by:
                            self._add_note_value(
                                actions[existing_index], f"use_by={general_use_by}"
                            )
                    continue
                if key in seen:
                    continue
                seen.add(key)
                action = ProposedInventoryEventAction(
                    event=InventoryEventCreateRequest(
                        event_type="add",
                        item_name=item_name,
                        quantity=quantity,
                        unit=unit,
                        note="",
                        source="chat",
                    )
                )
                if measurement_note:
                    self._add_note_value(action, measurement_note)
                if use_by_ord:
                    self._add_note_value(action, f"use_by={use_by_ord}")
                elif general_use_by:
                    self._add_note_value(action, f"use_by={general_use_by}")
                fraction_note = self._fraction_remaining_note(
                    text[start:end], quantity, unit
                )
                if fraction_note:
                    self._add_note_value(action, fraction_note)
                actions.append(action)
                seen_dedup_keys.add(dedup_key)
                dedup_action_index[dedup_key] = len(actions) - 1
                action_index[normalized_key] = len(actions) - 1
                dedup_action_index[dedup_key] = len(actions) - 1
                clause_action_index[clause_key] = len(actions) - 1
            for segment in segments:
                if self._is_chatter_clause(segment):
                    continue
                cleaned = self._clean_segment_text(segment)
                if not cleaned or self._is_filler_text(cleaned):
                    continue
                cleaned_lower = cleaned.lower()
                if cleaned_lower in ATTACHMENT_ONLY_WORDS or self._contains_date_marker(
                    cleaned
                ):
                    continue
                if re.search(r"\d", cleaned):
                    continue
                normalized_key = self._normalize_item_key(cleaned)
                if not normalized_key:
                    normalized_key = cleaned_lower
                if self._is_disallowed_item_name(cleaned, normalized_key):
                    continue
                dedup_key = self._dedup_key(normalized_key)
                if dedup_key in seen_dedup_keys:
                    continue
                key = (normalized_key, 1.0, "count")
                if key in seen:
                    continue
                has_fraction = bool(FRACTION_STATE_PATTERN.search(segment))
                if not has_fraction:
                    fallback_missing_quantity = True
                seen.add(key)
                action = ProposedInventoryEventAction(
                    event=InventoryEventCreateRequest(
                        event_type="add",
                        item_name=cleaned,
                        quantity=1.0,
                        unit="count",
                        note="",
                        source="chat",
                    )
                )
                use_by_key = self._find_use_by_target(cleaned, use_by_values)
                if use_by_key:
                    self._add_note_value(action, f"use_by={use_by_values[use_by_key]}")
                if has_fraction:
                    frac_note = self._fraction_remaining_note(segment, 1.0, "count")
                    if frac_note:
                        self._add_note_value(action, frac_note)
                actions.append(action)
                seen_dedup_keys.add(dedup_key)
                dedup_action_index[dedup_key] = len(actions) - 1
                action_index[normalized_key] = len(actions) - 1
        else:
            for segment in segments:
                if self._is_chatter_clause(segment):
                    continue
                cleaned = self._clean_segment_text(segment)
                if not cleaned or self._is_filler_text(cleaned):
                    continue
                cleaned_lower = cleaned.lower()
                if cleaned_lower in ATTACHMENT_ONLY_WORDS or self._contains_date_marker(
                    cleaned
                ):
                    continue
                normalized_key = self._normalize_item_key(cleaned)
                if not normalized_key:
                    normalized_key = cleaned_lower
                if self._is_disallowed_item_name(cleaned, normalized_key):
                    continue
                dedup_key = self._dedup_key(normalized_key)
                if dedup_key in seen_dedup_keys:
                    continue
                key = (normalized_key, 1.0, "count")
                if key in seen:
                    continue
                has_fraction = bool(FRACTION_STATE_PATTERN.search(segment))
                if not has_fraction:
                    fallback_missing_quantity = True
                seen.add(key)
                action = ProposedInventoryEventAction(
                    event=InventoryEventCreateRequest(
                        event_type="add",
                        item_name=cleaned,
                        quantity=1.0,
                        unit="count",
                        note="",
                        source="chat",
                    )
                )
                use_by_key = self._find_use_by_target(cleaned, use_by_values)
                if use_by_key:
                    self._add_note_value(action, f"use_by={use_by_values[use_by_key]}")
                if has_fraction:
                    frac_note = self._fraction_remaining_note(segment, 1.0, "count")
                    if frac_note:
                        self._add_note_value(action, frac_note)
                actions.append(action)
                seen_dedup_keys.add(dedup_key)
                action_index[normalized_key] = len(actions) - 1

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

    def _previous_sentence_boundary(self, lower_text: str, index: int) -> int:
        boundary = 0
        for sep in SENTENCE_TERMINATORS:
            pos = lower_text.rfind(sep, 0, index)
            if pos != -1:
                candidate = pos + 1
                if candidate > boundary:
                    boundary = candidate
        return boundary

    def _next_sentence_boundary(self, lower_text: str, index: int) -> int:
        boundary = len(lower_text)
        for sep in SENTENCE_TERMINATORS:
            pos = lower_text.find(sep, index)
            if pos != -1 and pos < boundary:
                boundary = pos
        return boundary

    def _extract_candidate_phrase(self, segment: str, rel_start: int, rel_end: int) -> str:
        before = segment[:rel_start]
        after = segment[rel_end:]
        after_phrase = self._pick_contextual_words(after, leading=True)
        if after_phrase and not self._looks_like_unit_phrase(after_phrase):
            return after_phrase
        before_phrase = self._pick_contextual_words(before, leading=False)
        if before_phrase and not self._looks_like_unit_phrase(before_phrase):
            return before_phrase
        return before_phrase or after_phrase

    def _pick_contextual_words(self, text: str, leading: bool) -> str:
        words = re.findall(r"[\w'-]+", text)
        if not words:
            return ""
        ignore = AFTER_IGNORE_WORDS if leading else BEFORE_IGNORE_WORDS
        collected: List[str] = []
        iterator = words if leading else reversed(words)
        for word in iterator:
            lower = word.lower()
            if any(char.isdigit() for char in lower):
                continue
            if lower in ignore:
                continue
            collected.append(word)
            if len(collected) >= 5:
                break
        if not collected:
            return ""
        if leading:
            return " ".join(collected)
        return " ".join(reversed(collected))

    def _looks_like_unit_phrase(self, phrase: str) -> bool:
        words = re.findall(r"[\w'-]+", phrase)
        if not words:
            return True
        for word in words:
            lower = word.lower()
            if lower in ITEM_STOP_WORDS:
                continue
            if any(
                keyword.startswith(lower)
                or keyword.endswith(lower)
                or lower.startswith(keyword)
                or lower.endswith(keyword)
                for keyword in PARTIAL_KEYWORDS
            ):
                continue
            return False
        return True

    def _remove_numeric_from_phrase(self, phrase: str, start: int, end: int) -> str:
        before = phrase[:start]
        after = phrase[end:]
        candidate = f"{before} {after}"
        return " ".join(candidate.split())

    def _clean_segment_text(self, segment: str) -> str:
        cleaned = re.sub(r"\s+", " ", segment).strip(" ,;.")
        cleaned = DATE_STRIP_PATTERN.sub("", cleaned)
        cleaned = FRACTION_STATE_PATTERN.sub("", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;.")
        lowered = cleaned.lower()
        for filler in FALLBACK_FILLERS:
            if lowered == filler:
                cleaned = ""
                lowered = ""
                break
            if lowered.startswith(filler):
                boundary = len(filler)
                if boundary == len(lowered) or lowered[boundary] in " ,;.":
                    cleaned = cleaned[boundary:].strip(" ,;.")
                    lowered = cleaned.lower()
        cleaned = cleaned.strip(" ,;.")
        cleaned = self._strip_item_stop_words(cleaned)
        cleaned = cleaned.strip(" ,;.")
        cleaned = self._strip_leading_chatter_tokens(cleaned)
        cleaned = self._strip_leading_prefixes(cleaned)
        if self._is_filler_text(cleaned):
            return ""
        return cleaned

    def _strip_item_stop_words(self, text: str) -> str:
        words = re.findall(r"[\w'-]+", text)
        filtered = [word for word in words if word.lower() not in ITEM_STOP_WORDS]
        return " ".join(filtered) if filtered else text

    def _strip_leading_chatter_tokens(self, text: str) -> str:
        trimmed = text.strip()
        lower = trimmed.lower()
        prefixes = sorted(CHATTER_LEADING_PREFIXES, key=len, reverse=True)
        for prefix in prefixes:
            if lower.startswith(prefix):
                trimmed = trimmed[len(prefix) :].strip()
                lower = trimmed.lower()
        return trimmed

    def _strip_leading_prefixes(self, text: str) -> str:
        trimmed = text.strip(" ,;.:")
        lower = trimmed.lower()
        changed = True
        while trimmed and changed:
            changed = False
            for prefix in sorted(LEAD_PREFIXES, key=len, reverse=True):
                if lower.startswith(prefix):
                    trimmed = trimmed[len(prefix) :].strip(" ,;.:")
                    lower = trimmed.lower()
                    changed = True
                    break
        return trimmed

    def _find_segment_boundary(self, lower_segment: str, after_idx: int) -> Optional[int]:
        markers = set(DATE_CONTEXT_PHRASES) | DATE_MARKER_PHRASES | UNCERTAINTY_MARKERS
        boundary: Optional[int] = None
        for marker in markers:
            idx = lower_segment.find(marker)
            if idx == -1 or idx < after_idx:
                continue
            if boundary is None or idx < boundary:
                boundary = idx
        return boundary

    def _find_general_use_by_after(
        self, lower_text: str, start_idx: int, end_idx: int
    ) -> Optional[Tuple[str, int]]:
        segment = lower_text[start_idx:end_idx]
        for match in re.finditer(rf"use by(?: the)?\s+({ORDINAL_PATTERN})", segment):
            remainder = segment[match.end() :].lstrip()
            if remainder.startswith("on ") or remainder.startswith("for "):
                continue
            return match.group(1), start_idx + match.start()
        return None

    def _contains_date_marker(self, text: str) -> bool:
        lower = text.lower()
        return any(phrase in lower for phrase in DATE_MARKER_PHRASES)

    def _is_chatter_clause(self, clause: str) -> bool:
        lower = clause.lower()
        if any(phrase in lower for phrase in CHATTER_DROP_PHRASES):
            return True
        if any(marker in lower for marker in UNCERTAINTY_MARKERS):
            return True
        return False

    def _is_valid_candidate(self, text: str, normalized_tokens: List[str]) -> bool:
        if not text:
            return False
        if self._is_filler_text(text):
            return False
        if self._contains_date_marker(text):
            return False
        return any(token.lower() not in ITEM_STOP_WORDS for token in normalized_tokens)

    def _is_disallowed_item_name(self, item_name: str, normalized_key: str) -> bool:
        lower = item_name.lower().strip()
        if not lower:
            return True
        if "little chef" in normalized_key:
            return True
        if lower in BARE_FILLER_WORDS:
            return True
        if FRACTION_LEFT_PATTERN.match(lower):
            return True
        if normalized_key in CONTAINER_WORDS:
            return True
        return False

    def _clamp_multi_anchor(self, item_name: str, unit: str) -> str:
        lower = item_name.lower()
        tokens = set(re.findall(r"[\w'-]+", lower))
        if any(token in {"egg", "eggs"} for token in tokens):
            return "eggs"
        if {"bread", "milk"}.issubset(tokens):
            if unit == "ml":
                return "milk"
            if unit == "count":
                return "bread"
        return item_name

    def _dedup_key(self, normalized_key: str) -> str:
        dedup = re.sub(r"\d+", "", normalized_key).strip()
        dedup = " ".join(dedup.split())
        return dedup or normalized_key

    def _guess_item_name(self, text: str, index: int, limit: int = 5) -> str:
        window = text[max(0, index - 40) : index]
        for term in SENTENCE_TERMINATORS:
            marker = term + " "
            last = window.rfind(marker)
            if last != -1:
                window = window[last + len(marker) :]
        words = re.findall(r"[\w'-]+", window)
        if not words:
            return ""
        return " ".join(words[-limit:])

    def _extract_left_clause(self, text: str) -> str:
        clause = text.strip(" ,;.")
        if not clause:
            return ""
        lower_clause = clause.lower()
        last_idx = -1
        last_len = 0
        for sep in CONTAINER_PHRASE_SEPARATORS:
            idx = lower_clause.rfind(sep)
            if idx != -1 and idx > last_idx:
                last_idx = idx
                last_len = len(sep)
        if last_idx != -1:
            clause = clause[last_idx + last_len :].strip(" ,;.")
        return clause.strip(" ,;.")

    def _extract_cereal_candidate(self, segment: str) -> Optional[str]:
        lower_segment = segment.lower()
        for token in CEREAL_TOKENS:
            if token in lower_segment:
                return token
        return None

    def _is_container_candidate(self, item_name: str) -> bool:
        if not item_name:
            return False
        tokens = [word for word in re.findall(r"[\w'-]+", item_name.lower()) if word]
        if not tokens:
            return False
        return all(token in CONTAINER_WORD_HINTS for token in tokens)

    def _normalize_quantity_and_unit(
        self, quantity_str: str, unit_str: Optional[str]
    ) -> Tuple[float, str]:
        qty = float(quantity_str.replace(",", "."))
        raw_unit = (unit_str or "").strip().lower()
        if raw_unit in {"g", "gram", "grams"}:
            return qty, "g"
        if raw_unit in {"kg", "kilogram", "kilograms"}:
            return qty * 1000, "g"
        if raw_unit in {"kilo", "kilos"}:
            return qty * 1000, "g"
        if raw_unit in {"ml", "milliliter", "milliliters"}:
            return qty, "ml"
        if raw_unit in {"l", "liter", "liters", "litre", "litres"}:
            return qty * 1000, "ml"
        return qty, "count"

    def _split_segments(self, text: str) -> List[str]:
        raw_segments = [segment.strip() for segment in SPLIT_PATTERN.split(text) if segment.strip()]
        expanded: List[str] = []
        for segment in raw_segments:
            expanded.extend(self._split_segment_on_uncertainty(segment))
        return [segment for segment in expanded if segment]

    def _split_segment_on_uncertainty(self, segment: str) -> List[str]:
        lower = segment.lower()
        earliest: Optional[int] = None
        for marker in UNCERTAINTY_MARKERS:
            idx = lower.find(marker)
            if idx != -1 and (earliest is None or idx < earliest):
                earliest = idx
        if earliest is None:
            return [segment.strip()]
        before = segment[:earliest].strip(" ,;.")
        after = segment[earliest:].strip(" ,;. ")
        results: List[str] = []
        if before:
            results.append(before)
        if after:
            results.append(after)
        return results

    def _append_warning(self, warnings: List[str], value: str) -> None:
        if value not in warnings:
            warnings.append(value)

    def _extract_use_by_values(self, lower_text: str) -> Dict[str, str]:
        values: Dict[str, str] = {}
        for match in USE_BY_VALUE_PATTERN.finditer(lower_text):
            ordinal = match.group(1)
            target = match.group(2).strip().lower()
            tokens = re.findall(r"[\w'-]+", target)
            while tokens and tokens[-1] in {"and", "also", "plus"}:
                tokens.pop()
            if not tokens:
                continue
            cleaned_target = " ".join(tokens)
            values[cleaned_target] = ordinal
        return values

    def _find_use_by_target(self, item_name: str, use_by_values: Dict[str, str]) -> Optional[str]:
        lower = item_name.lower()
        for target in use_by_values:
            if target in lower:
                return target
        return None

    def _measurement_note_value(self, unit: str, quantity: float) -> Optional[str]:
        if unit == "g":
            qty = int(quantity) if float(quantity).is_integer() else quantity
            return f"weight_g={qty}"
        if unit == "ml":
            qty = int(quantity) if float(quantity).is_integer() else quantity
            return f"volume_ml={qty}"
        return None

    def _fraction_remaining_note(
        self, segment: str, quantity: float, unit: str
    ) -> Optional[str]:
        match = FRACTION_STATE_PATTERN.search(segment)
        if not match:
            return None
        frac_word = match.group(1).lower()
        frac_val = FRACTION_VALUES.get(frac_word)
        if frac_val is None:
            return None
        if unit in ("g", "ml") and quantity > 0:
            derived = round(quantity * frac_val)
            return f"remaining={derived}{unit}"
        return f"remaining={frac_word}"

    def _add_note_value(
        self, action: ProposedInventoryEventAction, value: str
    ) -> None:
        note = (action.event.note or "").strip()
        if note:
            note = f"{note}; {value}"
        else:
            note = value
        action.event.note = note

    def _normalize_item_key(self, text: str) -> str:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        words = [
            word
            for word in cleaned.split()
            if word not in CONTEXT_IGNORE_WORDS
            and word not in CONTAINER_WORDS
            and word not in QUANTITY_ADVERBS
        ]
        if not words:
            return text.lower()
        return " ".join(words)

    def _replace_number_words(self, text: str) -> str:
        if not text:
            return text

        def repl(match: Match[str]) -> str:
            word = match.group(1).lower()
            return str(NUMBER_WORDS.get(word, word))

        return NUMBER_WORD_PATTERN.sub(repl, text)

    def _looks_like_date_quantity(self, lower_text: str, match: Match[str]) -> bool:
        start, end = match.span()
        # skip ordinals directly following the digits (e.g., "10th")
        suffix = lower_text[end:end + 2]
        if any(suffix.startswith(ord_suffix) for ord_suffix in ORDINAL_SUFFIXES):
            return True
        context_start = max(0, start - 30)
        for phrase in DATE_CONTEXT_PHRASES:
            phrase_pos = lower_text.rfind(phrase, context_start, start)
            if phrase_pos == -1:
                continue
            between = lower_text[phrase_pos:start]
            # A sentence boundary between the date phrase and this number
            # means this number belongs to a new clause, not the date.
            if any(t in between for t in (",", ".", "!", "?")):
                continue
            return True
        return False

    def _is_filler_text(self, text: str) -> bool:
        if not text:
            return True
        cleaned = re.sub(r"\s+", " ", text).strip(" ,;.")
        lowered = cleaned.lower()
        if not lowered:
            return True
        if any(phrase in lowered for phrase in FALLBACK_IGNORE_PHRASES):
            return True
        if "i've just been through" in lowered and any(loc in lowered for loc in INTRO_LOCATION_WORDS):
            return True
        if "no idea how many" in lowered:
            return True
        if not re.search(r"[a-zA-Z]", lowered):
            return True
        return False
