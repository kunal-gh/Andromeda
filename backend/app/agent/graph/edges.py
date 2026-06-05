"""
Conditional edge routing functions for the Andromeda LangGraph.

Each function receives the current AgentState and returns a string key
that LangGraph uses to select the next node. Keeping routing logic here
(instead of inline lambdas) makes it independently testable.
"""

from app.agent.graph.state import AgentState


def route_after_guardrail(state: AgentState) -> str:
    """
    After guardrail_node:
      - HIGH injection risk → block immediately (no LLM call)
      - MEDIUM / LOW → proceed to intent extraction
    """
    if state.get("injection_risk") == "HIGH":
        return "block"
    return "extraction"


def route_after_extraction(state: AgentState) -> str:
    """
    After extraction_node:
      - No order_id found → ask customer for missing info
      - Order ID present → proceed to retrieval then tools
    """
    if not state.get("extracted_order_id"):
        return "needs_info"
    return "retrieval"


def route_after_policy(state: AgentState) -> str:
    """
    After policy_node:
      - Escalated decisions → human_handoff (currently routes to response with ESCALATED context)
      - All others → compose response
    Both paths go through response_node; the difference is in the LLM compose context.
    """
    if state.get("needs_escalation"):
        return "human_handoff"
    return "response"
