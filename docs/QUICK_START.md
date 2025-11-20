# Quick Start Guide

## Prerequisites
- Python 3.8+
- Node.js 18+
- AWS Account with Bedrock access

## Setup Steps

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
cp env.example .env
# Edit .env and add your AWS credentials
```

Your `.env` file should look like:
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
```

### 2. Enable Bedrock Access

1. Log into AWS Console
2. Navigate to Amazon Bedrock
3. Click "Model access" → "Manage model access"
4. Enable **Amazon Nova Pro** (or your preferred model)
5. Wait for access approval (~5 minutes)

### 3. Start Backend

```bash
python main.py
```

Backend runs on `http://localhost:8000`

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

Frontend runs on `http://localhost:3000`

## Testing

1. Visit `http://localhost:3000`
2. Click **"AI Chat Assistant"**
3. Type a message and hit Enter
4. Watch the AI respond using AWS Bedrock!

## Architecture

```
┌─────────────────┐
│   Next.js UI    │  ← User interacts here
└────────┬────────┘
         │ HTTP POST /chat
         ▼
┌─────────────────┐
│  FastAPI Server │  ← Receives request
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Strands Agent   │  ← Orchestrates AI call
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ BedrockModel    │  ← Strands' Bedrock adapter
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AWS Bedrock    │  ← Amazon Nova generates response
│  (Nova Pro)     │
└─────────────────┘
```

## Key Features

✅ **Strands Agent Framework**: Model-driven AI agent orchestration  
✅ **AWS Bedrock**: Access to Amazon Nova and Claude models  
✅ **No Tool Integration**: Clean, simple chatbot (tools can be added later)  
✅ **Type Safety**: Pydantic models for request/response validation  
✅ **Modern UI**: Beautiful chat interface with shadcn/ui  

## Next Steps

- Add tools to your agent (see `backend/README.md`)
- Enable streaming responses
- Add conversation history/memory
- Implement authentication

## Troubleshooting

**Backend won't start?**
- Check your AWS credentials in `.env`
- Verify you have Bedrock access enabled

**No AI responses?**
- Ensure Amazon Nova Pro is enabled in Bedrock console
- Check AWS region matches your Bedrock access region
- Look at backend terminal for error messages

**Frontend can't connect?**
- Make sure backend is running on port 8000
- Check CORS settings in `main.py`

