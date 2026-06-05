<div align="center">
  <img src="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/zap.svg" width="80" alt="Andromeda Logo">
  
  <h1 align="center">Andromeda</h1>
  <p align="center">
    <strong>Production-Grade, Multi-Agent Enterprise Customer Support Architecture</strong>
  </p>

  <p align="center">
    <a href="https://andromeda-eight-vert.vercel.app"><img src="https://img.shields.io/badge/Status-Live_on_Vercel-000000?style=for-the-badge&logo=vercel" alt="Deployed on Vercel"></a>
    <img src="https://img.shields.io/badge/LangGraph-State_Machine-1c1c1c?style=for-the-badge&logo=langchain" alt="LangGraph">
    <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/Next.js_16-Frontend-000000?style=for-the-badge&logo=next.js" alt="Next.js">
    <img src="https://img.shields.io/badge/MCP-Tooling-FF4B4B?style=for-the-badge" alt="MCP Servers">
  </p>
</div>

---

## 📖 Executive Summary

**Andromeda** is a highly resilient, multi-agent AI system designed to handle complex enterprise customer support operations. By combining deterministic policy enforcement with the semantic reasoning capabilities of Large Language Models (LLMs), Andromeda automates customer workflows—specifically refund processing—while rigorously protecting against hallucination, prompt injection, and out-of-policy decisions.

This project was engineered to demonstrate modern **AI Platform Engineering** and **Applied GenAI Architectures**, focusing heavily on state orchestration, observability, and robust fallback mechanisms rather than naive prompt wrapping. 

---

## ⚡ Key Engineering Achievements

- **Stateful AI Orchestration (`LangGraph`)**: Implemented an 11-node, cyclic `StateGraph` that manages the conversation lifecycle, tool execution, and deterministic guardrails.
- **Model Context Protocol (`MCP`) Integration**: Extracted CRM and Policy lookups into isolated, standardized MCP servers, decoupling tools from the core inference engine.
- **Hybrid Routing (Deterministic + Stochastic)**: Built a pipeline where LLMs generate intent and extract entities, but *execution* and *policy verification* are strictly deterministic.
- **Agent Observability (`Langfuse` + `OpenTelemetry`)**: Instrumented the entire execution pipeline with OpenTelemetry standards, pushing traces to Langfuse for granular latency and cost analysis.
- **Human-in-the-Loop (HITL)**: Programmatic `ESCALATE` transitions allow human agents to take over high-risk or high-value cases.
- **Serverless Edge Deployment**: Seamlessly deployed on **Vercel** with Next.js 16 (App Router) and FastAPI.

---

## 🏗️ System Architecture

Andromeda completely abandons the "black-box" agent approach. Instead, it relies on a highly transparent state machine where the LLM is just one node in a larger computational graph.

```mermaid
graph TD
    %% Styling
    classDef client fill:#f0f4f8,stroke:#1e293b,stroke-width:2px,color:#1e293b
    classDef api fill:#e2e8f0,stroke:#334155,stroke-width:2px,color:#1e293b
    classDef graph fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e40af
    classDef llm fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e
    classDef data fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#166534
    
    %% Nodes
    Client[Next.js 16 Frontend / UI]:::client
    FastAPI[FastAPI Gateway]:::api
    
    subgraph "LangGraph State Machine Orchestrator"
        Input[Ingestion Node]:::graph
        Guardrail[Guardrail Check]:::graph
        Policy[Policy Evaluation]:::graph
        Router[Semantic Router Node]:::graph
        Decision[Decision Execution]:::graph
    end
    
    subgraph "Inference Layer"
        Gemini[Primary: Gemini 2.0 Flash]:::llm
        Llama[Fallback: Llama-3.3-70b]:::llm
    end
    
    subgraph "Infrastructure & Tooling"
        SQLite[(SQLite / PostgreSQL)]:::data
        MCP_CRM[MCP CRM Server]:::api
        MCP_Policy[MCP Policy Server]:::api
        Chroma[(ChromaDB RAG)]:::data
    end

    %% Edges
    Client -->|REST| FastAPI
    FastAPI --> Input
    Input --> Guardrail
    Guardrail -->|Injection Detected| Decision
    Guardrail -->|Clean| Router
    
    Router --> Gemini
    Gemini -.->|Timeout / Error| Llama
    Llama --> Policy
    Gemini --> Policy
    
    Policy --> MCP_CRM
    Policy --> MCP_Policy
    Policy --> Decision
    Decision --> FastAPI
    
    MCP_Policy -.-> Chroma
```

---

## 💻 Tech Stack in Depth

### Frontend
- **Framework**: Next.js 16 (App Router)
- **Styling**: Vanilla CSS with CSS Modules, strict glassmorphism aesthetic.
- **State**: React 19 Server Components.

### Backend & AI
- **API Framework**: FastAPI (Uvicorn, Pydantic validation).
- **AI Orchestration**: LangGraph, LangChain Core.
- **Primary Inference**: Gemini 2.0 Flash (via `google-genai`).
- **Fallback Inference**: Groq Llama-3.3-70b (ultra-low latency fallback).
- **Tooling Standardization**: Model Context Protocol (MCP).

### Data & Observability
- **Relational Data**: SQLAlchemy 2.0 (SQLite for `/tmp` Vercel dev, Postgres ready).
- **Vector Storage**: ChromaDB (Phase 3 RAG integration).
- **Tracing**: OpenTelemetry (OTEL) + Langfuse.

---

## 🛠️ Local Development & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/kunal-gh/Andromeda.git
cd Andromeda
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the `/backend` directory:
```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
LANGFUSE_PUBLIC_KEY=your_langfuse_pk
LANGFUSE_SECRET_KEY=your_langfuse_sk
LANGFUSE_HOST=https://us.cloud.langfuse.com
```

### 4. Run the Stack
Run the FastAPI backend:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
Run the Next.js frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 🗺️ Product Vision & Engineering Roadmap

Andromeda is designed to scale. While the current implementation successfully handles deterministic refund workflows via Vercel deployments, the architectural scope includes the following pipeline upgrades:

### Phase 4: Agent Evaluation (Pending)
- **Frameworks**: Integration with `RAGAS` and `DeepEval`.
- **Metrics**: Automated test suites for Answer Relevancy, Faithfulness, and Context Precision.

### Phase 5: Cloud Native Migration (Pending)
- **Vector Stores**: Transitioning local ChromaDB to highly-available **Qdrant** or Pinecone clusters.
- **Orchestration**: Migrating from Vercel Serverless to AWS ECS / GCP Cloud Run to support persistent WebSocket connections and heavy long-running agent threads.
- **Tracing**: Implementing **Phoenix** for LLM tracing alongside the existing OpenTelemetry/Langfuse setup.

---

<p align="center">
  <i>Engineered for resilience. Built for the Enterprise.</i>
</p>