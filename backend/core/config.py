import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # LLM settings
    groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
    model_name: str = os.getenv("MODEL_NAME", "openai/gpt-oss-120b").strip()
    model_temperature: float = float(os.getenv("MODEL_TEMPERATURE", "0.7"))

    # App and integration settings
    use_mcp: bool = _env_bool("USE_MCP", True)

    # Database settings
    db_host: str = os.getenv("DB_HOST", "localhost").strip()
    db_user: str = os.getenv("DB_USER", "root").strip()
    db_password: str = os.getenv("DB_PASSWORD", "root").strip()
    db_name: str = os.getenv("DB_NAME", "c_details").strip()

    # MCP server process settings
    mcp_server_command: str = os.getenv("MCP_SERVER_COMMAND", "python").strip()
    mcp_server_entry: str = os.getenv("MCP_SERVER_ENTRY", "-m backend.mcp_server").strip()
    mcp_server_cwd: str = os.getenv("MCP_SERVER_CWD", os.getcwd()).strip()


settings = Settings()


def validate_settings() -> None:
    if not settings.groq_api_key:
        raise RuntimeError("Missing GROQ_API_KEY in .env")
    if not settings.groq_api_key.startswith("gsk_"):
        raise RuntimeError("Invalid GROQ_API_KEY format. Expected prefix: gsk_")
0