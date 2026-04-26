import json

try:
    from backend.services.db_tools import get_admissions_guidance_data, run_safe_select
except ModuleNotFoundError:
    from services.db_tools import get_admissions_guidance_data, run_safe_select

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise RuntimeError("Missing MCP SDK. Install package: pip install mcp") from exc


mcp = FastMCP("college-admissions-server")


@mcp.tool()
def execute_select(sql_query: str) -> str:
    """Run a single safe SELECT query on the admissions database."""
    return json.dumps(run_safe_select(sql_query), ensure_ascii=True)


@mcp.tool()
def admissions_guidance(
    course_name: str,
    tenth_pct: float,
    twelfth_pct: float,
    stream: str,
    exam_name: str,
    category: str = "general",
    rank: int = None,
    preferred_state: str = "",
    preferred_location: str = "",
    max_annual_fee: float = None,
    limit: int = 5,
) -> str:
    """Return eligibility, documents, deadlines, and checklist-backed college guidance."""
    result = get_admissions_guidance_data(
        course_name=course_name,
        tenth_pct=tenth_pct,
        twelfth_pct=twelfth_pct,
        stream=stream,
        exam_name=exam_name,
        category=category,
        rank=rank,
        preferred_state=preferred_state,
        preferred_location=preferred_location,
        max_annual_fee=max_annual_fee,
        limit=limit,
    )
    return json.dumps(result, ensure_ascii=True)


if __name__ == "__main__":
    mcp.run()
