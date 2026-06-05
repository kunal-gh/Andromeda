<div align="center">

<img src="https://img.shields.io/badge/Andromeda-v2.0-818cf8?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTMgMkwzIDEzSDEyTDExIDIyTDIxIDExSDEyTDEzIDJaIiBzdHJva2U9IiM4MjhjZjgiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+" alt="Andromeda v2" />

# Andromeda

### Enterprise Multi-Agent AI Platform

*A production-grade, observable, multi-agent AI system built on LangGraph, MCP, and RAG.*

[![LangGraph](https://img.shields.io/badge/LangGraph-State%20Machine-818cf8?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## What Is Andromeda?

Andromeda is an end-to-end AI agent system that demonstrates what production AI engineering actually looks like in 2025 — not a chatbot wrapper, but a complete system with a state-machine orchestration layer, deterministic policy enforcement, adversarial safety, real-time observability, and an evaluation pipeline.

It processes customer support requests for a fictional e-commerce company (**ArcaShop**), enforcing a 10-rule refund policy with 100% deterministic decisions that the language model cannot override, while using LLMs only for what they are uniquely good at: natural language understanding and empathetic response composition.

**The point** is the architecture, not the domain. Swap the ArcaShop policy for any enterprise workflow and the system remains unchanged.

---

## Architecture at a Glance

```
HTTP Request → POST /api/chat
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  ANDROMEDA  —  LangGraph State Machine                      │
│                                                             │
│  [intake_node]  ──────────────────────────────────────┐    │
│       │                                               │    │
│       ▼                                               │    │
│  [guardrail_node]  ←── 35-pattern injection scanner   │    │
│       │                                               │    │
│       ├─(HIGH risk)──► [block_node]                   │    │
│       │                                               │    │
│       ▼ (LOW / MEDIUM)                                │    │
│  [extraction_node]  ←── LLM call 1: intent + order ID│    │
│       │                                               │    │
│       ├─(no order)──► [needs_info_node]               │    │
│       │                                               │    │
│       ▼                                               │    │
│  [tool_node]  ←── CRM lookup + order lookup           │    │
│       │                                               │    │
│       ▼                                               │    │
│  [policy_node]  ←── R1–R10 deterministic engine       │    │
│       │                                               │    │
│       ▼                                               │    │
│  [response_node]  ←── LLM call 2: compose reply       │    │
│       │                                               │    │
│       ▼                                               │    │
│  [persistence_node]  ←── DB write + SSE emission      │    │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
ChatResponse (decision + message + trace + injection_detected)
```

Every node is a pure function. State is a typed dictionary. No mutable globals, no god objects.

---

## Core Engineering Pillars

### 1 — LangGraph State Machine (Orchestration)

The agent is modelled as a directed graph with typed state (`AgentState`) passing through nodes via conditional edges. This is fundamentally different from a chain of function calls: if extraction fails to find an order ID, the graph routes to `needs_info_node` rather than proceeding with `None`. Conditional edge functions (`route_after_guardrail`, `route_after_extraction`, `route_after_policy`) make the routing logic explicit, testable, and auditable.

```
LangGraph compile-time graph → MemorySaver checkpointing
    ↓
Per-conversation thread state persists across turns
    ↓
Conditional edges tested independently of node logic
```

### 2 — Deterministic Policy Engine (AI Safety)

The LLM cannot approve or deny a refund. `policy_node` calls `evaluate_order_policy()` which is pure Python — no LLM, no probability, no hallucination. The result is locked into `AgentState.decision` before `response_node` runs. The LLM in `response_node` sees the decision as a fact and composes a human explanation. It cannot change it.

The policy engine enforces 10 named rules:

| Rule | Condition | Decision |
|---|---|---|
| R1_EXPIRED_WINDOW | Delivered > 30 days ago | DENIED |
| R2_FINAL_SALE | `final_sale = true` | DENIED |
| R3_ALREADY_RETURNED | `returned = true` | DENIED |
| R4_ESCALATE_OVER_500 | `price > $500` | ESCALATED |
| R5_DIGITAL_GOODS | Category: digital/gift_card | DENIED |
| R6_EMAIL_MISMATCH | Email ≠ order customer | DENIED |
| R7_NOT_DELIVERED | Status ≠ delivered | DENIED |
| R8_CONDITION_DAMAGED | `condition_note` present | ESCALATED |
| R9_ELIGIBLE_STANDARD_REFUND | All checks pass | APPROVED |
| R10_HIGH_FRAUD_RISK | `fraud_risk = HIGH` | ESCALATED |

### 3 — Adversarial Safety (Prompt Injection Defense)

A 35-pattern lexical scanner runs before any LLM call. If injection risk is `HIGH`, the request is blocked at `guardrail_node` and never reaches the LLM. Even if a crafted message passes the scanner with `MEDIUM` risk, it still cannot affect the policy outcome — the deterministic engine has no LLM surface area.

```python
# Pattern categories in guardrails.py
INJECTION_PATTERNS = [
    # Override attempts
    r"ignore (all |previous |above )?instructions",
    r"override (the |all |)?(policy|rules|system)",
    # Jailbreak prefixes
    r"you are now",  r"act as",  r"pretend you",
    # Privilege escalation
    r"admin (mode|override|access)",
    # ... 31 more patterns
]
```

### 4 — Multi-Provider LLM Architecture

Three providers are supported and fully interchangeable at runtime via `LLM_PROVIDER` env var:

| Provider | Model | Free Tier |
|---|---|---|
| Gemini | gemini-2.0-flash | ✅ 1M tokens/day |
| Groq | llama-3.3-70b-versatile | ✅ Generous free tier |
| OpenAI | gpt-4o-mini | ❌ Paid |

`providers.py` exposes a single interface: `extract_intent(message, email)` and `compose_reply(context)`. Adding a new provider requires implementing this interface only.

### 5 — Real-Time Observability (SSE Trace Stream)

Every node emits a `TraceEvent` to the database and broadcasts it via Server-Sent Events. The frontend subscribes to `/api/events/{conversation_id}` and renders the trace timeline in real time — every tool call, LLM invocation, policy check, and guard decision appears as an event within milliseconds.

```json
{
  "step": "tool.evaluate_refund_policy",
  "title": "Deterministic policy engine completed",
  "severity": "info",
  "detail": {
    "decision": "APPROVED",
    "triggered_rules": ["R9_ELIGIBLE_STANDARD_REFUND"],
    "confidence": 0.97,
    "risk_flags": []
  }
}
```

---

## Repository Structure

```
andromeda/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── graph/               # LangGraph state machine (Phase 1)
│   │   │   │   ├── state.py         # AgentState TypedDict
│   │   │   │   ├── builder.py       # compile + singleton graph
│   │   │   │   ├── edges.py         # conditional routing functions
│   │   │   │   └── nodes/           # one file per node
│   │   │   ├── guardrails.py        # 35-pattern injection scanner
│   │   │   ├── policy.py            # R1-R10 deterministic engine
│   │   │   ├── providers.py         # Gemini / Groq / OpenAI adapter
│   │   │   ├── runner.py            # thin adapter over graph.ainvoke()
│   │   │   └── tools.py             # CRM + Order + Policy tools
│   │   ├── api/
│   │   │   └── routes.py            # /api/chat, /api/events, /api/health
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings (all env vars)
│   │   │   └── time.py              # business_today() helper
│   │   ├── data/
│   │   │   ├── arcashop_refund_policy.md   # ArcaShop policy document
│   │   │   └── synthetic_crm.json          # 15 customers, 31 orders
│   │   ├── db/
│   │   │   ├── database.py          # SQLAlchemy engine + SessionLocal
│   │   │   ├── models.py            # ORM: Customer, Order, Conversation, etc.
│   │   │   └── seed.py              # reads synthetic_crm.json on first boot
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic request/response schemas
│   │   └── main.py                  # FastAPI app + CORS + lifespan
│   ├── tests/
│   │   └── test_policy.py           # 56 deterministic policy assertions
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── globals.css              # Andromeda indigo design system
│   │   ├── layout.tsx               # Meta, fonts (Inter + Space Grotesk + JetBrains Mono)
│   │   └── page.tsx                 # Root page → SupportConsole
│   ├── components/
│   │   └── SupportConsole.tsx       # Full UI: chat, trace timeline, scenarios
│   ├── lib/
│   │   └── api.ts                   # Typed API client
│   └── Dockerfile
│
├── docs/
│   └── assets/                      # Architecture diagrams + screenshots
│
├── docker-compose.yml               # Single-command: backend + frontend
├── .env.example                     # All env vars documented
└── README.md
```

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- One free API key: [Gemini](https://aistudio.google.com/apikey) (recommended) **or** [Groq](https://console.groq.com/keys)

### 1. Clone and Configure

```bash
git clone https://github.com/kunal-gh/Andromeda.git
cd Andromeda

cp .env.example .env
# Edit .env → set LLM_PROVIDER and the matching API key
```

### 2. Boot

```bash
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 3. Test Locally (No Docker)

```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Running the Test Suite

```bash
cd backend
python -m pytest tests/ -v
```

56 tests covering all 10 policy rules, boundary conditions, and edge cases. Tests are deterministic — no LLM calls, no network, no randomness.

```
tests/test_policy.py::test_expired_window           PASSED
tests/test_policy.py::test_final_sale               PASSED
tests/test_policy.py::test_already_returned         PASSED
tests/test_policy.py::test_escalate_over_500        PASSED
... 52 more PASSED
```

---

## API Reference

### `POST /api/chat`

Submit a customer support request. The agent extracts intent, enforces policy, and returns a decision with a natural-language response.

**Request:**
```json
{
  "conversation_id": "uuid-optional",
  "customer_email": "asha.rao@example.com",
  "message": "I'd like to return the jacket from order ORD-1001."
}
```

**Response:**
```json
{
  "conversation_id": "3fa85f64...",
  "assistant_message": "Your refund for order ORD-1001 has been approved...",
  "decision": "APPROVED",
  "triggered_rules": ["R9_ELIGIBLE_STANDARD_REFUND"],
  "needs_escalation": false,
  "injection_detected": false,
  "trace": [ ... 8 trace events ... ]
}
```

**Decision values:** `APPROVED` | `DENIED` | `ESCALATED` | `NEEDS_INFO`

### `GET /api/events/{conversation_id}`

Server-Sent Events stream. Subscribe to get real-time trace events for a conversation. Each event is a JSON `TraceEvent` broadcast as SSE.

### `GET /api/health`

```json
{
  "status": "ok",
  "llm_provider": "gemini",
  "provider_configured": true,
  "db": "connected"
}
```

### `GET /api/conversations`

Returns a list of conversation summaries ordered by recency.

---

## Scenario Demonstration

The frontend includes six pre-loaded scenarios that exercise distinct policy paths:

| Scenario | Customer | Order | Expected Decision | Rule |
|---|---|---|---|---|
| ✅ Standard Approval | asha.rao | ORD-1001 (jacket, $89) | **APPROVED** | R9 |
| 🚫 Final Sale Block | asha.rao | ORD-1002 (bag, final sale) | **DENIED** | R2 |
| 📋 High-Value Escalation | marcus.lee | ORD-1003 (camera, $720) | **ESCALATED** | R4 |
| ⚠️ Fraud Risk | owen.kim | ORD-1031 (fraud_risk=HIGH) | **ESCALATED** | R10 |
| 🔒 Email Mismatch | priya.shah | ORD-1001 (owned by asha) | **DENIED** | R6 |
| ⚡ Injection Attack | — | override instructions | **BLOCKED** | guardrail |

---

## Design Decisions

**Why SQLite for dev?** Zero infrastructure. The ORM (SQLAlchemy 2.0) abstracts the driver — swap `DATABASE_URL` to Postgres in production without touching application code.

**Why not let the LLM make the policy decision?** LLMs hallucinate. A customer support decision that is wrong by 5% is commercially unacceptable. The deterministic engine eliminates that class of failure entirely. The LLM is only used to understand natural language and write a clear response — tasks where probabilistic outputs are acceptable.

**Why SSE instead of WebSockets?** SSE is unidirectional and HTTP-native. No upgrade handshake, no connection state, reconnects automatically. For an observability stream, it is the right primitive.

**Why LangGraph instead of a chain?** LangGraph expresses the routing logic explicitly. The `needs_info` branch, the `block` branch, the `human_handoff` branch — these are first-class graph edges, not `if/else` buried inside a monolithic function. The graph can be visualised, tested per-node, and extended without touching existing nodes.

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| API Framework | FastAPI | 0.115 |
| Agent Orchestration | LangGraph | 0.2+ |
| ORM | SQLAlchemy | 2.0 |
| Database | SQLite (dev) / PostgreSQL (prod) | — |
| LLM: Primary | Google Gemini 2.0 Flash | — |
| LLM: Fallback | Groq Llama-3.3-70b | — |
| Validation | Pydantic v2 | 2.7+ |
| Frontend | Next.js 16 + React 19 | — |
| Styling | Vanilla CSS (design tokens) | — |
| Animations | Motion (Framer Motion v12) | — |
| Icons | Lucide React | — |
| Containerization | Docker + Compose | — |
| Testing | pytest + pytest-asyncio | 8.x |

---

## Roadmap

The following phases are designed and ready for implementation:

- **Phase 2 — MCP Servers:** Expose CRM, Orders, and Policy as Model Context Protocol servers (FastMCP). Tool mode switchable via `TOOL_MODE=mcp`.
- **Phase 3 — RAG Pipeline:** ChromaDB vector store with sentence-transformer embeddings for semantic policy retrieval. Policy sections chunked by heading, retrieved per query.
- **Phase 4 — Evaluation Framework:** RAGAS evaluation pipeline with 10-sample golden dataset. Faithfulness ≥ 0.80, answer relevancy ≥ 0.75, context precision ≥ 0.70.
- **Phase 5 — Observability:** Langfuse distributed tracing (free cloud tier) + OpenTelemetry instrumentation of FastAPI and SQLAlchemy.
- **Phase 6 — Multi-Agent:** Supervisor + Policy + Retrieval + Support + Evaluation agents. EvaluationAgent scores drafts before they reach the customer.
- **Phase 7 — CI/CD:** GitHub Actions test + lint + eval gate pipelines.

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

Built with precision. Designed for CTOs.

</div>
