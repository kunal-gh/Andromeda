"""extraction_node — Node 3: LLM-based intent extraction with heuristic fallback.

Identifies order_id, reason, and sentiment from raw customer message.
Falls back to _heuristic_extract() if the LLM provider fails.
"""

from app.agent.events import record_trace
from app.agent.graph.state import AgentState
from app.agent.providers import get_provider, _heuristic_extract


async def extraction_node(state: AgentState) -> dict:
    """
    LLM Call 1 — intent extraction.

    Extracts:
      - order_id: "ORD-XXXX" or None
      - reason: customer's stated reason for the request
      - sentiment: "positive" | "neutral" | "negative"
      - intent_type: "refund_request" | "faq" | "other"

    On provider failure falls back to regex heuristic (no LLM cost).
    """
    db = state["_db"]
    conversation_id = state["conversation_id"]
    raw_message = state["raw_message"]
    customer_email = state.get("customer_email")

    provider = get_provider()
    try:
        result = await provider.extract_intent(raw_message, customer_email)
        extracted = result.value

        await record_trace(
            db,
            conversation_id,
            "llm.extract",
            f"Intent extracted via {result.provider}",
            extracted.model_dump(),
        )

    except Exception as exc:
        extracted = _heuristic_extract(raw_message, customer_email)
        await record_trace(
            db,
            conversation_id,
            "llm.fallback",
            "Provider failed — heuristic extraction used",
            {"error": str(exc), "extracted": extracted.model_dump()},
            "warning",
        )

    # Normalise order_id to uppercase
    order_id = extracted.order_id.upper() if extracted.order_id else None

    return {
        "extracted_order_id": order_id,
        "extracted_reason": extracted.reason,
        "extracted_sentiment": getattr(extracted, "sentiment", "neutral"),
        "extracted_intent_type": "refund_request",
        "node_history": state.get("node_history", []) + ["extraction"],
    }


async def needs_info_node(state: AgentState) -> dict:
    """
    Terminal node when order_id is missing.
    Composes a clarification request — may use LLM or template.
    """
    db = state["_db"]
    conversation_id = state["conversation_id"]
    customer_email = state.get("customer_email")

    from app.agent.providers import get_provider, template_reply

    context = {
        "decision": "NEEDS_INFO",
        "order_id": None,
        "customer_email": customer_email,
        "missing_fields": ["order_id"],
        "triggered_rules": ["R0_ORDER_REQUIRED"],
        "explanation_facts": [
            "The agent needs a verified order ID before applying the refund policy."
        ],
        "injection_detected": state.get("injection_detected", False),
    }

    provider = get_provider()
    try:
        result = await provider.compose_reply(context)
        reply = result.value
        await record_trace(db, conversation_id, "llm.compose", f"Clarification composed via {result.provider}", {"decision": "NEEDS_INFO"})
    except Exception:
        reply = template_reply(context)

    await record_trace(db, conversation_id, "guardrail.lock", "Decision locked — NEEDS_INFO", {"decision": "NEEDS_INFO", "model_cannot_override": True})

    return {
        "decision": "NEEDS_INFO",
        "triggered_rules": ["R0_ORDER_REQUIRED"],
        "assistant_message": reply,
        "node_history": state.get("node_history", []) + ["needs_info"],
    }
