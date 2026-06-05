"""persistence_node — Node 8: Final DB writes and trace emission.

Persists the completed conversation state to the database:
- Saves the assistant's reply as a Message row
- Creates/updates the RefundRequest row
- Updates Conversation status
- Emits the final trace event

This is always the last node before END.
"""

from langchain_core.runnables import RunnableConfig

from app.agent.events import record_trace
from app.agent.graph.state import AgentState
from app.db.models import Conversation, Message, RefundRequest


async def persistence_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Writes all final state to SQLite/Postgres.

    Called for every execution path: approved, denied, escalated,
    needs_info, blocked, and human_handoff paths all end here.
    """
    db = config["configurable"]["db_session"]
    conversation_id = state["conversation_id"]
    reply = state.get("assistant_message", "")
    decision = state.get("decision", "NEEDS_INFO")
    customer_data = state.get("customer_data")
    order_id = state.get("extracted_order_id")
    explanation_facts = state.get("explanation_facts", [])

    # ── Persist assistant message ─────────────────────────────────
    db.add(Message(conversation_id=conversation_id, role="assistant", content=reply))

    # ── Create RefundRequest row (for all decisions except pure NEEDS_INFO) ──
    if decision != "NEEDS_INFO" or order_id:
        db.add(
            RefundRequest(
                conversation_id=conversation_id,
                customer_id=customer_data["id"] if customer_data else None,
                order_id=order_id,
                decision=decision,
                reason="; ".join(explanation_facts),
                injection_detected=state.get("injection_detected", False),
            )
        )

    # ── Update Conversation row ───────────────────────────────────
    conversation = db.get(Conversation, conversation_id)
    if conversation:
        conversation.status = decision
        conversation.latest_message = reply

    db.commit()

    # ── Final trace event ─────────────────────────────────────────
    await record_trace(
        db, conversation_id,
        "final",
        "Final response returned to client",
        {"decision": decision},
    )

    return {
        "node_history": state.get("node_history", []) + ["persistence"],
    }
