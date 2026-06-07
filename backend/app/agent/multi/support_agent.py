"""Support Agent — Handles general complaints, feedback, and empathetic dialogue."""

SUPPORT_SYSTEM_PROMPT = """You are a supportive customer service representative for Andromeda.
You handle complaints, feedback, and general inquiries with empathy and professionalism.

Guidelines:
- Always acknowledge the customer's feelings first
- Never make promises about refunds or policy changes
- Offer specific next steps when possible
- Maintain a warm, human tone
- If the issue requires policy action, suggest they mention their order ID
"""

async def support_agent_respond(message: str, history: list[dict], customer_data: dict | None = None) -> dict:
    from app.core.config import get_settings
    settings = get_settings()
    
    if settings.llm_provider.lower() == "mock":
        name = customer_data.get('name', 'there') if customer_data else 'there'
        return {
            "answer": f"Hi {name}, I'm the Andromeda support assistant. How can I help you today?",
            "agent": "support",
            "confidence": 1.0
        }

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
    history_text = "\n".join([f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content')}" for m in history[-10:]])
    customer_context = ""
    
    if customer_data:
        customer_context = f"""
Customer Profile:
- Name: {customer_data.get('name', 'Unknown')}
- Tier: {customer_data.get('loyalty_tier', 'Unknown')}
- Account Age: {customer_data.get('account_age_days', 'Unknown')} days
- Total Spent: ${customer_data.get('total_spent', 0)}
"""
        
    response = await llm.ainvoke([
        SystemMessage(content=SUPPORT_SYSTEM_PROMPT + customer_context),
        HumanMessage(content=f"Conversation history:\n{history_text}\n\nCurrent message: {message}"),
    ])
    
    return {"answer": response.content, "agent": "support", "confidence": 0.85}

