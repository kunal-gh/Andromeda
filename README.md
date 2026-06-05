# Andromeda Enterprise AI Support Platform
### *State-Machine Orchestrated LangGraph Engine & Deterministic Guardrail Node*

[![Status: Production](https://img.shields.io/badge/Status-Live_Production-10b981?style=for-the-badge&logo=vercel)](https://andromeda-eight-vert.vercel.app)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-Passing-3b82f6?style=for-the-badge&logo=githubactions&logoColor=white)](#)
[![Engine](https://img.shields.io/badge/Orchestration-LangGraph_v0.2-1c1c1c?style=for-the-badge&logo=langchain)](#)
[![Python](https://img.shields.io/badge/Python-3.12-4584b6?style=for-the-badge&logo=python&logoColor=white)](#)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](#)

---

> [!IMPORTANT]
> ### 🌌 LIVE PRODUCTION DEPLOYMENT
> The platform is fully deployed and active. You can access the live support console and admin reasoning dashboard directly at:
> 🔗 **[https://andromeda-eight-vert.vercel.app](https://andromeda-eight-vert.vercel.app)**
> 
> *All refund processing, prompt injection guardrails, database tools, policy rules, and real-time Server-Sent Events (SSE) telemetry tracing can be evaluated live via this public URL.*

---

## 📖 Executive Overview

**Andromeda** is a production-grade, state-machine-driven AI Agent Platform designed specifically for high-risk corporate workflows. The platform automates the evaluation, auditing, and resolution of e-commerce refund requests according to strict business policies.

In corporate customer support, stochastic AI agents built on naive "chatbot" loops present extreme liability (e.g., hallucinatory policy drift approving invalid refunds, infinite tool-calling loops, and prompt injection exploits). Andromeda solves this by establishing a strict architectural boundary: **Generative Comprehension is completely decoupled from Deterministic Policy Enforcement**.

The Large Language Model (LLM) is used purely as a translation layer—translating natural language into structured JSON schemas, and formatting final empathetic replies. The actual business decision (`APPROVED`, `DENIED`, or `ESCALATED`) is evaluated by a hardcoded Python rules engine and locked into a relational database before the LLM ever composes a response. The LLM has zero agency over database transactions and cannot alter the decision.

---

## 🏛️ System Architecture

The following diagram maps the macro-topology of the platform, showing how request payloads transition from the client through security guardrails, LangGraph state machine orchestrators, Model Context Protocol (MCP) tool boundaries, and the deterministic policy engine.

```mermaid
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'fontSize': '15px',
    'fontFamily': 'Space Grotesk, Inter, system-ui, sans-serif',
    'primaryColor': '#0f172a',
    'primaryTextColor': '#f8fafc',
    'primaryBorderColor': '#38bdf8',
    'lineColor': '#64748b',
    'secondaryColor': '#1e293b',
    'tertiaryColor': '#0f172a'
  }
}}%%
graph TD
    subgraph ClientPlane["🖥️ CLIENT PLANE (Next.js 15 / React 19)"]
        UI["Support Console UI<br/>(Monochrome Glassmorphic SPA)"]
        Telemetry["SSE Trace Receiver<br/>(Real-time State Observability)"]
    end

    subgraph APIGateway["🛡️ API GATEWAY (FastAPI / Serverless)"]
        ChatEndpoint["POST /api/chat<br/>(Pipeline Entry)"]
        SSEEndpoint["GET /api/conversations/id/events<br/>(Heartbeat Trace Stream)"]
        HealthEndpoint["GET /api/health<br/>(Self-Diagnosis Endpoint)"]
    end

    subgraph LangGraphEngine["🧠 ORCHESTRATION PLANE (LangGraph Cyclic State Machine)"]
        Ingest["1. Ingest Node<br/>(Session Loader)"]
        Guard["2. Guardrail Node<br/>(35 Prompt Injection Regexes)"]
        Extractor["3. LLM Extraction Node<br/>(Intent / ID JSON Parser)"]
        Retrieval["4. RAG Retrieval Node<br/>(Policy Context Lookup)"]
        Tools["5. MCP Tools Node<br/>(JSON-RPC CRM Lookup)"]
        Policy["6. Policy Node<br/>(10 Python Refund Rules)"]
        Block["7. Block Node<br/>(Immediate Denial State)"]
        NeedsInfo["8. Needs Info Node<br/>(Early Exit Input Request)"]
        Handoff["9. Human Handoff Node<br/>(Manual Escalation Queue)"]
        Response["10. Response Node<br/>(LLM Style Composer)"]
        Persistence["11. Persistence Node<br/>(State/Trace DB Commit)"]
    end

    subgraph MCPPlane["🔌 MODEL CONTEXT PROTOCOL (MCP Tool Boundary)"]
        MCPClient["MCP stdio Client<br/>(JSON-RPC Protocol Manager)"]
        CRMServer["CRM MCP Server<br/>(Customer/Order DB Isolation)"]
    end

    subgraph LLMPlane["☁️ INFERENCE PLANE (Multi-Provider Adapter)"]
        Gemini["Gemini 2.0 Flash<br/>(Primary Model)"]
        Groq["Llama-3.3-70b<br/>(Uptime Fallback)"]
        OpenAI["GPT-4o-mini<br/>(Alternate Adapter)"]
    end

    %% Client and Gateway Relations
    UI -->|REST Payload| ChatEndpoint
    UI -->|Subscribe| SSEEndpoint
    SSEEndpoint -->|SSE Events| Telemetry

    %% Gateway and Graph Relations
    ChatEndpoint --> Ingest
    Ingest --> Guard
    
    %% Graph Transitions
    Guard -->|Clean Input| Extractor
    Guard -->|Injection Detected| Block
    
    Extractor --> Retrieval
    Retrieval --> Tools
    Tools --> Policy
    
    Policy -->|Missing Data| NeedsInfo
    Policy -->|Approved/Denied| Response
    Policy -->|Requires Audit| Handoff
    
    Block --> Response
    NeedsInfo --> Response
    Handoff --> Response
    
    Response --> Persistence
    Persistence -->|Emit Event| SSEEndpoint

    %% Graph and Tool Boundary
    Tools <-->|stdio JSON-RPC| MCPClient
    MCPClient <--> CRMServer

    %% Graph and Inference
    Extractor <--> Gemini
    Response <--> Gemini
    LLMPlane === Gemini
    LLMPlane === Groq
    LLMPlane === OpenAI

    %% Styling classes
    classDef plane fill:#090d16,stroke:#0ea5e9,stroke-width:2px,color:#f8fafc;
    classDef node fill:#1e293b,stroke:#475569,stroke-width:1px,color:#f1f5f9;
    classDef highlighted fill:#0369a1,stroke:#38bdf8,stroke-width:2px,color:#f0f9ff;
    classDef database fill:#14532d,stroke:#22c55e,stroke-width:1px,color:#f0fdf4;
    classDef error fill:#7f1d1d,stroke:#ef4444,stroke-width:1px,color:#fef2f2;

    class ClientPlane,APIGateway,LangGraphEngine,MCPPlane,LLMPlane plane;
    class UI,Telemetry,ChatEndpoint,SSEEndpoint,HealthEndpoint,Ingest,Guard,Extractor,Retrieval,Tools,Block,NeedsInfo,Handoff,Response,Persistence,MCPClient,Gemini,Groq,OpenAI node;
    class Policy highlighted;
    class CRMServer database;
```

---

## ⚡ Core Technical Accomplishments

To satisfy the engineering expectations of enterprise technical recruiters, the system implements:

*   **Stateful AI Orchestration (`LangGraph`)**: Uses a strict 11-node cyclic state machine to manage the conversation lifecycle, state persistence, and deterministic action execution. The LLM never drives the graph; it only operates as a node within it.
*   **Model Context Protocol (MCP)**: Isolates database and tool access using Anthropic's standardized MCP. Tools run as independent processes communicating over standard stdio JSON-RPC, completely hiding the CRM database schema from the LLM.
*   **Immutable Backend Decision Lock**: Once computed by the rule engine, the final refund status (`APPROVED`, `DENIED`, `ESCALATED`) is immediately written to the relational database. The LLM is then invoked to format the response but has no pathway to alter the transaction record.
*   **Pre-LLM Adversarial Scanner**: Scans all customer input against **35 prompt injection patterns** across 6 threat categories (Instruction Overrides, System Prompt Extraction, Policy Bypass, Authority Spoofing, Persona Manipulation, and Hypothetical Framing) before the LLM is invoked.
*   **Self-Healing Provider Failover**: Implements a custom adapter pattern supporting OpenAI, Google Gemini, and Groq SDKs. If an API key is missing or a provider endpoint crashes, the gateway automatically falls back to secondary providers.
*   **Real-time SSE Observability Dashboard**: Built a dark monochrome glassmorphic Next.js interface that subscribes to an async Server-Sent Events (SSE) stream. As the backend executes, it streams granular JSON trace spans representing database hits, guardrail flags, policy calculations, and LLM confidence scores.
*   **Automated Evaluation Pipeline**: Integrates a custom evaluation framework in CI/CD that runs a scoring script measuring Answer Faithfulness, Context Precision, and F1 routing accuracy against a golden dataset.

---

## 🔄 The 11-Node LangGraph Lifecycle

1.  **Ingest Node**: Loads the request and binds the customer email context.
2.  **Guardrail Node**: Scans user input for prompt injection vectors.
3.  **Extraction Node**: Extracts structured intent parameters using LLM parsing.
4.  **Retrieval Node**: RAG-based context lookup from the corporate policy.
5.  **Tools Node**: Queries the CRM database via the Model Context Protocol (MCP) server.
6.  **Policy Node**: Evaluates eligibility deterministically using the Python rule engine.
7.  **Block Node**: Hardcoded state mapping for flagged adversarial inputs.
8.  **Needs Info Node**: Requests missing transaction details from the customer.
9.  **Human Handoff Node**: Escalates cases requiring manual review.
10. **Response Node**: Stylistic response composer using read-only decision contexts.
11. **Persistence Node**: Writes audit events and final states to the SQLite store.

---

## 📊 Evaluation & Verification Metrics

Prompts and agent routing are evaluated with software-engineering rigor. The repository contains a suite of **56 automated unit and integration assertions** that physically verify system parameters:

*   **Boundary Conditions**: Verifies exclusive date comparisons (exactly 30 days is approved, 31 days is denied) and price thresholds (exactly $500 is approved, $500.01 is escalated).
*   **Security Guardrails**: Tests the guardrail scanner against all 35 prompt injection sequences, verifying correct risk classification (LOW, MEDIUM, HIGH).
*   **Evaluation Metrics**: Context Precision (RAG retrieval accuracy), Answer Faithfulness (factuality checks), and F1 Decision Score.

### Execution Framework
```
[CI Workflow] ──► Static Linting (Ruff) ──► Pytest (56 Assertions) ──► golden_v1.json Evaluation
```

---

## 📚 Deep Technical Documentation

For an exhaustive, 60+ page technical reference guide detailing the complete codebase, algebraic decision formulations, mathematical evaluation metrics (Faithfulness, Context Precision, F1 Routing), threat models, database schemas, and architectural trade-offs:

👉 **[Read the Master DOCUMENTATION.md Specification](./DOCUMENTATION.md)**

---

*Designed and Engineered for Enterprise Scale. Submitted for the Andromeda Platform Evaluation.*
