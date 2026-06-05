"""
Phase 2 — MCP Server: CRM
Exposes customer and order lookups as Model Context Protocol tools.
Run standalone: python -m mcp_servers.crm_server.server

When TOOL_MODE=mcp in .env, tool_node routes all CRM calls here instead of
hitting SQLAlchemy directly. This decouples the agent from the database layer
and makes each tool independently scalable and versioned.
"""

from fastmcp import FastMCP

# Lazy import so server can run without full app context
mcp = FastMCP("andromeda-crm-server")


@mcp.tool()
async def lookup_customer_by_email(email: str) -> dict:
    """
    Find a customer profile by verified email address.

    Args:
        email: Customer's email address (case-insensitive)

    Returns:
        Customer dict with id, name, email, loyalty_tier, account_age_days,
        total_spent, fraud_risk. Returns empty dict if not found.
    """
    from app.db.database import SessionLocal
    from app.agent.tools import lookup_customer_by_email as _lookup

    db = SessionLocal()
    try:
        result = _lookup(db, email)
        return result or {}
    finally:
        db.close()


@mcp.tool()
async def lookup_order(order_id: str) -> dict:
    """
    Find one order by order ID (e.g. 'ORD-1001').

    Args:
        order_id: The order identifier string

    Returns:
        Order dict with id, customer_id, sku, item_name, category, price,
        purchase_date, delivery_date, final_sale, returned, status, condition_note.
        Returns empty dict if not found.
    """
    from app.db.database import SessionLocal
    from app.agent.tools import lookup_order as _lookup

    db = SessionLocal()
    try:
        result = _lookup(db, order_id)
        return result or {}
    finally:
        db.close()


@mcp.tool()
async def list_customer_orders(email: str) -> list[dict]:
    """
    List all orders associated with a verified customer email.

    Args:
        email: Customer's verified email address

    Returns:
        List of order dicts (may be empty if no orders or customer not found)
    """
    from app.db.database import SessionLocal
    from app.agent.tools import list_customer_orders as _list

    db = SessionLocal()
    try:
        return _list(db, email)
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.get_asgi_app(), host="0.0.0.0", port=8100)
