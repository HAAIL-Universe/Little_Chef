import logging
import re
import uuid
from typing import List, Optional

from app.schemas import (
    ChatRequest,
    ChatResponse,
    ProposedUpsertPrefsAction,
    UserPrefs,
    UserMe,
)
from app.services.prefs_service import PrefsPersistenceError, PrefsService
from app.services.proposal_store import ProposalStore
from app.services.inventory_service import InventoryService
from app.services.llm_client import (
    LlmClient,
    set_runtime_enabled,
    current_model,
    set_runtime_model,
)
from app.services.inventory_agent import InventoryAgent

NUMBER_WORDS: dict[str, int] = {
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
}
LIKE_CLAUSE_PATTERNS: tuple[str, ...] = (
    r"(?:i(?: really)? like|i love)\s+(.+?)(?:[.!?]|$)",
    r"(?<!dis)likes?:\s+(.+?)(?:[.!?]|$)",
)
DISLIKE_CLAUSE_PATTERNS: tuple[str, ...] = (
    rf"(?:i(?: don(?:'|’)?t|do not)\s+like|i(?: hate|detest))\s+(.+?)(?:[.!?]|$)",
    r"dislikes?:\s+(.+?)(?:[.!?]|$)",
)
ALLERGY_CLAUSE_PATTERNS: tuple[str, ...] = (
    r"(?:got|have)\s+(?:a\s+)?(.+?)\s+allerg(?:y|ies)",
    r"allergic to[^\S\r\n]*(.+?)(?:[.!?]|$)",
    rf"can(?:'|\u2019)?t have[^\S\r\n]*(.+?)(?:[.!?]|$)",
    r"cannot have[^\S\r\n]*(.+?)(?:[.!?]|$)",
    r"allerg(?:y|ies)[^\S\r\n]*[:\-][^\S\r\n]*(.+?)(?:[.!?]|$)",
)
CUISINE_CLAUSE_PATTERNS: tuple[str, ...] = (
    r"cuisine likes?:\s+(.+?)(?:[.!?]|$)",
    r"cuisines?:\s+(.+?)(?:[.!?]|$)",
)
ALLERGY_ITEM_PREFIXES: tuple[str, ...] = (
    "and i'm also allergic to",
    "i'm also allergic to",
    "also allergic to",
    "i'm allergic to",
    "i\u2019m allergic to",
    "i am allergic to",
    "i can't have",
    "i can\u2019t have",
    "i cannot have",
    "i cant have",
    "allergies",
    "allergy",
    "and ",
)

NONE_SENTINELS: frozenset[str] = frozenset({"none", "no", "n/a", "na", "nil", "nothing", "-"})


logger = logging.getLogger(__name__)
PREFS_PERSIST_FAILED_REASON = "prefs_persist_failed"


class ChatService:
    def __init__(
        self,
        prefs_service: PrefsService,
        inventory_service: InventoryService,
        proposal_store: ProposalStore,
        llm_client: LlmClient | None = None,
        thread_messages_repo=None,
        inventory_agent: InventoryAgent | None = None,
    ) -> None:
        self.prefs_service = prefs_service
        self.inventory_service = inventory_service
        self.proposal_store = proposal_store
        self.llm_client = llm_client
        self.thread_messages_repo = thread_messages_repo
        self.inventory_agent = inventory_agent or InventoryAgent(
            inventory_service, proposal_store, llm_client
        )
        self.prefs_drafts: dict[tuple[str, str], UserPrefs] = {}
        self._prefs_proposal_ids: dict[tuple[str, str], str] = {}
        self.thread_modes: dict[tuple[str, str], str] = {}

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
        effective_mode = self._effective_mode(user_id, request.thread_id, mode)

        if message.startswith("/ask"):
            if not request.thread_id:
                return ChatResponse(
                    reply_text="Thread id is required to switch mode.",
                    confirmation_required=False,
                    proposal_id=None,
                    proposed_actions=[],
                    suggested_next_questions=[],
                    mode=effective_mode,
                )
            self.thread_modes[(user_id, request.thread_id)] = "ask"
            return ChatResponse(
                reply_text=f"Mode set: ASK for thread {request.thread_id}",
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
                mode="ask",
            )

        if message.startswith("/fill"):
            if not request.thread_id:
                return ChatResponse(
                    reply_text="Thread id is required to switch mode.",
                    confirmation_required=False,
                    proposal_id=None,
                    proposed_actions=[],
                    suggested_next_questions=[],
                    mode=effective_mode,
                )
            self.thread_modes[(user_id, request.thread_id)] = "fill"
            return ChatResponse(
                reply_text=f"Mode set: FILL for thread {request.thread_id}",
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
                mode="fill",
            )

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
                mode=effective_mode,
            )

        if effective_mode == "ask":
            ask_reply = self._handle_ask(user_id, message, effective_mode)
            if ask_reply:
                self._append_messages(request.thread_id, user_id, request.message, ask_reply.reply_text)
                return ask_reply
            reply_text = "I can help set preferences or inventory. Try FILL mode with details."
            if self.llm_client:
                llm_text = self.llm_client.generate_reply(self._system_prompt, request.message)
                if llm_text:
                    reply_text = llm_text
            resp = ChatResponse(
                reply_text=reply_text,
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
                mode=effective_mode,
            )
            self._append_messages(request.thread_id, user_id, request.message, resp.reply_text)
            return resp

        if effective_mode == "fill":
            response = self._handle_prefs_flow_threaded(user, request, effective_mode)
            self._append_messages(request.thread_id, user.user_id, request.message, response.reply_text)
            return response

        return ChatResponse(
            reply_text="Unsupported mode. Use ask or fill.",
            confirmation_required=False,
            proposal_id=None,
            proposed_actions=[],
            suggested_next_questions=[],
            mode=effective_mode,
        )

    def _effective_mode(self, user_id: str, thread_id: str | None, requested: str) -> str:
        if thread_id:
            override = self.thread_modes.get((user_id, thread_id))
            if override:
                return override
        return requested or "ask"

    def _append_messages(self, thread_id: str | None, user_id: str, user_text: str, assistant_text: str | None) -> None:
        if not self.thread_messages_repo or not thread_id:
            return
        self.thread_messages_repo.append_message(thread_id, user_id, "user", user_text or "")
        if assistant_text:
            self.thread_messages_repo.append_message(thread_id, user_id, "assistant", assistant_text)

    def confirm(
        self,
        user: UserMe,
        proposal_id: str,
        confirm: bool,
        thread_id: str | None = None,
    ) -> tuple[bool, List[str], str | None]:
        if self.inventory_agent.handles_proposal(user.user_id, proposal_id):
            if not self.inventory_agent.handles_proposal(user.user_id, proposal_id, thread_id):
                return False, [], None
            return self.inventory_agent.confirm(user, proposal_id, confirm, thread_id)
        action = self.proposal_store.peek(user.user_id, proposal_id)
        if not action:
            return False, [], None
        if not confirm:
            if thread_id:
                self.prefs_drafts.pop((user.user_id, thread_id), None)
                self._prefs_proposal_ids.pop((user.user_id, thread_id), None)
            self.proposal_store.pop(user.user_id, proposal_id)
            return False, [], None

        applied_event_ids: List[str] = []
        actions = action if isinstance(action, list) else [action]
        reason: str | None = None
        success = False
        try:
            for act in actions:
                if isinstance(act, ProposedUpsertPrefsAction):
                    event_id = f"prefs-{uuid.uuid4()}"
                    self.prefs_service.upsert_prefs(
                        user.user_id,
                        user.provider_subject,
                        user.email,
                        act.prefs,
                        applied_event_id=event_id,
                        require_db=True,
                    )
                    applied_event_ids.append(event_id)
                else:
                    # Non-prefs actions should be handled elsewhere
                    continue
            success = True
        except PrefsPersistenceError as exc:
            logger.warning("Prefs confirm failed (%s): %s", proposal_id, exc)
            reason = PREFS_PERSIST_FAILED_REASON
        except Exception:
            logger.exception("Unexpected error while confirming proposal %s", proposal_id)
            reason = PREFS_PERSIST_FAILED_REASON
        finally:
            if success:
                self.proposal_store.pop(user.user_id, proposal_id)
                if thread_id:
                    self.prefs_drafts.pop((user.user_id, thread_id), None)
                    self._prefs_proposal_ids.pop((user.user_id, thread_id), None)
        return success, applied_event_ids, reason

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
        text_lower = text.lower()
        for pat in patterns:
            match = re.search(pat, text_lower)
            if match:
                return int(match.group(1))
        # Context-aware NUMBER_WORDS: expand each pattern to accept word numbers
        # in place of \d+, so "five days" matches the days pattern instead of
        # "two" from an unrelated "two servings" phrase.
        word_alt = "|".join(NUMBER_WORDS.keys())
        for pat in patterns:
            # Replace the first (\d+) capture group with a word-number alternative
            word_pat = re.sub(r"\(\\d\+\)", rf"({word_alt})", pat, count=1)
            if word_pat != pat:
                match = re.search(word_pat, text_lower)
                if match:
                    matched_word = match.group(1).strip()
                    if matched_word in NUMBER_WORDS:
                        return NUMBER_WORDS[matched_word]
        return None

    def _clean_list_item(self, value: str) -> str:
        cleaned = value.strip()
        cleaned = cleaned.strip(".,;:-\"'“”‘’")
        return cleaned

    # Trailing filler phrases that leak into clause captures
    _TRAILING_FILLER = re.compile(
        r"\s*,?\s*\b(?:so\s+please\s+avoid\s+(?:those|these|them)|please\s+avoid|if\s+possible|when\s+possible|for\s+me)\b.*$",
        re.IGNORECASE,
    )
    # Clause-boundary: comma/semicolon before pronoun "I" signals a new clause
    _INITIAL_CLAUSE_BOUNDARY = re.compile(r"[,;]\s*(?=(?:and\s+)?[Ii](?:[\s'\u2019]))")

    def _split_clause_items(self, segment: str) -> List[str]:
        if not segment:
            return []
        # Strip trailing filler ("so please avoid those")
        segment = self._TRAILING_FILLER.sub("", segment)
        # Split at clause boundaries before "I" so sub-clauses don't leak
        sub_segments = self._INITIAL_CLAUSE_BOUNDARY.split(segment)
        parts: list[str] = []
        for sub in sub_segments:
            parts.extend(re.split(r"\s*(?:,|\band\b|\bor\b)\s*", sub))
        return [item for item in (self._clean_list_item(part) for part in parts) if item]

    def _match_clause_segments(self, text: str, patterns: tuple[str, ...]) -> List[str]:
        segments: list[str] = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                segment = match.group(1)
                if segment:
                    segments.append(segment)
        return segments

    def _dedupe_items(self, items: List[str]) -> List[str]:
        seen: set[str] = set()
        result: List[str] = []
        for item in items:
            if not item:
                continue
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    # Filler prefixes that get captured inside clause items after splitting.
    # Ordered longest-first so "i'm happy with most" is stripped before "most".
    _ITEM_FILLER_PREFIXES = re.compile(
        r"^(?:"
        r"i'm happy with most|i'm happy with|i am happy with most|i am happy with|"
        r"i\u2019m happy with most|i\u2019m happy with|"
        r"i enjoy most|i enjoy|most|"
        r"happy with most|happy with"
        r")\s+",
        re.IGNORECASE,
    )

    def _extract_clause_items(self, text: str, patterns: tuple[str, ...]) -> List[str]:
        segments = self._match_clause_segments(text, patterns)
        items: List[str] = []
        for segment in segments:
            items.extend(self._split_clause_items(segment))
        cleaned: List[str] = []
        for item in items:
            # Strip filler prefixes ("i'm happy with most chicken meals" -> "chicken meals")
            item = self._ITEM_FILLER_PREFIXES.sub("", item).strip()
            if item and item.lower() not in NONE_SENTINELS:
                cleaned.append(item)
        return self._dedupe_items(cleaned)

    def _normalize_allergy_item(self, item: str) -> str:
        normalized = self._clean_list_item(item)
        lowered = normalized.lower()
        for prefix in ALLERGY_ITEM_PREFIXES:
            if lowered.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
                lowered = normalized
        return self._clean_list_item(normalized)

    def _extract_allergy_items(self, text: str) -> List[str]:
        segments = self._match_clause_segments(text, ALLERGY_CLAUSE_PATTERNS)
        raw_items: List[str] = []
        for segment in segments:
            raw_items.extend(self._split_clause_items(segment))
        normalized = [self._normalize_allergy_item(item) for item in raw_items if item]
        return self._dedupe_items([item for item in normalized if item and item.lower() not in NONE_SENTINELS])

    # Day-of-week map for "Monday to Friday"-style span detection
    _DOW_MAP: dict[str, int] = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
        "mon": 0, "tue": 1, "tues": 1, "wed": 2, "thu": 3, "thurs": 3,
        "fri": 4, "sat": 5, "sun": 6,
    }
    _DOW_SPAN_RE = re.compile(
        r"\b(" + "|".join(sorted(_DOW_MAP.keys(), key=len, reverse=True)) + r")\b"
        r"\s*(?:to|through|thru|-|–)\s*"
        r"\b(" + "|".join(sorted(_DOW_MAP.keys(), key=len, reverse=True)) + r")\b",
        re.IGNORECASE,
    )

    def _extract_day_span(self, text: str) -> int | None:
        """Detect 'Monday to Friday' style spans and return the day count."""
        m = self._DOW_SPAN_RE.search(text)
        if not m:
            return None
        start = self._DOW_MAP.get(m.group(1).lower())
        end = self._DOW_MAP.get(m.group(2).lower())
        if start is None or end is None:
            return None
        span = (end - start) % 7 + 1
        return span if span >= 1 else None

    def _parse_prefs_from_message(self, message: str) -> UserPrefs:
        lowered_message = message.lower()
        servings = self._extract_number(lowered_message, [r"(\d+)\s*servings?", r"servings?[^0-9]*(\d+)"])
        meals_per_day = self._extract_number(
            lowered_message,
            [
                r"meals?\s*per\s*day[^0-9]*(\d+)",
                r"(\d+)\s*meals?\s*per\s*day",
                r"meals?[^0-9]*(\d+)",
                r"(\d+)\s*days?",
                r"days?[^0-9]*(\d+)",
            ],
        )
        # Fallback: "Monday to Friday" style span
        if not meals_per_day:
            meals_per_day = self._extract_day_span(lowered_message)

        allergies = self._extract_allergy_items(lowered_message)
        dislikes = self._extract_clause_items(lowered_message, DISLIKE_CLAUSE_PATTERNS)
        likes = self._extract_clause_items(lowered_message, LIKE_CLAUSE_PATTERNS)
        cuisine_entries = self._extract_clause_items(lowered_message, CUISINE_CLAUSE_PATTERNS)
        cuisine_likes = self._dedupe_items(likes + cuisine_entries)

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

    # ------------------------------------------------------------------
    # Prefs edit-apply: mutate a pending prefs draft from free-text edits
    # ------------------------------------------------------------------
    # Apostrophe character class covering straight (') and smart (\u2019) quotes
    _APO = r"['\u2019]"

    _REMOVE_ALLERGY_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(rf"(?:i{_APO}?m\s+)?not\s+allergic\s+to\s+(.+?)(?:[.!?]|$)", re.IGNORECASE),
        re.compile(r"remove\s+allerg(?:y|ies)\s+(?:to\s+|for\s+)?(.+?)(?:[.!?]|$)", re.IGNORECASE),
        re.compile(r"no\s+allergy\s+to\s+(.+?)(?:[.!?]|$)", re.IGNORECASE),
    )
    _ADD_ALLERGY_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(rf"(?:i{_APO}?m\s+|i\s+am\s+)?allergic\s+to\s+(.+?)(?:[.!?]|$)", re.IGNORECASE),
        re.compile(rf"(?:i\s+)?can{_APO}?t\s+have\s+(.+?)(?:[.!?]|$)", re.IGNORECASE),
    )
    _ADD_LIKE_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"i\s+(?:actually\s+)?(?:really\s+)?like\s+(.+?)(?:[.!?]|$)", re.IGNORECASE),
        re.compile(r"i\s+love\s+(.+?)(?:[.!?]|$)", re.IGNORECASE),
    )
    _ADD_DISLIKE_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(rf"i\s+(?:don{_APO}?t|do\s+not)\s+like\s+(.+?)(?:[.!?]|$)", re.IGNORECASE),
        re.compile(r"i\s+(?:hate|detest|dislike)\s+(.+?)(?:[.!?]|$)", re.IGNORECASE),
    )
    # Clause-boundary normalizer: comma/semicolon before "I" (+ space or
    # apostrophe) is replaced with ". " so pattern terminators work correctly.
    # Avoids "I don't like eggs, I'm not allergic to X" capturing across clauses.
    _CLAUSE_BOUNDARY = re.compile(r"[,;]\s*(?=[Ii](?:\s|['\u2019]))")

    _GENERIC_REMOVE_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"remove\s+(.+?)(?:\s+from\s+(?:the\s+)?(?:list|proposal|allergies|likes|dislikes))?(?:[.!?]|$)", re.IGNORECASE),
        re.compile(r"(?:take\s+off|delete|drop)\s+(.+?)(?:\s+from\s+(?:the\s+)?(?:list|proposal|allergies|likes|dislikes))?(?:[.!?]|$)", re.IGNORECASE),
    )

    def _split_edit_items(self, segment: str) -> List[str]:
        """Split a matched segment like 'milk and peanuts' into individual items."""
        parts = re.split(r"\s*(?:,|\band\b|\bor\b)\s*", segment)
        return [p.strip().lower() for p in parts if p.strip() and p.strip().lower() not in NONE_SENTINELS]

    def _apply_prefs_edit_text(self, prefs: UserPrefs, text: str) -> UserPrefs:
        """Apply free-text edit instructions to a prefs object. Returns a mutated copy."""
        # Normalise clause boundaries so patterns don't capture across clauses.
        # "I don't like eggs, I'm not allergic to milk" → "… eggs. I'm not …"
        text = self._CLAUSE_BOUNDARY.sub(". ", text)

        edited = prefs.model_copy(deep=True)

        def _lower_set(items: List[str]) -> set[str]:
            return {i.lower() for i in items}

        def _remove_items(lst: List[str], to_remove: set[str]) -> List[str]:
            return [i for i in lst if i.lower() not in to_remove]

        def _add_items(lst: List[str], to_add: List[str]) -> List[str]:
            existing = _lower_set(lst)
            result = list(lst)
            for item in to_add:
                if item.lower() not in existing:
                    result.append(item)
                    existing.add(item.lower())
            return result

        # Generic "remove X" — strip item from ALL lists first, then
        # consume matched segments so later patterns don't re-add them.
        remaining_after_generic = text
        for pat in self._GENERIC_REMOVE_PATTERNS:
            for m in pat.finditer(text):
                items = self._split_edit_items(m.group(1))
                item_set = set(items)
                edited.allergies = _remove_items(edited.allergies, item_set)
                edited.cuisine_likes = _remove_items(edited.cuisine_likes, item_set)
                edited.dislikes = _remove_items(edited.dislikes, item_set)
            remaining_after_generic = pat.sub("", remaining_after_generic)

        # Remove allergies (must be checked BEFORE add-allergy to avoid
        # "not allergic to X" also matching "allergic to X")
        for pat in self._REMOVE_ALLERGY_PATTERNS:
            for m in pat.finditer(remaining_after_generic):
                items = self._split_edit_items(m.group(1))
                edited.allergies = _remove_items(edited.allergies, set(items))

        # Add allergies — only from segments NOT already consumed by remove patterns
        remaining = remaining_after_generic
        for pat in self._REMOVE_ALLERGY_PATTERNS:
            remaining = pat.sub("", remaining)
        for pat in self._ADD_ALLERGY_PATTERNS:
            for m in pat.finditer(remaining):
                items = self._split_edit_items(m.group(1))
                edited.allergies = _add_items(edited.allergies, items)

        # Add likes (also remove from dislikes)
        for pat in self._ADD_LIKE_PATTERNS:
            for m in pat.finditer(remaining_after_generic):
                items = self._split_edit_items(m.group(1))
                edited.cuisine_likes = _add_items(edited.cuisine_likes, items)
                edited.dislikes = _remove_items(edited.dislikes, set(items))

        # Add dislikes (also remove from likes)
        for pat in self._ADD_DISLIKE_PATTERNS:
            for m in pat.finditer(remaining_after_generic):
                items = self._split_edit_items(m.group(1))
                edited.dislikes = _add_items(edited.dislikes, items)
                edited.cuisine_likes = _remove_items(edited.cuisine_likes, set(items))

        return edited

    def _handle_prefs_flow_threaded(self, user: UserMe, request: ChatRequest, effective_mode: str) -> ChatResponse:
        user_id = user.user_id
        thread_id = request.thread_id
        key = (user_id, thread_id)

        # --- Pending prefs proposal: treat non-confirm input as edit ---
        existing_pid = self._prefs_proposal_ids.get(key)
        if existing_pid:
            existing_action = self.proposal_store.peek(user_id, existing_pid)
            if existing_action and isinstance(existing_action, ProposedUpsertPrefsAction):
                updated_prefs = self._apply_prefs_edit_text(existing_action.prefs, request.message)
                action = ProposedUpsertPrefsAction(prefs=updated_prefs)
                self.proposal_store.save(user_id, existing_pid, action)
                # Also update draft so future edits stack
                self.prefs_drafts[key] = updated_prefs

                summary = f"Proposed preferences: servings {updated_prefs.servings}, meals/day {updated_prefs.meals_per_day}."
                return ChatResponse(
                    reply_text=f"{summary} Reply 'confirm' to save, or send changes to edit.",
                    confirmation_required=True,
                    proposal_id=existing_pid,
                    proposed_actions=[action],
                    suggested_next_questions=[],
                    mode=effective_mode,
                )

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
                mode=effective_mode,
            )

        prefs = self._merge_with_defaults(user_id, draft)
        # Clean up stale prefs proposal for this thread before creating a new one
        old_pid = self._prefs_proposal_ids.get(key)
        if old_pid:
            self.proposal_store.pop(user_id, old_pid)
        proposal_id = str(uuid.uuid4())
        action = ProposedUpsertPrefsAction(prefs=prefs)
        self.proposal_store.save(user_id, proposal_id, action)
        self._prefs_proposal_ids[key] = proposal_id

        summary = f"Proposed preferences: servings {prefs.servings}, meals/day {prefs.meals_per_day}."
        return ChatResponse(
            reply_text=f"{summary} Reply 'confirm' to save, or send changes to edit.",
            confirmation_required=True,
            proposal_id=proposal_id,
            proposed_actions=[action],
            suggested_next_questions=[],
            mode=effective_mode,
        )

    def _format_prefs(self, prefs: UserPrefs) -> str:
        return (
            f"Servings: {prefs.servings}, meals/day: {prefs.meals_per_day}. "
            f"Allergies: {', '.join(prefs.allergies) or 'none'}. "
            f"Dislikes: {', '.join(prefs.dislikes) or 'none'}. "
            f"Cuisine likes: {', '.join(prefs.cuisine_likes) or 'none'}."
        )

    def _handle_ask(self, user_id: str, message: str, effective_mode: str) -> Optional[ChatResponse]:
        if "pref" in message or "preference" in message:
            prefs = self.prefs_service.get_prefs(user_id)
            reply = self._format_prefs(prefs)
            return ChatResponse(
                reply_text=reply,
                confirmation_required=False,
                proposal_id=None,
                proposed_actions=[],
                suggested_next_questions=[],
                mode=effective_mode,
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
                mode=effective_mode,
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
                mode=effective_mode,
            )
        return None

