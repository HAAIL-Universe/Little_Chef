CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    provider_subject TEXT NOT NULL UNIQUE,
    email TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS prefs (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    prefs JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS inventory_events (
    event_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    occurred_at TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_inventory_events_user_time ON inventory_events (user_id, occurred_at DESC);

INSERT INTO schema_migrations (version) VALUES ('0001_init') ON CONFLICT DO NOTHING;
