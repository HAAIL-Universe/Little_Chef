ALTER TABLE prefs
    ADD COLUMN IF NOT EXISTS applied_event_id TEXT NULL;

INSERT INTO schema_migrations (version) VALUES ('0004_prefs_event_id') ON CONFLICT DO NOTHING;
