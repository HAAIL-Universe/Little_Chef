CREATE TABLE IF NOT EXISTS recipe_books (
    book_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT '',
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'text/markdown',
    status TEXT NOT NULL DEFAULT 'ready',
    error_message TEXT NULL,
    text_content TEXT NULL,
    source TEXT NOT NULL DEFAULT 'upload',
    pack_id TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_recipe_books_user ON recipe_books (user_id);
CREATE INDEX IF NOT EXISTS idx_recipe_books_pack ON recipe_books (user_id, pack_id);

INSERT INTO schema_migrations (version) VALUES ('0005_recipe_books') ON CONFLICT DO NOTHING;
