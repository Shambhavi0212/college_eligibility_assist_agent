from datetime import date, datetime
from decimal import Decimal
import json
import re
from typing import Any

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


def _parse_admission_steps(raw_steps):
    if raw_steps is None:
        return []

    if isinstance(raw_steps, list):
        return [str(step).strip() for step in raw_steps if str(step).strip()]

    if isinstance(raw_steps, str):
        text = raw_steps.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(step).strip() for step in parsed if str(step).strip()]
        except json.JSONDecodeError:
            pass

        pieces = re.split(r"\n|\||;", text)
        return [piece.strip(" -") for piece in pieces if piece.strip(" -")]

    return [str(raw_steps).strip()]


def _build_checklist(row: dict):
    checklist = [
        "Verify you satisfy the minimum 10th/12th marks and stream criteria.",
        "Prepare required documents before application start date.",
        "Submit application before the deadline.",
        "Track counseling/admission notifications after submission.",
    ]

    checklist.extend(_parse_admission_steps(row.get("admission_steps")))

    deduped = []
    seen = set()
    for step in checklist:
        if step not in seen:
            deduped.append(step)
            seen.add(step)
    return deduped


def get_admissions_guidance_data(
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
):
    if not course_name or tenth_pct is None or twelfth_pct is None or not stream or not exam_name:
        return {
            "status": "error",
            "message": "Missing required inputs: course_name, tenth_pct, twelfth_pct, stream, and exam_name are mandatory.",
            "results": [],
        }

    limit = max(1, min(int(limit), 10))
    category = (category or "general").strip().lower()

    sql = """
        SELECT
            c.name AS college_name,
            c.state,
            c.location,
            c.type AS college_type,
            c.college_tier,
            c.nirf_ranking,
            c.website_url,
            cr.course_name,
            cr.annual_fee,
            ec.min_10th_pct,
            ec.min_12th_pct,
            ec.required_stream,
            ec.accepted_exams,
            ec.cutoff_rank_gen,
            ec.cutoff_rank_reserved,
            al.application_start,
            al.application_end,
            al.required_docs,
            al.apply_link,
            al.admission_steps
        FROM courses cr
        JOIN colleges c ON c.college_id = cr.college_id
        JOIN eligibility_criteria ec ON ec.course_id = cr.course_id
        LEFT JOIN admissions_logistics al ON al.course_id = cr.course_id
        WHERE cr.course_name LIKE %s
          AND ec.min_10th_pct <= %s
          AND ec.min_12th_pct <= %s
          AND LOWER(ec.required_stream) LIKE %s
          AND LOWER(ec.accepted_exams) LIKE %s
    """

    params = [
        f"%{course_name}%",
        float(tenth_pct),
        float(twelfth_pct),
        f"%{stream.strip().lower()}%",
        f"%{exam_name.strip().lower()}%",
    ]

    if preferred_state:
        sql += " AND LOWER(c.state) LIKE %s"
        params.append(f"%{preferred_state.strip().lower()}%")

    if preferred_location:
        sql += " AND LOWER(c.location) LIKE %s"
        params.append(f"%{preferred_location.strip().lower()}%")

    if max_annual_fee is not None:
        sql += " AND cr.annual_fee <= %s"
        params.append(float(max_annual_fee))

    if rank is not None:
        if category == "reserved":
            sql += " AND (ec.cutoff_rank_reserved IS NULL OR %s <= ec.cutoff_rank_reserved)"
        else:
            sql += " AND (ec.cutoff_rank_gen IS NULL OR %s <= ec.cutoff_rank_gen)"
        params.append(int(rank))

    sql += " ORDER BY c.nirf_ranking ASC, cr.annual_fee ASC LIMIT %s"
    params.append(limit)

    result = run_safe_select(sql, tuple(params))
    if result["status"] != "ok":
        return {
            "status": "error",
            "message": result["message"],
            "results": [],
        }

    formatted = []
    for row in result["rows"]:
        formatted.append(
            {
                "college": {
                    "name": row.get("college_name"),
                    "state": row.get("state"),
                    "location": row.get("location"),
                    "type": row.get("college_type"),
                    "tier": row.get("college_tier"),
                    "nirf_ranking": row.get("nirf_ranking"),
                    "website": row.get("website_url"),
                },
                "course": {
                    "name": row.get("course_name"),
                    "annual_fee": row.get("annual_fee"),
                },
                "eligibility": {
                    "min_10th_pct": row.get("min_10th_pct"),
                    "min_12th_pct": row.get("min_12th_pct"),
                    "required_stream": row.get("required_stream"),
                    "accepted_exams": row.get("accepted_exams"),
                    "cutoff_rank_general": row.get("cutoff_rank_gen"),
                    "cutoff_rank_reserved": row.get("cutoff_rank_reserved"),
                },
                "admission": {
                    "application_start": row.get("application_start"),
                    "application_end": row.get("application_end"),
                    "required_documents": row.get("required_docs"),
                    "apply_link": row.get("apply_link"),
                },
                "checklist": _build_checklist(row),
            }
        )

    return {
        "status": "ok",
        "message": "No matching colleges found." if not formatted else "Success",
        "results": formatted,
    }


@tool
def sql_executor(sql_query: str):
    """Execute a single, read-only SQL SELECT query on the college database."""
    return run_safe_select(sql_query)


@tool
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
):
    """Deterministically fetch admissions guidance with eligibility and checklist."""
    return get_admissions_guidance_data(
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
