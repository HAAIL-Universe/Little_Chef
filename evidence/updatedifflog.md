# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-11T17:27:09+00:00
- Branch: claude/romantic-jones
- HEAD: f895242b359e48581f4abb54afd40a44b2178cf3
- BASE_HEAD: 00391a0c84ce69f1052f19a456aaef7b462cc011
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Added `_env_get()` helper in `app/services/llm_client.py`: case-insensitive env var lookup + surrounding-quote stripping for Render (Linux) compatibility.
- Replaced all `os.getenv` calls for `LLM_ENABLED`, `OPENAI_MODEL`, and `OPENAI_API_KEY` in `LlmClient` with `_env_get`.
- Added startup LLM config diagnostic log line in `app/main.py` (prints enabled flag, model name, key presence — never prints secrets).
- Root cause: Linux env var names are case-sensitive. If user typed `llm_enabled` or `Openai_Model` in Render dashboard, `os.getenv("LLM_ENABLED")` returns `None`, triggering the "LLM disabled" gate. Quote-wrapped values (`"1"`) also fail the truthy check.

## Files Changed (staged)
- app/main.py
- app/services/llm_client.py

## git status -sb
    ## claude/romantic-jones
     M .claude/settings.local.json
    M  app/main.py
    M  app/services/llm_client.py
     M evidence/test_runs_latest.md
     M evidence/updatedifflog.md

## Minimal Diff Hunks
    diff --git a/app/main.py b/app/main.py
    index 31d0f5c..0838209 100644
    --- a/app/main.py
    +++ b/app/main.py
    @@ -47,6 +47,18 @@ async def lifespan(app: FastAPI):
     
     def create_app() -> FastAPI:
         load_env()
    +
    +    # --- Startup LLM config diagnostic (never prints secrets) ---
    +    from app.services.llm_client import _env_get, _is_truthy, _valid_model
    +    _llm_flag = _env_get("LLM_ENABLED")
    +    _llm_model = _env_get("OPENAI_MODEL")
    +    _llm_key_set = bool(_env_get("OPENAI_API_KEY"))
    +    logger.info(
    +        "LLM config: enabled=%s (raw=%r), model=%r (valid=%s), api_key_set=%s",
    +        _is_truthy(_llm_flag), _llm_flag, _llm_model,
    +        _valid_model(_llm_model), _llm_key_set,
    +    )
    +
         app = FastAPI(title="Little Chef", version="0.1.0", lifespan=lifespan)
         app.include_router(health.router)
         app.include_router(auth.router)
    diff --git a/app/services/llm_client.py b/app/services/llm_client.py
    index 4d7767a..44f6b7c 100644
    --- a/app/services/llm_client.py
    +++ b/app/services/llm_client.py
    @@ -10,6 +10,27 @@ logger = logging.getLogger(__name__)
     _runtime_enabled: Optional[bool] = None
     _runtime_model: Optional[str] = None
     
    +
    +def _env_get(key: str, default: Optional[str] = None) -> Optional[str]:
    +    """Case-insensitive env var lookup with quote stripping.
    +
    +    On Linux (Render), env var names are case-sensitive. If the user set
    +    ``LLM_enabled`` instead of ``LLM_ENABLED`` in the Render dashboard,
    +    ``_env_get("LLM_ENABLED")`` returns None.  This helper falls back
    +    to a case-insensitive scan of ``os.environ`` and also strips
    +    surrounding quotes from the value (common copy-paste artefact).
    +    """
    +    # Fast path: exact match
    +    val = os.getenv(key)
    +    if val is not None:
    +        return val.strip().strip("\"'")
    +    # Slow path: case-insensitive scan
    +    key_lower = key.lower()
    +    for k, v in os.environ.items():
    +        if k.lower() == key_lower:
    +            return v.strip().strip("\"'")
    +    return default
    +
     _PREFS_SYSTEM_PROMPT = (
         "You are a preference extractor for a meal planning app. "
         "Extract the user's food preferences from their message. "
    @@ -140,7 +161,7 @@ def runtime_enabled(default_env_enabled: bool) -> bool:
     
     
     def current_model() -> Optional[str]:
    -    return os.getenv("OPENAI_MODEL")
    +    return _env_get("OPENAI_MODEL")
     
     
     def set_runtime_model(model: Optional[str]) -> None:
    @@ -167,8 +188,8 @@ class LlmClient:
             self.structured_timeout = float(os.getenv("OPENAI_STRUCTURED_TIMEOUT_S", "120"))
     
         def generate_reply(self, system_prompt: str, user_text: str) -> str:
    -        env_enabled = _is_truthy(os.getenv("LLM_ENABLED"))
    -        env_model = os.getenv("OPENAI_MODEL")
    +        env_enabled = _is_truthy(_env_get("LLM_ENABLED"))
    +        env_model = _env_get("OPENAI_MODEL")
             model = effective_model(env_model)
     
             if not runtime_enabled(env_enabled):
    @@ -177,7 +198,7 @@ class LlmClient:
                 return self.INVALID_MODEL_REPLY
     
             try:
    -            client = OpenAI(timeout=self.timeout)
    +            client = OpenAI(api_key=_env_get("OPENAI_API_KEY"), timeout=self.timeout)
                 response = client.responses.create(
                     model=model,
                     input=[
    @@ -206,15 +227,15 @@ class LlmClient:
             When disabled/invalid model, returns None (signals LLM unavailable).
             When API call fails, returns empty dict {} (signals tried-and-failed).
             """
    -        env_enabled = _is_truthy(os.getenv("LLM_ENABLED"))
    -        env_model = os.getenv("OPENAI_MODEL")
    +        env_enabled = _is_truthy(_env_get("LLM_ENABLED"))
    +        env_model = _env_get("OPENAI_MODEL")
             model = effective_model(env_model)
             if not runtime_enabled(env_enabled):
                 return None
             if not _valid_model(model):
                 return None
             try:
    -            client = OpenAI(timeout=self.structured_timeout)
    +            client = OpenAI(api_key=_env_get("OPENAI_API_KEY"), timeout=self.structured_timeout)
                 if kind == "prefs":
                     schema = _PREFS_SCHEMA
                     schema_name = "prefs_output"

## Verification
- Static: `python -m compileall app` — pass (no errors)
- Runtime: pytest 183 passed, 1 warning in 113.48s
- Runtime: node ui_onboarding_hints_test.mjs: 17/17 PASS
- Behavioral: case-insensitive lookup resolves `llm_enabled` → `LLM_ENABLED` ✅
- Behavioral: quote-stripping resolves `"1"` → `1` ✅
- Behavioral: missing env vars still correctly block LLM gate ✅
- Contract: physics.yaml unchanged, minimal diff (2 files), no refactors, file boundaries preserved

## Notes (optional)
- The `_env_get` slow path iterates `os.environ` which is O(n) on every LLM call. For the 3 env vars checked per request this is negligible but could be cached if needed later.
- Startup log line is easy to remove once Render issue is confirmed resolved.
- The `OPENAI_TIMEOUT_S` and `OPENAI_STRUCTURED_TIMEOUT_S` env reads left as `os.getenv` (they have safe defaults and are not user-facing gates).

## Next Steps
- Deploy to Render and verify startup log shows `enabled=True, model='gpt-5-mini', api_key_set=True`.
- Check Render dashboard env var casing — correct to `LLM_ENABLED`, `OPENAI_MODEL`, `OPENAI_API_KEY` if mismatched.
- Remove startup diagnostic log once Render issue confirmed resolved.

