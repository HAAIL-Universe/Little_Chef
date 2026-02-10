"""
LLM-backed preference extraction from natural-language / STT paragraphs.

Mirrors the pattern used in inventory_parse_service.py:
  - When the LLM is enabled and returns a valid response, use it.
  - Otherwise return None so the caller can fall back to regex parsing.
"""

import logging
from typing import Optional

from app.schemas import UserPrefs
from app.services.llm_client import LlmClient

logger = logging.getLogger(__name__)


def extract_prefs_llm(text: str, llm: Optional[LlmClient]) -> Optional[UserPrefs]:
    """
    Ask the LLM to extract structured UserPrefs from free-text input.

    Returns a UserPrefs object on success, or None when the LLM is
    disabled / unavailable / returns an unparseable response.  The caller
    should fall back to regex-based parsing when None is returned.
    """
    if llm is None:
        return None

    reply = llm.generate_structured_reply(text, kind="prefs")
    if not reply or not isinstance(reply, dict):
        return None

    try:
        return _dict_to_user_prefs(reply)
    except Exception:
        logger.warning("Failed to convert LLM prefs reply to UserPrefs: %s", reply, exc_info=True)
        return None


def _dict_to_user_prefs(d: dict) -> UserPrefs:
    """
    Safely convert the LLM's JSON dict into a UserPrefs, applying
    type coercion and sensible defaults for missing / null fields.
    """

    def _str_list(val) -> list[str]:
        if not val or not isinstance(val, list):
            return []
        return [str(item).strip() for item in val if item and str(item).strip()]

    def _int_or(val, default: int) -> int:
        if val is None:
            return default
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    def _optional_int(val) -> Optional[int]:
        if val is None:
            return None
        try:
            v = int(val)
            return v if v > 0 else None
        except (TypeError, ValueError):
            return None

    return UserPrefs(
        allergies=_str_list(d.get("allergies")),
        dislikes=_str_list(d.get("dislikes")),
        cuisine_likes=_str_list(d.get("cuisine_likes")),
        servings=_int_or(d.get("servings"), 0),
        meals_per_day=_int_or(d.get("meals_per_day"), 0),
        plan_days=_int_or(d.get("plan_days"), 0),
        cook_time_weekday_mins=_optional_int(d.get("cook_time_weekday_mins")),
        cook_time_weekend_mins=_optional_int(d.get("cook_time_weekend_mins")),
        diet_goals=_str_list(d.get("diet_goals")),
        notes=str(d.get("notes") or ""),
    )
