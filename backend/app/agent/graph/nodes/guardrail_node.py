"""guardrail_node — Node 2: Adversarial prompt-injection scanner.

Runs before any LLM call. If risk is HIGH the graph routes to block_node
and no LLM is ever invoked. The policy decision cannot be overridden through
a blocked request.
"""

from langchain_core.runnables import RunnableConfig

from app.agent.events import record_trace
from app.agent.graph.state import AgentState
from app.agent.guardrails import scan_for_injection


async def guardrail_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Wraps the existing 35-pattern scan_for_injection() scanner.
    Returns injection metadata that edges.route_after_guardrail() reads.
    """
    db = config["configurable"]["db_session"]
    conversation_id = state["conversation_id"]

    injection = scan_for_injection(state["raw_message"])

    await record_trace(
        db,
        conversation_id,
        "safety.scan",
        "Prompt-injection scan completed",
        {
            "detected": injection.detected,
            "risk": injection.risk,
            "patterns": injection.patterns,
        },
        "warning" if injection.detected else "info",
    )

    return {
        "injection_detected": injection.detected,
        "injection_risk": injection.risk,
        "injection_patterns": injection.patterns,
        "node_history": state.get("node_history", []) + ["guardrail"],
    }


async def block_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Terminal node for HIGH-risk injection attempts.
    Returns a hardcoded refusal message — no LLM involved.
    """
    db = config["configurable"]["db_session"]
    conversation_id = state["conversation_id"]

    await record_trace(
        db,
        conversation_id,
        "safety.block",
        "Request blocked — HIGH injection risk detected",
        {
            "patterns": state.get("injection_patterns", []),
            "risk": state.get("injection_risk"),
        },
        "warning",
    )

    return {
        "decision": "DENIED",
        "triggered_rules": ["GUARDRAIL_INJECTION_BLOCK"],
        "assistant_message": (
            "I'm unable to process this request. A security concern was detected "
            "in the message content. Please rephrase your request or contact "
            "support directly."
        ),
        "node_history": state.get("node_history", []) + ["block"],
    }
