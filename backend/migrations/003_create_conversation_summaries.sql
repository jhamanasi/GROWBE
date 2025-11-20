-- Optional summaries per conversation (LLM-generated)
CREATE TABLE IF NOT EXISTS conversation_summaries (
    conversation_id    TEXT PRIMARY KEY,                      -- one summary per conversation
    short_title        TEXT,                                  -- ≤ 60 chars
    summary_text       TEXT,                                  -- paragraph summary
    updated_at         DATETIME DEFAULT (datetime('now')),
    metadata           TEXT DEFAULT '{}'                      -- JSON as TEXT
);

CREATE INDEX IF NOT EXISTS idx_conv_summaries_updated ON conversation_summaries(updated_at);


