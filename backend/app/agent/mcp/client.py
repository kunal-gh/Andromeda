"""MCP Client for Andromeda Agent."""
import json
import logging
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
    
    async def connect_server(self, name: str, command: str, args: list[str] = None):
        server_params = StdioServerParameters(command=command, args=args or [], env=None)
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()
        self.sessions[name] = session
        logger.info(f"Connected to MCP server: {name}")
        return session
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> dict | str:
        if server_name not in self.sessions:
            raise ValueError(f"Server {server_name} not connected")
        result = await self.sessions[server_name].call_tool(tool_name, arguments)
        text_content = result.content[0].text
        try:
            return json.loads(text_content)
        except (json.JSONDecodeError, TypeError):
            return text_content
    
    async def close(self):
        await self.exit_stack.aclose()


_mcp_client: MCPClient | None = None

async def get_mcp_client() -> MCPClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
        # Connect to stdio servers
        await _mcp_client.connect_server("crm", "python", ["-m", "mcp_servers.crm_server.server"])
        await _mcp_client.connect_server("orders", "python", ["-m", "mcp_servers.orders_server.server"])
        await _mcp_client.connect_server("policy", "python", ["-m", "mcp_servers.policy_server.server"])
    return _mcp_client

async def mcp_lookup_customer(email: str) -> dict:
    client = await get_mcp_client()
    return await client.call_tool("crm", "lookup_customer_by_email", {"email": email})

async def mcp_lookup_order(order_id: str) -> dict:
    client = await get_mcp_client()
    return await client.call_tool("orders", "lookup_order", {"order_id": order_id})

async def mcp_list_customer_orders(email: str) -> list[dict]:
    client = await get_mcp_client()
    return await client.call_tool("orders", "list_customer_orders", {"email": email})

async def mcp_evaluate_policy(order_id: str, customer_email: str) -> dict:
    client = await get_mcp_client()
    return await client.call_tool("policy", "evaluate_refund_policy", {
        "order_id": order_id,
        "customer_email": customer_email,
    })

async def mcp_read_refund_policy() -> str:
    client = await get_mcp_client()
    result = await client.call_tool("policy", "read_refund_policy", {})
    return str(result)
