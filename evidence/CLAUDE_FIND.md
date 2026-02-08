# Pantry Scan Parsing — Senior Review (2026-02-08)

## A) Diagnosis

### Failure mode 1 — Leading chatter not stripped before first quantity match

**JSON proof:** `"I ve got pasta"` (event #1)

The segment for the first quantity (`2`) spans from the text start. `_extract_candidate_phrase` looks at text *before* the number match (`"I ve got pasta"`) and text after (`"gram packs"`). After-text looks like a unit phrase → rejected. Before-text is returned as the candidate. `_clean_segment_text` runs `FALLBACK_FILLERS` stripping on `"i ve got pasta"` — it matches `"i've got"` in the list **but not `"i ve got"`** (the apostrophe-less STT variant). `"i ve got"` *is* in `CHATTER_LEADING_PREFIXES` but `_strip_leading_chatter_tokens` runs **after** `_strip_item_stop_words`, and the candidate phrase goes through `_clean_segment_text` where filler matching happens on the lowered form before chatter-token stripping. The net result: `"I ve got pasta"` leaks through.

### Failure mode 2 — Segment boundary failure across section transitions

**JSON proof:** `"Coco Pops box quarter full Now fridge stuff milk"` (event #12)

The quantity match for `2000` (from `"two litres"` after number-word replacement) lands in a clause that stretches back across the period-free transition `"… quarter full Now fridge stuff milk two litres …"`. No comma, semicolon, or sentence terminator separates "Coco Pops" from "milk". The `_previous_separator` call finds no boundary between them, so the entire run is treated as one segment. The candidate phrase greedily collects words from before the number, yielding `"Coco Pops box quarter full Now fridge stuff milk"`. `_clean_segment_text` strips some tokens but not enough to isolate `"milk"`.

**Root cause:** `SPLIT_PATTERN` doesn't split on section-transition phrases like `"now fridge stuff"`, `"now freezer"`, `"and freezer"`. These are *implicit segment boundaries* in natural speech.

### Failure mode 3 — `"unopened"` leaking into item names

**JSON proof:** `"unopened Chips"` (event #27)

`"unopened"` is in `BARE_FILLER_WORDS` and is checked in `_is_disallowed_item_name` — but only for an **exact** match (`lower in BARE_FILLER_WORDS`). It's not stripped *from within* a compound name. `_strip_item_stop_words` only removes `ITEM_STOP_WORDS`, and `BARE_FILLER_WORDS` is **not** a member of that union. So `"unopened Chips"` passes all guards: it's not filler-only, not container-only, not in the disallowed set (because it's `"unopened chips"`, not just `"unopened"`).

### Failure mode 4 — Dates not captured in `note`

**JSON proof:** All events with known best-before/use-by dates have `note: ""` (or only `weight_g` notes). The `DATE_STRIP_PATTERN` *removes* date text from the candidate to prevent name pollution, but the stripped date value is never captured and written into the event's `note` field. `_extract_use_by_values` only captures the ordinal+item pattern (`"10th on the milk"` format), which doesn't match the natural speech pattern `"best before 10 October"`.

### Failure mode 5 — `FALLBACK_MISSING_QUANTITY` warning from fraction-left items

Phrases like `"half left"`, `"third left"`, `"quarter full"` describe *remaining proportion*, not a parseable quantity. They contain no digit after number-word replacement (since "half"/"third"/"quarter" aren't in `NUMBER_WORDS`). These segments fall through to the no-quantity fallback path and trigger the warning. The fractions aren't being normalized to any useful value or note.

---

## B) Concrete Minimal Fixes (ordered by impact/effort)

### Fix 1 — Add section-transition phrases as segment splitters (HIGH impact, LOW effort)

**Problem:** "Now fridge stuff milk" glues to prior cereal clause.

**Change:** Add section-transition phrases to `SPLIT_PATTERN` or add a pre-processing step that inserts a separator before them.

In `inventory_agent.py` (line ~28), add a pre-split normalization in `_parse_inventory_actions` right after `_replace_number_words`:

```python
# Before segment splitting, insert separators at section transitions
SECTION_TRANSITIONS = re.compile(
    r"\b(now\s+(?:fridge|freezer|cupboard|pantry)\s+(?:stuff|items|things)?)"
    r"|\b(and\s+(?:fridge|freezer|cupboard|pantry))",
    re.IGNORECASE,
)
text = SECTION_TRANSITIONS.sub(r". \1\2", text)
```

**Test to lock it:**
```python
def test_section_transition_splits_milk_from_cereal():
    agent = InventoryAgent(...)
    actions, _ = agent._parse_inventory_actions(
        "Coco Pops one box quarter full Now fridge stuff milk two litres"
    )
    names = {a.event.item_name.lower() for a in actions}
    assert "milk" in names
    assert not any("fridge" in n or "now" in n for n in names)
    assert not any("coco pops" in n and "milk" in n for n in names)
```

---

### Fix 2 — Add `"i ve got"` (apostrophe-less) to `FALLBACK_FILLERS` (HIGH impact, TRIVIAL effort)

**Problem:** `"I ve got pasta"` — STT sometimes emits `"i ve got"` instead of `"i've got"`.

**Change:** In `FALLBACK_FILLERS` (line ~33), add `"i ve got"`. Also defensively add to `CHATTER_LEADING_PREFIXES` (already there, but the filler list is checked first and short-circuits).

```python
FALLBACK_FILLERS = [
    "i've got", "i ve got", "i have", "i got", ...
]
```

**Test:**
```python
def test_apostrophe_less_stt_filler_stripped():
    agent = InventoryAgent(...)
    actions, _ = agent._parse_inventory_actions(
        "I ve got pasta two 500 gram packs"
    )
    assert actions[0].event.item_name.lower() == "pasta"
```

---

### Fix 3 — Add `BARE_FILLER_WORDS` to per-token stripping (MEDIUM impact, LOW effort)

**Problem:** `"unopened Chips"` — `BARE_FILLER_WORDS` are only checked as whole-name disqualifiers, not stripped token-by-token.

**Change:** Add `BARE_FILLER_WORDS` to the `ITEM_STOP_WORDS` union (line ~121):

```python
ITEM_STOP_WORDS = (
    CONTEXT_IGNORE_WORDS
    | CONTAINER_WORDS
    | QUANTITY_ADVERBS
    | UNIT_KEYWORDS
    | ATTACHMENT_ONLY_WORDS
    | CHATTER_WORDS
    | BARE_FILLER_WORDS  # ← add this
)
```

**Caution:** This means `"cereal"` as a standalone will always be stripped. But `"cereal"` alone is already disallowed by `_is_disallowed_item_name`, so no loss. The cereal *brand* names (`"cornflakes"`, `"coco pops"`) are extracted via `_extract_cereal_candidate` before stop-word stripping, so they're safe.

**Test:**
```python
def test_unopened_stripped_from_item_name():
    agent = InventoryAgent(...)
    actions, _ = agent._parse_inventory_actions(
        "Mixed veg one bag unopened. Chips one bag third left"
    )
    names = {a.event.item_name.lower() for a in actions}
    assert "chips" in names
    assert "unopened chips" not in names
    assert "mixed veg" in names
```

---

### Fix 4 — Capture date values into `note` field before stripping (MEDIUM impact, MEDIUM effort)

**Problem:** Best-before/use-by dates present in STT but lost during `DATE_STRIP_PATTERN.sub("", ...)`.

**Change:** In `_clean_segment_text`, before stripping dates, extract them into a return channel. Or better: in `_parse_inventory_actions`, after extracting the candidate and before cleaning, run a date-extraction regex and stash the result, then attach it as a note.

```python
DATE_VALUE_PATTERN = re.compile(
    r"\b(?:best before|use by|use-by|sell by|expires on|due by)\s+"
    r"(\d{1,2})\s*(?:st|nd|rd|th)?\s*(?:of\s+)?"
    rf"({MONTH_NAME_PATTERN})\b",
    re.IGNORECASE,
)
```

For each quantity match's segment, find `DATE_VALUE_PATTERN`, extract `f"bb={day} {month}"` or `f"use_by={day} {month}"`, and inject into the action's `note`.

**Test:**
```python
def test_best_before_captured_in_note():
    agent = InventoryAgent(...)
    actions, _ = agent._parse_inventory_actions(
        "Tuna four tins best before 3 March"
    )
    tuna = [a for a in actions if "tuna" in a.event.item_name.lower()][0]
    assert "bb=3 march" in tuna.event.note.lower() or "best_before=" in tuna.event.note.lower()
```

---

### Fix 5 — Add a final-gate invariant: item name must contain ≥1 likely-food alpha token (MEDIUM impact, LOW effort)

**Problem:** Defense-in-depth against future regressions. Names like `"left"`, `"stuff"`, `"fridge"` could sneak back in. Current guards are additive (each checks one thing); no single invariant prevents all junk.

**Change:** After all cleaning and before creating the `ProposedInventoryEventAction`, add:

```python
def _passes_final_gate(self, item_name: str) -> bool:
    """Item name must have ≥1 token that is not in any stop/filler/container set."""
    ALL_NON_FOOD = ITEM_STOP_WORDS | BARE_FILLER_WORDS | CONTAINER_WORD_HINTS
    tokens = re.findall(r"[a-zA-Z]+", item_name.lower())
    return any(t not in ALL_NON_FOOD for t in tokens)
```

This is a structural invariant — it guarantees no name composed entirely of non-food tokens can reach DB.

**Test:**
```python
@pytest.mark.parametrize("junk", [
    "unopened", "sliced", "left", "fridge", "now", "freezer",
    "bag pack", "tin jar", "about roughly",
])
def test_final_gate_rejects_all_junk_names(junk):
    agent = InventoryAgent(...)
    assert not agent._passes_final_gate(junk)

@pytest.mark.parametrize("good", ["pasta", "milk", "chicken breast", "coco pops"])
def test_final_gate_accepts_food_names(good):
    agent = InventoryAgent(...)
    assert agent._passes_final_gate(good)
```

---

### Fix 6 — Normalize `"both unopened"` and `"half full"` / `"quarter full"` as state notes (LOW impact, MEDIUM effort)

**Problem:** Phrases like `"both unopened"`, `"half full"`, `"quarter full"` either pollute names or are silently lost. They carry useful state info.

**Change:** Add a pattern that extracts state descriptors and attaches them as notes:

```python
STATE_DESCRIPTOR = re.compile(
    r"\b(unopened|half\s+(?:left|full)|third\s+(?:left|full)|quarter\s+(?:left|full)|both\s+unopened)\b",
    re.IGNORECASE,
)
```

Before cleaning, extract matches and append to note as `state=unopened` or `remaining=half`. Then strip them from the candidate.

**Test:**
```python
def test_state_descriptor_captured_as_note():
    agent = InventoryAgent(...)
    actions, _ = agent._parse_inventory_actions("Chips one bag half left")
    chips = [a for a in actions if "chips" in a.event.item_name.lower()][0]
    assert "remaining=half" in chips.event.note or "half left" in chips.event.note
```

---

## C) Stretch Ideas

### Small curated alias file (brand → generic)

Worth it, but **controlled**:
- A `data/item_aliases.json` with human-approved entries: `{"coco pops": "chocolate cereal", "lurpak": "butter", ...}`
- Loaded once at startup; used only for **dedup matching**, not for renaming. The user sees `"Coco Pops"` in the proposal; the dedup key maps through the alias.
- Rule: aliases can only be added via PR, never auto-generated.
- Max ~50 entries. Not a food database.

### Confidence scoring / "needs-edit" UI hint

Each proposed action could carry a `confidence: "high" | "medium" | "low"` field:
- **High:** quantity extracted from explicit number + recognized unit.
- **Medium:** quantity=1 fallback, or state descriptor stripped.
- **Low:** `_guess_item_name` was used, or name came from container fallback.

The UI renders low-confidence items with an edit icon. This is a 1-field schema addition + a few assignment lines — not a rewrite.

---

## D) Red-Team Safety Check

### How junk can still slip into DB today:

| Vector | Example | Current guard gap |
|--------|---------|-------------------|
| **Adjective-only names** | `"sliced"`, `"unopened"` as part of compound | `BARE_FILLER_WORDS` only blocks exact match, not substring (Fix 3 solves) |
| **Location words surviving** | `"fridge stuff milk"` | `"fridge"` and `"stuff"` not in `ITEM_STOP_WORDS`; `"stuff"` not in any set | Add `"stuff"`, `"things"`, `"items"` to `BARE_FILLER_WORDS` |
| **Future new fillers** | Any new STT preamble pattern | No structural invariant catches unknown filler | Fix 5's final gate solves |
| **Numeric-only after cleaning** | Edge case: segment cleaned to `"250"` | `_is_filler_text` checks for alpha but `re.search(r"[a-zA-Z]")` would still pass `"250g"` | Add check: reject names where *all* alpha tokens are stop words |
| **LLM path bypass** | If LLM is enabled and returns junk `name_raw` | `normalize_items` doesn't run `_is_disallowed_item_name` | Add the same final-gate to the LLM path |

### Proposed invariant (hard safety wall):

```python
# In confirm() — right before DB write, not just at proposal time
for action in proposal.actions:
    if action.action_type == "create_inventory_event":
        assert self._passes_final_gate(action.event.item_name), \
            f"Blocked junk item: {action.event.item_name}"
```

This ensures that even if parsing regresses, **nothing hits the DB** without passing the structural check. It's the equivalent of a database constraint — defense at the write boundary.

---

## E) Questions (4)

1. **Is the LLM extraction path (`extract_new_draft`) currently enabled in production/test, or is the regex parser always the active path?** This affects whether Fix 5's final gate needs to be duplicated into `normalize_items`.

2. **Can I see `_split_segments` (around line 1091)?** I want to confirm whether it already handles any implicit boundaries beyond `SPLIT_PATTERN`, or if Fix 1 is the first such logic.

3. **Is `"stuff"` appearing in any legitimate item name in your test fixtures?** I want to add it to `BARE_FILLER_WORDS` but need to confirm it won't break `"stuffed peppers"` or similar.

4. **What's the current test count on `test_inventory_agent.py` and pass rate?** This tells me how much regression surface exists for the fixes above.
