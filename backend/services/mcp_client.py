import asyncio
import json
from typing import Any, Dict

from langchain.tools import tool

try:
    from backend.core.config import settings
except ModuleNotFoundError:
    from core.config import settings

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None


class MCPAdmissionsClient:
    def __init__(self):
        entry_tokens = settings.mcp_server_entry.split()
        self.command = settings.mcp_server_command
        self.args = entry_tokens
        self.cwd = settings.mcp_server_cwd

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if ClientSession is None or StdioServerParameters is None or stdio_client is None:
            return {
                "status": "error",
                "message": "MCP SDK not installed. Run: pip install mcp",
            }

        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            cwd=self.cwd,
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)

        if hasattr(result, "structuredContent") and result.structuredContent:
            return result.structuredContent

        parts = []
        for item in getattr(result, "content", []):
            text = getattr(item, "text", "")
            if text:
                parts.append(text)

        if not parts:
            return {"status": "error", "message": "No content returned from MCP server."}

        combined = "\n".join(parts)
        try:
            return json.loads(combined)
        except json.JSONDecodeError:
            return {"status": "ok", "message": combined}

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        return asyncio.run(self._call_tool(tool_name, arguments))


client = MCPAdmissionsClient()


@tool
def mcp_sql_executor(sql_query: str):
    """Execute read-only SQL through the MCP server."""
    return client.call_tool("execute_select", {"sql_query": sql_query})
