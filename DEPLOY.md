# Andromeda — Deployment Guide

This project is configured as a **monolithic Vercel deployment**. Both the Next.js frontend and the FastAPI + LangGraph backend are deployed to Vercel using a single repository integration.

## Vercel Architecture ($0/month, No Credit Card)

| Layer | Platform | Plan | Credit Card? | Cost |
|---|---|---|---|---|
| Frontend (Next.js) | Vercel | Hobby (Free) | ❌ No | $0 |
| Backend (FastAPI) | Vercel (Python Serverless) | Hobby (Free) | ❌ No | $0 |
| Database | SQLite (local) | Free | ❌ No | $0 |
| LLM | Gemini 2.0 Flash | Google AI Studio Free | ❌ No | $0 |

> **Vercel Hobby Plan Details:** Vercel's free tier has been specifically configured in ercel.json to allow maximum 60-second timeouts for the Python backend. This gives the LangGraph AI sufficient time to execute. Furthermore, heavy ML dependencies have been split into equirements-ml.txt to guarantee the backend stays well under Vercel's 250MB size limit.

---

## 1. Deploy Full Stack → Vercel

1. Log in to your Vercel account at [vercel.com](https://vercel.com).
2. Click **Add New Project** → **Import Git Repository**.
3. Select the Andromeda repository.
4. Leave the Framework Preset as **Next.js** and the Root Directory empty. Vercel will automatically read the custom ercel.json and build both the Python backend and the Next.js frontend.
5. Add the following **Environment Variables**:
   `env
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=<your-key-from-aistudio.google.com>
   GEMINI_MODEL=gemini-2.0-flash
   DATABASE_URL=sqlite:////tmp/andromeda.db
   BUSINESS_TODAY=2025-01-15
   AGENT_MODE=graph
   TOOL_MODE=local
   RAG_ENABLED=false
   `
   *(Note: On Vercel, the SQLite database must be written to /tmp as it is the only writable directory in serverless functions).*
6. Click **Deploy**.

The frontend will be available at the root URL (e.g. https://andromeda.vercel.app), and the backend API will be seamlessly routed under /api (e.g. https://andromeda.vercel.app/api/health).

---

## 2. Local Development (Without Docker)

You can run the full stack locally using two terminals.

**Terminal 1: Start the Backend (FastAPI)**
`ash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Start FastAPI server
python -m uvicorn app.main:app --reload --port 8000
`
*API Docs (Swagger): http://localhost:8000/docs*

**Terminal 2: Start the Frontend (Next.js)**
`ash
cd frontend
npm install
npm run dev
`
*Frontend: http://localhost:3000*

---

## 3. CI/CD Pipeline (GitHub Actions)

The ci.yml workflow runs automatically on every push to main:

| Job | What it does | Signal |
|---|---|---|
| ackend-tests | 60 pytest tests (policy + eval) | Reliability |
| ackend-lint | ruff lint check | Code quality |
| rontend-typecheck | TypeScript type check | Type safety |
| evaluation-smoke | 3-sample golden dataset eval | AI quality |

---

## 4. Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| LLM_PROVIDER | Yes | gemini / groq / openai / mock |
| GEMINI_API_KEY | If gemini | Free at aistudio.google.com/apikey |
| DATABASE_URL | No | Defaults to SQLite |
| AGENT_MODE | No | graph (LangGraph) or legacy |
| RAG_ENABLED | No | 	rue to enable ChromaDB RAG |
| LANGFUSE_PUBLIC_KEY | No | LangFuse observability (free at cloud.langfuse.com) |
