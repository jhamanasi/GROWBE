-- Conversations table (supports Scenario A via customer_id and Scenario B via session_id)
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id    TEXT PRIMARY KEY,                      -- UUIDv4
    customer_id        VARCHAR(16),                           -- e.g., C0xx; nullable for Scenario B
    session_id         TEXT,                                  -- UUIDv4; nullable once customer_id exists
    title              TEXT,
    summary            TEXT,                                  -- Short AI-generated summary (optional)
    scenario_type      VARCHAR(16) NOT NULL,                  -- 'existing' | 'new'
    is_active          INTEGER DEFAULT 1,
    created_at         DATETIME DEFAULT (datetime('now')),
    updated_at         DATETIME DEFAULT (datetime('now')),
    metadata           TEXT DEFAULT '{}',                     -- JSON as TEXT
    message_count      INTEGER DEFAULT 0,
    last_message_at    DATETIME
);

CREATE INDEX IF NOT EXISTS idx_conversations_customer ON conversations(customer_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_activity ON conversations(is_active, updated_at);


