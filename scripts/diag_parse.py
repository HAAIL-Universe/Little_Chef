"""Diagnostic: reproduce STT parsing to find missing items."""
from app.services.inventory_agent import InventoryAgent
from app.services.proposal_store import ProposalStore


class DummyInv:
    def create_event(self, *a, **kw):
        pass


agent = InventoryAgent(DummyInv(), ProposalStore())

stt = (
    "Alright Little Chef quick pantry scan: Pasta two 500 gram packs both unopened. "
    "Rice one kilo bag about half left. Tinned chopped tomatoes six tins best before 10 October. "
    "Tuna four tins best before 3 March. Baked beans five tins best before 20 January. "
    "Chickpeas three tins best before 12 May. Peas 900 gram bag half left. "
    "Mince beef 500 grams use by 10 February. Spinach one bag half left use by 8 February."
)

# Debug: trace quantity matches and _looks_like_date_quantity
from app.services.inventory_agent import (
    QUANTITY_PATTERN, SECTION_TRANSITION_PATTERN,
)
import re

text = agent._replace_number_words(stt.strip())
text = SECTION_TRANSITION_PATTERN.sub(". ", text)
lower = text.lower()
matches = list(QUANTITY_PATTERN.finditer(lower))
print(f"Total quantity matches: {len(matches)}")
for i, m in enumerate(matches):
    is_date = agent._looks_like_date_quantity(lower, m)
    ctx_start = max(0, m.start() - 35)
    ctx_end = min(len(lower), m.end() + 20)
    context = lower[ctx_start:ctx_end]
    print(f"  [{i}] match='{m.group()}' pos={m.start()}-{m.end()} date_qty={is_date} ctx='...{context}...'")
print()

actions, warnings = agent._parse_inventory_actions(stt)
print(f"Total actions: {len(actions)}")
print(f"Warnings: {warnings}")
for a in actions:
    e = a.event
    print(f"  [{e.item_name}] qty={e.quantity} unit={e.unit} note={e.note}")

expected = ["pasta", "rice", "tomato", "tuna", "baked beans", "chickpeas", "peas 900", "mince", "spinach"]
names_lower = {a.event.item_name.lower() for a in actions}
print()
print(f"All names: {names_lower}")
for exp in expected:
    found = any(exp in n for n in names_lower)
    status = "FOUND" if found else "MISSING"
    print(f"  {exp}: {status}")

# Also show what "alright little chef" and "both" look like
print()
print("Junk check:")
for a in actions:
    n = a.event.item_name.lower()
    if "little chef" in n or n == "both" or "quick" in n or "scan" in n or "alright" in n:
        print(f"  JUNK: [{a.event.item_name}]")
