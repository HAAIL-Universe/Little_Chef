def ensure_user(cur, user_id: str, provider_subject: str, email: str | None):
    cur.execute(
        """
        INSERT INTO users (user_id, provider_subject, email)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET email = EXCLUDED.email
        """,
        (user_id, provider_subject, email),
    )
