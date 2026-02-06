-- Thread messages (append-only)
CREATE TABLE IF NOT EXISTS thread_messages (
    message_id TEXT PRIMARY KEY,
    thread_id UUID NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS thread_messages_thread_id_idx ON thread_messages (thread_id, created_at);
