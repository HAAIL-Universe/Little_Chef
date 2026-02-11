def ensure_user(cur, user_id: str, provider_subject: str, email: str | None):
    cur.execute(
        """
        INSERT INTO users (user_id, provider_subject, email)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET email = EXCLUDED.email
        """,
        (user_id, provider_subject, email),
    )


def delete_user(cur, user_id: str) -> bool:
    """Delete a user and all cascade-linked data. Returns True if a row was deleted."""
    cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    return cur.rowcount > 0
