from backend.services.db_tools import get_admissions_guidance_data, is_safe_select


def test_is_safe_select_accepts_simple_select():
    assert is_safe_select("SELECT * FROM colleges") is True


def test_is_safe_select_blocks_mutation_query():
    assert is_safe_select("DELETE FROM colleges") is False


def test_is_safe_select_blocks_stacked_statement():
    assert is_safe_select("SELECT * FROM colleges; DROP TABLE colleges") is False


def test_admissions_guidance_validates_required_input():
    result = get_admissions_guidance_data(
        course_name="",
        tenth_pct=90,
        twelfth_pct=90,
        stream="PCM",
        exam_name="JEE",
    )
    assert result["status"] == "error"
    assert "mandatory" in result["message"].lower()
