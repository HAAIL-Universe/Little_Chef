import json
import logging
import os
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

_runtime_enabled: Optional[bool] = None
_runtime_model: Optional[str] = None

_PREFS_SYSTEM_PROMPT = (
    "You are a preference extractor for a meal planning app. "
    "Extract the user's food preferences from their message. "
    "Classify EACH item into the correct category — do NOT let items bleed across categories.\n"
    "Rules:\n"
    "- allergies: genuine allergies or intolerances. "
    "When the user mentions an allergen GROUP (e.g. 'dairy', 'nuts', 'shellfish'), "
    "list BOTH the group name AND every specific item they mention. "
    "Example: 'allergic to dairy, avoid milk cheese butter cream' → "
    "[\"dairy\", \"milk\", \"cheese\", \"butter\", \"cream\"]. "
    "Common allergen groups: dairy, nuts/tree nuts, peanuts, gluten/wheat, "
    "shellfish, soy, eggs, fish, sesame.\n"
    "- dislikes: foods the user explicitly says they dislike or don't want "
    "(but NOT allergens — if they avoid something due to allergy/intolerance, put it in allergies)\n"
    "- cuisine_likes: cuisines, flavour profiles, or broad food styles the user likes. "
    "Do NOT include specific proteins here — put food preferences like 'chicken' in notes instead\n"
    "- servings: integer, how many people to cook for\n"
    "- meals_per_day: integer, how many meals per day\n"
    "- plan_days: integer, how many days to plan for (0 if not mentioned)\n"
    "- cook_time_weekday_mins: max cooking time on weekdays in minutes (null if not mentioned). "
    "Convert words to numbers: 'twenty' = 20, 'thirty' = 30, etc.\n"
    "- cook_time_weekend_mins: max cooking time on weekends in minutes (null if not mentioned)\n"
    "- diet_goals: dietary goals like 'high protein', 'low sugar', 'low carb'\n"
    "- notes: any other relevant info that doesn't fit above. "
    "Include protein preferences (e.g. 'fine with chicken, beef, pork'), "
    "general comments about vegetables, and other context.\n"
    "Return valid JSON matching the schema. Use empty lists [] for categories with no items. "
    "Never put likes in dislikes or vice versa. "
    "If the user says 'im fine with X', that is NOT an allergy or dislike."
)

_DRAFT_SYSTEM_PROMPT = (
    "You are an inventory extraction assistant for a meal-planning app. "
    "The user will describe the contents of their kitchen in free-form speech-to-text. "
    "Extract EVERY distinct food item into the JSON array.\n"
    "Rules:\n"
    "- name_raw: The FULL common name of the item. Use a clean, natural name like "
    "'chopped tomatoes', 'chicken breast', 'olive oil', 'frozen peas', 'peanut butter', "
    "'baked beans', 'minced beef', 'mixed herbs', 'chilli powder', 'curry powder'. "
    "Do NOT include container words like 'tin', 'bag', 'jar', 'bottle', 'box', 'pack' in the name "
    "— those belong in unit_raw. Do NOT include 'frozen' unless it is part of the common product name "
    "(e.g. 'frozen peas' yes, 'frozen chicken breast' → just 'chicken breast' with notes='frozen').\n"
    "- quantity_raw: A string number representing the quantity THE USER ACTUALLY HAS. "
    "Interpret partial amounts: 'half left of a 1 kilo bag' → quantity_raw='500', unit_raw='g'. "
    "'about a quarter left of 500ml' → quantity_raw='125', unit_raw='ml'. "
    "'about a third left of 1 kilo' → quantity_raw='333', unit_raw='g'. "
    "If user says '2 bags of 500g', total = 1000g → quantity_raw='1000', unit_raw='g'. "
    "Convert: kg→g (multiply by 1000), litres→ml (multiply by 1000). "
    "Word numbers: 'two'=2, 'six'=6, 'a dozen'=12, 'eight'=8.\n"
    "- unit_raw: The storage/measurement unit. Use EXACTLY one of: "
    "'g', 'ml', 'tin', 'bag', 'box', 'jar', 'bottle', 'pack', 'loaf', 'slice', 'piece', 'count'. "
    "For countable items with no clear unit (eggs, onions, peppers), use 'count'. "
    "IMPORTANT: Only use quantity_raw=null and unit_raw=null for loose spices/condiments "
    "where the user gives NO container and only a vague level ('mostly full', 'nearly empty'). "
    "If the user mentions a container ('one box', 'one jar', 'a bag', 'one bottle'), "
    "ALWAYS set quantity_raw to the container count and unit_raw to the container type, "
    "even when the contents are partially used. Put the partial amount in notes_raw instead. "
    "Examples: 'one box about half full' → quantity_raw='1', unit_raw='box', notes_raw='about half full'. "
    "'one jar about half left' → quantity_raw='1', unit_raw='jar', notes_raw='about half left'. "
    "'a bag about half' → quantity_raw='1', unit_raw='bag', notes_raw='about half'.\n"
    "- expires_raw: If the user mentions a use-by / best-before date, write it as YYYY-MM-DD "
    "(ISO format). Today is {today}. 'tomorrow' = next day, 'thursday' = the coming Thursday, "
    "'friday' = the coming Friday, etc. If no expiry mentioned, use null.\n"
    "- notes_raw: Additional context: 'for someone else not for me', 'about half full', "
    "'frozen', 'unopened', location hints ('in the freezer', 'in the fridge'). "
    "If the user says an item is NOT for them or belongs to someone else, note that here. "
    "If the user mentions an allergy related to an item, note it. null if nothing extra.\n"
    "- Disambiguation: When the same word could mean different items, use distinct names. "
    "For example, if the user mentions 'pepper' (spice) AND 'peppers' (vegetable), "
    "use 'pepper' for the spice and 'bell peppers' for the vegetable. "
    "Similarly: 'ginger' (spice) vs 'stem ginger' (preserved), etc.\n"
    "Return valid JSON with an 'items' array. Every food item mentioned gets its own entry. "
    "Spices can be grouped individually (salt, pepper, paprika = 3 separate items). "
    "Do NOT merge different items into one entry."
)

_PREFS_SCHEMA = {
    "type": "object",
    "properties": {
        "allergies": {"type": "array", "items": {"type": "string"}},
        "dislikes": {"type": "array", "items": {"type": "string"}},
        "cuisine_likes": {"type": "array", "items": {"type": "string"}},
        "servings": {"type": "integer"},
        "meals_per_day": {"type": "integer"},
        "plan_days": {"type": "integer"},
        "cook_time_weekday_mins": {"type": ["integer", "null"]},
        "cook_time_weekend_mins": {"type": ["integer", "null"]},
        "diet_goals": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
    "required": [
        "allergies", "dislikes", "cuisine_likes",
        "servings", "meals_per_day", "plan_days",
        "cook_time_weekday_mins", "cook_time_weekend_mins",
        "diet_goals", "notes",
    ],
    "additionalProperties": False,
}


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _valid_model(model: Optional[str]) -> bool:
    if not model:
        return False
    lower = model.strip().lower()
    return lower.startswith("gpt-5") and ("-mini" in lower or "-nano" in lower)


def set_runtime_enabled(enabled: bool) -> None:
    global _runtime_enabled
    _runtime_enabled = enabled


def reset_runtime_enabled() -> None:
    global _runtime_enabled
    _runtime_enabled = None


def runtime_enabled(default_env_enabled: bool) -> bool:
    if _runtime_enabled is None:
        return default_env_enabled
    return _runtime_enabled


def current_model() -> Optional[str]:
    return os.getenv("OPENAI_MODEL")


def set_runtime_model(model: Optional[str]) -> None:
    global _runtime_model
    _runtime_model = model.strip() if model else None


def reset_runtime_model() -> None:
    global _runtime_model
    _runtime_model = None


def effective_model(env_model: Optional[str]) -> Optional[str]:
    return _runtime_model if _runtime_model else env_model


class LlmClient:
    DISABLED_REPLY = "LLM disabled; set LLM_ENABLED=1 and a gpt-5*-mini or gpt-5*-nano model to enable replies."
    INVALID_MODEL_REPLY = "Set OPENAI_MODEL to a valid gpt-5*-mini or gpt-5*-nano model (e.g., gpt-5.1-mini or gpt-5-nano) to enable LLM replies."
    ERROR_REPLY = "LLM temporarily unavailable; please try again."

    def __init__(self) -> None:
        self.timeout = float(os.getenv("OPENAI_TIMEOUT_S", "30"))
        self.structured_timeout = float(os.getenv("OPENAI_STRUCTURED_TIMEOUT_S", "120"))

    def generate_reply(self, system_prompt: str, user_text: str) -> str:
        env_enabled = _is_truthy(os.getenv("LLM_ENABLED"))
        env_model = os.getenv("OPENAI_MODEL")
        model = effective_model(env_model)

        if not runtime_enabled(env_enabled):
            return self.DISABLED_REPLY
        if not _valid_model(model):
            return self.INVALID_MODEL_REPLY

        try:
            client = OpenAI(timeout=self.timeout)
            response = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                max_output_tokens=256,
            )
            # Prefer output_text; fall back to the first text content chunk.
            if hasattr(response, "output_text"):
                return response.output_text  # type: ignore[attr-defined]
            output = getattr(response, "output", None)
            if output and isinstance(output, list):
                first = output[0]
                content = getattr(first, "content", None)
                if content and isinstance(content, list) and content[0].get("text"):
                    return content[0]["text"]
            return self.ERROR_REPLY
        except Exception as exc:  # pragma: no cover - error path asserted via message text
            logger.warning("LLM call failed: %s", exc)
            return self.ERROR_REPLY

    def generate_structured_reply(self, user_text: str, kind: str) -> Optional[dict]:
        """
        Very small helper to support inventory parsing/edit ops.
        When disabled/invalid model, returns None (signals LLM unavailable).
        When API call fails, returns empty dict {} (signals tried-and-failed).
        """
        env_enabled = _is_truthy(os.getenv("LLM_ENABLED"))
        env_model = os.getenv("OPENAI_MODEL")
        model = effective_model(env_model)
        if not runtime_enabled(env_enabled):
            return None
        if not _valid_model(model):
            return None
        try:
            client = OpenAI(timeout=self.structured_timeout)
            if kind == "prefs":
                schema = _PREFS_SCHEMA
                schema_name = "prefs_output"
                system_msg = _PREFS_SYSTEM_PROMPT
                max_tokens = 2048
            elif kind == "edit":
                schema = {
                    "type": "object",
                    "properties": {
                        "ops": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "op": {"type": "string"},
                                    "target": {"type": "string"},
                                    "quantity": {"type": ["number", "null"]},
                                    "unit": {"type": ["string", "null"]},
                                    "expires_on": {"type": ["string", "null"]},
                                    "notes": {"type": ["string", "null"]},
                                    "name_raw": {"type": ["string", "null"]},
                                    "quantity_raw": {"type": ["string", "null"]},
                                    "unit_raw": {"type": ["string", "null"]},
                                    "expires_raw": {"type": ["string", "null"]},
                                    "notes_raw": {"type": ["string", "null"]},
                                },
                                "required": [
                                    "op", "target", "quantity", "unit",
                                    "expires_on", "notes", "name_raw",
                                    "quantity_raw", "unit_raw",
                                    "expires_raw", "notes_raw",
                                ],
                                "additionalProperties": False,
                            },
                        }
                    },
                    "required": ["ops"],
                    "additionalProperties": False,
                }
                schema_name = "edit_output"
                system_msg = None
                max_tokens = 2048
            else:
                schema = {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name_raw": {"type": "string"},
                                    "quantity_raw": {"type": ["string", "null"]},
                                    "unit_raw": {"type": ["string", "null"]},
                                    "expires_raw": {"type": ["string", "null"]},
                                    "notes_raw": {"type": ["string", "null"]},
                                },
                                "required": [
                                    "name_raw", "quantity_raw", "unit_raw",
                                    "expires_raw", "notes_raw",
                                ],
                                "additionalProperties": False,
                            },
                        }
                    },
                    "required": ["items"],
                    "additionalProperties": False,
                }
                schema_name = "draft_output"
                from datetime import date as _date
                system_msg = _DRAFT_SYSTEM_PROMPT.format(today=_date.today().isoformat())
                max_tokens = 8192

            input_msgs = []
            if system_msg:
                input_msgs.append({"role": "system", "content": system_msg})
            input_msgs.append({"role": "user", "content": user_text})

            last_exc = None
            for attempt in range(2):  # 1 initial + 1 retry
                try:
                    resp = client.responses.create(
                        model=model,
                        input=input_msgs,
                        text={
                            "format": {
                                "type": "json_schema",
                                "name": schema_name,
                                "strict": True,
                                "schema": schema,
                            }
                        },
                        max_output_tokens=max_tokens,
                        reasoning={"effort": "low"},
                    )
                    raw = resp.output_text
                    if raw:
                        return json.loads(raw)
                    logger.warning("LLM returned empty output (attempt %d)", attempt + 1)
                except Exception as exc:
                    last_exc = exc
                    logger.warning("LLM call failed (attempt %d): %s", attempt + 1, exc)
                if attempt == 0:
                    import time
                    time.sleep(1)
            return {}  # LLM was available but all attempts failed
        except Exception as exc:  # pragma: no cover
            logger.warning("LLM call setup failed: %s", exc)
            return {}  # LLM was available but setup failed


def get_llm_client() -> LlmClient:
    return LlmClient()
