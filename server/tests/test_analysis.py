from app.analysis import profile_csv
from app.planner import plan_analysis


def test_profile_csv(tmp_path) -> None:
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "order_id,revenue,region\n"
        "1,125.0,north\n"
        "2,80.5,south\n"
        "3,200.0,north\n",
        encoding="utf-8",
    )

    result = profile_csv(str(csv_path))

    assert result["rows"] == 3
    assert result["columns"] == ["order_id", "revenue", "region"]


def test_profile_csv_missing_values(tmp_path) -> None:
    csv_path = tmp_path / "messy.csv"
    csv_path.write_text(
        "id,name,score\n"
        "1,alice,90\n"
        "2,,75\n"
        "3,bob,\n",
        encoding="utf-8",
    )

    result = profile_csv(str(csv_path))

    assert result["rows"] == 3
    assert result["stats"]["name"]["null_count"] == 1
    assert result["stats"]["score"]["null_count"] == 1
    assert result["stats"]["id"]["null_count"] == 0


# A row carrying more fields than the header - a stray trailing comma, as a
# spreadsheet export or a hand-edit produces - derails read_csv_auto's delimiter
# guess, and the whole file then reads as one column holding each raw line.
STRAY_COMMA_CSV = (
    "order_id,quarter,region,revenue\n"
    "101,2024q2,north,4200.0\n"
    "106,2024q3,west,,\n"
    "107,2024q3,west,2700.0\n"
)


def test_sniffed_reader_leaves_a_well_formed_file_alone(tmp_path) -> None:
    from app.analysis import _sniffed_reader_for

    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "order_id,revenue,region\n1,125.0,north\n2,80.5,south\n", encoding="utf-8"
    )
    parquet_path = tmp_path / "sales.parquet"
    parquet_path.write_bytes(b"PAR1" + b"\x00" * 8)

    # A well-formed CSV keeps the strict reader: ignore_errors on a clean file
    # would turn a genuine conversion error into a silent null.
    assert _sniffed_reader_for(str(csv_path)) == ("read_csv_auto(?)", str(csv_path))
    # Parquet is never sniffed, so the recovery cannot fire on it.
    assert _sniffed_reader_for(str(parquet_path)) == (
        "read_parquet(?)",
        str(parquet_path),
    )


def test_sniffed_reader_recovers_a_stray_trailing_comma(tmp_path) -> None:
    from app.analysis import _sniffed_reader_for

    csv_path = tmp_path / "messy.csv"
    csv_path.write_text(STRAY_COMMA_CSV, encoding="utf-8")

    assert _sniffed_reader_for(str(csv_path)) == (
        "read_csv_auto(?, ignore_errors=true)",
        str(csv_path),
    )


def test_profile_csv_stray_trailing_comma(tmp_path) -> None:
    csv_path = tmp_path / "messy.csv"
    csv_path.write_text(STRAY_COMMA_CSV, encoding="utf-8")

    result = profile_csv(str(csv_path))

    # The file reads as four columns, not one raw line per row, and every row
    # survives: the stray field is dropped, leaving revenue null.
    assert result["rows"] == 3
    assert result["columns"] == ["order_id", "quarter", "region", "revenue"]
    assert result["stats"]["revenue"]["null_count"] == 1
    assert result["stats"]["region"]["distinct_count"] == 2


# --- P8-CONTEXT-001: intent outranks inference in the plan -------------------

PROFILE = {
    "rows": 3,
    "columns": ["score", "region"],
    "stats": {
        "score": {"type": "numeric", "min": 1, "max": 3, "avg": 2.0, "null_count": 0},
        "region": {"type": "other", "distinct_count": 2, "null_count": 0},
    },
    "duplicate_rows": 0,
}


def test_plan_without_context_records_no_basis() -> None:
    plan = plan_analysis("Why did revenue dip?", PROFILE)
    assert plan["context_basis"] == []


def test_plan_records_which_context_fields_it_read() -> None:
    plan = plan_analysis(
        "Why did revenue dip?",
        PROFILE,
        {
            "purpose": "Understand the Q3 dip",
            "sub_questions": ["Is it west?", "Is it Q3?"],
            "hypotheses": ["West drove it"],
        },
    )
    assert plan["context_basis"] == ["purpose", "sub_questions:2", "hypotheses:1"]


def test_the_analysts_sub_questions_outrank_the_derived_ones() -> None:
    plan = plan_analysis(
        "Why did revenue dip?",
        PROFILE,
        {"purpose": "", "sub_questions": ["Is it concentrated in one region?"],
         "hypotheses": ["A single region drove it"]},
    )
    assert plan["sub_questions"][0] == "Is it concentrated in one region?"
    # The derived questions still appear, after the analyst's own.
    assert len(plan["sub_questions"]) > 1
    assert any(h["statement"] == "A single region drove it" for h in plan["hypotheses"])


def test_a_stated_purpose_stands_in_for_a_thin_question() -> None:
    plan = plan_analysis("", PROFILE, {"purpose": "Understand the dip",
                                       "sub_questions": [], "hypotheses": []})
    assert plan["objective"] == "Understand the dip"


def test_an_empty_context_behaves_like_none_at_all() -> None:
    # A case that saved an empty form is planned from the profile alone.
    assert plan_analysis("q", PROFILE, {"purpose": "", "sub_questions": [],
                                        "hypotheses": []})["context_basis"] == []


# --- P8-GOLDEN-005: a run's rows must survive serialisation ----------------
# Grouping by a date column is ordinary analysis, and the profile already
# describes one as an ISO string; the run path used to hand a raw
# datetime.date to json.dumps and answer a 500 for a valid query.
DATE_CSV = (
    "day,amount\n"
    "2024-06-01,10.0\n"
    "2024-06-01,20.0\n"
    "2024-06-02,5.0\n"
)


def test_a_date_column_serialises_as_an_iso_string(tmp_path) -> None:
    import json

    from app.analysis import run_query

    csv_path = tmp_path / "days.csv"
    csv_path.write_text(DATE_CSV, encoding="utf-8")

    result = run_query(
        str(csv_path),
        "SELECT day, SUM(amount) AS total FROM read_csv_auto(?) "
        "GROUP BY day ORDER BY day",
    )

    assert result["columns"] == ["day", "total"]
    assert result["rows"] == [["2024-06-01", 30.0], ["2024-06-02", 5.0]]
    # The persisted shape is what the API answers, so this is the failure a
    # user would have seen.
    json.dumps(result["rows"])


def test_a_timestamp_column_serialises_as_an_iso_string(tmp_path) -> None:
    import json

    from app.analysis import run_query

    csv_path = tmp_path / "events.csv"
    csv_path.write_text("ts,kind\n2024-06-01 09:30:00,a\n2024-06-01 10:00:00,b\n",
                        encoding="utf-8")

    result = run_query(str(csv_path), "SELECT ts FROM read_csv_auto(?) ORDER BY ts")

    assert result["rows"] == [["2024-06-01T09:30:00"], ["2024-06-01T10:00:00"]]
    json.dumps(result["rows"])


def test_a_numeric_stays_a_numeric_and_a_null_stays_a_null(tmp_path) -> None:
    # Normalisation must not launder a count into a string or a null into a
    # zero: the validation budget compares these values.
    from app.analysis import run_query

    csv_path = tmp_path / "mix.csv"
    csv_path.write_text("n,s\n1,1.5\n2,\n", encoding="utf-8")

    result = run_query(
        str(csv_path),
        "SELECT COUNT(*) AS rows, COUNT(s) AS present, AVG(s) AS mean "
        "FROM read_csv_auto(?)",
    )
    assert result["rows"] == [[2, 1, 1.5]]
    assert isinstance(result["rows"][0][0], int)
    assert result["rows"][0][1] is None or result["rows"][0][1] == 1
