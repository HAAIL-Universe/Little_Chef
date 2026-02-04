import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple

from app.db.conn import connect, get_database_url


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def migrations_dir(root: Path) -> Path:
    return root / "db" / "migrations"


def discover_migration_files(migrations_path: Path) -> List[Path]:
    files = sorted(p for p in migrations_path.glob("*.sql"))
    return files


def parse_version(path: Path) -> str:
    stem = path.stem
    if "_" in stem:
        return stem.split("_", 1)[0]
    return stem


def ensure_schema_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    conn.commit()


def applied_versions(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def split_statements(sql_text: str) -> Iterable[str]:
    for stmt in sql_text.split(";"):
        cleaned = stmt.strip()
        if cleaned:
            yield cleaned


def apply_migration(conn, version: str, sql_path: Path):
    sql = sql_path.read_text(encoding="utf-8")
    statements = list(split_statements(sql))
    if not statements:
        return
    with conn.cursor() as cur:
        cur.execute("BEGIN")
        try:
            for stmt in statements:
                cur.execute(stmt)
            cur.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (%s, %s)",
                (version, datetime.now(tz=timezone.utc)),
            )
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise


def list_migrations_with_versions(paths: List[Path]) -> List[Tuple[str, Path]]:
    return [(parse_version(p), p) for p in paths]


def run():
    root = repo_root()
    mig_dir = migrations_dir(root)
    files = discover_migration_files(mig_dir)
    if not files:
        print(f"[migrate] No migrations found in {mig_dir}")
        return

    if not get_database_url():
        print("[migrate] DATABASE_URL not set; skipping migrations.")
        return

    print(f"[migrate] migrations dir: {mig_dir}")
    print("[migrate] discovered:", ", ".join(p.name for p in files))

    with connect() as conn:
        ensure_schema_table(conn)
        applied = applied_versions(conn)
        print("[migrate] applied versions:", ", ".join(sorted(applied)) or "(none)")

        for version, path in list_migrations_with_versions(files):
            if version in applied:
                print(f"[migrate] {version} already applied; skipping.")
                continue
            print(f"[migrate] applying {version} from {path.name} ...")
            apply_migration(conn, version, path)
            print(f"[migrate] applied {version} OK")
        print("[migrate] done.")


if __name__ == "__main__":
    run()
