"""Quick diagnostic: test the LLM prefs extraction path end-to-end."""
import os, sys, json

# Ensure app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env like run_local.ps1 would
from dotenv import load_dotenv
load_dotenv()

from app.services.llm_client import (
    LlmClient, _is_truthy, effective_model, _valid_model, runtime_enabled,
)

env_enabled = _is_truthy(os.getenv("LLM_ENABLED"))
env_model = os.getenv("OPENAI_MODEL")
model = effective_model(env_model)

print(f"LLM_ENABLED  = {os.getenv('LLM_ENABLED')!r} -> truthy={env_enabled}")
print(f"OPENAI_MODEL = {env_model!r} -> effective={model!r}, valid={_valid_model(model)}")
print(f"runtime_enabled = {runtime_enabled(env_enabled)}")
print(f"OPENAI_API_KEY set = {bool(os.getenv('OPENAI_API_KEY'))}")
print()

if not runtime_enabled(env_enabled) or not _valid_model(model):
    print("ABORT: LLM is disabled or model invalid — nothing to test.")
    sys.exit(1)

test_text = (
    "alright lets do my preferences, im cooking for two people, and i want two "
    "meals per day usually lunch and dinner, im allergic to peanuts and i also "
    "react badly to milk and dairy so avoid milk cheese butter cream and anything "
    "like that, i dont like mushrooms olives or tuna, im fine with chicken beef "
    "pork and fish as long as its not tuna, i like meals that are spicy, i love "
    "mexican and indian style food and im good with italian too, i prefer quick "
    "meals on weekdays like twenty to thirty minutes but weekends can be longer, "
    "if theres a choice id rather have high protein meals and not loads of sugar, "
    "notes im fine with garlic and onions and im not fussy about vegetables apart "
    "from mushrooms"
)

print("--- Calling generate_structured_reply(kind='prefs') ---")
client = LlmClient()

# Temporarily patch to see the exception
import app.services.llm_client as _llm_mod
_orig = client.generate_structured_reply

def _verbose_call(text, kind):
    import traceback
    # Copy the logic but show the error
    from openai import OpenAI
    import json as _json
    oc = OpenAI(timeout=30)
    input_msgs = [
        {"role": "system", "content": _llm_mod._PREFS_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    try:
        resp = oc.responses.create(
            model="gpt-5-mini",
            input=input_msgs,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "prefs_output",
                    "strict": True,
                    "schema": _llm_mod._PREFS_SCHEMA,
                }
            },
            max_output_tokens=2048,
            reasoning={"effort": "low"},
        )
        print(f"resp.status: {getattr(resp, 'status', 'N/A')}")
        print(f"resp.usage: {getattr(resp, 'usage', 'N/A')}")
        print(f"resp.incomplete_details: {getattr(resp, 'incomplete_details', 'N/A')}")
        raw = resp.output_text
        print(f"output_text: {raw[:500] if raw else raw}")
        if raw:
            return _json.loads(raw)
        return None
    except Exception as e:
        print(f"EXCEPTION: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None

try:
    result = _verbose_call(test_text, "prefs")
    print(f"Return type: {type(result)}")
    if result is None:
        print("RESULT: None (LLM path failed, would fall back to regex)")
    else:
        print(json.dumps(result, indent=2))
except Exception as e:
    print(f"EXCEPTION: {type(e).__name__}: {e}")
