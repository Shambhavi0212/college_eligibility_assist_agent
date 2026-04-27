import json

try:
    from backend.services.db_tools import run_safe_select
except ModuleNotFoundError:
    from services.db_tools import run_safe_select

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise RuntimeError("Missing MCP SDK. Install package: pip install mcp") from exc


mcp = FastMCP("college-admissions-server")


@mcp.tool()
def execute_select(sql_query: str) -> str:
    """Run a single safe SELECT query on the admissions database."""
    return json.dumps(run_safe_select(sql_query), ensure_ascii=True)


if __name__ == "__main__":
    mcp.run()
