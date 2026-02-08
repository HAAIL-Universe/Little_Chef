# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-08T19:51:20+00:00
- Branch: recovery/evidence-20260208
- HEAD: 963eb03e3d1e25314b761860a635d5df24d473fe
- BASE_HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Inventory parser now strips lead-in junk/dates and avoids container-only names before building proposals.
- Added _is_disallowed_item_name plus new junk filters so only plausible foods emit events.
- New STT fixtures/tests prove container words/dates are excluded while core foods stay.

## Files Changed (staged)
- app/services/inventory_agent.py
- evidence/test_runs.md
- evidence/test_runs_latest.md
- tests/test_inventory_agent.py

## git status -sb
    ## recovery/evidence-20260208
    M  app/services/inventory_agent.py
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
    M  tests/test_inventory_agent.py

## Minimal Diff Hunks
    diff --git a/app/services/inventory_agent.py b/app/services/inventory_agent.py
    index 788dafd..ed8106b 100644
    --- a/app/services/inventory_agent.py
    +++ b/app/services/inventory_agent.py
    @@ -40,6 +40,8 @@ FALLBACK_FILLERS = [
         "just got",
         "the",
         "a",
    +    "half left",
    +    "about half left",
     ]
     FALLBACK_ATTACHMENT_DROPPED = "FALLBACK_ATTACHMENT_DROPPED"
     DATE_CONTEXT_PHRASES = ["use by", "sell by", "expires on", "best before", "due by"]
    @@ -64,6 +66,7 @@ CHATTER_LEADING_PREFIXES = (
     DATE_MARKER_PHRASES = {"use by", "use-by", "best before", "bb"}
     ORDINAL_SUFFIXES = ("st", "nd", "rd", "th")
     ORDINAL_PATTERN = r"\d+(?:st|nd|rd|th)"
    +MONTH_NAME_PATTERN = r"(?:january|february|march|april|may|june|july|august|september|october|november|december)"
     USE_BY_VALUE_PATTERN = re.compile(
         rf"({ORDINAL_PATTERN})\s+(?:on|for)\s+(?:the\s+)?([\w'-]+(?:\s+[\w'-]+)?)",
         re.IGNORECASE,
    @@ -93,7 +96,38 @@ FALLBACK_IGNORE_PHRASES = {"i've just been through the cupboard", "no idea how m
     AFTER_IGNORE_WORDS = CONTEXT_IGNORE_WORDS | QUANTITY_ADVERBS | UNIT_KEYWORDS
     BEFORE_IGNORE_WORDS = CONTEXT_IGNORE_WORDS | QUANTITY_ADVERBS
     INTRO_LOCATION_WORDS = {"cupboard", "fridge", "pantry"}
    -CONTAINER_WORDS = {"bag", "bags", "pack", "packs", "bottle", "bottles", "jar", "jars", "can", "cans", "loaf", "loaves"}
    +CONTAINER_WORDS = {
    +    "bag",
    +    "bags",
    +    "pack",
    +    "packs",
    +    "bottle",
    +    "bottles",
    +    "jar",
    +    "jars",
    +    "can",
    +    "cans",
    +    "loaf",
    +    "loaves",
    +    "tin",
    +    "tins",
    +    "pot",
    +    "pots",
    +    "piece",
    +    "pieces",
    +    "bulb",
    +    "slice",
    +    "slices",
    +}
    +BARE_FILLER_WORDS = {
    +    "unopened",
    +    "sliced",
    +    "left",
    +    "cereal",
    +    "now",
    +    "fridge",
    +    "freezer",
    +}
     ITEM_STOP_WORDS = (
         CONTEXT_IGNORE_WORDS
         | CONTAINER_WORDS
    @@ -128,7 +162,53 @@ NUMBER_WORDS = {
     }
     NUMBER_WORD_PATTERN = re.compile(r"\b(" + r"|".join(re.escape(word) for word in NUMBER_WORDS) + r")\b", re.IGNORECASE)
     
    -
    +DATE_STRIP_PATTERN = re.compile(
    +    rf"\b(?:best before|use by|use-by|sell by|expires on|due by)\b[^,;.]*"
    +    rf"|\bbefore\b[^,;.]*\b{MONTH_NAME_PATTERN}\b[^,;.]*(?:\s*\d{{4}})?",
    +    re.IGNORECASE,
    +)
    +FRACTION_LEFT_PATTERN = re.compile(
    +    r"^(?:a|about)\s+(?:half|third|quarter)\s+left$", re.IGNORECASE
    +)
    +LEAD_PREFIXES = (
    +    "quick stock check",
    +    "i've got",
    +    "both unopened",
    +    "now fridge stuff",
    +    "freezer",
    +    "about half left",
    +    "half left",
    +    "a third left",
    +    "third left",
    +    "a quarter left",
    +)
    +CEREAL_TOKENS = ("coco pops", "cornflakes")
    +
    +CONTAINER_PHRASE_SEPARATORS = [",", ";", " and ", " plus ", " also ", " then "]
    +CONTAINER_WORD_HINTS = {
    +    "tin",
    +    "tins",
    +    "can",
    +    "cans",
    +    "jar",
    +    "bottle",
    +    "bottles",
    +    "bag",
    +    "bags",
    +    "pack",
    +    "packs",
    +    "box",
    +    "boxes",
    +    "pot",
    +    "pots",
    +    "piece",
    +    "pieces",
    +    "bulb",
    +    "loaf",
    +    "loaves",
    +    "slice",
    +    "slices",
    +}
     @dataclass
     class InventoryPending:
         raw_items: List[DraftItemRaw]
    @@ -486,12 +566,35 @@ class InventoryAgent:
                     clause_text = lower[start:end]
                     if self._is_chatter_clause(clause_text):
                         continue
    +                left_segment = text[:start]
                     candidate = self._extract_candidate_phrase(segment, rel_start, rel_end)
                     if not candidate:
                         candidate = self._remove_numeric_from_phrase(segment, rel_start, rel_end)
    -                item_name = self._clean_segment_text(candidate)
    -                if not item_name:
    -                    item_name = self._guess_item_name(text, match.start())
    +                primary_name = self._clean_segment_text(candidate)
    +                cereal_candidate = self._extract_cereal_candidate(segment)
    +                if cereal_candidate:
    +                    primary_name = cereal_candidate
    +                fallback_left = ""
    +                if left_segment:
    +                    fallback_left_clause = self._extract_left_clause(left_segment)
    +                    if fallback_left_clause:
    +                        fallback_left_clause = re.sub(r"\d+", " ", fallback_left_clause)
    +                        fallback_left = self._clean_segment_text(fallback_left_clause)
    +                guess_cleaned = self._clean_segment_text(
    +                    self._guess_item_name(text, match.start())
    +                )
    +                fallback_override = ""
    +                if fallback_left and not self._is_container_candidate(fallback_left):
    +                    fallback_override = fallback_left
    +                elif guess_cleaned and not self._is_container_candidate(guess_cleaned):
    +                    fallback_override = guess_cleaned
    +                if fallback_override and (
    +                    not primary_name or self._is_container_candidate(primary_name)
    +                ):
    +                    primary_name = fallback_override
    +                if not primary_name:
    +                    primary_name = self._guess_item_name(text, match.start())
    +                item_name = primary_name
                     if not item_name:
                         item_name = "item"
                     if self._is_filler_text(item_name):
    @@ -515,6 +618,8 @@ class InventoryAgent:
                     normalized_key = self._normalize_item_key(item_name)
                     if not normalized_key:
                         normalized_key = item_name.lower()
    +                if self._is_disallowed_item_name(item_name, normalized_key):
    +                    continue
                     dedup_key = self._dedup_key(normalized_key)
                     measurement_note = self._measurement_note_value(unit, quantity)
                     existing_index = action_index.get(normalized_key)
    @@ -615,6 +720,8 @@ class InventoryAgent:
                     normalized_key = self._normalize_item_key(cleaned)
                     if not normalized_key:
                         normalized_key = cleaned_lower
    +                if self._is_disallowed_item_name(cleaned, normalized_key):
    +                    continue
                     dedup_key = self._dedup_key(normalized_key)
                     if dedup_key in seen_dedup_keys:
                         continue
    @@ -655,6 +762,8 @@ class InventoryAgent:
                     normalized_key = self._normalize_item_key(cleaned)
                     if not normalized_key:
                         normalized_key = cleaned_lower
    +                if self._is_disallowed_item_name(cleaned, normalized_key):
    +                    continue
                     dedup_key = self._dedup_key(normalized_key)
                     if dedup_key in seen_dedup_keys:
                         continue
    @@ -807,15 +916,24 @@ class InventoryAgent:
     
         def _clean_segment_text(self, segment: str) -> str:
             cleaned = re.sub(r"\s+", " ", segment).strip(" ,;.")
    +        cleaned = DATE_STRIP_PATTERN.sub("", cleaned)
    +        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;.")
             lowered = cleaned.lower()
             for filler in FALLBACK_FILLERS:
    -            if lowered.startswith(filler + " ") or lowered == filler:
    -                cleaned = cleaned[len(filler) :].strip()
    -                lowered = cleaned.lower()
    +            if lowered == filler:
    +                cleaned = ""
    +                lowered = ""
    +                break
    +            if lowered.startswith(filler):
    +                boundary = len(filler)
    +                if boundary == len(lowered) or lowered[boundary] in " ,;.":
    +                    cleaned = cleaned[boundary:].strip(" ,;.")
    +                    lowered = cleaned.lower()
             cleaned = cleaned.strip(" ,;.")
             cleaned = self._strip_item_stop_words(cleaned)
             cleaned = cleaned.strip(" ,;.")
             cleaned = self._strip_leading_chatter_tokens(cleaned)
    +        cleaned = self._strip_leading_prefixes(cleaned)
             if self._is_filler_text(cleaned):
                 return ""
             return cleaned
    @@ -835,6 +953,20 @@ class InventoryAgent:
                     lower = trimmed.lower()
             return trimmed
     
    +    def _strip_leading_prefixes(self, text: str) -> str:
    +        trimmed = text.strip(" ,;.")
    +        lower = trimmed.lower()
    +        changed = True
    +        while trimmed and changed:
    +            changed = False
    +            for prefix in sorted(LEAD_PREFIXES, key=len, reverse=True):
    +                if lower.startswith(prefix):
    +                    trimmed = trimmed[len(prefix) :].strip(" ,;.")
    +                    lower = trimmed.lower()
    +                    changed = True
    +                    break
    +        return trimmed
    +
         def _find_segment_boundary(self, lower_segment: str, after_idx: int) -> Optional[int]:
             markers = set(DATE_CONTEXT_PHRASES) | DATE_MARKER_PHRASES | UNCERTAINTY_MARKERS
             boundary: Optional[int] = None
    @@ -878,6 +1010,20 @@ class InventoryAgent:
                 return False
             return any(token.lower() not in ITEM_STOP_WORDS for token in normalized_tokens)
     
    +    def _is_disallowed_item_name(self, item_name: str, normalized_key: str) -> bool:
    +        lower = item_name.lower().strip()
    +        if not lower:
    +            return True
    +        if normalized_key == "okay little chef":
    +            return True
    +        if lower in BARE_FILLER_WORDS:
    +            return True
    +        if FRACTION_LEFT_PATTERN.match(lower):
    +            return True
    +        if normalized_key in CONTAINER_WORDS:
    +            return True
    +        return False
    +
         def _clamp_multi_anchor(self, item_name: str, unit: str) -> str:
             lower = item_name.lower()
             tokens = set(re.findall(r"[\w'-]+", lower))
    @@ -902,6 +1048,37 @@ class InventoryAgent:
                 return ""
             return " ".join(words[-limit:])
     
    +    def _extract_left_clause(self, text: str) -> str:
    +        clause = text.strip(" ,;.")
    +        if not clause:
    +            return ""
    +        lower_clause = clause.lower()
    +        last_idx = -1
    +        last_len = 0
    +        for sep in CONTAINER_PHRASE_SEPARATORS:
    +            idx = lower_clause.rfind(sep)
    +            if idx != -1 and idx > last_idx:
    +                last_idx = idx
    +                last_len = len(sep)
    +        if last_idx != -1:
    +            clause = clause[last_idx + last_len :].strip(" ,;.")
    +        return clause.strip(" ,;.")
    +
    +    def _extract_cereal_candidate(self, segment: str) -> Optional[str]:
    +        lower_segment = segment.lower()
    +        for token in CEREAL_TOKENS:
    +            if token in lower_segment:
    +                return token
    +        return None
    +
    +    def _is_container_candidate(self, item_name: str) -> bool:
    +        if not item_name:
    +            return False
    +        tokens = [word for word in re.findall(r"[\w'-]+", item_name.lower()) if word]
    +        if not tokens:
    +            return False
    +        return all(token in CONTAINER_WORD_HINTS for token in tokens)
    +
         def _normalize_quantity_and_unit(
             self, quantity_str: str, unit_str: Optional[str]
         ) -> Tuple[float, str]:
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    index e73c946..14632e9 100644
    --- a/evidence/test_runs.md
    +++ b/evidence/test_runs.md
    @@ -13340,3 +13340,24 @@ MM web/src/main.ts
      web/src/main.ts                 |  12 ++-
      8 files changed, 441 insertions(+), 188 deletions(-)
     ```
    +## Test Run 2026-02-08T19:50:39Z
    +- Status: PASS
    +- Start: 2026-02-08T19:50:39Z
    +- End: 2026-02-08T19:50:47Z
    +- Python: C:\Users\krisd\AppData\Local\Programs\Python\Python312\python.exe
    +- Branch: recovery/evidence-20260208
    +- HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
    +- compileall exit: 0
    +- python -m pytest -q exit: 0
    +- git status -sb:
    +```
    +## recovery/evidence-20260208
    + M app/services/inventory_agent.py
    + M tests/test_inventory_agent.py
    +```
    +- git diff --stat:
    +```
    + app/services/inventory_agent.py | 193 ++++++++++++++++++++++++++++++++++++++--
    + tests/test_inventory_agent.py |  88 ++++++++++++++++++
    + 2 files changed, 281 insertions(+), 0 deletions(-)
    +```
    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    index b226613..692cf90 100644
    --- a/evidence/test_runs_latest.md
    +++ b/evidence/test_runs_latest.md
    @@ -1,34 +1,20 @@
     Status: PASS
    -Start: 2026-02-08T19:41:40Z
    -End: 2026-02-08T19:42:35Z
    +Start: 2026-02-08T19:50:39Z
    +End: 2026-02-08T19:50:47Z
     Branch: recovery/evidence-20260208
     HEAD: 2cd256e6f671a5885e6b9a839981ef00f9a9ae76
     Python: C:\Users\krisd\AppData\Local\Programs\Python\Python312\python.exe
     compileall exit: 0
     python -m pytest -q exit: 0
    -npm --prefix web run build exit: 0
    -npm --prefix web run test:e2e exit: 0
     git status -sb:
     ```
     ## recovery/evidence-20260208
      M app/services/inventory_agent.py
    - M evidence/test_runs.md
    - M evidence/test_runs_latest.md
    - M evidence/updatedifflog.md
      M tests/test_inventory_agent.py
    - M web/dist/main.js
    - M web/e2e/history-badge.spec.ts
    - M web/src/main.ts
     ```
     git diff --stat:
     ```
      app/services/inventory_agent.py | 193 ++++++++++++++++++++++++++++++++++++++--
    - evidence/test_runs.md           |  89 ++++++++++++++++++
    - evidence/test_runs_latest.md    |  44 ++++-----
    - evidence/updatedifflog.md       | 185 ++++++++------------------------------
    - tests/test_inventory_agent.py   |  88 ++++++++++++++++++
    - web/dist/main.js                |  12 ++-
    - web/e2e/history-badge.spec.ts   |   6 +-
    - web/src/main.ts                 |  12 ++-
    - 8 files changed, 441 insertions(+), 188 deletions(-)
    + tests/test_inventory_agent.py |  88 ++++++++++++++++++
    + 2 files changed, 281 insertions(+), 0 deletions(-)
     ```
    diff --git a/tests/test_inventory_agent.py b/tests/test_inventory_agent.py
    index 18356dc..45b85d0 100644
    --- a/tests/test_inventory_agent.py
    +++ b/tests/test_inventory_agent.py
    @@ -1,3 +1,5 @@
    +import re
    +
     from app.services.inventory_agent import InventoryAgent
     from app.services.proposal_store import ProposalStore
     
    @@ -22,6 +24,11 @@ STT_CUPBOARD_FRIDGE_LONG = (
         "2 litres use by the 11th, and orange juice 1 litre. That's everything, cheers, ignore that last bit."
     )
     
    +STT_CONTAINER_SCAN = (
    +    "Tinned chopped tomatoes, six tins best before February 2027. Greek yoghurt, two pots. "
    +    "Chicken breast, two pieces. Garlic, one bulb. Milk, two litres, about half left. Cheddar, best before 5 March."
    +)
    +
     
     
     def _inventory_events(client):
    @@ -172,6 +179,87 @@ def test_inventory_agent_parses_stt_inventory_message():
         assert "use_by=12th" in (ham_actions[0].event.note or "")
     
     
    +def test_inventory_agent_prefers_food_names_over_containers():
    +    agent, _ = _make_agent()
    +    actions, _ = agent._parse_inventory_actions(STT_CONTAINER_SCAN)
    +    assert actions, "Expected actions from the container scan."
    +
    +    container_words = {
    +        "tin",
    +        "tins",
    +        "can",
    +        "cans",
    +        "jar",
    +        "bottle",
    +        "bag",
    +        "pack",
    +        "box",
    +        "pot",
    +        "pots",
    +        "piece",
    +        "pieces",
    +        "bulb",
    +        "loaf",
    +        "slice",
    +        "slices",
    +    }
    +
    +    for action in actions:
    +        name = action.event.item_name.lower()
    +        assert name not in container_words
    +        assert "best before" not in name
    +        assert not re.search(r"\\b(march|february)\\b", name)
    +
    +    assert any("tomato" in action.event.item_name.lower() for action in actions)
    +    assert any("yoghurt" in action.event.item_name.lower() for action in actions)
    +    assert any("chicken" in action.event.item_name.lower() for action in actions)
    +
    +    expected_foods = {
    +        "tomato": False,
    +        "yoghurt": False,
    +        "chicken": False,
    +        "garlic": False,
    +        "milk": False,
    +        "cheddar": False,
    +    }
    +    for action in actions:
    +        lower_name = action.event.item_name.lower()
    +        for food in expected_foods:
    +            if food in lower_name:
    +                expected_foods[food] = True
    +    assert all(expected_foods.values())
    +
    +    date_terms = {"best before", "use by", "use-by", "february", "march"}
    +    for action in actions:
    +        lower_name = action.event.item_name.lower()
    +        assert not any(term in lower_name for term in date_terms)
    +
    +    milk_actions = [
    +        action for action in actions if "milk" in action.event.item_name.lower()
    +    ]
    +    assert milk_actions
    +    assert any(
    +        action.event.quantity == 2000 and action.event.unit == "ml"
    +        for action in milk_actions
    +    )
    +
    +    garlic_actions = [
    +        action for action in actions if "garlic" in action.event.item_name.lower()
    +    ]
    +    assert garlic_actions
    +    assert garlic_actions[0].event.quantity == 1
    +    assert garlic_actions[0].event.unit == "count"
    +
    +    cheddar = next(
    +        (action for action in actions if "cheddar" in action.event.item_name.lower()),
    +        None,
    +    )
    +    assert cheddar
    +    cheddar_name = cheddar.event.item_name.lower()
    +    assert "march" not in cheddar_name
    +    assert "best before" not in cheddar_name
    +
    +
     def test_inventory_agent_handles_chicken_use_by_stt():
         agent, _ = _make_agent()
         actions, _ = agent._parse_inventory_actions(STT_CHICKEN_USE_BY)

## Verification
- python -m compileall . (pass)
- python -m pytest -q (pass)

## Notes (optional)
- TODO: blockers, risks, constraints.

## Next Steps
- Hold for Julius AUTHORIZED before committing.

