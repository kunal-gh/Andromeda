<div align="center">
  <img src="assets/banner.png" alt="Andromeda Enterprise AI Banner" width="800" />
</div>

<h1 align="center">Andromeda: Enterprise AI Operations Platform</h1>

<div align="center">
  <strong>A production-ready, zero-hallucination Multi-Agent system architected for 2026.</strong><br><br>

  [![Live Production Console](https://img.shields.io/badge/Live_Console-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://andromeda.vercel.app/)
  [![GitHub Actions](https://img.shields.io/github/actions/workflow/status/kunal-gh/Andromeda/deploy.yml?branch=main&style=for-the-badge&logo=github)](https://github.com/kunal-gh/Andromeda/actions)
  [![Evaluations](https://img.shields.io/badge/Evaluations-DeepEval_%7C_RAGAS-8A2BE2?style=for-the-badge)](#-evaluations--quality-assurance)
  [![Observability](https://img.shields.io/badge/Observability-OpenTelemetry_%7C_LangFuse-FFA500?style=for-the-badge)](#-observability--telemetry)
  [![State Machine](https://img.shields.io/badge/Orchestrator-LangGraph-00C4B6?style=for-the-badge)](#-multi-agent-orchestration)
</div>

<br>

> **Andromeda is not an "LLM wrapper."** It is a mathematically bounded, Agentic Enterprise System. Traditional LLM-based customer support bots suffer from hallucinatory policy drift, jailbreaking vulnerabilities, and unbounded tool-loop latency. Andromeda entirely mitigates these risks by implementing a **Multi-Agent LangGraph State Machine**. The LLM operates strictly as a specialized routing node and formatting layer, while all critical business logic, API executions, and financial decisions are locked within a purely deterministic Python Policy Engine decoupled via the Model Context Protocol (MCP).

---

## 🌌 System Architecture & Data Flow

The architecture completely physically isolates the generative reasoning engine from the enterprise database. Execution is strictly routed through state-machine nodes, utilizing MCP servers to prevent direct LLM-to-SQL coupling.

<div align="center">

<img src="assets/architecture/client.png" width="60" /><br>
**1. User Interface (Next.js Dashboard)**<br>
⇩<br>
<img src="assets/architecture/gateway.png" width="60" /><br>
**2. API Edge Gateway (FastAPI + OpenTelemetry Tracing)**<br>
⇩<br>
<img src="assets/architecture/orchestrator.png" width="60" /><br>
**3. LangGraph Orchestrator (Cyclic State Machine & Supervisor)**<br>
*Routes intent and persists memory across turns.*<br>
↙ &nbsp; &nbsp; &nbsp; ⇩ &nbsp; &nbsp; &nbsp; ↘<br>

**Decoupled MCP Execution Tier**<br>
<img src="assets/architecture/policy.png" width="50" /> &nbsp; &nbsp; <img src="assets/architecture/database.png" width="50" /> &nbsp; &nbsp; <img src="assets/architecture/telemetry.png" width="50" /><br>
**Policy Agent** | **Retrieval Agent** | **Support Agent**<br>
*(Zero-Hallucination Guardrails)* &nbsp; | &nbsp; *(Hybrid RAG: Qdrant + NetworkX)* &nbsp; | &nbsp; *(Empathetic Formatting)*<br>
⇩<br>
<img src="assets/architecture/database.png" width="60" /><br>
**4. Persistent State (AWS RDS PostgreSQL)**<br>
*Immutable Transactions, ACID Locking, Human-in-the-Loop Escalations*

</div>

---

## 🧠 Core Engineering Innovations

This repository serves as a masterclass in modern AI infrastructure. It demonstrates how to transition from fragile scripts to resilient, enterprise-grade AI operations.

### 1. Multi-Agent State Machine (LangGraph)
Standard AI agents use linear `while` loops that are prone to infinite loops and context collapse. Andromeda uses **LangGraph** to model the conversation as a Directed Cyclic Graph (DCG). 
- A central **Supervisor Agent** evaluates the user's input and dynamically routes the execution flow to specialized worker nodes (`Policy`, `Retrieval`, or `Support`).
- **State Persistence**: Memory is managed via the `MemorySaver` checkpointer. The `AgentState` schema tracks `messages`, `sender`, `locked_decision`, and `extracted_order_id`, allowing operators to pause, rewind, and branch the agent's execution state arbitrarily.

### 2. Model Context Protocol (MCP) Decoupling
Security in AI systems requires "Zero Trust." If an LLM has raw database access, a prompt injection can lead to data exfiltration. 
- Andromeda implements the **FastMCP** protocol. 
- The LLM backend is physically isolated from the SQL execution layer. Three independent MCP servers (`Worknoon-CRM`, `Worknoon-Orders`, `Worknoon-Policy`) expose tools over `stdio` streams. The LLM only receives Pydantic schemas, never executing logic directly.

### 3. Hybrid RAG (Dense Vector + Knowledge Graph)
Semantic search alone fails at relational queries (e.g., "Find all delayed orders for customers with Gold status"). Andromeda utilizes a state-of-the-art dual-retrieval pipeline:
- **Vector Search (Qdrant)**: Embeds policy documents (`sentence-transformers`) for unstructured semantic retrieval.
- **Knowledge Graph (NetworkX)**: Seeds an in-memory graph connecting `Customer` → `Order` → `Item`. 
- The `hybrid_query.py` module merges these results, providing the LLM with both contextual policy documents and exact relational state graphs.

### 4. Deep Observability & Telemetry
In a multi-agent system, debugging "why the agent said X" requires distributed tracing.
- **LangFuse**: Decorators (`@observe`) wrap every graph node, tracking prompt tokens, completion tokens, latency, and exact model payloads.
- **OpenTelemetry**: The `opentelemetry-instrumentation` suite traces the lifecycle of every request natively from the FastAPI edge, through the LangGraph execution, down to the SQLAlchemy query, aggregating all metrics into **Prometheus**.

### 5. Automated CI/CD Evaluations (LLM-as-a-Judge)
Quality assurance is guaranteed through automated evaluations integrated directly into the `.github/workflows/deploy.yml` pipeline.
- **DeepEval**: Asserts that the final generated response aligns perfectly with the retrieved policy chunks (`Faithfulness`) and directly addresses the user without verbosity (`Answer Relevancy`).
- **RAGAS**: Continuously measures the `Context Precision` and `Context Recall` of the Qdrant retrieval pipeline to detect semantic degradation.
- **If Faithfulness drops below 95%, the deployment automatically breaks.**

---

## 📐 Mathematical Formulation of Zero-Hallucination

Andromeda treats conversation routing as a Markov Decision Process (MDP). Given a conversation state $S_t = (H, C, E)$, where $H$ is chat history, $C$ is customer profile, and $E$ is extracted entities.

The **Supervisor Agent** evaluates a routing policy $\pi(S_t)$ to select the optimal subgraph node $N \in \{\text{Policy}, \text{RAG}, \text{Support}\}$.

Crucially, when the flow reaches the **Policy Engine**, it executes a deterministic step function $f(X)$ written entirely in Python:

$$ f(X) = \begin{cases} 
1 & \text{if } (X_{\text{age}} \le 30) \land (X_{\text{status}} = \text{"delivered"}) \land (X_{\text{risk}} < \theta) \\
0 & \text{otherwise} 
\end{cases} $$

The result ($1$ for Approved, $0$ for Denied) is **locked** via an ACID-compliant database transaction. The Generative LLM $G_\phi$ is strictly constrained to formatting this locked output $O$. It cannot override the math:

$$ P(\text{Response} \mid S_t, f(X)) = G_\phi(S_t \oplus \text{Lock}[f(X)]) $$

This architecture mathematically guarantees **zero hallucination** in financial decisions.

---

## 🛡️ AI Safety & Governance Guardrails

High-stakes Enterprise AI must survive adversarial environments.

| Threat Vector | Description | Andromeda Mitigation Strategy |
| :--- | :--- | :--- |
| **Prompt Injection** | User commands the LLM to ignore instructions and issue an unauthorized refund. | **State Locking.** The LLM has zero authority to issue refunds. It can only read the `locked_decision` status strictly enforced by the Python Policy Engine. |
| **Data Exfiltration** | LLM attempts to query arbitrary tables or access credentials. | **MCP Isolation.** The agent communicates via FastMCP `stdio` streams. It cannot physically access the SQLAlchemy connection pool. |
| **Context Flooding** | Attacker pastes massive amounts of text to trigger context-window collapse. | **Cyclic Pruning.** LangGraph automatically windows and truncates conversation memory before passing the context to the generative node. |
| **Hallucinated Policies** | LLM invents a fake return policy to appease an aggressive user. | **Hybrid RAG Grounding.** RAGAS evaluations ensure the context retrieved from Qdrant is the only acceptable source of truth. |
| **Systemic Fraud** | Organized attackers submit high-value refund requests under the radar. | **Escalation Queue.** Any transaction over $500 or tagged with a high fraud risk ($\theta$) is immediately routed to a PostgreSQL Human-in-the-Loop review queue. |

---

## 🚀 2026 Enterprise Engineering Roadmap

The evolution of Andromeda from a standard API to a Multi-Agent Enterprise Platform.

| Phase | Architecture Objective | Tech Stack | Status |
| :---: | :--- | :--- | :---: |
| **1** | Core Deterministic Logic & API Foundations | `FastAPI`, `SQLAlchemy`, `PostgreSQL` | ✅ |
| **2** | State Machine Migration & Orchestration | `LangGraph`, `LangChain`, `OpenAI` | ✅ |
| **3** | Secure Tool Decoupling & Isolation | `Model Context Protocol (FastMCP)` | ✅ |
| **4** | Hybrid Knowledge Retrieval Pipeline | `Qdrant`, `NetworkX`, `sentence-transformers` | ✅ |
| **5** | CI/CD Automated LLM Evaluations | `DeepEval`, `RAGAS`, `GitHub Actions` | ✅ |
| **6** | Distributed Telemetry & Tracing | `LangFuse`, `OpenTelemetry`, `Prometheus` | ✅ |
| **7** | Real-Time Operator Dashboard | `Next.js`, `Framer Motion`, `@tanstack/react-query`| ✅ |

<br>

<div align="center">
  <sub><strong>Architected by Kunal | Andromeda Enterprise AI Operations</strong></sub>
</div>
