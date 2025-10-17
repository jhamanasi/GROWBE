# FastAPI Backend with Strands Agent & AWS Bedrock

This backend uses the Strands agent framework integrated with AWS Bedrock (Claude 3) to power an AI chatbot.

## Prerequisites

1. **Python 3.8+**
2. **AWS Account** with Bedrock access enabled
3. **AWS IAM User** with appropriate permissions

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

**Initialize the SQLite database with schema and sample data:**

```bash
python db_setup.py
```

**What this does:**
- Creates the database schema from `schema_fixed.sql` (customers, products, orders, inventory, etc.)
- Populates with 10,000+ sample e-commerce records from `sample_populate_10k_fixed.sql`
- Performs a quick sanity check to verify the setup

**When to run `db_setup.py`:**
- ✅ **First time setup** - Creates the database from scratch
- ✅ **Fresh development environment** - Sets up schema + sample data
- ✅ **Database reset** - When you want to start fresh with clean data
- ✅ **After schema changes** - Rebuilds database with updated structure
- ✅ **When `shop.db` is missing or corrupted**

**⚠️ Warning:** This script **recreates the entire database**, so don't run it if you have important data you want to keep. It will drop all existing tables and data.

**Database Location:**
- The database file `shop.db` will be created in the `backend/` directory
- Used by SQLite tools and the Natural Language to SQL tool (`nl2sql_query`)

### 3. Configure AWS Credentials

#### Option A: Environment Variables (Recommended for Development)

Create a `.env` file in the backend directory:

```bash
cp env.example .env
```

Edit `.env` and add your AWS credentials:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_actual_access_key_here
AWS_SECRET_ACCESS_KEY=your_actual_secret_key_here
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

#### Option B: AWS CLI Configuration

```bash
aws configure
```

Provide your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Default output format (json)

### 4. Enable AWS Bedrock Access

1. Log into AWS Console
2. Navigate to Amazon Bedrock service
3. Go to "Model access" in the left sidebar
4. Click "Manage model access"
5. Enable access to **Anthropic Claude 3 Sonnet**
6. Wait for access to be granted (usually a few minutes)

### 5. IAM Permissions

Ensure your IAM user has the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "arn:aws:bedrock:*::foundation-model/*"
        }
    ]
}
```

## Running the Backend

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### `GET /`
Health check endpoint.

**Response:**
```json
{
    "message": "FastAPI Backend is running!"
}
```

### `POST /greet`
Simple greeting endpoint for testing.

**Request:**
```json
{
    "name": "John"
}
```

**Response:**
```json
{
    "message": "Hello, John! Nice to meet you!"
}
```

### `POST /chat`
AI-powered chat endpoint using Strands Agent with AWS Bedrock.

**Request:**
```json
{
    "message": "What is the capital of France?"
}
```

**Response:**
```json
{
    "response": "The capital of France is Paris. It's a beautiful city known for its art, culture, and iconic landmarks like the Eiffel Tower."
}
```

## Architecture

- **FastAPI**: Web framework for building the API
- **Strands Agent**: Model-driven framework for building AI agents
- **BedrockModel**: Strands' built-in adapter for AWS Bedrock
- **AWS Bedrock**: Provides access to Amazon Nova and Claude foundation models

## Strands Agent Configuration

The agent is initialized with:
- **Model**: BedrockModel with Amazon Nova Pro (configurable via env)
- **Temperature**: 0.7 (controls response randomness)
- **Streaming**: Disabled (can be enabled for real-time responses)
- **Tools**: Auto-loaded from `tools/` directory using ToolRegistry

### How It Works

1. **BedrockModel**: Strands' built-in model adapter for AWS Bedrock
2. **Agent**: Orchestrates the conversation and handles tool calls
3. **ToolRegistry**: Automatically discovers and loads all tools
4. **BaseTool**: Base class that enforces standard tool structure
5. **Simple API**: Just call `agent(user_message)` to get a response

### Tool System Architecture

The project uses a sophisticated tool management system:

```
tools/
├── __init__.py          # Package initialization
├── base_tool.py         # Abstract base class for all tools
├── tool_manager.py      # Registry for auto-discovery and registration
├── letter_counter.py    # Letter counting tool
├── word_counter.py      # Word counting tool
└── README.md           # Tool development guide
```

**Benefits:**
- ✅ **Auto-discovery**: Tools are automatically loaded at startup
- ✅ **Standardization**: All tools follow the same structure
- ✅ **Type Safety**: BaseTool enforces required methods
- ✅ **Easy to Add**: Just create a new file and implement BaseTool
- ✅ **Isolated**: Each tool is in its own file

### Available Tools

#### Letter Counter (`letter_counter.py`)
Counts the number of letters in text, excluding spaces, numbers, and special characters.

**Example usage:**
```
User: "How many letters are in 'Hello World'?"
Agent: *Uses letter_counter tool*
Response: "The text 'Hello World' contains 10 letters..."
```

**Returns:**
- Total letter count
- Breakdown of each letter's frequency
- Total text length
- Unique letter count

#### Word Counter (`word_counter.py`)
Counts words in text and provides detailed statistics.

**Example usage:**
```
User: "How many words in 'The quick brown fox'?"
Agent: *Uses word_counter tool*
Response: "The text contains 4 words..."
```

**Returns:**
- Total word count
- Average word length
- Longest word
- Shortest word

### Creating New Tools

See `tools/README.md` for detailed instructions on creating custom tools.

Quick example:
```python
from .base_tool import BaseTool

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "What this tool does..."
    
    def execute(self, input: str) -> dict:
        # Tool logic here
        return {"result": "success"}
```

Save the file in `tools/` directory and it will be automatically loaded!

## Available Bedrock Models

You can change the model by updating `BEDROCK_MODEL_ID` in your `.env` file:

### Amazon Nova Models (Recommended)
- `us.amazon.nova-pro-v1:0` (default, balanced performance)
- `us.amazon.nova-lite-v1:0` (faster, lower cost)
- `us.amazon.nova-micro-v1:0` (fastest, lowest cost)

### Anthropic Claude Models
- `anthropic.claude-3-sonnet-20240229-v1:0` (balanced performance)
- `anthropic.claude-3-haiku-20240307-v1:0` (faster, lower cost)
- `anthropic.claude-3-opus-20240229-v1:0` (most capable, higher cost)

## Troubleshooting

### Error: "Could not connect to the endpoint URL"
- Check your AWS region is correct
- Ensure Bedrock is available in your region (us-east-1, us-west-2 recommended)

### Error: "AccessDeniedException"
- Verify your IAM user has the necessary Bedrock permissions
- Ensure you've requested and been granted access to Claude models in Bedrock console

### Error: "ValidationException: The provided model identifier is invalid"
- Check that the model ID is correct in your `.env` file
- Verify you have access to the specific model in the Bedrock console

## Development

To run with auto-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Future Enhancements

- Add tools to the Strands agent (web search, calculations, etc.)
- Implement conversation history/memory
- Add streaming responses
- Implement rate limiting
- Add authentication/authorization

