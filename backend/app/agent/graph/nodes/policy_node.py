"""policy_node — Node 6: Deterministic R1-R10 refund policy evaluation.

This node is the core safety guarantee of Andromeda. The LLM cannot
influence this decision. The policy engine is pure Python — no probability,
no hallucination, no model-dependent output.

The 10 rules (R1–R10) are evaluated in priority order. The first matching
rule determines the outcome. If no denial or escalation rule fires, R9
grants a standard approval.
"""

from langchain_core.runnables import RunnableConfig

from app.agent.events import record_trace
from app.agent.graph.state import AgentState
from app.agent.tools import create_escalation_case, evaluate_refund_policy
from app.core.config import get_settings
from app.agent.mcp.client import mcp_evaluate_policy


async def policy_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Runs the deterministic policy engine and locks the decision.

    If missing_fields is non-empty or order was not found, the state
    should have been caught at tool_node and routed to needs_info.
    This node runs only when we have a confirmed order.
    """
    db = config["configurable"]["db_session"]
    conversation_id = state["conversation_id"]
    order_id = state.get("extracted_order_id")
    customer_email = state.get("customer_email")
    missing_fields = state.get("missing_fields", [])

    # Fallback: if tools couldn't find the order, deny with info request
    if missing_fields or not state.get("order_data"):
        await record_trace(
            db, conversation_id,
            "policy.skip",
            "Policy evaluation skipped — order not found",
            {"missing_fields": missing_fields, "order_id": order_id},
            "warning",
        )
        return {
            "decision": "NEEDS_INFO",
            "triggered_rules": ["R0_ORDER_REQUIRED"],
            "explanation_facts": [f"Order {order_id or '(unknown)'} could not be verified."],
            "confidence": 1.0,
            "risk_flags": [],
            "needs_escalation": False,
            "requires_human_review": False,
            "node_history": state.get("node_history", []) + ["policy"],
        }

    # ── Deterministic policy evaluation ──────────────────────────
    settings = get_settings()
    if settings.tool_mode == "mcp":
        evaluation = await mcp_evaluate_policy(order_id, customer_email)
    else:
        evaluation = evaluate_refund_policy(db, order_id, customer_email)

    await record_trace(
        db, conversation_id,
        "tool.evaluate_refund_policy",
        "Deterministic policy engine completed",
        evaluation,
    )

    # ── Create escalation case if needed ─────────────────────────
    if evaluation["decision"] == "ESCALATED":
        escalation = create_escalation_case(
            db,
            conversation_id,
            order_id,
            "; ".join(evaluation["explanation_facts"]),
        )
        await record_trace(
            db, conversation_id,
            "tool.create_escalation_case",
            "Human escalation case created",
            escalation,
            "warning",
        )

    # ── Lock the decision — model cannot override ─────────────────
    await record_trace(
        db, conversation_id,
        "guardrail.lock",
        "Backend safety gate locked the final decision",
        {
            "decision": evaluation["decision"],
            "model_cannot_override": True,
        },
    )

    return {
        "decision": evaluation["decision"],
        "triggered_rules": evaluation["triggered_rules"],
        "confidence": evaluation["confidence"],
        "risk_flags": evaluation["risk_flags"],
        "needs_escalation": evaluation["requires_human_review"],
        "requires_human_review": evaluation["requires_human_review"],
        "explanation_facts": evaluation["explanation_facts"],
        "node_history": state.get("node_history", []) + ["policy"],
    }


async def human_handoff_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Reached when decision is ESCALATED and needs_escalation=True.
    Currently routes through response_node with full ESCALATED context.
    In Phase 6 (Human-in-the-Loop), this would pause the graph
    and await a human decision via the Supervisor pattern.
    """
    db = config["configurable"]["db_session"]
    conversation_id = state["conversation_id"]

    await record_trace(
        db, conversation_id,
        "handoff.human",
        "Case routed to human review queue",
        {
            "decision": state.get("decision"),
            "order_id": state.get("extracted_order_id"),
        },
        "warning",
    )

    # Signal to response_node that this was escalated for human review
    return {
        "node_history": state.get("node_history", []) + ["human_handoff"],
    }
