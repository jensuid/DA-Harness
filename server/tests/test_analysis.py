from app.analysis import profile_csv


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
