import logging
import os
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

_runtime_enabled: Optional[bool] = None


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _valid_model(model: Optional[str]) -> bool:
    if not model:
        return False
    lower = model.strip().lower()
    return lower.startswith("gpt-5") and "-mini" in lower


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


class LlmClient:
    DISABLED_REPLY = "LLM disabled; set LLM_ENABLED=1 and a gpt-5*-mini model to enable replies."
    INVALID_MODEL_REPLY = "Set OPENAI_MODEL to a valid gpt-5*-mini model (e.g., gpt-5.1-mini) to enable LLM replies."
    ERROR_REPLY = "LLM temporarily unavailable; please try again."

    def __init__(self) -> None:
        self.env_enabled = _is_truthy(os.getenv("LLM_ENABLED"))
        self.model = os.getenv("OPENAI_MODEL")
        self.timeout = float(os.getenv("OPENAI_TIMEOUT_S", "30"))

    def generate_reply(self, system_prompt: str, user_text: str) -> str:
        if not runtime_enabled(self.env_enabled):
            return self.DISABLED_REPLY
        if not _valid_model(self.model):
            return self.INVALID_MODEL_REPLY

        try:
            client = OpenAI(timeout=self.timeout)
            response = client.responses.create(
                model=self.model,
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


def get_llm_client() -> LlmClient:
    return LlmClient()
