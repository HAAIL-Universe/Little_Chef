-- Threads MVP: store thread ids per user
CREATE TABLE IF NOT EXISTS threads (
    thread_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS threads_user_id_idx ON threads (user_id);
