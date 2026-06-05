"""
AgentState — The shared state object passed between all LangGraph nodes.

TypedDict total=False allows partial updates from each node (each node only
returns the keys it modifies, not the full state).

Private fields prefixed with _ are runtime objects not serialized to API responses.
"""

from typing import Any, Optional


class AgentState(dict):
    """
    LangGraph state for the Andromeda agent.
    Inherits from dict so LangGraph can merge partial updates.

    Field groups:
      Input        — set at entry point by runner.py
      Safety       — guardrail_node output
      Extraction   — extraction_node output
      RAG          — retrieval_node output (Phase 3, defaults to empty)
      Tools        — tool_node output
      Policy       — policy_node output
      Response     — response_node output
      Routing      — flags used by edge routing functions
      Private      — runtime objects not returned in API response
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

    # ── Private (runtime, not serialized) ─────────────────────────
    # Access as state["_db"], state["_lf_trace"]
    # _db: SQLAlchemy Session
    # _lf_trace: Langfuse ConversationTrace (Phase 5)


def initial_state(
    conversation_id: str,
    customer_email: Optional[str],
    raw_message: str,
    db: Any,
) -> AgentState:
    """Build a clean initial AgentState for a new request."""
    state = AgentState()
    state["conversation_id"] = conversation_id
    state["customer_email"] = customer_email
    state["raw_message"] = raw_message
    state["injection_detected"] = False
    state["injection_risk"] = "LOW"
    state["injection_patterns"] = []
    state["extracted_order_id"] = None
    state["extracted_reason"] = None
    state["extracted_sentiment"] = None
    state["extracted_intent_type"] = "unknown"
    state["retrieved_policy_chunks"] = []
    state["retrieval_scores"] = []
    state["customer_data"] = None
    state["order_data"] = None
    state["policy_text"] = ""
    state["missing_fields"] = []
    state["decision"] = "NEEDS_INFO"
    state["triggered_rules"] = []
    state["confidence"] = 0.0
    state["risk_flags"] = []
    state["needs_escalation"] = False
    state["explanation_facts"] = []
    state["requires_human_review"] = False
    state["assistant_message"] = ""
    state["error"] = None
    state["node_history"] = []
    state["_db"] = db
    state["_lf_trace"] = None
    return state
