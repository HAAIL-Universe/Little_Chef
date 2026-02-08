"""Diagnostic: trace parsing of the user's real STT to identify all gaps."""
import re
from app.services.inventory_agent import (
    InventoryAgent, QUANTITY_PATTERN, SECTION_TRANSITION_PATTERN,
    DATE_STRIP_PATTERN, LEAD_PREFIXES, FALLBACK_FILLERS,
    CHATTER_LEADING_PREFIXES,
)
from app.services.inventory_service import InventoryService
from app.services.proposal_store import ProposalStore

class _Stub:
    def create_event(self, *a, **kw): pass

agent = InventoryAgent(_Stub(), ProposalStore())

STT = (
    "Alright Little Chef, quick pantry scan: I've got pasta two 500 gram packs both "
    "unopened, and rice one kilo bag about quarter left. Chopped tomatoes six tins best "
    "before 10 October. Tuna four tins best before 3 March. Now fridge stuff: milk two "
    "litres half left use by 10 February, Greek yoghurt two pots use by 11 February, "
    "cheddar cheese 400 grams about half left use by 14 February, ham one pack half left "
    "use by 9 February, spinach one bag half left use by 8 February, eggs six pack four "
    "left best before 12 February. And freezer: peas 900 grams third left, chicken "
    "nuggets one bag quarter full, chips one bag quarter full, bread one loaf about half left."
)

# Step 1: pre-processing
text = STT.strip()
text = agent._replace_number_words(text)
print("=== After number-word replacement (first 200 chars) ===")
print(text[:200])
print()

text = SECTION_TRANSITION_PATTERN.sub(". ", text)
print("=== After section transitions (first 300 chars) ===")
print(text[:300])
print()

# Step 2: greeting strip
text = re.sub(
    r"^(?:alright|okay|hey|hi|hello)\s+little\s+chef\b[,;:\s]*",
    "", text, flags=re.IGNORECASE,
).strip()
print("=== After greeting strip (first 200 chars) ===")
print(text[:200])
print()

# Note: after greeting strip, text starts with: "quick pantry scan: I've got pasta 2 ..."
# The LEAD_PREFIXES / FALLBACK_FILLERS stripping only happens in _clean_segment_text (per-candidate)
# NOT at the text level. This is why the first item picks up the prefix.

# Step 3: show all quantity matches
lower = text.lower()
matches = list(QUANTITY_PATTERN.finditer(lower))
print(f"=== Quantity matches: {len(matches)} ===")
for i, m in enumerate(matches):
    is_date = agent._looks_like_date_quantity(lower, m)
    ctx_start = max(0, m.start()-30)
    ctx_end = min(len(lower), m.end()+25)
    print(f"  [{i:2d}] '{m.group()}'  pos={m.start()}-{m.end()}  date_qty={is_date}  ctx='...{lower[ctx_start:ctx_end]}...'")
print()

# Step 4: parse and show actions
actions, warnings = agent._parse_inventory_actions(STT)
print(f"=== Actions: {len(actions)}, Warnings: {warnings} ===")
for a in actions:
    e = a.event
    print(f"  [{e.item_name}] qty={e.quantity} unit={e.unit} note={e.note}")
print()

# Step 5: verify expected items
EXPECTED = {
    "pasta": {"qty": 2, "notes_should_contain": ["weight_g=500"]},
    "rice": {"qty": 1000, "notes_should_contain": ["remaining=250g"]},
    "chopped tomatoes": {"qty": 6, "notes_should_contain": ["best before", "10"]},
    "tuna": {"qty": 4, "notes_should_contain": ["best before", "3"]},
    "milk": {"qty": 2000, "notes_should_contain": ["remaining=1000ml", "use by", "10"]},
    "greek yoghurt": {"qty": 2, "notes_should_contain": ["use by", "11"]},
    "cheddar cheese": {"qty": 400, "notes_should_contain": ["remaining=200g", "use by", "14"]},
    "ham": {"qty": 1, "notes_should_contain": ["remaining=half", "use by", "9"]},
    "spinach": {"qty": 1, "notes_should_contain": ["remaining=half", "use by", "8"]},
    "eggs": {"qty": 6, "notes_should_contain": ["remaining=4", "best before", "12"]},
    "peas": {"qty": 900, "notes_should_contain": ["remaining=300g"]},
    "chicken nuggets": {"qty": 1, "notes_should_contain": ["remaining=quarter"]},
    "chips": {"qty": 1, "notes_should_contain": ["remaining=quarter"]},
    "bread": {"qty": 1, "notes_should_contain": ["remaining=half"]},
}

print("=== Expected vs Actual ===")
names_lower = {a.event.item_name.lower(): a for a in actions}
for expected_name, expected_data in EXPECTED.items():
    found = None
    for name, act in names_lower.items():
        if expected_name in name or name in expected_name:
            found = act
            break
    if not found:
        print(f"  MISSING: {expected_name}")
        continue
    e = found.event
    issues = []
    if expected_name not in e.item_name.lower():
        issues.append(f"name='{e.item_name}' (expected '{expected_name}')")
    if e.item_name.lower() != expected_name and len(e.item_name) > len(expected_name) + 3:
        issues.append(f"junk_in_name='{e.item_name}'")
    note = (e.note or "").lower()
    for expected_note in expected_data.get("notes_should_contain", []):
        if expected_note.lower() not in note:
            issues.append(f"missing_note='{expected_note}'")
    if issues:
        print(f"  ISSUES [{expected_name}]: {'; '.join(issues)}  (actual note='{e.note}')")
    else:
        print(f"  OK: {expected_name} qty={e.quantity} note='{e.note}'")

# Step 6: junk check
print("\n=== Junk items ===")
expected_names = set(EXPECTED.keys())
for a in actions:
    name = a.event.item_name.lower()
    if not any(en in name or name in en for en in expected_names):
        print(f"  JUNK: [{a.event.item_name}]")
