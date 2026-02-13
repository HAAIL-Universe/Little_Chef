CREATE TABLE IF NOT EXISTS meal_plans (
    plan_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    thread_id TEXT NOT NULL,
    proposal_id TEXT NOT NULL,
    plan JSONB NOT NULL,
    plan_created_at TIMESTAMPTZ NOT NULL,
    confirmed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_meal_plans_user_confirmed
    ON meal_plans (user_id, confirmed_at DESC);

INSERT INTO schema_migrations (version) VALUES ('0006_meal_plans') ON CONFLICT DO NOTHING;
