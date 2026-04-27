import backend.services.db_tools as db_tools
from backend.services.db_tools import get_admissions_guidance_data, is_safe_select, search_colleges_flexible_data


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


def test_admissions_guidance_falls_back_when_logistics_table_missing(monkeypatch):
    calls = []

    def fake_run_safe_select(sql_query, params=None):
        calls.append(sql_query)
        if "admissions_logistics" in sql_query:
            return {
                "status": "error",
                "message": "Database error: 1146 (42S02): Table 'c_details.admissions_logistics' doesn't exist",
                "rows": [],
            }

        return {
            "status": "ok",
            "message": "Success",
            "rows": [
                {
                    "college_name": "Sample College",
                    "state": "Telangana",
                    "location": "Hyderabad",
                    "college_type": "Private",
                    "college_tier": "Tier 2",
                    "nirf_ranking": 90,
                    "website_url": "https://example.edu",
                    "course_name": "CSE",
                    "annual_fee": 250000,
                    "min_10th_pct": 60,
                    "min_12th_pct": 60,
                    "required_stream": "MPC",
                    "accepted_exams": "Management",
                    "cutoff_rank_gen": None,
                    "cutoff_rank_reserved": None,
                    "application_start": None,
                    "application_end": None,
                    "required_docs": None,
                    "apply_link": None,
                    "admission_steps": None,
                }
            ],
        }

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    result = get_admissions_guidance_data(
        course_name="CSE",
        tenth_pct=85,
        twelfth_pct=80,
        stream="MPC",
        exam_name="Management",
        preferred_location="Hyderabad",
        max_annual_fee=500000,
        limit=5,
    )

    assert result["status"] == "ok"
    assert len(calls) == 2
    assert "admissions_logistics" not in calls[1]
    assert result["results"][0]["admission"]["application_start"] is None


def test_admissions_guidance_maps_none_exam_to_management_filter(monkeypatch):
    calls = []

    def fake_run_safe_select(sql_query, params=None):
        calls.append((sql_query, params))
        return {"status": "ok", "message": "No results found.", "rows": []}

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    _ = get_admissions_guidance_data(
        course_name="CSE",
        tenth_pct=75,
        twelfth_pct=85,
        stream="MPC",
        exam_name="none",
        preferred_location="Hyderabad",
        max_annual_fee=500000,
        limit=5,
    )

    first_sql, first_params = calls[0]
    assert "and (lower(ec.accepted_exams) like %s or lower(ec.accepted_exams) like %s or lower(ec.accepted_exams) like %s)" in first_sql.lower()
    joined_params = " ".join(str(p) for p in first_params)
    assert "%management%" in joined_params


def test_admissions_guidance_relaxes_exam_filter_after_no_exact_match(monkeypatch):
    calls = []

    def fake_run_safe_select(sql_query, params=None):
        calls.append((sql_query, params))
        if len(calls) == 1:
            return {"status": "ok", "message": "No results found.", "rows": []}

        return {
            "status": "ok",
            "message": "Success",
            "rows": [
                {
                    "college_name": "Closest Match College",
                    "state": "Tamil Nadu",
                    "location": "Chennai",
                    "college_type": "Private",
                    "college_tier": "Tier 2",
                    "nirf_ranking": 110,
                    "website_url": "https://example.edu",
                    "course_name": "CSE",
                    "annual_fee": 450000,
                    "min_10th_pct": 60,
                    "min_12th_pct": 60,
                    "required_stream": "MPC",
                    "accepted_exams": "TNEA",
                    "cutoff_rank_gen": None,
                    "cutoff_rank_reserved": None,
                    "application_start": None,
                    "application_end": None,
                    "required_docs": None,
                    "apply_link": None,
                    "admission_steps": None,
                }
            ],
        }

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    result = get_admissions_guidance_data(
        course_name="CSE",
        tenth_pct=75,
        twelfth_pct=85,
        stream="MPC",
        exam_name="none",
        preferred_location="Chennai",
        max_annual_fee=800000,
        limit=5,
    )

    assert len(calls) == 2
    assert "and (lower(ec.accepted_exams) like %s or lower(ec.accepted_exams) like %s or lower(ec.accepted_exams) like %s)" in calls[0][0].lower()
    assert "and lower(ec.accepted_exams) like %s" not in calls[1][0].lower()
    assert "and (lower(ec.accepted_exams) like %s or lower(ec.accepted_exams) like %s or lower(ec.accepted_exams) like %s)" not in calls[1][0].lower()
    assert result["status"] == "ok"
    assert "relaxing exam constraint" in result["message"].lower()
    assert result["results"][0]["college"]["name"] == "Closest Match College"


def test_admissions_guidance_maps_mpc_to_pcm_stream(monkeypatch):
    captured = {}

    def fake_run_safe_select(sql_query, params=None):
        captured["sql"] = sql_query
        captured["params"] = params
        return {"status": "ok", "message": "No results found.", "rows": []}

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    _ = get_admissions_guidance_data(
        course_name="CSE",
        tenth_pct=75,
        twelfth_pct=85,
        stream="MPC",
        exam_name="",
        limit=5,
    )

    assert "lower(ec.required_stream) like %s or lower(ec.required_stream) like %s" in captured["sql"].lower()
    assert "%pcm%" in captured["params"]
    assert "%mpc%" in captured["params"]


def test_admissions_guidance_normalizes_common_location_typo(monkeypatch):
    captured = {}

    def fake_run_safe_select(sql_query, params=None):
        captured["params"] = params
        return {"status": "ok", "message": "No results found.", "rows": []}

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    _ = get_admissions_guidance_data(
        course_name="CSE",
        tenth_pct=75,
        twelfth_pct=85,
        stream="PCM",
        preferred_location="hyderbad",
        limit=5,
    )

    joined_params = " ".join(str(p) for p in captured["params"])
    assert "%hyderabad%" in joined_params


def test_admissions_guidance_interprets_small_fee_as_lakhs(monkeypatch):
    calls = []

    def fake_run_safe_select(sql_query, params=None):
        calls.append((sql_query, params))
        return {"status": "ok", "message": "No results found.", "rows": []}

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    _ = get_admissions_guidance_data(
        course_name="CSE",
        tenth_pct=75,
        twelfth_pct=85,
        stream="PCM",
        max_annual_fee=5,
        limit=5,
    )

    assert 500000.0 in calls[0][1]


def test_admissions_guidance_applies_college_type_filter(monkeypatch):
    calls = []

    def fake_run_safe_select(sql_query, params=None):
        calls.append((sql_query, params))
        return {"status": "ok", "message": "No results found.", "rows": []}

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    _ = get_admissions_guidance_data(
        course_name="CSE",
        tenth_pct=75,
        twelfth_pct=85,
        stream="PCM",
        college_type="private",
        limit=5,
    )

    assert "lower(c.type) like %s" in calls[0][0].lower()
    assert "%private%" in calls[0][1]


def test_admissions_guidance_relaxes_type_fee_rank_when_still_empty(monkeypatch):
    calls = []

    def fake_run_safe_select(sql_query, params=None):
        calls.append((sql_query, params))
        if len(calls) <= 2:
            return {"status": "ok", "message": "No results found.", "rows": []}

        return {
            "status": "ok",
            "message": "Success",
            "rows": [
                {
                    "college_name": "Relaxed Match College",
                    "state": "Telangana",
                    "location": "Hyderabad",
                    "college_type": "Government",
                    "college_tier": "Tier 2",
                    "nirf_ranking": 80,
                    "website_url": "https://example.edu",
                    "course_name": "CSE",
                    "annual_fee": 180000,
                    "min_10th_pct": 60,
                    "min_12th_pct": 60,
                    "required_stream": "PCM",
                    "accepted_exams": "State Exam",
                    "cutoff_rank_gen": 10000,
                    "cutoff_rank_reserved": 15000,
                    "application_start": None,
                    "application_end": None,
                    "required_docs": None,
                    "apply_link": None,
                    "admission_steps": None,
                }
            ],
        }

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    result = get_admissions_guidance_data(
        course_name="CSE",
        tenth_pct=75,
        twelfth_pct=85,
        stream="PCM",
        exam_name="none",
        preferred_location="Hyderabad",
        college_type="private",
        max_annual_fee=500000,
        rank=5000,
        limit=5,
    )

    assert len(calls) == 3
    assert "lower(c.type) like %s" in calls[0][0].lower()
    assert "annual_fee <= %s" in calls[0][0].lower()
    assert "<= ec.cutoff_rank_gen" in calls[0][0].lower()
    assert "lower(c.type) like %s" not in calls[2][0].lower()
    assert "annual_fee <= %s" not in calls[2][0].lower()
    assert "<= ec.cutoff_rank_gen" not in calls[2][0].lower()
    assert result["status"] == "ok"
    assert "relaxing fee/rank/type constraints" in result["message"].lower()
    assert result["results"][0]["college"]["name"] == "Relaxed Match College"


def test_admissions_guidance_supports_multi_location_filter(monkeypatch):
    captured = {}

    def fake_run_safe_select(sql_query, params=None):
        captured["sql"] = sql_query
        captured["params"] = params
        return {"status": "ok", "message": "No results found.", "rows": []}

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    _ = get_admissions_guidance_data(
        course_name="CSE",
        tenth_pct=75,
        twelfth_pct=85,
        stream="MPC",
        preferred_location="Hyderabad, Secunderabad and Nizamabad",
        limit=5,
    )

    assert "lower(c.location) like %s or lower(c.location) like %s or lower(c.location) like %s" in captured["sql"].lower()
    params_text = " ".join(str(p) for p in captured["params"])
    assert "%hyderabad%" in params_text
    assert "%secunderabad%" in params_text
    assert "%nizamabad%" in params_text


def test_admissions_guidance_supports_multi_college_type_filter(monkeypatch):
    calls = []

    def fake_run_safe_select(sql_query, params=None):
        calls.append((sql_query, params))
        return {"status": "ok", "message": "No results found.", "rows": []}

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    _ = get_admissions_guidance_data(
        course_name="CSE",
        tenth_pct=75,
        twelfth_pct=85,
        stream="PCM",
        college_type="private + government + autonomous",
        limit=5,
    )

    first_sql, first_params = calls[0]
    assert "lower(c.type) like %s or lower(c.type) like %s or lower(c.type) like %s" in first_sql.lower()
    params_text = " ".join(str(p) for p in first_params)
    assert "%private%" in params_text
    assert "%government%" in params_text
    assert "%autonomous%" in params_text


def test_flexible_search_allows_partial_inputs(monkeypatch):
    captured = {}

    def fake_run_safe_select(sql_query, params=None):
        captured["sql"] = sql_query
        captured["params"] = params
        return {"status": "ok", "message": "No results found.", "rows": []}

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    result = search_colleges_flexible_data(preferred_location="chennai", limit=10)

    assert result["status"] == "ok"
    assert "lower(c.location) like %s" in captured["sql"].lower()
    assert "%chennai%" in " ".join(str(p) for p in captured["params"])


def test_flexible_search_interprets_fee_in_lakhs(monkeypatch):
    captured = {}

    def fake_run_safe_select(sql_query, params=None):
        captured["params"] = params
        return {"status": "ok", "message": "No results found.", "rows": []}

    monkeypatch.setattr(db_tools, "run_safe_select", fake_run_safe_select)

    _ = search_colleges_flexible_data(course_name="CSE", min_annual_fee=5, max_annual_fee=7, limit=10)

    assert 500000.0 in captured["params"]
    assert 700000.0 in captured["params"]
