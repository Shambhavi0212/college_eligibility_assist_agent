from datetime import date, datetime
from decimal import Decimal
import json
import re
from typing import Any, Optional

from langchain.tools import tool
import mysql.connector

try:
    from backend.core.config import settings
except ModuleNotFoundError:
    from core.config import settings


FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|replace|grant|revoke)\b",
    re.IGNORECASE,
)


def get_connection():
    return mysql.connector.connect(
        host=settings.db_host,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
    )


def is_safe_select(sql_query: str) -> bool:
    if not isinstance(sql_query, str) or not sql_query.strip():
        return False

    sql = sql_query.strip()
    sql_lower = sql.lower()

    if not sql_lower.startswith("select"):
        return False

    if FORBIDDEN_SQL_PATTERN.search(sql_lower):
        return False

    # Block stacked statements while allowing one trailing semicolon.
    if ";" in sql[:-1]:
        return False

    return True


def _json_safe_value(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _json_safe_row(row: dict) -> dict:
    return {key: _json_safe_value(value) for key, value in row.items()}


def run_safe_select(sql_query: str, params=None):
    if not is_safe_select(sql_query):
        return {
            "status": "error",
            "message": "Only a single read-only SELECT query is allowed.",
            "rows": [],
        }

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql_query, params or ())
        rows = cursor.fetchall()
        return {
            "status": "ok",
            "message": "No results found." if not rows else "Success",
            "rows": [_json_safe_row(row) for row in rows],
        }
    except mysql.connector.Error as exc:
        return {
            "status": "error",
            "message": f"Database error: {exc}",
            "rows": [],
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@tool
def sql_executor(sql_query: str):
    """Execute a single, read-only SQL SELECT query on the college database."""
    return run_safe_select(sql_query)


