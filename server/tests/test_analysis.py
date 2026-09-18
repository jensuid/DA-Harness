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
