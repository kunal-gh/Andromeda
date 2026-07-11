# Andromeda — Deployment Guide

This project uses a **decoupled free-tier architecture**:

| Layer | Platform | Plan | Cost |
|---|---|---|---|
| Frontend (Next.js) | Vercel | Hobby (Free) | $0 |
| Backend (FastAPI + LangGraph) | Koyeb | Free Instance | $0 |
| Database | SQLite (local) ? Neon (Postgres) | Free | $0 |
| LLM | Gemini 2.0 Flash | Google AI Studio Free Tier | $0 |
| CI/CD | GitHub Actions | Free (public repo) | $0 |

**Total monthly cost: $0**

---

## Why Koyeb for the Backend?

Vercel Serverless Functions have a **15-second timeout** on the free tier. LangGraph
state machines running real LLMs consistently take 15–60 seconds. Koyeb provides a
**permanently free, always-on Docker container** — no cold starts, no timeouts.

---

## 1. Deploy Backend ? Koyeb

### Prerequisites
- Koyeb account: https://app.koyeb.com (free, no credit card)
- Your `GEMINI_API_KEY` from https://aistudio.google.com/apikey

### Steps

1. Log in to [app.koyeb.com](https://app.koyeb.com)
2. Click **Create App** ? choose **GitHub**
3. Select `kunal-gh/Andromeda` repository
4. Configure the service:
   - **Builder:** Docker
   - **Dockerfile path:** `backend/Dockerfile`
   - **Port:** `8000`
   - **Instance:** Free (nano)
5. Add **Environment Variables** in the Koyeb dashboard:
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=<your-key>
   GEMINI_MODEL=gemini-2.0-flash
   DATABASE_URL=sqlite:////app/data/andromeda.db
   BUSINESS_TODAY=2025-01-15
   FRONTEND_ORIGIN=https://<your-vercel-app>.vercel.app
   AGENT_MODE=graph
   TOOL_MODE=local
   RAG_ENABLED=false
   ```
6. Click **Deploy**. Koyeb will build the Docker image and start the container.
7. Copy your Koyeb public URL (e.g., `https://andromeda-xxxx.koyeb.app`).

---

## 2. Deploy Frontend ? Vercel (New Account)

### Prerequisites
- New Vercel account at https://vercel.com (use a different email/GitHub account)

### Steps

1. Log in to your **new** Vercel account
2. Click **Add New Project** ? **Import Git Repository**
3. Select `kunal-gh/Andromeda`
4. Vercel will detect the `vercel.json` and set:
   - **Framework:** Next.js
   - **Root Directory:** `frontend/`
5. Add **Environment Variables** in Vercel settings:
   ```
   NEXT_PUBLIC_API_BASE_URL=https://<your-koyeb-url>.koyeb.app
   ```
6. Click **Deploy**

> **Important:** Set the `FRONTEND_ORIGIN` env var on Koyeb to match your Vercel
> deployment URL to ensure CORS headers are correct.

---

## 3. Local Development

```bash
# Copy env template and fill in your keys
cp .env.example .env

# Start everything with Docker Compose
docker compose up

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 4. CI/CD Pipeline (GitHub Actions)

The `ci.yml` workflow runs automatically on every push to `main`:

| Job | What it does |
|---|---|
| `backend-tests` | 60 pytest tests (policy engine + evaluation pipeline) |
| `backend-lint` | ruff lint check |
| `frontend-typecheck` | TypeScript type check |
| `evaluation-smoke` | 3-sample golden dataset evaluation |
| `docker-build` | Validates both Dockerfiles build cleanly |

All jobs must pass before merging. Koyeb auto-deploys from `main` once CI passes.

---

## 5. Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `LLM_PROVIDER` | Yes | `gemini` / `groq` / `openai` / `mock` |
| `GEMINI_API_KEY` | If gemini | Google AI Studio key |
| `GROQ_API_KEY` | If groq | Groq API key |
| `OPENAI_API_KEY` | If openai | OpenAI API key |
| `DATABASE_URL` | No | Defaults to SQLite |
| `FRONTEND_ORIGIN` | Yes | Vercel URL (for CORS) |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Koyeb backend URL |
| `AGENT_MODE` | No | `graph` (LangGraph) or `legacy` |
| `RAG_ENABLED` | No | `true` to enable ChromaDB RAG |
| `LANGFUSE_PUBLIC_KEY` | No | LangFuse observability key |
