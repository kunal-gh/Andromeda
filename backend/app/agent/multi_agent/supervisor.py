"""
Phase 6 — Multi-Agent: Supervisor + Specialized Workers

Architecture (Supervisor pattern):
  SupervisorAgent routes tasks to:
    ├── PolicyAgent       — deterministic rule evaluation
    ├── RetrievalAgent    — ChromaDB RAG queries
    ├── SupportAgent      — customer response composition
    └── EvaluationAgent   — scores drafts before customer delivery

In Phase 1 (current), the supervisor simply calls the single LangGraph.
Phase 6 enables AGENT_ARCHITECTURE=multi in .env to activate all workers.

Each worker is a separate async function that can be run in parallel
(via asyncio.gather) for latency-critical paths.
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings


# ── Worker: Policy Agent ──────────────────────────────────────────────────

async def policy_agent(order_id: str, customer_email: str, db) -> dict[str, Any]:
    """
    Deterministic policy evaluation worker.
    Wraps evaluate_refund_policy() — zero LLM cost, pure Python.
    """
    from app.agent.tools import evaluate_refund_policy
    return evaluate_refund_policy(db, order_id, customer_email)


# ── Worker: Retrieval Agent ───────────────────────────────────────────────

async def retrieval_agent(query: str) -> list[dict]:
    """
    Semantic policy retrieval worker.
    Returns top-K relevant policy chunks from ChromaDB.
    Silently returns [] when RAG is disabled.
    """
    settings = get_settings()
    if not settings.rag_enabled:
        return []
    try:
        from app.rag.retriever import retrieve_relevant_policy
        return retrieve_relevant_policy(query)
    except Exception:
        return []


# ── Worker: Support Agent ─────────────────────────────────────────────────

async def support_agent(context: dict[str, Any]) -> str:
    """
    Response composition worker.
    Uses the LLM to write the customer-facing reply given locked decision context.
    """
    from app.agent.providers import get_provider, template_reply
    provider = get_provider()
    try:
        result = await provider.compose_reply(context)
        return result.value
    except Exception:
        return template_reply(context)


# ── Worker: Evaluation Agent ──────────────────────────────────────────────

async def evaluation_agent(draft: str, context: dict[str, Any]) -> dict[str, Any]:
    """
    Draft quality scoring worker (Phase 6 gate).

    Scores the draft response on:
      - faithfulness:     Does it accurately reflect the locked decision?
      - tone:             Is the language empathetic and professional?
      - completeness:     Does it address all aspects of the customer request?

    Returns the draft unchanged if the score passes. If below threshold,
    requests a retry from support_agent (max 2 retries).
    """
    # Heuristic scoring (full LLM-as-judge in Phase 6)
    decision = context.get("decision", "")
    draft_lower = draft.lower()

    # Faithfulness check: decision keyword must appear
    decision_keywords = {
        "APPROVED": ["approved", "approve", "refund"],
        "DENIED": ["denied", "unable", "not eligible", "unfortunately"],
        "ESCALATED": ["escalat", "review", "specialist", "team"],
        "NEEDS_INFO": ["order number", "provide", "could you"],
    }
    keywords = decision_keywords.get(decision, [])
    faithfulness = 1.0 if any(kw in draft_lower for kw in keywords) else 0.5

    # Tone check: no aggressive language
    aggressive = ["cannot", "refuse", "reject", "denied"]
    tone = 0.7 if any(w in draft_lower for w in aggressive) else 1.0

    # Completeness: minimum length
    completeness = min(1.0, len(draft.split()) / 30)

    composite = faithfulness * 0.5 + tone * 0.3 + completeness * 0.2

    return {
        "draft": draft,
        "score": composite,
        "pass": composite >= 0.70,
        "metrics": {
            "faithfulness": faithfulness,
            "tone": tone,
            "completeness": completeness,
        },
    }


# ── Supervisor ────────────────────────────────────────────────────────────

async def supervisor_run(
    order_id: str | None,
    customer_email: str | None,
    message: str,
    db,
    max_eval_retries: int = 2,
) -> dict[str, Any]:
    """
    Supervisor orchestrator — coordinates all workers.

    In AGENT_ARCHITECTURE=single mode: delegates directly to the LangGraph.
    In AGENT_ARCHITECTURE=multi mode: fans out workers in parallel then aggregates.

    Currently always uses single mode — multi activates in Phase 6.
    """
    settings = get_settings()

    if settings.agent_architecture == "single" or not order_id:
        # Single-agent path (Phase 1 default): handled by LangGraph runner
        raise NotImplementedError(
            "supervisor_run in multi mode — use runner.run_refund_agent for single mode"
        )

    import asyncio

    # ── Fan-out: run Policy + Retrieval in parallel ────────────────
    policy_task = policy_agent(order_id, customer_email, db)
    retrieval_task = retrieval_agent(message)

    policy_result, retrieval_chunks = await asyncio.gather(policy_task, retrieval_task)

    compose_context = {
        "decision": policy_result["decision"],
        "order_id": order_id,
        "customer_email": customer_email,
        "triggered_rules": policy_result["triggered_rules"],
        "explanation_facts": policy_result["explanation_facts"],
        "risk_flags": policy_result["risk_flags"],
        "requires_human_review": policy_result["requires_human_review"],
        "policy_context": [c["text"] for c in retrieval_chunks],
        "injection_detected": False,
    }

    # ── Support Agent → Evaluation Agent loop ──────────────────────
    for attempt in range(max_eval_retries + 1):
        draft = await support_agent(compose_context)
        eval_result = await evaluation_agent(draft, compose_context)

        if eval_result["pass"] or attempt == max_eval_retries:
            return {
                "decision": policy_result["decision"],
                "assistant_message": draft,
                "triggered_rules": policy_result["triggered_rules"],
                "explanation_facts": policy_result["explanation_facts"],
                "confidence": policy_result.get("confidence", 0.95),
                "eval_score": eval_result["score"],
                "eval_attempts": attempt + 1,
            }

    return {
        "decision": policy_result["decision"],
        "assistant_message": draft,
        "triggered_rules": policy_result["triggered_rules"],
        "explanation_facts": policy_result["explanation_facts"],
        "confidence": 0.5,
    }
