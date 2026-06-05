"""
runner.py — Thin adapter over the LangGraph state machine.

This module is the single public interface for the API routes layer.
All orchestration logic lives in app/agent/graph/. This file only
constructs the initial state and delegates to graph.ainvoke().

Backward compatible: routes.py calls run_refund_agent(db, request)
exactly as before — the signature is unchanged.
"""

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.agent.events import serialize_trace_event
from app.agent.graph.builder import get_agent_graph
from app.agent.graph.state import initial_state
from app.db.models import RefundRequest, TraceEvent
from app.models.schemas import ChatRequest, ChatResponse, TraceEventOut


async def run_refund_agent(db: Session, request: ChatRequest) -> ChatResponse:
    """
    Entry point for all customer support requests.

    1. Builds initial AgentState from the ChatRequest
    2. Invokes the LangGraph state machine
    3. Returns a ChatResponse with the full conversation trace
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())

    state = initial_state(
        conversation_id=conversation_id,
        customer_email=str(request.customer_email).lower() if request.customer_email else None,
        raw_message=request.message,
        db=db,
    )

    graph = get_agent_graph()
    # Pass db_session via configurable — LangGraph never tries to serialize
    # configurable values, so non-picklable objects (SQLAlchemy Session) are safe.
    config = {"configurable": {"thread_id": conversation_id, "db_session": db}}

    # graph.ainvoke runs the full state machine and returns the final state
    final_state = await graph.ainvoke(state, config=config)

    # Collect all trace events from DB for this conversation
    return _build_response(db, conversation_id, final_state)


def _build_response(db: Session, conversation_id: str, final_state: dict) -> ChatResponse:
    """Assemble ChatResponse from final graph state + DB trace events."""
    events = db.scalars(
        select(TraceEvent)
        .where(TraceEvent.conversation_id == conversation_id)
        .order_by(TraceEvent.id)
    ).all()

    return ChatResponse(
        conversation_id=conversation_id,
        assistant_message=final_state.get("assistant_message", ""),
        decision=final_state.get("decision", "NEEDS_INFO"),  # type: ignore[arg-type]
        triggered_rules=final_state.get("triggered_rules", []),
        needs_escalation=final_state.get("needs_escalation", False),
        injection_detected=final_state.get("injection_detected", False),
        trace=[TraceEventOut(**serialize_trace_event(event)) for event in events],
    )


def latest_decision_for_conversation(db: Session, conversation_id: str) -> str | None:
    """Return the most recent decision for a conversation (used by health checks)."""
    refund = db.scalar(
        select(RefundRequest)
        .where(RefundRequest.conversation_id == conversation_id)
        .order_by(desc(RefundRequest.created_at))
        .limit(1)
    )
    return refund.decision if refund else None
