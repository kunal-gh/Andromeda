"""Multi-Agent Orchestrator — Supervisor + Workers via LangGraph."""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.graph.state import AgentState
from app.agent.multi.supervisor import supervise
from app.agent.multi.retrieval_agent import retrieval_agent_answer
from app.agent.multi.support_agent import support_agent_respond
from app.agent.graph.nodes.guardrail_node import guardrail_node
from app.agent.graph.nodes.tool_node import tool_node
from app.agent.graph.nodes.policy_node import policy_node
from app.agent.graph.nodes.response_node import response_node
from app.agent.graph.nodes.persistence_node import persistence_node

async def node_supervisor(state: AgentState, config) -> dict:
    last_message = state.get("raw_message", "")
    if state.get("messages"):
        last_message = state["messages"][-1].get("content", last_message)
        
    routing = await supervise(last_message, state.get("messages", []), state.get("customer_email"))
    
    # Store routing decision in state
    return {
        "target_agent": routing.target_agent,
        "extracted_intent": {
            **(state.get("extracted_intent") or {}),
            "routing_confidence": routing.confidence,
            "routing_reasoning": routing.reasoning,
            **routing.extracted_entities,
        },
        "node_history": state.get("node_history", []) + ["supervisor"],
    }

async def node_retrieval(state: AgentState, config) -> dict:
    last_message = state.get("raw_message", "")
    if state.get("messages"):
        last_message = state["messages"][-1].get("content", last_message)
        
    result = await retrieval_agent_answer(last_message, state["conversation_id"])
    return {
        "assistant_message": result["answer"],
        "node_history": state.get("node_history", []) + ["retrieval_agent"],
    }

async def node_support(state: AgentState, config) -> dict:
    last_message = state.get("raw_message", "")
    if state.get("messages"):
        last_message = state["messages"][-1].get("content", last_message)
        
    customer_data = state.get("customer_data")
    result = await support_agent_respond(last_message, state.get("messages", []), customer_data)
    
    return {
        "assistant_message": result["answer"],
        "node_history": state.get("node_history", []) + ["support_agent"],
    }

def route_after_supervisor(state: AgentState) -> str:
    routes = {
        "policy": "tool_execution",
        "retrieval": "retrieval_agent",
        "support": "support_agent",
        "escalation": "response_composition",
    }
    target = state.get("target_agent", "support")
    return routes.get(target, "support_agent")

def build_multi_agent_graph():
    builder = StateGraph(AgentState)
    
    # We add an intake pass-through to align with existing structure
    builder.add_node("intake", lambda state, config: {"node_history": state.get("node_history", []) + ["intake"]})
    
    builder.add_node("safety_guard", guardrail_node)
    builder.add_node("supervisor", node_supervisor)
    
    # Specialized Agents / Subgraphs
    builder.add_node("tool_execution", tool_node)
    builder.add_node("policy_engine", policy_node)
    builder.add_node("retrieval_agent", node_retrieval)
    builder.add_node("support_agent", node_support)
    
    builder.add_node("response_composition", response_node)
    builder.add_node("persistence", persistence_node)
    
    builder.set_entry_point("intake")
    builder.add_edge("intake", "safety_guard")
    builder.add_edge("safety_guard", "supervisor")
    
    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "tool_execution": "tool_execution",
            "retrieval_agent": "retrieval_agent",
            "support_agent": "support_agent",
            "response_composition": "response_composition",
        }
    )
    
    builder.add_edge("tool_execution", "policy_engine")
    builder.add_edge("policy_engine", "response_composition")
    
    builder.add_edge("retrieval_agent", "persistence")
    builder.add_edge("support_agent", "persistence")
    builder.add_edge("response_composition", "persistence")
    builder.add_edge("persistence", END)
    
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

_multi_agent_graph = None

def get_multi_agent_graph():
    global _multi_agent_graph
    if _multi_agent_graph is None:
        _multi_agent_graph = build_multi_agent_graph()
    return _multi_agent_graph
