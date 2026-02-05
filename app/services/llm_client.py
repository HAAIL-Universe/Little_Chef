import logging
import os
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

_runtime_enabled: Optional[bool] = None
_runtime_model: Optional[str] = None


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
        When disabled/invalid model, returns None deterministically.
        """
        env_enabled = _is_truthy(os.getenv("LLM_ENABLED"))
        env_model = os.getenv("OPENAI_MODEL")
        model = effective_model(env_model)
        if not runtime_enabled(env_enabled):
            return None
        if not _valid_model(model):
            return None
        try:
            client = OpenAI(timeout=self.timeout)
            if kind == "edit":
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
                                    "quantity": {"type": "number"},
                                    "unit": {"type": "string"},
                                    "expires_on": {"type": "string"},
                                    "notes": {"type": "string"},
                                    "name_raw": {"type": "string"},
                                    "quantity_raw": {"type": "string"},
                                    "unit_raw": {"type": "string"},
                                    "expires_raw": {"type": "string"},
                                    "notes_raw": {"type": "string"},
                                },
                                "required": ["op"],
                            },
                        }
                    },
                    "required": ["ops"],
                }
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
                                "required": ["name_raw"],
                            },
                        }
                    },
                    "required": ["items"],
                }

            resp = client.responses.create(
                model=model,
                input=[{"role": "user", "content": user_text}],
                response_format={"type": "json_schema", "json_schema": schema},
                max_output_tokens=400,
            )
            if hasattr(resp, "output"):
                return resp.output  # type: ignore[attr-defined]
            if hasattr(resp, "output_text"):
                return None
            return None
        except Exception as exc:  # pragma: no cover
            logger.warning("LLM call failed: %s", exc)
            return None


def get_llm_client() -> LlmClient:
    return LlmClient()
