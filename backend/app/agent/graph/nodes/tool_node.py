"""tool_node — Node 5: CRM and Order lookups.

Reads the ArcaShop refund policy document, fetches customer profile and
order details from the database. Supports both local SQLAlchemy mode (default)
and MCP server mode (Phase 2, TOOL_MODE=mcp).
"""

from langchain_core.runnables import RunnableConfig

from app.agent.events import record_trace
from app.agent.graph.state import AgentState
from app.agent.tools import (
    list_customer_orders,
    lookup_customer_by_email,
    lookup_order,
    read_refund_policy,
)
from app.core.config import get_settings
from app.agent.mcp.client import (
    mcp_list_customer_orders,
    mcp_lookup_customer,
    mcp_lookup_order,
    mcp_read_refund_policy,
)


async def tool_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Executes all CRM lookups needed before policy evaluation.

    Emits one trace event per tool call so the frontend trace timeline
    shows every data fetch step in real time.
    """
    db = config["configurable"]["db_session"]
    conversation_id = state["conversation_id"]
    customer_email = state.get("customer_email")
    order_id = state.get("extracted_order_id")

    settings = get_settings()
    use_mcp = settings.tool_mode == "mcp"

    # ── Policy document ───────────────────────────────────────────
    if use_mcp:
        policy_text = await mcp_read_refund_policy()
    else:
        policy_text = read_refund_policy()
        
    await record_trace(
        db, conversation_id,
        "tool.read_refund_policy",
        "ArcaShop refund policy loaded via MCP" if use_mcp else "ArcaShop refund policy loaded",
        {"characters": len(policy_text)},
    )

    # ── Customer lookup ───────────────────────────────────────────
    if use_mcp:
        customer = await mcp_lookup_customer(customer_email)
    else:
        customer = lookup_customer_by_email(db, customer_email)
        
    await record_trace(
        db, conversation_id,
        "tool.lookup_customer_by_email",
        "Customer profile lookup completed via MCP" if use_mcp else "Customer profile lookup completed",
        {"email": customer_email, "found": bool(customer)},
    )

    # ── Order lookup ──────────────────────────────────────────────
    if use_mcp:
        order = await mcp_lookup_order(order_id)
    else:
        order = lookup_order(db, order_id)
        
    await record_trace(
        db, conversation_id,
        "tool.lookup_order",
        "Order details lookup completed via MCP" if use_mcp else "Order details lookup completed",
        {"order_id": order_id, "found": bool(order)},
    )

    # ── If no order found, list customer's known orders (helpful for UX) ──
    missing_fields: list[str] = []
    if not order_id:
        missing_fields.append("order_id")
    if not customer_email:
        missing_fields.append("customer_email")

    if customer_email and not order_id:
        if use_mcp:
            orders = await mcp_list_customer_orders(customer_email)
        else:
            orders = list_customer_orders(db, customer_email)
            
        await record_trace(
            db, conversation_id,
            "tool.list_customer_orders",
            "Customer order history listed via MCP" if use_mcp else "Customer order history listed",
            {"count": len(orders)},
        )

    if not order and order_id:
        missing_fields.append("valid_order_id")

    return {
        "policy_text": policy_text,
        "customer_data": customer,
        "order_data": order,
        "missing_fields": missing_fields,
        "node_history": state.get("node_history", []) + ["tools"],
    }
