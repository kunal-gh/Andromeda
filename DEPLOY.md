# Andromeda — Deployment Guide

## Verified Free-Tier Architecture ($0/month, No Credit Card)

| Layer | Platform | Plan | Credit Card? | Cost |
|---|---|---|---|---|
| Frontend (Next.js) | Vercel | Hobby (Free) | ? No | $0 |
| Backend (FastAPI + LangGraph) | Render.com | Free Web Service | ? No | $0 |
| LLM | Gemini 2.0 Flash | Google AI Studio Free | ? No | $0 |
| CI/CD | GitHub Actions | Free (public repo) | ? No | $0 |

**Total: $0/month. Zero credit cards required.**

> ?? **Render Free Tier Limitation:** Free web services sleep after 15 minutes of
> inactivity. Cold start on the first request takes ~30-60 seconds. This is perfectly
> acceptable for a portfolio/interview demo. Upgrade to $7/month Starter to remove sleep.

> ?? **Alternative:** Deploy the backend on **Hugging Face Spaces** (also free, no credit card)
> — popular in the AI community and looks great on an AI engineer resume. See Option B below.

---

## Option A: Render (Recommended — Simplest Setup)

### Step 1: Deploy Backend ? Render

1. Sign up at [render.com](https://render.com) — no credit card needed
2. Click **New** ? **Web Service**
3. Connect your GitHub account ? select `Andromeda` repository
4. Configure:
   - **Name:** `andromeda-backend`
   - **Root Directory:** `backend`
   - **Runtime:** Docker
   - **Instance Type:** Free
5. Add **Environment Variables** under the Environment tab:
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=<your-key-from-aistudio.google.com>
   GEMINI_MODEL=gemini-2.0-flash
   DATABASE_URL=sqlite:///./data/andromeda.db
   BUSINESS_TODAY=2025-01-15
   FRONTEND_ORIGIN=https://<your-vercel-app>.vercel.app
   AGENT_MODE=graph
   TOOL_MODE=local
   RAG_ENABLED=false
   ```
6. Click **Create Web Service**. Render uses `backend/Dockerfile` automatically.
7. Copy your Render URL (e.g., `https://andromeda-backend.onrender.com`)

### Step 2: Deploy Frontend ? Vercel (New Account)

1. Sign up at [vercel.com](https://vercel.com) with your new account — no credit card
2. Click **Add New Project** ? **Import Git Repository** ? select `Andromeda`
3. Vercel reads `vercel.json` ? auto-configures the `frontend/` directory
4. Add **Environment Variable**:
   ```
   NEXT_PUBLIC_API_BASE_URL=https://andromeda-backend.onrender.com
   ```
5. Click **Deploy** ?

> **Important:** Once you have the Vercel URL, go back to Render and update
> `FRONTEND_ORIGIN` to `https://<your-app>.vercel.app` for correct CORS headers.

---

## Option B: Hugging Face Spaces (Best for AI Engineer Resume Signal)

Hugging Face Spaces supports free Docker deployments — ideal for an AI platform
because it signals you ship AI work where AI engineers actually deploy things.

### Step 1: Create a Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) — no credit card
2. Click **Create new Space**
3. Settings:
   - **SDK:** Docker
   - **Hardware:** CPU Basic (Free)
   - **Visibility:** Public
4. In the Space **Settings** tab, add secrets:
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=<your-key>
   GEMINI_MODEL=gemini-2.0-flash
   DATABASE_URL=sqlite:////tmp/andromeda.db
   BUSINESS_TODAY=2025-01-15
   AGENT_MODE=graph
   TOOL_MODE=local
   RAG_ENABLED=false
   ```
5. In your local repo, create a `backend/README.md` with:
   ```yaml
   ---
   title: Andromeda AI Backend
   sdk: docker
   app_port: 8000
   ---
   ```
6. Push — Hugging Face builds and runs `backend/Dockerfile` automatically

> **Note:** HF Spaces writes only to `/tmp`. The SQLite DB path must be
> `sqlite:////tmp/andromeda.db` on Hugging Face (set via `DATABASE_URL` env var).

---

## Local Development

```bash
# Copy env template and fill in your keys
cp .env.example .env

# Start everything with Docker Compose
docker compose up

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs (Swagger): http://localhost:8000/docs
```

---

## CI/CD Pipeline (GitHub Actions)

The `ci.yml` workflow runs automatically on every push to `main`:

| Job | What it does | Signal |
|---|---|---|
| `backend-tests` | 60 pytest tests (policy + eval) | Reliability |
| `backend-lint` | ruff lint check | Code quality |
| `frontend-typecheck` | TypeScript type check | Type safety |
| `evaluation-smoke` | 3-sample golden dataset eval | AI quality |
| `docker-build` | Validates both Dockerfiles | Deployability |

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `LLM_PROVIDER` | Yes | `gemini` / `groq` / `openai` / `mock` |
| `GEMINI_API_KEY` | If gemini | Free at aistudio.google.com/apikey |
| `DATABASE_URL` | No | Defaults to SQLite |
| `FRONTEND_ORIGIN` | Yes | Vercel URL (for CORS) |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Render/HF Spaces backend URL |
| `AGENT_MODE` | No | `graph` (LangGraph) or `legacy` |
| `RAG_ENABLED` | No | `true` to enable ChromaDB RAG |
| `LANGFUSE_PUBLIC_KEY` | No | LangFuse observability (free at cloud.langfuse.com) |
