"""
Diagnostic: test the LLM inventory draft extraction end-to-end.
Run with:  .\.venv\Scripts\python.exe scripts/diag_llm_inventory.py
Requires .env with LLM_ENABLED=1, OPENAI_API_KEY, OPENAI_MODEL=gpt-5-mini
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from app.services.llm_client import LlmClient, _is_truthy, effective_model, _valid_model, runtime_enabled
from app.services.inventory_normalizer import normalize_items

STT_INPUT = (
    "okay im doing an inventory scan, in the cupboards ive got pasta two unopened "
    "five hundred gram bags, rice one one kilo bag but its about half left, tinned "
    "chopped tomatoes six tins, chickpeas three tins, baked beans five tins, flour "
    "one one kilo bag but only about a third left, olive oil a five hundred ml bottle "
    "with about a quarter left, cereal cornflakes one box about half full, peanut "
    "butter one jar about half left but thats for someone else not for me because im "
    "allergic, ive also got salt pepper chilli powder paprika curry powder and mixed "
    "herbs and theyre mostly full, in the fridge ive got eggs about eight left, "
    "chicken breast a pack of two pieces use by thursday, minced beef five hundred "
    "grams use by tomorrow, one small yogurt use by friday, milk about one litre but "
    "only a bit left maybe a quarter, veg ive got one cucumber two peppers a bag of "
    "spinach about half full and two onions, theres also cheddar cheese about two "
    "hundred grams but dairy isnt for me, in the freezer ive got frozen peas about "
    "nine hundred grams total in a big bag, frozen chips one bag about half, bread "
    "one loaf sliced about six slices left, and two frozen pizzas, thats everything "
    "i can see right now"
)

# --- Check environment ---
env_enabled = _is_truthy(os.getenv("LLM_ENABLED"))
env_model = os.getenv("OPENAI_MODEL")
model = effective_model(env_model)
print(f"LLM_ENABLED  = {os.getenv('LLM_ENABLED')!r} -> truthy={env_enabled}")
print(f"OPENAI_MODEL = {env_model!r} -> effective={model!r}, valid={_valid_model(model)}")
print(f"runtime_enabled = {runtime_enabled(env_enabled)}")
print(f"OPENAI_API_KEY set = {bool(os.getenv('OPENAI_API_KEY'))}")
print()

# --- Call LLM ---
llm = LlmClient()
print("--- Calling generate_structured_reply(kind='draft') ---")
result = llm.generate_structured_reply(STT_INPUT, kind="draft")
print(f"Return type: {type(result)}")
if result is None:
    print("RESULT: None (LLM path failed)")
    sys.exit(1)

items = result.get("items", [])
print(f"\n=== RAW LLM OUTPUT ({len(items)} items) ===")
print(json.dumps(items, indent=2))

# --- Normalize ---
print(f"\n=== NORMALIZED OUTPUT ===")
normalized = normalize_items(items, "pantry")
for idx, n in enumerate(normalized, 1):
    it = n["item"]
    w = n.get("warnings", [])
    q = it.get("quantity")
    u = it.get("unit") or ""
    if q is not None:
        q_str = f"{q:g}" if q == int(q) else f"{q}"
        qty = f"{q_str}{u}" if u in ("g", "ml") else f"{q_str} {u}".strip()
    else:
        qty = "(no qty)"
    expiry = it.get("expires_on") or ""
    notes = it.get("notes") or ""
    name = it.get("display_name", "")
    warn_txt = " ".join(f"[{w_}]" for w_ in w) if w else ""
    print(f"  {idx:2d}. {name:<25s} {qty:<15s} {expiry:<12s} {notes[:40]:<42s} {warn_txt}")

print(f"\n=== DONE ===")
