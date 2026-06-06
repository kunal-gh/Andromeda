"""Supervisor Agent — Routes incoming requests to specialized worker agents."""
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class RoutingDecision(BaseModel):
    target_agent: Literal["policy", "retrieval", "support", "escalation"] = Field(description="Which agent should handle this request")
    confidence: float = Field(ge=0.0, le=1.0, description="Routing confidence")
    reasoning: str = Field(description="Why this routing decision was made")
    extracted_entities: dict = Field(default_factory=dict, description="Key entities found")

SUPERVISOR_PROMPT = """You are the Supervisor Agent for Worknoon Customer Support.
Your job is to analyze the customer's message and route it to the correct specialized agent.

Available agents:
- policy: Handles refund requests, returns, exchanges, and policy-related questions
- retrieval: Handles product FAQs, shipping questions, sizing guides, and general product info
- support: Handles complaints, feedback, general chat, and non-specific requests
- escalation: Use only when the customer explicitly demands a human or the request is abusive

Analyze the message carefully. Extract key entities (order_id, product_name, intent).
Return your routing decision with confidence and reasoning.

Customer message: {message}
Conversation history: {history}
"""

async def supervise(message: str, history: list[dict], customer_email: str | None = None) -> RoutingDecision:
    # Use gpt-4o-mini as the cheap/fast router
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(RoutingDecision)
    
    # Format history
    history_text = "\n".join([f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content')}" for m in history[-5:]])
    
    result = await llm.ainvoke([
        SystemMessage(content=SUPERVISOR_PROMPT.format(message=message, history=history_text)),
        HumanMessage(content=f"Route this request from {customer_email or 'unknown'}"),
    ])
    return result
