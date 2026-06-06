# Worknoon Enterprise AI Operations Platform

<div align="center">
  <img src="assets/banner.png" alt="Worknoon Banner" width="800"/>
  <p><strong>A production-ready, multi-agent customer operations platform built for 2026.</strong></p>
</div>

Worknoon is an enterprise-grade AI support platform that handles complex customer workflows using LangGraph, Model Context Protocol (MCP), Qdrant-powered hybrid RAG, and deep observability. It demonstrates a massive paradigm shift from standard "LLM wrappers" to robust, agentic architectures suitable for senior AI Engineer portfolios.

## System Capabilities

- **Multi-Agent Orchestration**: LangGraph-powered Supervisor coordinating specialized Worker agents (Policy, Support, Retrieval).
- **Decoupled Data via MCP**: FastMCP servers physically isolate the LLM from backend SQL databases for absolute security.
- **Deterministic Policy Engine**: Pure-Python rule evaluation gate ensuring zero-hallucination refunds.
- **Hybrid RAG**: Qdrant vector search combined with a NetworkX Entity-Relationship knowledge graph.
- **Automated Evaluations**: DeepEval and RAGAS integrated into CI/CD for regression testing on Faithfulness and Answer Relevancy.
- **Deep Observability**: LangFuse and OpenTelemetry tracking LLM token costs, generation latency, and DB traces.
- **Human-in-the-Loop**: Asynchronous escalation queues and adversarial testing frameworks (Red Teaming).
- **Cloud Native**: Terraform IaC for AWS ECS Fargate deployment, GitHub Actions CI/CD.

## Tech Stack

- **AI Framework**: LangGraph, LangChain, OpenAI
- **Vector Store & Graph**: Qdrant, NetworkX
- **Observability**: LangFuse, OpenTelemetry (OTLP Collector), Prometheus
- **Evaluation**: DeepEval, RAGAS
- **Backend API**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: Next.js, Radix UI, Recharts, Framer Motion
- **Deployment**: AWS (ECS, RDS, ALB), Docker, Terraform, Vercel

## Comprehensive Documentation

For an exhaustive, 50-page enterprise deep-dive into the architecture, mathematics, and operational workflows of this platform, please read the official specification:

👉 **[ENTERPRISE_DOCUMENTATION.md](ENTERPRISE_DOCUMENTATION.md)**

## Local Setup

Ensure Docker and Docker Compose are installed.

1. Clone the repository
2. Configure `.env`:
   ```bash
   cp .env.example .env
   # Add your OPENAI_API_KEY and LANGFUSE keys
   ```
3. Start the ecosystem:
   ```bash
   docker-compose up --build
   ```
4. Access the Multi-Agent Dashboard at `http://localhost:3000`

## Production Deployment

Deployment to AWS is automated via GitHub Actions (`.github/workflows/deploy.yml`). Infrastructure is managed in `infra/terraform`.

## Contact & License

Built as an advanced agentic coding project to showcase modern AI engineering patterns.
