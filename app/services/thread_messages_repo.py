from app.db.conn import connect


class ThreadMessagesRepo:
    """
    Append-only storage for per-thread messages.
    """

    def append_message(self, thread_id: str, user_id: str, role: str, content: str) -> str | None:
        if not thread_id:
            return None
        try:
            with connect() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(MAX(split_part(message_id, '-', 2)::int), 0) + 1
                    FROM thread_messages
                    WHERE thread_id = %s
                    """,
                    (thread_id,),
                )
                next_n = cur.fetchone()[0]
                message_id = f"{thread_id}-{next_n}"
                cur.execute(
                    """
                    INSERT INTO thread_messages (message_id, thread_id, user_id, role, content)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (message_id, thread_id, user_id, role, content),
                )
                conn.commit()
                return message_id
        except Exception:
            # Non-fatal: skip persistence if DB unavailable
            return None

