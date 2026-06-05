"""
Andromeda LangGraph — Graph builder and singleton accessor.

build_agent_graph() assembles all nodes and edges into a compiled
StateGraph. The singleton pattern (get_agent_graph) ensures the graph
is compiled once at application startup and reused across requests.

Graph topology:
  intake → guardrail →(HIGH)→ block → persistence → END
                     →(LOW/MED)→ extraction →(no order)→ needs_info → persistence → END
                                            →(order found)→ retrieval → tools → policy
                                                                                 →(ESCALATED)→ human_handoff → response → persistence → END
                                                                                 →(other)→ response → persistence → END
"""

from langgraph.graph import StateGraph, END

from app.agent.graph.edges import (
    route_after_extraction,
    route_after_guardrail,
    route_after_policy,
)
from app.agent.graph.nodes.extraction_node import extraction_node, needs_info_node
from app.agent.graph.nodes.guardrail_node import block_node, guardrail_node
from app.agent.graph.nodes.intake_node import intake_node
from app.agent.graph.nodes.persistence_node import persistence_node
from app.agent.graph.nodes.policy_node import human_handoff_node, policy_node
from app.agent.graph.nodes.response_node import response_node
from app.agent.graph.nodes.retrieval_node import retrieval_node
from app.agent.graph.nodes.tool_node import tool_node
from app.agent.graph.state import AgentState

_compiled_graph = None


def build_agent_graph():
    """
    Compile the Andromeda LangGraph state machine.

    Uses dict-based state (AgentState inherits from dict) which allows
    each node to return only the keys it modifies. LangGraph merges
    partial updates into the running state automatically.
    """
    builder = StateGraph(dict)  # dict state with AgentState shape

    # ── Register nodes ────────────────────────────────────────────
    builder.add_node("intake",        intake_node)
    builder.add_node("guardrail",     guardrail_node)
    builder.add_node("extraction",    extraction_node)
    builder.add_node("retrieval",     retrieval_node)
    builder.add_node("tools",         tool_node)
    builder.add_node("policy",        policy_node)
    builder.add_node("response",      response_node)
    builder.add_node("persistence",   persistence_node)
    # Terminal fork nodes
    builder.add_node("block",         block_node)
    builder.add_node("needs_info",    needs_info_node)
    builder.add_node("human_handoff", human_handoff_node)

    # ── Set entry point ───────────────────────────────────────────
    builder.set_entry_point("intake")

    # ── Wire edges ────────────────────────────────────────────────
    builder.add_edge("intake", "guardrail")

    builder.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {"extraction": "extraction", "block": "block"},
    )

    builder.add_conditional_edges(
        "extraction",
        route_after_extraction,
        {"retrieval": "retrieval", "needs_info": "needs_info"},
    )

    builder.add_edge("retrieval", "tools")
    builder.add_edge("tools", "policy")

    builder.add_conditional_edges(
        "policy",
        route_after_policy,
        {"response": "response", "human_handoff": "human_handoff"},
    )

    # All paths converge at response → persistence → END
    builder.add_edge("human_handoff", "response")
    builder.add_edge("response",      "persistence")

    # Short-circuit paths also end at persistence
    builder.add_edge("block",      "persistence")
    builder.add_edge("needs_info", "persistence")

    builder.add_edge("persistence", END)

    return builder.compile()


def get_agent_graph():
    """Return the singleton compiled graph, building it on first call."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_agent_graph()
    return _compiled_graph
