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
