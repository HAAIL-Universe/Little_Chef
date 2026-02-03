import os
from typing import Optional

from app.config.env import load_env

try:
    import psycopg
except ImportError:  # pragma: no cover - surfaced only when DATABASE_URL set without driver
    psycopg = None


def get_database_url() -> Optional[str]:
    load_env()
    return os.environ.get("DATABASE_URL")


def connect():
    url = get_database_url()
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    if psycopg is None:
        raise RuntimeError("psycopg is required for database operations")
    return psycopg.connect(url)
