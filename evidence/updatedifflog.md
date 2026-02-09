# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-09T14:20:20+00:00
- Branch: main
- HEAD: 18bf41f68adfcb82cefa713d12a5694dbf00082a
- BASE_HEAD: c21e36671b6407f49ccd3d814678b1ce49259632
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- fix(prefs): remove legacy duplicate prefs summary display from proposal renderer
- UI proposalRenderer.ts now skips describePrefs() for upsert_prefs actions
- Wizard rolling summary in reply_text is the single canonical display
- Added 2 new Python tests: no-duplicate summary + backward compat
- Updated UI proposal renderer test for prefs-returns-null behavior

## Files Changed (staged)
- app/services/chat_service.py
- app/services/inventory_agent.py
- evidence/updatedifflog.md
- scripts/ui_proposal_renderer_test.mjs
- tests/test_chat_prefs_propose_confirm.py
- tests/test_chat_prefs_thread.py
- tests/test_prefs_edit_apply.py
- tests/test_prefs_wizard.py
- tests/test_proposal_edit_semantics.py
- web/dist/proposalRenderer.js
- web/src/proposalRenderer.ts

## git status -sb
    ## main...origin/main
    M  app/services/chat_service.py
    M  app/services/inventory_agent.py
    M  evidence/updatedifflog.md
    M  scripts/ui_proposal_renderer_test.mjs
    M  tests/test_chat_prefs_propose_confirm.py
    M  tests/test_chat_prefs_thread.py
    M  tests/test_prefs_edit_apply.py
    A  tests/test_prefs_wizard.py
    M  tests/test_proposal_edit_semantics.py
     M web/dist/main.js
    M  web/dist/proposalRenderer.js
    M  web/src/proposalRenderer.ts
    ?? .claude/

## Minimal Diff Hunks
    diff --git a/app/services/chat_service.py b/app/services/chat_service.py
    index 9d88132..ac60a49 100644
    --- a/app/services/chat_service.py
    +++ b/app/services/chat_service.py
    @@ -73,6 +73,24 @@ ALLERGY_ITEM_PREFIXES: tuple[str, ...] = (
     
     NONE_SENTINELS: frozenset[str] = frozenset({"none", "no", "n/a", "na", "nil", "nothing", "-"})
     
    +WIZARD_FIELD_ORDER: tuple[str, ...] = (
    +    "allergies", "dislikes", "likes", "servings", "plan_days", "meals_per_day",
    +)
    +WIZARD_QUESTIONS: dict[str, str] = {
    +    "allergies": "Please tell me your allergies (or say 'none').",
    +    "dislikes": "Any foods you dislike? (or say 'none')",
    +    "likes": "What foods or cuisines do you like? (or say 'none')",
    +    "servings": "How many servings should I plan for?",
    +    "plan_days": "How many days do you want to plan for?",
    +    "meals_per_day": "How many meals per day?",
    +}
    +
    +_INVENTORY_ACTION_WORDS: frozenset[str] = frozenset({
    +    "bought", "picked up", "stocked up", "threw away", "used up",
    +})
    +_INVENTORY_QTY_UNIT_RE = re.compile(
    +    r'\d+\s*(?:g|kg|ml|l|pack|packs|bag|bags|tin|tins|can|cans|bottle|bottles|loaf|loaves)\b'
    +)
     
     logger = logging.getLogger(__name__)
     PREFS_PERSIST_FAILED_REASON = "prefs_persist_failed"
    @@ -99,6 +117,8 @@ class ChatService:
             self.prefs_drafts: dict[tuple[str, str], UserPrefs] = {}
             self._prefs_proposal_ids: dict[tuple[str, str], str] = {}
             self.thread_modes: dict[tuple[str, str], str] = {}
    +        self._prefs_wizard_answered: dict[tuple[str, str], set[str]] = {}
    +        self._prefs_wizard_current_q: dict[tuple[str, str], str | None] = {}
     
         @property
         def _system_prompt(self) -> str:
    @@ -245,6 +265,8 @@ class ChatService:
                 if thread_id:
                     self.prefs_drafts.pop((user.user_id, thread_id), None)
                     self._prefs_proposal_ids.pop((user.user_id, thread_id), None)
    +                self._prefs_wizard_answered.pop((user.user_id, thread_id), None)
    +                self._prefs_wizard_current_q.pop((user.user_id, thread_id), None)
                 self.proposal_store.pop(user.user_id, proposal_id)
                 return False, [], None
     
    @@ -281,6 +303,8 @@ class ChatService:
                     if thread_id:
                         self.prefs_drafts.pop((user.user_id, thread_id), None)
                         self._prefs_proposal_ids.pop((user.user_id, thread_id), None)
    +                    self._prefs_wizard_answered.pop((user.user_id, thread_id), None)
    +                    self._prefs_wizard_current_q.pop((user.user_id, thread_id), None)
             return success, applied_event_ids, reason
     
         def _merge_with_defaults(self, user_id: str, parsed: UserPrefs) -> UserPrefs:
    @@ -463,7 +487,13 @@ class ChatService:
     
         def _parse_prefs_from_message(self, message: str) -> UserPrefs:
             lowered_message = message.lower()
    -        servings = self._extract_number(lowered_message, [r"(\d+)\s*servings?", r"servings?[^0-9]*(\d+)"])
    +        servings = self._extract_number(lowered_message, [
    +            r"(\d+)\s*servings?",
    +            r"servings?[^0-9]*(\d+)",
    +            r"(\d+)\s*people",
    +            r"(?:for|feeds?)\s*(\d+)",
    +            r"family\s+of\s*(\d+)",
    +        ])
             meals_per_day = self._extract_number(
                 lowered_message,
                 [
    @@ -612,11 +642,186 @@ class ChatService:
     
             return edited
     
    +    # ------------------------------------------------------------------
    +    # Wizard helpers
    +    # ------------------------------------------------------------------
    +
    +    _ALLERGY_MENTION_RE = re.compile(
    +        r"\b(?:allerg(?:y|ies|ic)|can(?:'|\u2019)?t\s+have|cannot\s+have)\b", re.IGNORECASE,
    +    )
    +    _DISLIKE_MENTION_RE = re.compile(
    +        r"\b(?:dislikes?|don(?:'|\u2019)?t\s+like|do\s+not\s+like|hate|detest)\b", re.IGNORECASE,
    +    )
    +    _LIKE_MENTION_RE = re.compile(
    +        r"\b(?:(?<!dis)likes?|love|enjoy|prefer)\b", re.IGNORECASE,
    +    )
    +
    +    def _detect_mentioned_fields(self, message: str, parsed: UserPrefs) -> set[str]:
    +        """Detect which prefs fields were explicitly mentioned in the message."""
    +        mentioned: set[str] = set()
    +        lowered = message.lower()
    +
    +        # Allergy signals
    +        if self._ALLERGY_MENTION_RE.search(message) or parsed.allergies:
    +            mentioned.add("allergies")
    +        # Check for explicit "no allergies" sentinel
    +        if re.search(r"\bno\s+allerg", lowered) or re.search(r"\ballerg\w*\s*[:=-]\s*(?:none|no|n/?a|nil|nothing|-)", lowered):
    +            mentioned.add("allergies")
    +
    +        # Dislike signals
    +        if self._DISLIKE_MENTION_RE.search(message) or parsed.dislikes:
    +            mentioned.add("dislikes")
    +        if re.search(r"\bdislike\w*\s*[:=-]\s*(?:none|no|n/?a|nil|nothing|-)", lowered):
    +            mentioned.add("dislikes")
    +
    +        # Like signals (careful: "dislike" contains "like")
    +        if self._LIKE_MENTION_RE.search(message) and not self._DISLIKE_MENTION_RE.search(message):
    +            mentioned.add("likes")
    +        if parsed.cuisine_likes:
    +            mentioned.add("likes")
    +        if re.search(r"\b(?:cuisine\s+)?likes?\s*[:=-]\s*(?:none|no|n/?a|nil|nothing|-)", lowered):
    +            mentioned.add("likes")
    +
    +        # Numeric fields
    +        if parsed.servings > 0:
    +            mentioned.add("servings")
    +        if parsed.plan_days > 0:
    +            mentioned.add("plan_days")
    +        if parsed.meals_per_day > 0:
    +            mentioned.add("meals_per_day")
    +
    +        return mentioned
    +
    +    def _is_inventory_misroute(self, message: str) -> bool:
    +        """Conservative check: does this message look like inventory input?"""
    +        lowered = message.lower()
    +        has_action = any(word in lowered for word in _INVENTORY_ACTION_WORDS)
    +        has_qty_unit = bool(_INVENTORY_QTY_UNIT_RE.search(lowered))
    +        # Require BOTH signals to avoid false positives
    +        return has_action and has_qty_unit
    +
    +    def _is_prefs_misroute(self, message: str) -> bool:
    +        """Check if a message sent to inventory looks like prefs input."""
    +        lowered = message.lower()
    +        prefs_signals = 0
    +        if self._ALLERGY_MENTION_RE.search(message):
    +            prefs_signals += 1
    +        if re.search(r"\b(?:servings?|meals?\s*per\s*day|plan\s*days?)\b", lowered):
    +            prefs_signals += 1
    +        if self._DISLIKE_MENTION_RE.search(message):
    +            prefs_signals += 1
    +        if self._LIKE_MENTION_RE.search(message) and not self._DISLIKE_MENTION_RE.search(message):
    +            prefs_signals += 1
    +        return prefs_signals >= 2
    +
    +    def _next_wizard_question(self, answered: set[str], draft: UserPrefs) -> str | None:
    +        """Return the next unanswered wizard field, enforcing allergy hard stop."""
    +        # Allergy hard stop: MUST be answered first, regardless of order
    +        if "allergies" not in answered:
    +            return "allergies"
    +        for field in WIZARD_FIELD_ORDER:
    +            if field == "allergies":
    +                continue  # Already checked above
    +            if field in answered:
    +                continue
    +            # plan_days and meals_per_day are alternatives ÔÇö if one is answered, skip the other
    +            if field == "meals_per_day" and "plan_days" in answered and draft.plan_days > 0:
    +                continue
    +            if field == "plan_days" and "meals_per_day" in answered and draft.meals_per_day > 0:
    +                continue
    +            return field
    +        return None  # All fields answered
    +
    +    def _build_rolling_summary(self, draft: UserPrefs, answered: set[str]) -> str:
    +        """Build a bullet-point summary of collected and missing fields."""
    +        lines: list[str] = []
    +        if "allergies" in answered:
    +            val = ", ".join(draft.allergies) if draft.allergies else "none"
    +            lines.append(f"Allergies: {val}")
    +        if "dislikes" in answered:
    +            val = ", ".join(draft.dislikes) if draft.dislikes else "none"
    +            lines.append(f"Dislikes: {val}")
    +        if "likes" in answered:
    +            val = ", ".join(draft.cuisine_likes) if draft.cuisine_likes else "none"
    +            lines.append(f"Likes: {val}")
    +        if "servings" in answered and draft.servings > 0:
    +            lines.append(f"Servings: {draft.servings}")
    +        if "plan_days" in answered and draft.plan_days > 0:
    +            lines.append(f"Plan days: {draft.plan_days}")
    +        if "meals_per_day" in answered and draft.meals_per_day > 0:
    +            lines.append(f"Meals/day: {draft.meals_per_day}")
    +        return "\n".join(f"- {l}" for l in lines) if lines else ""
    +
    +    def _attribute_bare_answer(self, message: str, current_q: str | None, draft: UserPrefs, answered: set[str]) -> set[str]:
    +        """If the message is a bare answer (none sentinel or bare number), attribute it to current_q."""
    +        if not current_q:
    +            return set()
    +        stripped = message.strip().lower()
    +        newly_answered: set[str] = set()
    +
    +        # None sentinel for list fields
    +        if stripped in NONE_SENTINELS and current_q in ("allergies", "dislikes", "likes"):
    +            newly_answered.add(current_q)
    +            return newly_answered
    +
    +        # Bare number for numeric fields
    +        bare_num = re.fullmatch(r"\s*(\d+)\s*", message.strip())
    +        if bare_num and current_q in ("servings", "plan_days", "meals_per_day"):
    +            val = int(bare_num.group(1))
    +            if val > 0:
    +                if current_q == "servings":
    +                    draft.servings = val
    +                elif current_q == "plan_days":
    +                    draft.plan_days = val
    +                elif current_q == "meals_per_day":
    +                    draft.meals_per_day = val
    +                newly_answered.add(current_q)
    +            return newly_answered
    +
    +        # Bare word list for list fields (e.g. "peanuts, shellfish" as answer to allergies)
    +        if current_q == "allergies" and not re.search(r"\b(?:servings?|meals?|days?)\b", stripped):
    +            items = self._extract_allergy_items(stripped)
    +            if not items:
    +                # Try splitting as comma-separated items
    +                items = [i.strip() for i in re.split(r"\s*[,]\s*|\s+and\s+", stripped) if i.strip() and i.strip().lower() not in NONE_SENTINELS]
    +            if items:
    +                draft.allergies = self._dedupe_items(draft.allergies + items)
    +                newly_answered.add("allergies")
    +        elif current_q == "dislikes" and not re.search(r"\b(?:servings?|meals?|days?|allerg)\b", stripped):
    +            items = self._extract_clause_items(stripped, DISLIKE_CLAUSE_PATTERNS)
    +            if not items:
    +                items = [i.strip() for i in re.split(r"\s*[,]\s*|\s+and\s+", stripped) if i.strip() and i.strip().lower() not in NONE_SENTINELS]
    +            if items:
    +                draft.dislikes = self._dedupe_items(draft.dislikes + items)
    +                newly_answered.add("dislikes")
    +        elif current_q == "likes" and not re.search(r"\b(?:servings?|meals?|days?|allerg)\b", stripped):
    +            items = self._extract_clause_items(stripped, LIKE_CLAUSE_PATTERNS)
    +            if not items:
    +                items = self._extract_clause_items(stripped, CUISINE_CLAUSE_PATTERNS)
    +            if not items:
    +                items = [i.strip() for i in re.split(r"\s*[,]\s*|\s+and\s+", stripped) if i.strip() and i.strip().lower() not in NONE_SENTINELS]
    +            if items:
    +                draft.cuisine_likes = self._dedupe_items(draft.cuisine_likes + items)
    +                newly_answered.add("likes")
    +
    +        return newly_answered
    +
         def _handle_prefs_flow_threaded(self, user: UserMe, request: ChatRequest, effective_mode: str) -> ChatResponse:
             user_id = user.user_id
             thread_id = request.thread_id
             key = (user_id, thread_id)
     
    +        # --- Misroute detection: inventory text in prefs flow ---
    +        if self._is_inventory_misroute(request.message):
    +            return ChatResponse(
    +                reply_text="That looks like inventory input. Try sending it to the inventory flow instead.",
    +                confirmation_required=False,
    +                proposal_id=None,
    +                proposed_actions=[],
    +                suggested_next_questions=[],
    +                mode=effective_mode,
    +            )
    +
             # --- Pending prefs proposal: treat non-confirm input as edit ---
             existing_pid = self._prefs_proposal_ids.get(key)
             if existing_pid:
    @@ -625,12 +830,14 @@ class ChatService:
                     updated_prefs = self._apply_prefs_edit_text(existing_action.prefs, request.message)
                     action = ProposedUpsertPrefsAction(prefs=updated_prefs)
                     self.proposal_store.save(user_id, existing_pid, action)
    -                # Also update draft so future edits stack
                     self.prefs_drafts[key] = updated_prefs
     
    -                summary = f"Proposed preferences: {updated_prefs.plan_days} days, {updated_prefs.servings} servings, {updated_prefs.meals_per_day} meals/day."
    +                summary = self._build_rolling_summary(
    +                    updated_prefs,
    +                    self._prefs_wizard_answered.get(key, set(WIZARD_FIELD_ORDER)),
    +                )
                     return ChatResponse(
    -                    reply_text=f"{summary} Reply 'confirm' to save, or send changes to edit.",
    +                    reply_text=f"{summary}\nReply 'confirm' to save, or send changes to edit.",
                         confirmation_required=True,
                         proposal_id=existing_pid,
                         proposed_actions=[action],
    @@ -638,19 +845,43 @@ class ChatService:
                         mode=effective_mode,
                     )
     
    +        # --- Wizard: collect fields one at a time ---
             draft = self.prefs_drafts.get(
                 key, UserPrefs(allergies=[], dislikes=[], cuisine_likes=[], servings=0, meals_per_day=0, plan_days=0, notes="")
             )
    +        answered = self._prefs_wizard_answered.get(key, set())
    +        current_q = self._prefs_wizard_current_q.get(key)
     
    +        # Parse structured fields from the message
             parsed = self._parse_prefs_from_message(request.message.lower())
    +
    +        # Detect explicitly mentioned fields
    +        mentioned = self._detect_mentioned_fields(request.message, parsed)
    +
    +        # Attribute bare answers to the current wizard question
    +        bare_attributed = self._attribute_bare_answer(request.message, current_q, draft, answered)
    +
    +        # Merge parsed fields into the draft
             draft = self._merge_prefs_draft(draft, parsed)
    +
    +        # Update answered set
    +        answered = answered | mentioned | bare_attributed
    +
    +        # Store updated state
             self.prefs_drafts[key] = draft
    +        self._prefs_wizard_answered[key] = answered
    +
    +        # Determine next question
    +        next_field = self._next_wizard_question(answered, draft)
     
    -        missing = self._collect_missing_questions(draft)
    -        if missing:
    -            prompt = missing[0]
    +        if next_field is not None:
    +            # Still have questions to ask
    +            self._prefs_wizard_current_q[key] = next_field
    +            question = WIZARD_QUESTIONS[next_field]
    +            summary = self._build_rolling_summary(draft, answered)
    +            reply = f"{summary}\n{question}" if summary else question
                 return ChatResponse(
    -                reply_text=prompt,
    +                reply_text=reply,
                     confirmation_required=False,
                     proposal_id=None,
                     proposed_actions=[],
    @@ -658,7 +889,10 @@ class ChatService:
                     mode=effective_mode,
                 )
     
    +        # All fields collected ÔÇö produce proposal
    +        self._prefs_wizard_current_q[key] = None
             prefs = self._merge_with_defaults(user_id, draft)
    +
             # Clean up stale prefs proposal for this thread before creating a new one
             old_pid = self._prefs_proposal_ids.get(key)
             if old_pid:
    @@ -668,9 +902,9 @@ class ChatService:
             self.proposal_store.save(user_id, proposal_id, action)
             self._prefs_proposal_ids[key] = proposal_id
     
    -        summary = f"Proposed preferences: {prefs.plan_days} days, {prefs.servings} servings, {prefs.meals_per_day} meals/day."
    +        summary = self._build_rolling_summary(prefs, answered)
             return ChatResponse(
    -            reply_text=f"{summary} Reply 'confirm' to save, or send changes to edit.",
    +            reply_text=f"{summary}\nReply 'confirm' to save, or send changes to edit.",
                 confirmation_required=True,
                 proposal_id=proposal_id,
                 proposed_actions=[action],
    diff --git a/app/services/inventory_agent.py b/app/services/inventory_agent.py
    index 8f1c4a5..9a493d3 100644
    --- a/app/services/inventory_agent.py
    +++ b/app/services/inventory_agent.py
    @@ -21,6 +21,27 @@ from app.services.llm_client import LlmClient
     from app.services.proposal_store import ProposalStore
     
     
    +_PREFS_MISROUTE_RE = re.compile(
    +    r"\b(?:allerg(?:y|ies|ic)|can't\s+have|cannot\s+have)\b", re.IGNORECASE,
    +)
    +_PREFS_FIELD_RE = re.compile(
    +    r"\b(?:servings?|meals?\s*per\s*day|plan\s*days?)\b", re.IGNORECASE,
    +)
    +_PREFS_DISLIKE_RE = re.compile(
    +    r"\b(?:dislike|don't\s+like|do\s+not\s+like|hate|detest)\b", re.IGNORECASE,
    +)
    +
    +def _looks_like_prefs(message: str) -> bool:
    +    """Conservative check: does this message look like prefs input sent to inventory?"""
    +    signals = 0
    +    if _PREFS_MISROUTE_RE.search(message):
    +        signals += 1
    +    if _PREFS_FIELD_RE.search(message):
    +        signals += 1
    +    if _PREFS_DISLIKE_RE.search(message):
    +        signals += 1
    +    return signals >= 2
    +
     SEPARATORS = [",", ";", " and ", " plus ", " also ", " then "]
     SPLIT_PATTERN = re.compile(r",|;|\band\b|\bplus\b|\balso\b|\bthen\b", re.IGNORECASE)
     QUANTITY_PATTERN = re.compile(
    @@ -283,6 +304,17 @@ class InventoryAgent:
                     mode=request.mode or "fill",
                 )
     
    +        # Misroute detection: prefs-like text in inventory flow
    +        if _looks_like_prefs(request.message):
    +            return ChatResponse(
    +                reply_text="That looks like preferences input. Try sending it to the preferences flow instead.",
    +                confirmation_required=False,
    +                proposal_id=None,
    +                proposed_actions=[],
    +                suggested_next_questions=[],
    +                mode=request.mode or "fill",
    +            )
    +
             key = (user.user_id, thread_id)
             location = request.location or "pantry"
             pending = self._pending.get(key)
    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    index 10ae5ef..6cfda90 100644
    --- a/evidence/updatedifflog.md
    +++ b/evidence/updatedifflog.md
    @@ -1,41 +1,63 @@
     # Diff Log (overwrite each cycle)
     
     ## Cycle Metadata
    -- Timestamp: 2026-02-09T10:00:00+00:00
    +- Timestamp: 2026-02-09
     - Branch: main
    +- HEAD: 18bf41f68adfcb82cefa713d12a5694dbf00082a
    +- Diff basis: staged
     
     ## Cycle Status
    -- Status: STAGED ÔÇö awaiting AUTHORIZED
    +- Status: COMPLETE ÔÇö awaiting AUTHORIZED
     
     ## Summary
    -- Reconciled partial rename from `duet-flow-status` ÔåÆ unified to `id="duet-flow-chip"` + `class="duet-flow-chip"` across all HTML/TS/CSS/dist files.
    -- `web/dist/index.html` was missing the `duet-status-row` wrapper and `duet-flow-chip` element (dist HTML diverged from source); now brought in sync.
    -- `web/dist/style.css` was missing `.duet-status-row` and `.duet-flow-chip` rules; added to match `web/src/style.css`.
    -- Added `duet-flow-chip` presence check to `tests/test_ui_mount.py`.
    -- Created Playwright e2e spec `web/e2e/flow-chip.spec.ts` (initial load `[General]`, flow switch to `[Inventory]`, `[Preferences]`).
    -
    -## Files Changed
    -- `web/index.html` ÔÇö id `duet-flow` ÔåÆ `duet-flow-chip`
    -- `web/src/main.ts:554` ÔÇö `getElementById("duet-flow")` ÔåÆ `getElementById("duet-flow-chip")`
    -- `web/src/style.css:777` ÔÇö class already `.duet-flow-chip` (no change this cycle)
    -- `web/dist/index.html:37-40` ÔÇö added `duet-status-row` wrapper + `duet-flow-chip` div
    -- `web/dist/main.js:509` ÔÇö `getElementById("duet-flow")` ÔåÆ `getElementById("duet-flow-chip")`
    -- `web/dist/style.css:760-786` ÔÇö added `.duet-status-row` and `.duet-flow-chip` rules; `.duet-status` simplified
    -- `tests/test_ui_mount.py:18` ÔÇö added `assert "duet-flow-chip" in html`
    -- `web/e2e/flow-chip.spec.ts` ÔÇö NEW: 3 Playwright tests for flow chip
    -- `evidence/test_runs.md` ÔÇö appended run entry
    -- `evidence/test_runs_latest.md` ÔÇö overwritten with current run
    -
    -## Key Anchors (source-of-truth for flow tag)
    -- `web/src/main.ts:80-86` ÔÇö `flowOptions[]` defines `{key, label, placeholder}` for each flow
    -- `web/src/main.ts:114` ÔÇö `currentFlowKey` stores active flow key (default `"general"`)
    -- `web/src/main.ts:553-559` ÔÇö `updateFlowStatusText()` reads `currentFlowKey`, formats `[Label]`, writes to `#duet-flow-chip`
    -- `web/src/main.ts:1778-1792` ÔÇö `selectFlow(key)` updates `currentFlowKey` and calls `updateFlowStatusText()`
    -- `web/src/main.ts:1356` ÔÇö History uses same `flow.label` via `[${flowLabel}] ${message}` bracket format
    -- `web/index.html:37` ÔÇö DOM element: `<div class="duet-flow-chip" id="duet-flow-chip">[General]</div>`
    +- feat(prefs): one-question-at-a-time wizard with allergy hard stop
    +- feat(prefs): misroute detection in prefs and inventory flows
    +- refactor: replaced `_handle_prefs_flow_threaded` with wizard-driven flow
    +- test: added `tests/test_prefs_wizard.py` (13 new tests)
    +- test: updated 4 existing test files for wizard compatibility
    +
    +## Files Changed (staged)
    +- app/services/chat_service.py
    +- app/services/inventory_agent.py
    +- tests/test_prefs_wizard.py (NEW)
    +- tests/test_chat_prefs_propose_confirm.py
    +- tests/test_chat_prefs_thread.py
    +- tests/test_prefs_edit_apply.py
    +- tests/test_proposal_edit_semantics.py
    +
    +## Implementation Details
    +
    +### chat_service.py changes:
    +- Added wizard constants: `WIZARD_FIELD_ORDER`, `WIZARD_QUESTIONS`, `_INVENTORY_ACTION_WORDS`, `_INVENTORY_QTY_UNIT_RE`
    +- Added wizard state: `_prefs_wizard_answered`, `_prefs_wizard_current_q` (keyed by user_id, thread_id)
    +- Added mention-detection regexes: `_ALLERGY_MENTION_RE`, `_DISLIKE_MENTION_RE`, `_LIKE_MENTION_RE`
    +- New methods: `_detect_mentioned_fields`, `_is_inventory_misroute`, `_is_prefs_misroute`, `_next_wizard_question`, `_build_rolling_summary`, `_attribute_bare_answer`
    +- Rewrote `_handle_prefs_flow_threaded`: misroute check ÔåÆ parse ÔåÆ detect fields ÔåÆ bare answer attribution ÔåÆ merge draft ÔåÆ wizard progression ÔåÆ proposal on completion
    +- Added wizard state cleanup to `confirm()` (both deny and success paths)
    +
    +### inventory_agent.py changes:
    +- Added `_PREFS_MISROUTE_RE`, `_PREFS_FIELD_RE`, `_PREFS_DISLIKE_RE` patterns
    +- Added `_looks_like_prefs()` standalone function (conservative: requires 2+ prefs signals)
    +- Added misroute check at top of `handle_fill()` ÔÇö returns nudge if prefs text detected
    +
    +### Test updates:
    +- Existing tests that sent only numeric fields (servings/days) now include all wizard fields (`Allergies: none. Dislikes: none. Likes: none.`) for immediate proposal backward compat
    +- `test_chat_prefs_thread.py`: expanded multi-step flow to walk through full wizard progression
    +- `test_chat_prefs_propose_confirm.py`: updated initial messages, adjusted plan_days test to reflect wizard-first-asks-allergies behavior
     
     ## Verification
    -- `python -m pytest --tb=short` ÔåÆ 96 passed, 2 pre-existing failures (encoding, unrelated)
    -- `node scripts/ui_proposal_renderer_test.mjs` ÔåÆ PASS
    -- 2 pre-existing failures confirmed on clean tree via `git stash` / run / `git stash pop`
    -- Playwright e2e spec written but not run (requires live server + browser ÔÇö manual gate)
    +- compileall: pass (0 errors)
    +- pytest: 140 passed, 0 failed, 1 warning
    +- No schema changes (physics.yaml untouched)
    +- Backward compat: all-fields-in-one-message still produces immediate proposal
    +- Edit-apply semantics: all existing edit tests pass with same proposal_id behavior
    +- Wizard cleanup: confirm (both accept and deny) clears wizard state
    +
    +## Notes
    +- Misroute detection is conservative (requires 2+ signals) to avoid false positives
    +- Wizard field order: allergies (hard stop) ÔåÆ dislikes ÔåÆ likes ÔåÆ servings ÔåÆ plan_days ÔåÆ meals_per_day
    +- plan_days and meals_per_day remain alternatives ÔÇö if one is provided, the other is skipped
    +
    +## Next Steps
    +- Get AUTHORIZED to commit
    +- Consider UI integration for wizard step indicators
    diff --git a/scripts/ui_proposal_renderer_test.mjs b/scripts/ui_proposal_renderer_test.mjs
    index 925b8a8..0e563e0 100644
    --- a/scripts/ui_proposal_renderer_test.mjs
    +++ b/scripts/ui_proposal_renderer_test.mjs
    @@ -19,17 +19,13 @@ const sampleResponse = {
       ],
     };
     
    +// Prefs proposals should return null ÔÇö the canonical summary is now in reply_text (wizard rolling summary).
     const summary = formatProposalSummary(sampleResponse);
    -assert(summary, "proposal summary should be generated");
    -assert(summary.includes("Proposed preferences"), "summary heading missing");
    -assert(summary.includes("Servings: 2"), "servings value missing");
    -assert(summary.includes("Allergies: peanuts, shellfish"), "allergy list missing");
    -assert(summary.includes("Dislikes: mushrooms, olives"), "dislikes missing");
    -assert(summary.includes("Cuisine likes: chicken, salmon"), "cuisine likes missing");
     assert(
    -  summary.indexOf("Proposed preferences") === summary.lastIndexOf("Proposed preferences"),
    -  "heading should appear only once"
    +  summary === null,
    +  "formatProposalSummary should return null for prefs-only proposals (wizard reply_text is canonical)"
     );
    +console.log("prefs proposal returns null: PASS");
     
     const inventoryResponse = {
       confirmation_required: true,
    @@ -168,27 +164,19 @@ assert(
     );
     
     const rawReply =
    -  "Proposed preferences: servings 2, meals/day 2. Reply 'confirm' to save, or send changes to edit.";
    -const cleaned = stripProposalPrefix(rawReply);
    -assert(cleaned, "reply text should remain after stripping prefix");
    -assert(!cleaned.startsWith("Proposed preferences"), "prefix should be removed");
    -assert(cleaned.includes("Reply"), "confirmation instruction preserved");
    -const assistantText = `${summary}\n\n${cleaned}`;
    -const confirmCount = (assistantText.match(/Reply/g) ?? []).length;
    -const headingCount = (assistantText.match(/Proposed preferences/g) ?? []).length;
    -assert(confirmCount >= 1, "confirmation instruction should appear at least once");
    -assert(headingCount === 1, "heading should appear once");
    -assert(assistantText.startsWith("Proposed preferences"), "heading should appear first");
    -assert(assistantText.includes("\nÔÇó Servings: 2"), "servings line present");
    -assert(assistantText.includes("\nÔÇó Meals/day: 2"), "meals/day line present");
    -assert(
    -  assistantText.includes("\nÔÇó Allergies:"),
    -  "allergies bullet on its own line"
    -);
    -assert(
    -  assistantText.indexOf("Reply") > assistantText.indexOf("Proposed preferences"),
    -  "confirm instruction should appear after the proposal block"
    -);
    +  "- Allergies: peanuts, shellfish\n- Dislikes: mushrooms, olives\n- Likes: chicken, salmon\n- Servings: 2\n- Plan days: 5\nReply 'confirm' to save, or send changes to edit.";
    +// Since formatProposalSummary returns null for prefs proposals,
    +// the UI will use reply_text directly as the sole summary display.
    +const prefsProposalSummary = formatProposalSummary(sampleResponse);
    +assert(prefsProposalSummary === null, "prefs summary is null ÔÇö reply_text is canonical");
    +// Simulate UI logic: assistantText = proposalSummary ? ... : replyBase
    +const assistantText = prefsProposalSummary ? `${prefsProposalSummary}\n\n${rawReply}` : rawReply;
    +assert(assistantText === rawReply, "display should be exactly the reply_text (no legacy prepend)");
    +assert(!assistantText.includes("Cuisine likes"), "legacy 'Cuisine likes' label must not appear");
    +assert(!assistantText.includes("ÔÇó"), "legacy bullet format must not appear");
    +assert(assistantText.includes("- Allergies:"), "wizard summary uses hyphen format");
    +assert(assistantText.includes("Reply 'confirm'"), "confirm instruction present");
    +console.log("no-duplicate prefs display: PASS");
     // --- date= format tests (new-style DD Month dates from parser) ---
     const dateResponse = {
       confirmation_required: true,
    diff --git a/tests/test_chat_prefs_propose_confirm.py b/tests/test_chat_prefs_propose_confirm.py
    index 2f3db27..6898392 100644
    --- a/tests/test_chat_prefs_propose_confirm.py
    +++ b/tests/test_chat_prefs_propose_confirm.py
    @@ -17,10 +17,10 @@ class FakeDbPrefsRepository(DbPrefsRepository):
     def test_chat_prefs_propose_confirm_flow(authed_client):
         get_prefs_service().repo = FakeDbPrefsRepository()
         thread = "t-prefs-confirm"
    -    # propose
    +    # propose (include all wizard fields for immediate proposal)
         resp = authed_client.post(
             "/chat",
    -        json={"mode": "fill", "message": "set servings 4 meals per day 2", "thread_id": thread},
    +        json={"mode": "fill", "message": "Allergies: none. Dislikes: none. Likes: none. servings 4 meals per day 2", "thread_id": thread},
         )
         assert resp.status_code == 200
         body = resp.json()
    @@ -101,7 +101,7 @@ def test_chat_prefs_confirm_failure_is_retriable(authed_client, monkeypatch):
         thread = "t-prefs-confirm-fail"
         resp = authed_client.post(
             "/chat",
    -        json={"mode": "fill", "message": "set servings 3 meals per day 2", "thread_id": thread},
    +        json={"mode": "fill", "message": "Allergies: none. Dislikes: none. Likes: none. servings 3 meals per day 2", "thread_id": thread},
         )
         assert resp.status_code == 200
         proposal_id = resp.json()["proposal_id"]
    @@ -211,10 +211,11 @@ def test_labeled_paragraph_persists_after_confirm(authed_client):
     
     
     def test_plan_days_asked_only_when_truly_missing(authed_client):
    -    """When servings supplied but days not, must ask. When days supplied, must not."""
    +    """When servings supplied but days not, wizard still has missing fields.
    +    When all fields supplied, must produce proposal."""
         get_prefs_service().repo = FakeDbPrefsRepository()
     
    -    # Case 1: only servings -> asks for plan days
    +    # Case 1: only servings -> wizard asks for allergies first (wizard flow)
         thread1 = "t-prefs-missing-mpd"
         resp1 = authed_client.post(
             "/chat",
    @@ -223,13 +224,14 @@ def test_plan_days_asked_only_when_truly_missing(authed_client):
         assert resp1.status_code == 200
         body1 = resp1.json()
         assert body1["confirmation_required"] is False
    -    assert "day" in body1["reply_text"].lower()
    +    # Wizard asks allergies first (hard stop)
    +    assert "allerg" in body1["reply_text"].lower()
     
    -    # Case 2: servings + days -> proposal (no follow-up)
    +    # Case 2: all fields -> proposal (no follow-up)
         thread2 = "t-prefs-has-days"
         resp2 = authed_client.post(
             "/chat",
    -        json={"mode": "fill", "message": "Servings: 3. Days: 7.", "thread_id": thread2},
    +        json={"mode": "fill", "message": "Allergies: none. Dislikes: none. Likes: none. Servings: 3. Days: 7.", "thread_id": thread2},
         )
         assert resp2.status_code == 200
         body2 = resp2.json()
    diff --git a/tests/test_chat_prefs_thread.py b/tests/test_chat_prefs_thread.py
    index 73dbb0f..9522a5b 100644
    --- a/tests/test_chat_prefs_thread.py
    +++ b/tests/test_chat_prefs_thread.py
    @@ -43,7 +43,7 @@ def test_prefs_missing_loop_and_confirm(client, monkeypatch):
     
         thread = "11111111-1111-4111-8111-111111111111"
     
    -    # missing fields -> ask question
    +    # Step 1: allergies -> wizard asks dislikes next
         resp1 = client.post(
             "/chat",
             json={"mode": "fill", "message": "allergies peanuts", "include_user_library": True, "thread_id": thread},
    @@ -51,24 +51,44 @@ def test_prefs_missing_loop_and_confirm(client, monkeypatch):
         assert resp1.status_code == 200
         data1 = resp1.json()
         assert data1["confirmation_required"] is False
    -    assert "servings" in data1["reply_text"].lower() or "meals" in data1["reply_text"].lower()
    +    assert "dislike" in data1["reply_text"].lower()
     
    -    # supply required fields
    +    # Step 2: dislikes none -> wizard asks likes
         resp2 = client.post(
             "/chat",
    -        json={"mode": "fill", "message": "2 servings and 3 meals per day", "include_user_library": True, "thread_id": thread},
    +        json={"mode": "fill", "message": "none", "include_user_library": True, "thread_id": thread},
         )
         assert resp2.status_code == 200
         data2 = resp2.json()
    -    assert data2["confirmation_required"] is True
    -    proposal_id = data2["proposal_id"]
    +    assert data2["confirmation_required"] is False
    +    assert "like" in data2["reply_text"].lower()
    +
    +    # Step 3: likes none -> wizard asks servings
    +    resp3 = client.post(
    +        "/chat",
    +        json={"mode": "fill", "message": "none", "include_user_library": True, "thread_id": thread},
    +    )
    +    assert resp3.status_code == 200
    +    data3 = resp3.json()
    +    assert data3["confirmation_required"] is False
    +    assert "servings" in data3["reply_text"].lower()
    +
    +    # Step 4: supply servings and meals per day -> proposal
    +    resp4 = client.post(
    +        "/chat",
    +        json={"mode": "fill", "message": "2 servings and 3 meals per day", "include_user_library": True, "thread_id": thread},
    +    )
    +    assert resp4.status_code == 200
    +    data4 = resp4.json()
    +    assert data4["confirmation_required"] is True
    +    proposal_id = data4["proposal_id"]
         assert proposal_id
     
         # confirm writes once
    -    resp3 = client.post("/chat/confirm", json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread})
    -    assert resp3.status_code == 200
    -    assert resp3.json()["applied"] is True
    -    assert resp3.json()["reason"] is None
    +    resp5 = client.post("/chat/confirm", json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread})
    +    assert resp5.status_code == 200
    +    assert resp5.json()["applied"] is True
    +    assert resp5.json()["reason"] is None
         assert len(calls) == 1
         saved = calls[0]
         assert saved.servings == 2
    diff --git a/tests/test_prefs_edit_apply.py b/tests/test_prefs_edit_apply.py
    index a8d927f..2256c8b 100644
    --- a/tests/test_prefs_edit_apply.py
    +++ b/tests/test_prefs_edit_apply.py
    @@ -92,7 +92,7 @@ def test_prefs_edit_adds_allergy(authed_client):
         thread = "t-edit-add-allergy"
     
         resp1 = authed_client.post(
    -        "/chat", json={"mode": "fill", "message": "servings 2 meals per day 3", "thread_id": thread}
    +        "/chat", json={"mode": "fill", "message": "Allergies: none. Dislikes: none. Likes: none. servings 2 meals per day 3", "thread_id": thread}
         )
         body1 = resp1.json()
         pid = body1["proposal_id"]
    @@ -113,7 +113,7 @@ def test_prefs_edit_adds_dislike(authed_client):
     
         resp1 = authed_client.post(
             "/chat",
    -        json={"mode": "fill", "message": "I like chicken and rice. servings 2. days 3.", "thread_id": thread},
    +        json={"mode": "fill", "message": "Allergies: none. Dislikes: none. I like chicken and rice. servings 2. days 3.", "thread_id": thread},
         )
         body1 = resp1.json()
         pid = body1["proposal_id"]
    @@ -139,7 +139,7 @@ def test_prefs_edit_dislike_verb_removes_from_likes(authed_client):
     
         resp1 = authed_client.post(
             "/chat",
    -        json={"mode": "fill", "message": "I like chicken, eggs and rice. Servings 2. Days 3.", "thread_id": thread},
    +        json={"mode": "fill", "message": "Allergies: none. Dislikes: none. I like chicken, eggs and rice. Servings 2. Days 3.", "thread_id": thread},
         )
         body1 = resp1.json()
         pid = body1["proposal_id"]
    @@ -208,7 +208,7 @@ def test_prefs_edit_stacks_multiple_edits(authed_client):
         thread = "t-edit-stacking"
     
         resp1 = authed_client.post(
    -        "/chat", json={"mode": "fill", "message": "Servings: 2. Days: 5.", "thread_id": thread}
    +        "/chat", json={"mode": "fill", "message": "Allergies: none. Dislikes: none. Likes: none. Servings: 2. Days: 5.", "thread_id": thread}
         )
         pid = resp1.json()["proposal_id"]
     
    @@ -239,10 +239,10 @@ def test_prefs_confirm_persists_edited_proposal(authed_client):
         get_prefs_service().repo = FakeDbPrefsRepository()
         thread = "t-edit-then-confirm"
     
    -    # Create proposal
    +    # Create proposal (include all wizard fields)
         resp1 = authed_client.post(
             "/chat",
    -        json={"mode": "fill", "message": "Allergies: milk. Servings: 2. Days: 3.", "thread_id": thread},
    +        json={"mode": "fill", "message": "Allergies: milk. Dislikes: none. Likes: none. Servings: 2. Days: 3.", "thread_id": thread},
         )
         pid = resp1.json()["proposal_id"]
         assert "milk" in resp1.json()["proposed_actions"][0]["prefs"]["allergies"]
    @@ -273,7 +273,7 @@ def test_prefs_confirm_clears_proposal_after_edit(authed_client):
         thread = "t-edit-confirm-clear"
     
         resp1 = authed_client.post(
    -        "/chat", json={"mode": "fill", "message": "Servings: 2. Days: 5.", "thread_id": thread}
    +        "/chat", json={"mode": "fill", "message": "Allergies: none. Dislikes: none. Likes: none. Servings: 2. Days: 5.", "thread_id": thread}
         )
         pid = resp1.json()["proposal_id"]
     
    diff --git a/tests/test_prefs_wizard.py b/tests/test_prefs_wizard.py
    new file mode 100644
    index 0000000..70893ba
    --- /dev/null
    +++ b/tests/test_prefs_wizard.py
    @@ -0,0 +1,308 @@
    +"""Tests for the one-question-at-a-time preferences wizard.
    +
    +Covers:
    +- Wizard progression (field by field)
    +- Allergy hard stop (must be answered first)
    +- Bare answer attribution (none sentinel, bare number, bare list)
    +- Misroute detection (inventory text in prefs flow, prefs text in inventory flow)
    +- Backward compat: all-fields-in-one-message produces immediate proposal
    +- Rolling summary presence
    +"""
    +from app.repos.prefs_repo import DbPrefsRepository
    +from app.services.prefs_service import get_prefs_service
    +
    +
    +class FakeDbPrefsRepository(DbPrefsRepository):
    +    def __init__(self):
    +        self._store: dict[str, object] = {}
    +
    +    def get_prefs(self, user_id: str):
    +        return self._store.get(user_id)
    +
    +    def upsert_prefs(self, user_id, provider_subject, email, prefs, applied_event_id=None):
    +        self._store[user_id] = prefs
    +        return prefs
    +
    +
    +def _post_chat(client, message, thread_id="t-wizard"):
    +    return client.post(
    +        "/chat",
    +        json={"mode": "fill", "message": message, "thread_id": thread_id},
    +    )
    +
    +
    +# ---------------------------------------------------------------------------
    +# 1) Wizard progression: field by field
    +# ---------------------------------------------------------------------------
    +
    +def test_wizard_asks_allergies_first(authed_client):
    +    """First message without allergies triggers allergy question."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    resp = _post_chat(authed_client, "2 servings")
    +    body = resp.json()
    +    assert resp.status_code == 200
    +    assert body["confirmation_required"] is False
    +    assert "allerg" in body["reply_text"].lower()
    +
    +
    +def test_wizard_full_progression(authed_client):
    +    """Walk through the full wizard: allergies -> dislikes -> likes -> servings -> days -> proposal."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-wizard-full"
    +
    +    # Step 1: allergies
    +    r1 = _post_chat(authed_client, "no allergies", thread)
    +    b1 = r1.json()
    +    assert b1["confirmation_required"] is False
    +    assert "dislike" in b1["reply_text"].lower()
    +
    +    # Step 2: dislikes
    +    r2 = _post_chat(authed_client, "none", thread)
    +    b2 = r2.json()
    +    assert b2["confirmation_required"] is False
    +    assert "like" in b2["reply_text"].lower()
    +
    +    # Step 3: likes
    +    r3 = _post_chat(authed_client, "italian, mexican", thread)
    +    b3 = r3.json()
    +    assert b3["confirmation_required"] is False
    +    assert "servings" in b3["reply_text"].lower()
    +
    +    # Step 4: servings
    +    r4 = _post_chat(authed_client, "4", thread)
    +    b4 = r4.json()
    +    assert b4["confirmation_required"] is False
    +    assert "days" in b4["reply_text"].lower() or "meals" in b4["reply_text"].lower()
    +
    +    # Step 5: plan_days
    +    r5 = _post_chat(authed_client, "7", thread)
    +    b5 = r5.json()
    +    # Should now produce a proposal
    +    assert b5["confirmation_required"] is True
    +    assert b5["proposal_id"] is not None
    +    assert b5["proposed_actions"]
    +    prefs = b5["proposed_actions"][0]["prefs"]
    +    assert prefs["servings"] == 4
    +    assert prefs["plan_days"] == 7
    +
    +
    +# ---------------------------------------------------------------------------
    +# 2) Allergy hard stop
    +# ---------------------------------------------------------------------------
    +
    +def test_allergy_hard_stop_blocks_other_fields(authed_client):
    +    """Even if servings/days are provided, allergies must be answered first."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-allergy-stop"
    +
    +    resp = _post_chat(authed_client, "4 servings 7 days", thread)
    +    body = resp.json()
    +    assert body["confirmation_required"] is False
    +    # Must ask about allergies, not proceed to proposal
    +    assert "allerg" in body["reply_text"].lower()
    +
    +
    +def test_allergy_none_sentinel_progresses(authed_client):
    +    """Saying 'none' to allergies moves to the next question."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-allergy-none"
    +
    +    # Start wizard
    +    r1 = _post_chat(authed_client, "2 servings", thread)
    +    assert "allerg" in r1.json()["reply_text"].lower()
    +
    +    # Answer 'none'
    +    r2 = _post_chat(authed_client, "none", thread)
    +    b2 = r2.json()
    +    # Should ask about dislikes, not allergies again
    +    assert "dislike" in b2["reply_text"].lower()
    +
    +
    +def test_allergy_explicit_list_progresses(authed_client):
    +    """Providing explicit allergy list moves to next question."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-allergy-list"
    +
    +    r1 = _post_chat(authed_client, "allergic to peanuts and shellfish", thread)
    +    b1 = r1.json()
    +    assert b1["confirmation_required"] is False
    +    # Should ask about dislikes, not allergies
    +    assert "dislike" in b1["reply_text"].lower()
    +    # Rolling summary should show allergies
    +    assert "peanuts" in b1["reply_text"].lower()
    +
    +
    +# ---------------------------------------------------------------------------
    +# 3) Backward compat: all fields in one message
    +# ---------------------------------------------------------------------------
    +
    +def test_all_fields_one_message_produces_proposal(authed_client):
    +    """A message containing all required fields produces an immediate proposal."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-all-fields"
    +
    +    resp = _post_chat(
    +        authed_client,
    +        "no allergies, dislikes: none, likes: italian, 4 servings, 7 days, 3 meals per day",
    +        thread,
    +    )
    +    body = resp.json()
    +    assert body["confirmation_required"] is True
    +    assert body["proposal_id"] is not None
    +    prefs = body["proposed_actions"][0]["prefs"]
    +    assert prefs["servings"] == 4
    +    assert prefs["plan_days"] == 7
    +    assert prefs["meals_per_day"] == 3
    +
    +
    +def test_paragraph_with_allergies_produces_proposal(authed_client):
    +    """Paragraph providing allergies + all numeric fields + likes/dislikes produces proposal."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-para-allergy"
    +
    +    resp = _post_chat(
    +        authed_client,
    +        "I'm allergic to peanuts, I dislike mushrooms, I like pasta, 2 servings, 5 days, 2 meals per day",
    +        thread,
    +    )
    +    body = resp.json()
    +    assert body["confirmation_required"] is True
    +    prefs = body["proposed_actions"][0]["prefs"]
    +    assert "peanuts" in prefs["allergies"]
    +    assert prefs["servings"] == 2
    +
    +
    +# ---------------------------------------------------------------------------
    +# 4) Misroute detection
    +# ---------------------------------------------------------------------------
    +
    +def test_inventory_misroute_in_prefs_flow(authed_client):
    +    """Inventory-like text in prefs flow returns a nudge."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-misroute-inv"
    +
    +    resp = _post_chat(authed_client, "bought 2kg chicken and picked up 500ml milk", thread)
    +    body = resp.json()
    +    assert body["confirmation_required"] is False
    +    assert "inventory" in body["reply_text"].lower()
    +
    +
    +def test_prefs_misroute_in_inventory_flow(authed_client):
    +    """Prefs-like text in inventory flow returns a nudge."""
    +    resp = authed_client.post(
    +        "/chat/inventory",
    +        json={
    +            "mode": "fill",
    +            "message": "allergic to peanuts, 4 servings, 3 meals per day",
    +            "thread_id": "t-misroute-prefs",
    +        },
    +    )
    +    body = resp.json()
    +    assert body["confirmation_required"] is False
    +    assert "preferences" in body["reply_text"].lower() or "prefs" in body["reply_text"].lower()
    +
    +
    +# ---------------------------------------------------------------------------
    +# 5) Rolling summary
    +# ---------------------------------------------------------------------------
    +
    +def test_rolling_summary_shown_during_wizard(authed_client):
    +    """After answering allergies, the next question shows a summary."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-rolling"
    +
    +    _post_chat(authed_client, "allergic to dairy", thread)
    +    r2 = _post_chat(authed_client, "none", thread)  # dislikes: none
    +    body = r2.json()
    +    # Should mention dairy in summary and ask about likes
    +    assert "dairy" in body["reply_text"].lower()
    +    assert "like" in body["reply_text"].lower()
    +
    +
    +# ---------------------------------------------------------------------------
    +# 6) Wizard cleanup on deny
    +# ---------------------------------------------------------------------------
    +
    +def test_wizard_state_cleared_on_deny(authed_client):
    +    """Denying a proposal clears wizard state; next message starts fresh."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-wizard-deny"
    +
    +    # Walk through full wizard to proposal
    +    _post_chat(authed_client, "no allergies", thread)
    +    _post_chat(authed_client, "none", thread)
    +    _post_chat(authed_client, "none", thread)
    +    _post_chat(authed_client, "4", thread)
    +    r5 = _post_chat(authed_client, "7", thread)
    +    b5 = r5.json()
    +    assert b5["confirmation_required"] is True
    +    pid = b5["proposal_id"]
    +
    +    # Deny
    +    authed_client.post(
    +        "/chat/confirm",
    +        json={"proposal_id": pid, "confirm": False, "thread_id": thread},
    +    )
    +
    +    # Next message should start fresh ÔÇö ask about allergies
    +    r_fresh = _post_chat(authed_client, "2 servings", thread)
    +    body = r_fresh.json()
    +    assert body["confirmation_required"] is False
    +    assert "allerg" in body["reply_text"].lower()
    +
    +
    +# ---------------------------------------------------------------------------
    +# 7) No duplicate summary ÔÇö single canonical display
    +# ---------------------------------------------------------------------------
    +
    +def test_proposal_reply_has_single_summary_no_legacy(authed_client):
    +    """Wizard proposal reply_text must contain exactly one summary (hyphen format),
    +    not the legacy bullet (ÔÇó) or 'Cuisine likes' label."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-no-dup"
    +
    +    _post_chat(authed_client, "allergic to peanuts", thread)
    +    _post_chat(authed_client, "mushrooms", thread)  # dislikes
    +    _post_chat(authed_client, "italian, thai", thread)  # likes
    +    _post_chat(authed_client, "4", thread)  # servings
    +    r5 = _post_chat(authed_client, "7", thread)  # plan_days
    +    b5 = r5.json()
    +
    +    assert b5["confirmation_required"] is True
    +    reply = b5["reply_text"]
    +
    +    # Wizard rolling summary uses "- Field: value" format
    +    assert "- Allergies:" in reply, "wizard summary should use hyphen format"
    +    assert "- Likes:" in reply, "wizard summary should include Likes"
    +    assert "- Servings:" in reply, "wizard summary should include Servings"
    +
    +    # Legacy describePrefs labels must NOT appear in reply_text
    +    assert "Cuisine likes" not in reply, "legacy 'Cuisine likes' label must not appear in reply_text"
    +    assert "\u2022" not in reply, "legacy bullet (ÔÇó) must not appear in reply_text"
    +
    +    # Only one summary block ÔÇö count summary-style lines
    +    summary_lines = [l for l in reply.splitlines() if l.startswith("- ")]
    +    assert len(summary_lines) >= 3, "at least 3 summary lines expected"
    +    # No duplicate: each field label appears at most once
    +    labels = [l.split(":")[0] for l in summary_lines]
    +    assert len(labels) == len(set(labels)), f"duplicate labels found in summary: {labels}"
    +
    +
    +def test_backward_compat_all_fields_single_summary(authed_client):
    +    """All-fields-in-one-message still produces a single canonical summary."""
    +    get_prefs_service().repo = FakeDbPrefsRepository()
    +    thread = "t-compat-dup"
    +
    +    resp = _post_chat(
    +        authed_client,
    +        "Allergies: none. Dislikes: none. Likes: pasta. 2 servings, 5 days.",
    +        thread,
    +    )
    +    body = resp.json()
    +    assert body["confirmation_required"] is True
    +    reply = body["reply_text"]
    +
    +    # Single hyphen-format summary only
    +    assert "- Allergies:" in reply
    +    assert "Cuisine likes" not in reply, "legacy label must not appear"
    +    assert "\u2022" not in reply, "legacy bullet must not appear"
    \ No newline at end of file
    diff --git a/tests/test_proposal_edit_semantics.py b/tests/test_proposal_edit_semantics.py
    index 33d968f..6db0dad 100644
    --- a/tests/test_proposal_edit_semantics.py
    +++ b/tests/test_proposal_edit_semantics.py
    @@ -28,10 +28,10 @@ def test_prefs_deny_clears_proposal(authed_client):
         get_prefs_service().repo = FakeDbPrefsRepository()
         thread = "t-edit-deny"
     
    -    # Create proposal
    +    # Create proposal (include all wizard fields for immediate proposal)
         resp1 = authed_client.post(
             "/chat",
    -        json={"mode": "fill", "message": "servings 2 meals per day 3", "thread_id": thread},
    +        json={"mode": "fill", "message": "Allergies: none. Dislikes: none. Likes: none. servings 2 meals per day 3", "thread_id": thread},
         )
         body1 = resp1.json()
         pid = body1["proposal_id"]
    @@ -59,7 +59,7 @@ def test_reply_copy_updated(authed_client):
         thread = "t-edit-copy"
         resp = authed_client.post(
             "/chat",
    -        json={"mode": "fill", "message": "servings 2 meals per day 3", "thread_id": thread},
    +        json={"mode": "fill", "message": "Allergies: none. Dislikes: none. Likes: none. servings 2 meals per day 3", "thread_id": thread},
         )
         body = resp.json()
         assert "continue editing" not in body["reply_text"]
    diff --git a/web/dist/proposalRenderer.js b/web/dist/proposalRenderer.js
    index ca4cc4d..a5d6946 100644
    --- a/web/dist/proposalRenderer.js
    +++ b/web/dist/proposalRenderer.js
    @@ -122,12 +122,12 @@ export function formatProposalSummary(response) {
         const actions = (_a = response.proposed_actions) !== null && _a !== void 0 ? _a : [];
         const details = [];
         actions.forEach((action) => {
    -        if (action.action_type === "upsert_prefs" && action.prefs) {
    -            details.push(...describePrefs(action.prefs));
    -        }
    -        else {
    -            details.push(formatInventoryAction(action));
    +        if (action.action_type === "upsert_prefs") {
    +            // Prefs summary is canonical in reply_text (wizard rolling summary);
    +            // skip legacy describePrefs to avoid duplicate display.
    +            return;
             }
    +        details.push(formatInventoryAction(action));
         });
         if (!details.length) {
             return null;
    diff --git a/web/src/proposalRenderer.ts b/web/src/proposalRenderer.ts
    index 5530075..9bd415a 100644
    --- a/web/src/proposalRenderer.ts
    +++ b/web/src/proposalRenderer.ts
    @@ -160,11 +160,12 @@ export function formatProposalSummary(response: ChatResponse | null): string | n
       const actions = response.proposed_actions ?? [];
       const details: string[] = [];
       actions.forEach((action) => {
    -    if (action.action_type === "upsert_prefs" && action.prefs) {
    -      details.push(...describePrefs(action.prefs));
    -    } else {
    -      details.push(formatInventoryAction(action));
    +    if (action.action_type === "upsert_prefs") {
    +      // Prefs summary is canonical in reply_text (wizard rolling summary);
    +      // skip legacy describePrefs to avoid duplicate display.
    +      return;
         }
    +    details.push(formatInventoryAction(action));
       });
       if (!details.length) {
         return null;

## Verification
- compileall: pass (0 errors)
- runtime import: OK
- pytest: 142 passed, 0 failed, 1 warning
- node ui_proposal_renderer_test.mjs: PASS (all 4 sections)

## Notes (optional)
- TODO: blockers, risks, constraints.

## Next Steps
- Get AUTHORIZED to commit

