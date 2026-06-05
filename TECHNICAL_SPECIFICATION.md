# Andromeda — Technical Specification

> **Version:** 2.0.0 · **Status:** Active Development · **Architecture:** Multi-Agent LangGraph

---

## 1. Executive Summary

Andromeda is a production-grade, observable, multi-agent AI platform built to demonstrate the full stack of modern AI engineering skills in one coherent system. The domain is customer support automation for ArcaShop (a fictional premium e-commerce brand), but the architecture is domain-agnostic — every component is designed to be swapped for any enterprise workflow.

The system is engineered around one central idea: **LLMs are powerful at understanding language and generating prose, but unreliable at making structured decisions**. Andromeda separates these concerns completely. The LLM handles natural language understanding (intent extraction) and response composition. All decisions — approve, deny, escalate — are made by a deterministic Python policy engine that cannot hallucinate, cannot be prompt-injected into a wrong answer, and produces the same result for the same input every single time.

---

## 2. Architecture

### 2.1 System Overview

```
Customer HTTP Request
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  FastAPI  (CORS · lifespan · /api/chat · /api/events SSE)   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  LangGraph State Machine  (app/agent/graph/)                 │
│                                                              │
│  intake → guardrail ──(HIGH)──→ block ──────────────┐       │
│               │                                     │       │
│          (LOW/MED)                                  │       │
│               ▼                                     │       │
│          extraction ──(no order)──→ needs_info ──┐  │       │
│               │                                  │  │       │
│          (order found)                           │  │       │
│               ▼                                  ▼  ▼       │
│           retrieval → tools → policy ──────→ response       │
│                                  │              │           │
│                             (ESCALATED)         │           │
│                                  ▼              │           │
│                           human_handoff ────────┘           │
│                                                             │
│                    All paths → persistence → END            │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
ChatResponse (decision + message + trace[] + injection_detected)
        │
        ▼ SSE stream
Frontend (Next.js) — real-time trace timeline
```

### 2.2 LangGraph State Machine (Phase 1)

The agent is modelled as a directed acyclic graph (with conditional branching) using LangGraph's `StateGraph`. State is a plain Python `dict` (`AgentState`) that each node receives and partially updates.

**Nodes:**

| Node | File | Responsibility |
|---|---|---|
| `intake_node` | `graph/nodes/intake_node.py` | Upsert Conversation row, persist user Message, emit trace |
| `guardrail_node` | `graph/nodes/guardrail_node.py` | 35-pattern injection scan |
| `block_node` | `graph/nodes/guardrail_node.py` | Hard refusal, no LLM invoked |
| `extraction_node` | `graph/nodes/extraction_node.py` | LLM Call 1 — intent + order_id |
| `needs_info_node` | `graph/nodes/extraction_node.py` | Compose clarification request |
| `retrieval_node` | `graph/nodes/retrieval_node.py` | ChromaDB semantic lookup (Phase 3) |
| `tool_node` | `graph/nodes/tool_node.py` | CRM + Order lookups |
| `policy_node` | `graph/nodes/policy_node.py` | R1–R10 deterministic engine |
| `human_handoff_node` | `graph/nodes/policy_node.py` | Route ESCALATED to review queue |
| `response_node` | `graph/nodes/response_node.py` | LLM Call 2 — compose reply |
| `persistence_node` | `graph/nodes/persistence_node.py` | DB writes, final trace |

**Conditional Edges:**

| Source | Function | Targets |
|---|---|---|
| `guardrail` | `route_after_guardrail` | `extraction` \| `block` |
| `extraction` | `route_after_extraction` | `retrieval` \| `needs_info` |
| `policy` | `route_after_policy` | `response` \| `human_handoff` |

### 2.3 Deterministic Policy Engine

`app/agent/policy.py` implements 10 named rules evaluated in priority order. No LLM, no randomness.

| Rule ID | Condition | Decision |
|---|---|---|
| `R1_EXPIRED_WINDOW` | Delivered > 30 days before `BUSINESS_TODAY` | DENIED |
| `R2_FINAL_SALE` | `order.final_sale = true` | DENIED |
| `R3_ALREADY_RETURNED` | `order.returned = true` | DENIED |
| `R4_ESCALATE_OVER_500` | `order.price > 500` | ESCALATED |
| `R5_DIGITAL_GOODS` | `order.category in {digital, gift_card}` | DENIED |
| `R6_EMAIL_MISMATCH` | Customer email ≠ order owner email | DENIED |
| `R7_NOT_DELIVERED` | `order.status ≠ delivered` | DENIED |
| `R8_CONDITION_DAMAGED` | `order.condition_note` present | ESCALATED |
| `R9_ELIGIBLE_STANDARD_REFUND` | All above rules pass | APPROVED |
| `R10_HIGH_FRAUD_RISK` | `customer.fraud_risk = HIGH` | ESCALATED |

The `policy_node` calls `evaluate_order_policy()`, locks the result into `AgentState.decision`, and then emits a `guardrail.lock` trace event. The `response_node` receives this locked decision as a fact — it has no mechanism to change it.

### 2.4 Adversarial Safety (Prompt Injection Defense)

`app/agent/guardrails.py` scans every incoming message against 35 regex patterns before any LLM call. Pattern categories:

- **Override directives** — "ignore previous instructions", "override policy"
- **Persona hijacking** — "you are now", "act as", "pretend you"
- **Privilege escalation** — "admin mode", "developer access", "system override"
- **Jailbreak prefixes** — "DAN", "JAILBREAK", "hypothetically speaking"
- **Role assertion** — "I am the system", "as the AI developer"

If risk is `HIGH` → `block_node` fires. If `MEDIUM` → logged as warning but processing continues (policy engine still cannot be overridden).

### 2.5 Multi-Provider LLM

`app/agent/providers.py` implements a unified interface with three backends:

```python
class LLMProvider(Protocol):
    async def extract_intent(message: str, email: str | None) -> ProviderResult[ExtractedIntent]: ...
    async def compose_reply(context: dict) -> ProviderResult[str]: ...
```

| `LLM_PROVIDER` | Model | Free? | Notes |
|---|---|---|---|
| `gemini` | gemini-2.0-flash | ✅ 1M tokens/day | Default |
| `groq` | llama-3.3-70b-versatile | ✅ Generous | Fast inference |
| `openai` | gpt-4o-mini | ❌ Paid | Optional |
| `mock` | Local heuristic | ✅ Free | For testing |

Both `extract_intent` and `compose_reply` have heuristic fallbacks — the system degrades gracefully if all providers fail.

---

## 3. API Reference

### `POST /api/chat`

Primary endpoint. Runs the full LangGraph state machine and returns the result.

**Request schema:**
```json
{
  "conversation_id": "string | null",
  "customer_email": "email | null",
  "message": "string (required)"
}
```

**Response schema:**
```json
{
  "conversation_id": "uuid",
  "assistant_message": "string",
  "decision": "APPROVED | DENIED | ESCALATED | NEEDS_INFO",
  "triggered_rules": ["R9_ELIGIBLE_STANDARD_REFUND"],
  "needs_escalation": false,
  "injection_detected": false,
  "trace": [
    {
      "id": 1,
      "step": "intake",
      "title": "Customer message received",
      "severity": "info",
      "detail": {},
      "created_at": "ISO8601"
    }
  ]
}
```

### `GET /api/events/{conversation_id}`

Server-Sent Events stream. Each event is broadcast as:
```
event: trace
data: {"id":1,"step":"guardrail","title":"...","severity":"info","detail":{}}
```

### `GET /api/health`
```json
{"status": "ok", "llm_provider": "gemini", "provider_configured": true, "db": "connected"}
```

### `GET /api/conversations`
Returns `ConversationSummary[]` ordered by `updated_at DESC`.

---

## 4. Data Model

### 4.1 Synthetic CRM

`backend/app/data/synthetic_crm.json` — 15 customers, 31 orders designed to exercise all 10 policy rules:

| Customer | Email | Fraud Risk | Orders |
|---|---|---|---|
| Asha Rao | asha.rao@example.com | LOW | ORD-1001 (eligible), ORD-1002 (final sale) |
| Marcus Lee | marcus.lee@example.com | LOW | ORD-1003 ($720 — escalates R4) |
| Owen Kim | owen.kim@example.com | HIGH | ORD-1031 (triggers R10) |
| + 12 others | — | various | covers R1, R3, R5, R6, R7, R8 |

### 4.2 Database Schema

**SQLAlchemy 2.0 ORM — SQLite (dev) / PostgreSQL (prod)**

```
customers          orders             conversations
─────────────      ──────────────     ─────────────────
id (PK)       ←── customer_id        id (PK)
name               id (PK)           customer_email
email              sku               status
loyalty_tier       item_name         latest_message
account_age_days   category          created_at
total_spent        price             updated_at
fraud_risk         purchase_date
                   delivery_date     messages
                   final_sale        ─────────
                   returned          id (PK)
                   status            conversation_id (FK)
                   condition_note    role
                                     content
refund_requests    trace_events      created_at
────────────────   ────────────────
id (PK)            id (PK)          escalations
conversation_id    conversation_id  ───────────
customer_id        step             id (PK)
order_id           title            conversation_id
decision           detail (JSON)    order_id
reason             severity         reason
injection_detected created_at       created_at
created_at
                   evaluation_runs  (Phase 4)
                   ───────────────
                   id (PK, UUID)
                   dataset_path
                   sample_count
                   faithfulness
                   answer_relevancy
                   context_precision
                   composite_score
                   overall_pass
                   status
                   created_at
```

---

## 5. Phase Roadmap

### Phase 1 — LangGraph ✅ Complete
Replace linear `runner.py` with a `StateGraph`. 11 nodes, 3 conditional edges, full trace continuity.

### Phase 2 — MCP Servers 🔧 Implemented (stub)
`mcp_servers/crm_server/` and `mcp_servers/policy_server/` expose tools as Model Context Protocol endpoints. Enabled via `TOOL_MODE=mcp`. Currently disabled — enable by running servers and flipping env var.

### Phase 3 — RAG Pipeline 🔧 Implemented (gated)
`app/rag/retriever.py` — ChromaDB + `sentence-transformers/all-MiniLM-L6-v2`. Policy document split by `##` headings into semantic chunks. Top-K retrieved per query and injected into `response_node` compose context. Enable via `RAG_ENABLED=true` after running `scripts/index_rag.py`.

### Phase 4 — Evaluation 🔧 Implemented
`evaluation/run_eval.py` with 10-sample golden dataset (`evaluation/datasets/golden_v1.json`). Metrics: decision accuracy, answer relevancy (heuristic), faithfulness proxy. Run: `python evaluation/run_eval.py --smoke`.

### Phase 5 — Observability 🔧 Implemented (gated)
`app/observability/tracing.py` — Langfuse distributed tracing + OpenTelemetry FastAPI/SQLAlchemy instrumentation. Enable by setting `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` (free at cloud.langfuse.com).

### Phase 6 — Multi-Agent 🔧 Implemented (gated)
`app/agent/multi_agent/supervisor.py` — Supervisor pattern with Policy, Retrieval, Support, and Evaluation worker agents. Enable via `AGENT_ARCHITECTURE=multi`.

### Phase 7 — CI/CD ✅ Complete
`.github/workflows/ci.yml` — 5 GitHub Actions jobs: pytest, ruff lint, TypeScript typecheck, evaluation smoke test, Docker build verification.

---

## 6. Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| API Framework | FastAPI | 0.115 | Async HTTP API, SSE streaming |
| Agent Orchestration | LangGraph | 0.2+ | State machine graph |
| LLM Abstraction | LangChain Core | 0.3+ | Provider interface |
| ORM | SQLAlchemy | 2.0 | Type-safe DB access |
| Database (dev) | SQLite | — | Zero-infrastructure local |
| Database (prod) | PostgreSQL | 15+ | Via `DATABASE_URL` swap |
| LLM: Primary | Gemini 2.0 Flash | — | Free 1M tokens/day |
| LLM: Fallback | Groq Llama-3.3-70b | — | Fast, free tier |
| Vector Store | ChromaDB | 0.5+ | Local persistent (Phase 3) |
| Embeddings | sentence-transformers | 3.0+ | all-MiniLM-L6-v2, 22MB local |
| Observability | Langfuse | 2.0+ | LLM-aware distributed tracing |
| Telemetry | OpenTelemetry | 1.25+ | HTTP + DB spans |
| Validation | Pydantic v2 | 2.7+ | Request/response schemas |
| Frontend | Next.js 16 + React 19 | — | Streaming UI |
| Styling | Vanilla CSS (design tokens) | — | Indigo dark system |
| Animations | Motion (Framer) | 12+ | Micro-animations |
| Icons | Lucide React | — | Consistent iconography |
| Containerization | Docker + Compose | — | Single-command deployment |
| CI | GitHub Actions | — | 5-job pipeline |
| Testing | pytest + pytest-asyncio | 8.x | 56 deterministic tests |
| MCP | FastMCP | 0.4+ | Protocol servers (Phase 2) |

---

## 7. Deployment

### Development (Single Command)
```bash
cp .env.example .env   # add your Gemini or Groq key
docker compose up --build
# Frontend: http://localhost:3000
# API:      http://localhost:8000
# Docs:     http://localhost:8000/docs
```

### Production Checklist
- [ ] Set `DATABASE_URL` to PostgreSQL connection string
- [ ] Set `LLM_PROVIDER` + API key
- [ ] Set `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` for tracing
- [ ] Run `scripts/seed_db.py` once after first boot
- [ ] If using RAG: `RAG_ENABLED=true` and run `scripts/index_rag.py`
- [ ] Set `FRONTEND_ORIGIN` to your production domain

### Environment Variables (Complete Reference)

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini` \| `groq` \| `openai` \| `mock` |
| `GEMINI_API_KEY` | — | Required if `LLM_PROVIDER=gemini` |
| `GROQ_API_KEY` | — | Required if `LLM_PROVIDER=groq` |
| `DATABASE_URL` | SQLite | Connection string |
| `BUSINESS_TODAY` | `2025-01-15` | Fixed reference date for demo |
| `AGENT_MODE` | `graph` | `graph` \| `legacy` |
| `TOOL_MODE` | `local` | `local` \| `mcp` |
| `AGENT_ARCHITECTURE` | `single` | `single` \| `multi` |
| `RAG_ENABLED` | `false` | Enable ChromaDB retrieval |
| `LANGFUSE_PUBLIC_KEY` | — | Langfuse cloud public key |
| `LANGFUSE_SECRET_KEY` | — | Langfuse cloud secret key |

---

## 8. Testing

```bash
cd backend
python -m pytest tests/ -v
# 56 tests — all deterministic (no LLM, no network, no randomness)
```

### Test Coverage

| Test File | Count | What It Tests |
|---|---|---|
| `tests/test_policy.py` | 56 | All 10 rules × boundary conditions |

All 56 tests use `mock` provider, in-memory SQLite, and a fixed `BUSINESS_TODAY`. They are idempotent and run in under 3 seconds.

---

## 9. Security Design

### Threat Model

| Threat | Mitigation |
|---|---|
| Prompt injection via customer message | 35-pattern lexical scanner blocks HIGH-risk before LLM |
| LLM decision manipulation | Policy engine is pure Python — LLM only writes prose |
| Data exfiltration via message | Scanner + rate limiting (production) |
| Cross-customer order access | `R6_EMAIL_MISMATCH` enforced deterministically |
| Replay / double-return | `R3_ALREADY_RETURNED` checked from DB state |

### Key Invariants
1. `policy_node` runs BEFORE `response_node` — always
2. `response_node` receives `decision` as a read-only fact
3. `injection_detected=True` is always recorded in `RefundRequest.injection_detected`
4. All LLM calls have a heuristic fallback — no request can fail due to provider outage

---

*Generated by Andromeda v2.0.0*
