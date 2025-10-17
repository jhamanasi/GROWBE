#!/bin/bash

# Kill any existing process on port 3001
echo "🔍 Checking for existing processes on port 3001..."
lsof -ti :3001 | xargs kill -9 2>/dev/null && echo "✅ Killed existing process" || echo "✅ Port 3001 is available"

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Start the frontend server
echo "🚀 Starting Next.js frontend on port 3001..."
npm run dev

