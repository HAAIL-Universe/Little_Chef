from typing import Any, Dict, List, Optional

from app.services.llm_client import LlmClient


DraftItemRaw = Dict[str, Optional[str]]
EditOps = Dict[str, Any]


def extract_new_draft(text: str, llm: Optional[LlmClient]) -> Optional[List[DraftItemRaw]]:
    """
    LLM-backed extractor for NEW drafts.
    Returns None when LLM is unavailable (disabled / no client),
    returns [] when LLM was called but produced no items.
    """
    if llm is None:
        return None
    reply = llm.generate_structured_reply(text, kind="draft")
    if reply is None:
        # LLM is disabled or model invalid — signal unavailable
        return None
    if not reply:
        # Empty dict = LLM was available but API call failed — treat as unavailable
        # so the caller can fall back to the regex parser
        return None
    if "items" not in reply:
        return []
    items = reply.get("items") or []
    out: List[DraftItemRaw] = []
    for it in items:
        out.append(
            {
                "name_raw": it.get("name_raw"),
                "quantity_raw": it.get("quantity_raw"),
                "unit_raw": it.get("unit_raw"),
                "expires_raw": it.get("expires_raw"),
                "notes_raw": it.get("notes_raw"),
            }
        )
    return out


def extract_edit_ops(text: str, llm: Optional[LlmClient]) -> EditOps:
    """
    Placeholder LLM-backed extractor for EDIT ops.
    Returns {"ops": []} deterministically when LLM is disabled/invalid.
    """
    if llm is None:
        return {"ops": []}
    reply = llm.generate_structured_reply(text, kind="edit")
    if not reply or "ops" not in reply:
        return {"ops": []}
    return {"ops": reply.get("ops") or []}
