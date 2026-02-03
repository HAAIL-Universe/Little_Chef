import glob
import os
from pathlib import Path
from datetime import datetime

from app.db.conn import connect, get_database_url


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


def applied_versions(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def apply_migration(conn, version: str, sql_path: Path):
    sql = sql_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute("BEGIN")
        cur.execute(sql)
        cur.execute("INSERT INTO schema_migrations (version, applied_at) VALUES (%s, %s)", (version, datetime.utcnow()))
        cur.execute("COMMIT")


def run():
    if not get_database_url():
        print("[migrate] DATABASE_URL not set; skipping migrations.")
        return
    with connect() as conn:
        ensure_schema_table(conn)
        applied = applied_versions(conn)
        migrations = sorted(glob.glob(str(Path("db") / "migrations" / "*.sql")))
        for path in migrations:
            version = Path(path).stem
            if version in applied:
                print(f"[migrate] {version} already applied; skipping.")
                continue
            print(f"[migrate] applying {version} ...")
            apply_migration(conn, version, Path(path))
        print("[migrate] done.")


if __name__ == "__main__":
    run()
