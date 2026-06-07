# Andromeda Enterprise AI Operations Platform Architecture

## Executive Summary
Andromeda is an enterprise-grade AI operations platform built to handle complex customer support workflows. It evolves a standard deterministic pipeline into a multi-agent orchestrated state machine using LangGraph, Model Context Protocol (MCP), and Qdrant-powered RAG.

## Core Architecture

### 1. LangGraph State Machine
The core routing and decision-making is handled by a cyclic directed graph (LangGraph) instead of a linear script.
- **State Persistence**: MemorySaver checkpoints allow resuming multi-turn conversations.
- **Subgraphs**: Specialized agents (Policy, Retrieval, Support) operate as subgraphs orchestrated by a central Supervisor Agent.

### 2. Multi-Agent Topology
- **Supervisor Agent**: A fast LLM router (GPT-4o-mini) that classifies intent and delegates tasks.
- **Policy Agent**: A deterministic gate that evaluates refunds securely without LLM hallucinations.
- **Retrieval Agent**: A hybrid RAG system (Vector + Knowledge Graph) for answering FAQs.
- **Support Agent**: An empathetic response composer that adheres to strict context boundaries.

### 3. Model Context Protocol (MCP) Integration
To secure data access, tools are decoupled into local FastMCP servers:
- **Andromeda-CRM**: Handles customer profile lookups.
- **Andromeda-Orders**: Manages order lookups and refund processing.
- **Andromeda-Policy**: Executes the deterministic policy engine.
Communication occurs over stdio streams, strictly isolating backend databases from the LLM execution environment.

### 4. RAG & Knowledge Graph (Qdrant + NetworkX)
- **Qdrant**: Stores embedded policy documents and FAQs for semantic search.
- **NetworkX**: Models relationships between Customers and Orders, enabling hybrid queries that combine semantic intent with relational data.

### 5. Evaluation & Observability
- **DeepEval & RAGAS**: Automated CI/CD gates test for Faithfulness, Hallucinations, and Answer Relevancy.
- **LangFuse**: Traces LLM calls, costs, and latencies locally.
- **OpenTelemetry**: Provides distributed tracing across FastAPI and SQLAlchemy boundaries.

### 6. Safety & Human-in-the-Loop
- **Red Teaming**: Automated adversarial suites test against prompt injection and authority spoofing.
- **Human Review Queue**: Escalations are persisted in PostgreSQL, pending asynchronous manual review.

## Deployment Strategy
- **Infrastructure**: AWS ECS Fargate serverless containers for both frontend (Next.js) and backend (FastAPI), configured via Terraform IaC.
- **Image Registry**: Amazon Elastic Container Registry (ECR) for hosting private multi-stage Docker images.
- **Database**: PostgreSQL for relational CRM, orders, and audits; self-hosted Qdrant for vector embeddings.
- **CI/CD Pipeline**: GitHub Actions pipeline triggering unit tests, coverage reporting, and automated DeepEval/RAGAS evaluation suites before ECR container build, push, and zero-downtime ECS rolling service deployment.
