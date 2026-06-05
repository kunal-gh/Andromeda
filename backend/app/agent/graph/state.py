"""
AgentState — The shared state object passed between all LangGraph nodes.

TypedDict total=False allows partial updates from each node (each node only
returns the keys it modifies, not the full state).

Runtime objects (db session, trace handles) are passed via
config["configurable"] to avoid LangGraph checkpoint serialization issues.
"""

from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """
    LangGraph state for the Andromeda agent.
    Inherits from TypedDict so LangGraph can read its schema.

    Field groups:
      Input        — set at entry point by runner.py
      Safety       — guardrail_node output
      Extraction   — extraction_node output
      RAG          — retrieval_node output (Phase 3, defaults to empty)
      Tools        — tool_node output
      Policy       — policy_node output
      Response     — response_node output
      Routing      — flags used by edge routing functions

    NOTE: db_session and lf_trace are NOT here — they travel via
    config["configurable"] so LangGraph checkpointing never tries to
    serialize a SQLAlchemy Session or other non-picklable object.
    """

    # ── Input ──────────────────────────────────────────────────────
    conversation_id: str
    customer_email: Optional[str]
    raw_message: str

    # ── Safety ────────────────────────────────────────────────────
    injection_detected: bool
    injection_risk: str           # "LOW" | "MEDIUM" | "HIGH"
    injection_patterns: list[str]

    # ── Extraction ────────────────────────────────────────────────
    extracted_order_id: Optional[str]
    extracted_reason: Optional[str]
    extracted_sentiment: Optional[str]
    extracted_intent_type: str    # "refund_request" | "faq" | "other"

    # ── RAG (Phase 3) ─────────────────────────────────────────────
    retrieved_policy_chunks: list[str]
    retrieval_scores: list[float]

    # ── Tools ─────────────────────────────────────────────────────
    customer_data: Optional[dict[str, Any]]
    order_data: Optional[dict[str, Any]]
    policy_text: str
    missing_fields: list[str]

    # ── Policy ────────────────────────────────────────────────────
    decision: str                 # "APPROVED" | "DENIED" | "ESCALATED" | "NEEDS_INFO"
    triggered_rules: list[str]
    confidence: float
    risk_flags: list[str]
    needs_escalation: bool
    explanation_facts: list[str]
    requires_human_review: bool

    # ── Response ──────────────────────────────────────────────────
    assistant_message: str

    # ── Routing / Debug ───────────────────────────────────────────
    error: Optional[str]
    node_history: list[str]


def initial_state(
    conversation_id: str,
    customer_email: Optional[str],
    raw_message: str,
    db: Any,  # kept for runner.py backward compat, but no longer put in state
) -> AgentState:
    """Build a clean initial AgentState for a new request.

    db is accepted but NOT stored in state — it goes into
    config["configurable"]["db_session"] in runner.py instead.
    """
    return AgentState(
        conversation_id=conversation_id,
        customer_email=customer_email,
        raw_message=raw_message,
        injection_detected=False,
        injection_risk="LOW",
        injection_patterns=[],
        extracted_order_id=None,
        extracted_reason=None,
        extracted_sentiment=None,
        extracted_intent_type="unknown",
        retrieved_policy_chunks=[],
        retrieval_scores=[],
        customer_data=None,
        order_data=None,
        policy_text="",
        missing_fields=[],
        decision="NEEDS_INFO",
        triggered_rules=[],
        confidence=0.0,
        risk_flags=[],
        needs_escalation=False,
        explanation_facts=[],
        requires_human_review=False,
        assistant_message="",
        error=None,
        node_history=[],
    )
