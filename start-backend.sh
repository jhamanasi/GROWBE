#!/bin/bash

# Kill any existing process on port 9000
echo "🔍 Checking for existing processes on port 9000..."
lsof -ti :9000 | xargs kill -9 2>/dev/null && echo "✅ Killed existing process" || echo "✅ Port 9000 is available"

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source ../venv/bin/activate

# Start the backend server
echo "🚀 Starting FastAPI backend on port 9000..."
python main.py

