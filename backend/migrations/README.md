# Database Migrations System

## Overview

The migrations system manages the evolution of the Financial Advisory Agent's SQLite database schema over time. It provides a structured way to apply database changes incrementally, ensuring data integrity and enabling smooth deployment updates.

## Architecture

### Migration Files
Each migration is a numbered SQL file that contains schema changes:
- **Naming Convention**: `###_descriptive_name.sql`
- **Numbering**: Sequential, zero-padded (001, 002, 003, etc.)
- **Content**: Pure SQL statements (CREATE, ALTER, INSERT, etc.)

### Migration Runner
The `run_migrations.py` script:
- Discovers and applies migrations in order
- Tracks applied migrations to prevent re-execution
- Ensures atomic execution with proper error handling
- Supports foreign key constraints and transaction management

## Migration Files

### 001_create_conversations.sql
**Purpose**: Creates the core conversations table for chat management.

**Tables Created**:
- `conversations` - Stores conversation metadata and state

**Key Features**:
- Supports both Scenario A (existing customers) and Scenario B (new users)
- Dual indexing on `customer_id` and `session_id`
- JSON metadata storage for extensibility
- Message counting and activity tracking

### 002_create_chat_messages.sql
**Purpose**: Creates message storage for conversation history.

**Tables Created**:
- `chat_messages` - Individual messages within conversations

**Key Features**:
- Rich message metadata (role, tool calls, SQL results)
- Foreign key relationships to conversations
- JSON storage for complex tool results (calculations, SQL details)
- Soft delete capability with `is_active` flag

### 003_create_conversation_summaries.sql
**Purpose**: Adds optional AI-generated conversation summaries.

**Tables Created**:
- `conversation_summaries` - LLM-generated conversation overviews

**Key Features**:
- One summary per conversation
- Short titles for quick identification
- JSON metadata for summary quality metrics
- Automatic timestamp tracking

### 004_add_chart_data_to_messages.sql
**Purpose**: Extends message storage to include chart visualizations.

**Changes Made**:
- Adds `chart_data` column to `chat_messages` table
- Stores chart configurations as JSON text
- Enables inline visualization rendering

## Migration System Components

### Migration Tracking
The system uses a `_migrations` table to track applied migrations:
```sql
CREATE TABLE _migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,
    applied_at DATETIME DEFAULT (datetime('now'))
);
```

### Execution Flow
1. **Discovery**: Scans for `*.sql` files in migrations directory
2. **Ordering**: Sorts files numerically to ensure correct sequence
3. **Validation**: Checks if migration was already applied
4. **Execution**: Runs SQL scripts within transactions
5. **Recording**: Marks migration as applied in tracking table

### Safety Features
- **Idempotent**: Safe to run multiple times
- **Transactional**: All-or-nothing execution per migration
- **Foreign Keys**: Enabled during migration execution
- **Error Handling**: Detailed error reporting and rollback

## Usage

### Running Migrations
```bash
# From backend/migrations directory
python run_migrations.py

# Or from backend directory
python migrations/run_migrations.py
```

### Adding New Migrations
1. **Create numbered file**: `005_new_feature.sql`
2. **Write SQL**: Include only schema changes
3. **Test locally**: Run migrations on development database
4. **Commit**: Include migration in version control

### Migration Best Practices
- **One change per migration**: Keep migrations focused
- **Idempotent SQL**: Use `IF NOT EXISTS` and `IF EXISTS`
- **Backwards compatible**: Don't break existing functionality
- **Indexed appropriately**: Add indexes for frequently queried columns
- **Document changes**: Include comments explaining purpose

## Database Schema Overview

### Core Tables
```
conversations (main chat sessions)
├── chat_messages (individual messages)
├── conversation_summaries (AI summaries)
└── _migrations (system tracking)
```

### Key Relationships
- `conversations.conversation_id` → `chat_messages.conversation_id`
- `conversations.conversation_id` → `conversation_summaries.conversation_id`

### Data Flow
1. **Conversations** created for each chat session
2. **Messages** stored with rich metadata (tool calls, results)
3. **Summaries** generated periodically for conversation overview
4. **Charts** embedded directly in message records

## Migration History

| Migration | Date | Description | Impact |
|-----------|------|-------------|---------|
| 001 | Initial | Conversation management | Core functionality |
| 002 | Initial | Message storage | Chat history |
| 003 | Initial | AI summaries | Enhanced UX |
| 004 | Later | Chart integration | Visual enhancements |

## Configuration

### Database Path
Migrations target: `backend/data/financial_data.db`

### Migration Directory
Located at: `backend/migrations/`

### Supported SQL Features
- **SQLite 3.0+** compatible syntax
- **Foreign keys** (enabled during execution)
- **Indexes** for performance
- **JSON storage** in TEXT columns
- **Triggers and views** (if needed)

## Error Handling & Troubleshooting

### Common Issues
1. **Migration fails**: Check SQL syntax and foreign key constraints
2. **Already applied**: System skips already-run migrations automatically
3. **Missing file**: Ensure migration files exist and are readable

### Recovery
- **Failed migration**: Fix SQL and re-run (system is idempotent)
- **Corrupt state**: Drop `_migrations` table and re-run all migrations
- **Data conflicts**: Review migration order and dependencies

### Debugging
Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- **Rollback support**: Ability to undo migrations
- **Dry-run mode**: Preview changes before applying
- **Migration dependencies**: Declare prerequisites between migrations
- **Data migrations**: Support for data transformations during schema changes
- **Environment-specific migrations**: Different schemas for dev/staging/prod

### Schema Evolution
- **Audit logging**: Track all schema changes with timestamps
- **Performance monitoring**: Migration execution time tracking
- **Backup integration**: Automatic backups before destructive changes
- **Multi-database support**: PostgreSQL/MySQL migration paths

## Integration with Development Workflow

### Development Process
1. **Schema change needed** → Create migration file
2. **Test locally** → Run migrations on dev database
3. **Commit migration** → Include in pull request
4. **Deploy** → Migrations run automatically on server startup

### CI/CD Integration
Migrations can be integrated into deployment pipelines:
- Run during container startup
- Validate schema consistency across environments
- Generate schema documentation automatically

## Conclusion

The migrations system ensures reliable database schema evolution while maintaining data integrity. It supports the Financial Advisory Agent's need for flexible conversation management, rich message metadata, and continuous feature development.

The incremental approach allows for safe deployment updates and provides a clear history of database changes over time.
