from __future__ import annotations

def load_env() -> None:
    """
    Best-effort .env loader for local/dev. OS env wins.
    No output; safe if python-dotenv is absent.
    """
    try:
        import dotenv  # type: ignore
    except Exception:
        return
    try:
        dotenv.load_dotenv(override=False)
    except Exception:
        # If dotenv misbehaves, fail silently to keep runtime deterministic
        return
