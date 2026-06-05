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

    # ── Policy document ───────────────────────────────────────────
    policy_text = read_refund_policy()
    await record_trace(
        db, conversation_id,
        "tool.read_refund_policy",
        "ArcaShop refund policy loaded",
        {"characters": len(policy_text)},
    )

    # ── Customer lookup ───────────────────────────────────────────
    customer = lookup_customer_by_email(db, customer_email)
    await record_trace(
        db, conversation_id,
        "tool.lookup_customer_by_email",
        "Customer profile lookup completed",
        {"email": customer_email, "found": bool(customer)},
    )

    # ── Order lookup ──────────────────────────────────────────────
    order = lookup_order(db, order_id)
    await record_trace(
        db, conversation_id,
        "tool.lookup_order",
        "Order details lookup completed",
        {"order_id": order_id, "found": bool(order)},
    )

    # ── If no order found, list customer's known orders (helpful for UX) ──
    missing_fields: list[str] = []
    if not order_id:
        missing_fields.append("order_id")
    if not customer_email:
        missing_fields.append("customer_email")

    if customer_email and not order_id:
        orders = list_customer_orders(db, customer_email)
        await record_trace(
            db, conversation_id,
            "tool.list_customer_orders",
            "Customer order history listed",
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
