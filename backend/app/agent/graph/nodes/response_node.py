"""response_node — Node 7: LLM-powered response composition.

LLM Call 2 — composes the customer-facing reply based on the LOCKED decision
from policy_node. The LLM receives the decision as a fact and writes a clear,
empathetic response explaining it. It cannot change the outcome.

If Phase 3 RAG chunks are present, they are injected into the compose context
so the LLM can cite specific policy sections in its reply.
"""

from app.agent.events import record_trace
from app.agent.graph.state import AgentState
from app.agent.providers import get_provider, template_reply


async def response_node(state: AgentState) -> dict:
    """
    Composes the customer-facing response using the locked policy decision.

    Build compose_context from:
      - The locked decision + triggered rules + explanation facts
      - Customer and order data for personalisation
      - Retrieved policy chunks (empty in Phase 1, populated in Phase 3)
    """
    db = state["_db"]
    conversation_id = state["conversation_id"]

    # ── Build compose context (decision is locked, LLM only writes prose) ──
    compose_context = {
        "decision": state["decision"],
        "order_id": state.get("extracted_order_id"),
        "customer_email": state.get("customer_email"),
        "customer": state.get("customer_data"),
        "order": state.get("order_data"),
        "triggered_rules": state.get("triggered_rules", []),
        "explanation_facts": state.get("explanation_facts", []),
        "risk_flags": state.get("risk_flags", []),
        "requires_human_review": state.get("requires_human_review", False),
        "injection_detected": state.get("injection_detected", False),
        # Phase 3: inject RAG chunks if available
        "policy_context": state.get("retrieved_policy_chunks", []),
    }

    provider = get_provider()
    try:
        result = await provider.compose_reply(compose_context)
        assert isinstance(result.value, str)
        reply = result.value

        await record_trace(
            db, conversation_id,
            "llm.compose",
            f"Customer reply composed via {result.provider}",
            {"decision": state["decision"]},
        )

    except Exception as exc:
        reply = template_reply(compose_context)
        await record_trace(
            db, conversation_id,
            "llm.fallback",
            "Provider failed — template response used",
            {"error": str(exc)},
            "warning",
        )

    return {
        "assistant_message": reply,
        "node_history": state.get("node_history", []) + ["response"],
    }
