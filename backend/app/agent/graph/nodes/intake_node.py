"""intake_node — Node 1: Initialize conversation context and emit first trace."""

from langchain_core.runnables import RunnableConfig

from app.agent.events import record_trace
from app.agent.graph.state import AgentState
from app.db.models import Conversation, Message


async def intake_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Responsibilities:
    - Create or fetch the Conversation row
    - Persist the incoming user message
    - Emit the first trace event for this request
    """
    db = config["configurable"]["db_session"]
    conversation_id = state["conversation_id"]
    customer_email = state.get("customer_email")
    raw_message = state["raw_message"]

    # Upsert conversation
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        conversation = Conversation(
            id=conversation_id,
            customer_email=str(customer_email) if customer_email else None,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Keep email fresh (may arrive on first turn only)
    if customer_email:
        conversation.customer_email = str(customer_email).lower()

    conversation.latest_message = raw_message
    db.add(Message(conversation_id=conversation_id, role="user", content=raw_message))
    db.commit()

    await record_trace(
        db,
        conversation_id,
        "intake",
        "Customer message received",
        {"message_length": len(raw_message)},
    )

    return {
        "node_history": state.get("node_history", []) + ["intake"],
        # Normalise email early so all downstream nodes use lowercase
        "customer_email": str(customer_email).lower() if customer_email else None,
    }
