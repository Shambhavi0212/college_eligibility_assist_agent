from functools import lru_cache

from langchain.agents import create_agent
from langchain_groq import ChatGroq

try:
    from backend.core.config import settings, validate_settings
    from backend.core.prompt import SYSTEM_PROMPT
    from backend.services.db_tools import admissions_guidance, sql_executor
except ModuleNotFoundError:
    from core.config import settings, validate_settings
    from core.prompt import SYSTEM_PROMPT
    from services.db_tools import admissions_guidance, sql_executor

try:
    from backend.services.mcp_client import mcp_admissions_guidance, mcp_sql_executor
except Exception:
    try:
        from services.mcp_client import mcp_admissions_guidance, mcp_sql_executor
    except Exception:
        mcp_admissions_guidance = None
        mcp_sql_executor = None


@lru_cache(maxsize=1)
def get_agent():
    # Validate startup-critical settings once.
    validate_settings()

    llm = ChatGroq(
        model_name=settings.model_name,
        temperature=settings.model_temperature,
        groq_api_key=settings.groq_api_key,
    )

    if settings.use_mcp and mcp_sql_executor and mcp_admissions_guidance:
        tools = [mcp_sql_executor, mcp_admissions_guidance]
    else:
        tools = [sql_executor, admissions_guidance]

    return create_agent(llm, tools=tools, system_prompt=SYSTEM_PROMPT)
