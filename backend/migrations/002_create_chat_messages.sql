-- Chat messages for each conversation
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id         TEXT PRIMARY KEY,                      -- UUIDv4
    conversation_id    TEXT NOT NULL,                         -- FK to conversations
    role               TEXT NOT NULL,                         -- 'user' | 'assistant' | 'tool'
    content            TEXT,                                  -- message text
    tool_name          TEXT,                                  -- nullable
    tool_payload       TEXT,                                  -- JSON as TEXT (full tool result)
    sql_details        TEXT,                                  -- JSON as TEXT (if applicable)
    calculation_details TEXT,                                 -- JSON as TEXT (if applicable)
    error              TEXT,                                  -- nullable
    is_active          INTEGER DEFAULT 1,                     -- soft delete
    created_at         DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON chat_messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_role ON chat_messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_active ON chat_messages(is_active);


