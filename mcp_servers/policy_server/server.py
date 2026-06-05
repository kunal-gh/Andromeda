"""
Phase 2 — MCP Server: Policy
Exposes policy document reading and evaluation as MCP tools.
Run standalone: python -m mcp_servers.policy_server.server

Separating the policy engine into its own MCP server allows:
- Independent versioning of the refund policy
- Hot-swapping policy rules without restarting the main agent
- Auditing all policy reads in a dedicated service
"""

from fastmcp import FastMCP

mcp = FastMCP("andromeda-policy-server")


@mcp.tool()
async def read_refund_policy() -> str:
    """
    Read the current ArcaShop refund policy document.

    Returns:
        Full Markdown text of the ArcaShop refund policy.
        Used by LLM response_node for context, and by evaluate_refund_policy
        for deterministic rule matching.
    """
    from app.agent.tools import read_refund_policy as _read
    return _read()


@mcp.tool()
async def evaluate_refund_policy(order_id: str, customer_email: str) -> dict:
    """
    Run the deterministic R1–R10 refund policy evaluation engine.

    This function contains NO LLM calls. It is pure Python logic that
    evaluates all 10 policy rules against the order and customer data.
    The result is final — the LLM cannot override it.

    Args:
        order_id: The order to evaluate (e.g. 'ORD-1001')
        customer_email: The requesting customer's email (for ownership check)

    Returns:
        dict with keys:
          decision: str — 'APPROVED' | 'DENIED' | 'ESCALATED'
          triggered_rules: list[str] — rules that fired
          explanation_facts: list[str] — human-readable reasons
          risk_flags: list[str] — any risk signals detected
          requires_human_review: bool
          confidence: float — 0.0–1.0
    """
    from app.db.database import SessionLocal
    from app.agent.tools import evaluate_refund_policy as _eval

    db = SessionLocal()
    try:
        return _eval(db, order_id, customer_email)
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.get_asgi_app(), host="0.0.0.0", port=8102)
