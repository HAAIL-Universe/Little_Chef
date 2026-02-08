"""Diagnostic: trace parsing of new STT to identify all gaps."""
import re
from app.services.inventory_agent import InventoryAgent
from app.services.proposal_store import ProposalStore

class _Stub:
    def create_event(self, *a, **kw): pass

agent = InventoryAgent(_Stub(), ProposalStore())

STT = (
    "Okay Little Chef, full scan again: cupboard first, pasta three packs 500 grams, "
    "one pack opened and about half left, rice one kilo bag about a third left, lentils "
    "500 grams about quarter left, chopped tomatoes eight tins best before 12 October, "
    "tuna six tins best before 5 March, baked beans four tins best before 20 January, "
    "peanut butter one jar half left best before 6 June, olive oil 500 ml bottle quarter "
    "left. Now fridge stuff: milk two litres half left use by 10 February, cheddar cheese "
    "400 grams about half left use by 14 February, Greek yoghurt three pots use by 11 "
    "February, butter 250 grams half left best before 2 March, eggs ten pack six left "
    "best before 12 February, spinach one bag half left use by 8 February, chicken "
    "breast two pieces use by 9 February, mince beef 500 grams use by 10 February. And "
    "freezer: peas 900 grams third left, mixed veg one bag unopened, chips one bag "
    "quarter full, bread one loaf about half left, ice cream one tub half full."
)

actions, warnings = agent._parse_inventory_actions(STT)
print(f"Actions: {len(actions)}, Warnings: {warnings}\n")
for a in actions:
    e = a.event
    print(f"  [{e.item_name}] qty={e.quantity} unit={e.unit} note={e.note}")

EXPECTED = {
    "pasta": {},
    "rice": {},
    "lentils": {},
    "chopped tomatoes": {"date": "12 October"},
    "tuna": {"date": "5 March"},
    "baked beans": {"date": "20 January"},
    "peanut butter": {"date": "6 June"},
    "olive oil": {},
    "milk": {"date": "10 February"},
    "cheddar cheese": {"date": "14 February"},
    "greek yoghurt": {"date": "11 February"},
    "butter": {"date": "2 March"},
    "eggs": {"date": "12 February"},
    "spinach": {"date": "8 February"},
    "chicken breast": {"date": "9 February"},
    "mince beef": {"date": "10 February"},
    "peas": {},
    "mixed veg": {},
    "chips": {},
    "bread": {},
    "ice cream": {},
}

print("\n=== Verification ===")
names_lower = {a.event.item_name.lower(): a for a in actions}
for expected_name, meta in EXPECTED.items():
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
        issues.append(f"name='{e.item_name}'")
    if len(e.item_name) > len(expected_name) + 3:
        issues.append(f"junk_name='{e.item_name}'")
    note = (e.note or "").lower()
    if "date" in meta and f"date={meta['date']}".lower() not in note:
        issues.append(f"missing_date={meta['date']}")
    if "date" not in meta and "date=" in note:
        issues.append(f"WRONG_date_in_note='{e.note}'")
    if issues:
        print(f"  ISSUES [{expected_name}]: {'; '.join(issues)}")
    else:
        print(f"  OK: {expected_name}")

print("\n=== Junk ===")
expected_set = set(EXPECTED.keys())
for a in actions:
    name = a.event.item_name.lower()
    if not any(en in name or name in en for en in expected_set):
        print(f"  JUNK: [{a.event.item_name}] qty={a.event.quantity} note={a.event.note}")
