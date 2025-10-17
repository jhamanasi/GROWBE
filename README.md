# Ava - AI Assistant

A full-stack AI assistant application with Next.js frontend and FastAPI backend, featuring complete authentication and user management.

## Project Structure

```
Vogen-Starter/
├── frontend/          # Next.js frontend with Clerk.js authentication
├── backend/           # FastAPI backend with JWT validation
├── frontend.env.example # Frontend environment template
└── backend.env.example  # Backend environment template
```

## 🔐 Authentication Setup

This application uses **Clerk.js** for complete authentication. All pages and API endpoints are protected.

### 1. Create Clerk Account

1. Go to [Clerk Dashboard](https://dashboard.clerk.com)
2. Create a new application
3. Get your **Publishable Key** and **Secret Key**

### 2. Configure Environment Variables

**Frontend** (`frontend/.env.local`):
```bash
cp frontend.env.example frontend/.env.local
```
Edit `frontend/.env.local` and add your Clerk keys:
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
CLERK_SECRET_KEY=sk_test_your_secret_key_here
```

**Backend** (`backend/.env`):
```bash
cp backend.env.example backend/.env
```
Edit `backend/.env` and add your keys:
```env
CLERK_SECRET_KEY=sk_test_your_secret_key_here
# ... other AWS/Bedrock keys
```

## Getting Started

### Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables (see Authentication Setup above)

5. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   
   The backend will be available at `http://localhost:8000`

### Frontend (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables (see Authentication Setup above)

4. Run the development server:
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:3000`

## 🎭 User Experience

- **🔒 Protected Access**: All pages require authentication
- **✨ Beautiful Auth**: Pre-built sign-in/sign-up pages
- **👤 User Profile**: Built-in user management with Clerk
- **🔄 Automatic Redirects**: Seamless authentication flow
- **🛡️ Secure API**: All endpoints validate JWT tokens

## Features

- **Homepage**: Simple landing page with navigation to dashboard and chat
- **Dashboard**: Interactive page with a greeting form that communicates with the FastAPI backend
- **Chat**: AI-powered chatbot interface using Strands Agent framework with AWS Bedrock (Amazon Nova)
- **Backend API**: FastAPI server with CORS enabled for frontend communication

## API Endpoints

- `GET /`: Health check endpoint
- `POST /greet`: Accepts a name and returns a personalized greeting
- `POST /chat`: AI chat endpoint powered by Strands Agent and AWS Bedrock (Amazon Nova Pro)

## Tech Stack

### Frontend
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components
- React hooks for state management

### Backend
- FastAPI
- Python
- Strands Agent Framework (model-driven AI agents)
- BedrockModel (Strands' AWS Bedrock adapter)
- AWS Bedrock (Amazon Nova Pro)
- Pydantic for data validation
- CORS middleware for frontend integration 