from fastapi.testclient import TestClient

from app.db import DATA_DIR, get_connection
from app.main import app, get_db


def _temp_env(tmp_path):
    """Point the app at a fresh DB and on-disk data dir for this test."""
    import app.db as db_module

    db_path = tmp_path / "test.db"
    data_dir = tmp_path / "data"
    db_module.DATA_DIR = data_dir
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    return data_dir


CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"


def _golden_parquet(tmp_path) -> bytes:
    """Build a two-row parquet file from the golden CSV content."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    path = tmp_path / "golden.parquet"
    table = pa.table(
        {
            "order_id": pa.array([1, 2, 3], type=pa.int64()),
            "revenue": pa.array([125.0, 80.5, 200.0], type=pa.float64()),
            "region": pa.array(["north", "south", "north"]),
        }
    )
    pq.write_table(table, path)
    return path.read_bytes()


def _golden_xlsx(tmp_path) -> bytes:
    """Build a two-row xlsx file from the golden CSV content."""
    import openpyxl

    path = tmp_path / "golden.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["order_id", "revenue", "region"])
    sheet.append([1, 125.0, "north"])
    sheet.append([2, 80.5, "south"])
    sheet.append([3, 200.0, "north"])
    workbook.save(path)
    return path.read_bytes()


def _make_case(client) -> str:
    response = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    )
    return response.json()["id"]


def test_attach_and_reopen_dataset(tmp_path) -> None:
    data_dir = _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        response = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )
        assert response.status_code == 201
        dataset = response.json()
        assert dataset["filename"] == "sales.csv"
        assert dataset["format"] == "csv"
        assert (data_dir / case_id / f"{dataset['id']}.csv").exists()

    # Reopen in a fresh client - the dataset must still be listed.
    with TestClient(app) as client:
        listed = client.get(f"/cases/{case_id}/datasets")

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["filename"] == "sales.csv"


def _attach(client, case_id: str, filename: str, content: bytes) -> str:
    response = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": (filename, content, "application/octet-stream")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _profile(client, case_id: str, dataset_id: str) -> dict:
    response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    assert response.status_code == 201
    return response.json()


def test_attach_and_profile_parquet(tmp_path) -> None:
    data_dir = _temp_env(tmp_path)
    parquet = _golden_parquet(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        dataset_id = _attach(client, case_id, "sales.parquet", parquet)
        dataset = client.get(f"/cases/{case_id}/datasets").json()[0]
        assert dataset["format"] == "parquet"
        assert (data_dir / case_id / f"{dataset_id}.parquet").exists()

        profile = _profile(client, case_id, dataset_id)
        assert profile["rows"] == 3
        assert profile["columns"] == ["order_id", "revenue", "region"]


def test_attach_and_profile_xlsx(tmp_path) -> None:
    _temp_env(tmp_path)
    xlsx = _golden_xlsx(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        dataset_id = _attach(client, case_id, "sales.xlsx", xlsx)
        dataset = client.get(f"/cases/{case_id}/datasets").json()[0]
        assert dataset["format"] == "xlsx"

        profile = _profile(client, case_id, dataset_id)
        assert profile["rows"] == 3
        assert profile["columns"] == ["order_id", "revenue", "region"]


def test_query_across_each_format(tmp_path) -> None:
    """The same SQL runs against csv, parquet, and xlsx datasets."""
    _temp_env(tmp_path)
    sql = (
        "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
        "GROUP BY region ORDER BY region"
    )
    payloads = [
        ("sales.csv", CSV),
        ("sales.parquet", _golden_parquet(tmp_path)),
        ("sales.xlsx", _golden_xlsx(tmp_path)),
    ]

    with TestClient(app) as client:
        case_id = _make_case(client)
        for filename, content in payloads:
            dataset_id = _attach(client, case_id, filename, content)
            run = client.post(
                f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": sql}
            )
            assert run.status_code == 201, run.text
            assert run.json()["rows"] == [["north", 325.0], ["south", 80.5]]


def test_parquet_placeholder_form_is_accepted(tmp_path) -> None:
    """Writing the natural read_parquet(?) placeholder works on a parquet file."""
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        dataset_id = _attach(client, case_id, "sales.parquet", _golden_parquet(tmp_path))
        run = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT COUNT(*) AS n FROM read_parquet(?)"},
        )
        assert run.status_code == 201, run.text
        assert run.json()["rows"] == [[3]]


def test_attach_to_unknown_case_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/cases/does-not-exist/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )

    assert response.status_code == 404


def test_attach_rejects_non_csv(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        response = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )

    assert response.status_code == 400


def test_attach_rejects_empty_file(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        response = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("empty.csv", b"   ", "text/csv")},
        )

    assert response.status_code == 400


def test_attach_rejects_the_same_filename_twice(tmp_path) -> None:
    """W5X-001: a second attach of the same filename is refused with a
    sentence naming the dataset already attached, and nothing is written."""
    data_dir = _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        first = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )
        assert first.status_code == 201
        first_id = first.json()["id"]

        second = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )

    assert second.status_code == 409
    detail = second.json()["detail"]
    assert "sales.csv" in detail
    assert first_id in detail
    assert "already attached" in detail

    # The refusal must leave the dataset list unchanged.
    with TestClient(app) as client:
        listed = client.get(f"/cases/{case_id}/datasets")

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == first_id
    # And no second file was written to disk.
    assert len(list((data_dir / case_id).glob("*.csv"))) == 1


def test_attach_accepts_two_different_filenames(tmp_path) -> None:
    """W5X-001: the refusal is per filename - a different file still attaches."""
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        first = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )
        second = client.post(
            f"/cases/{case_id}/datasets",
            files={
                "file": (
                    "orders.csv",
                    b"order_id,region\n1,north\n2,south\n",
                    "text/csv",
                )
            },
        )

    assert first.status_code == 201
    assert second.status_code == 201

    with TestClient(app) as client:
        listed = client.get(f"/cases/{case_id}/datasets")

    assert len(listed.json()) == 2
    assert {d["filename"] for d in listed.json()} == {"sales.csv", "orders.csv"}


def test_the_same_filename_is_allowed_in_a_different_case(tmp_path) -> None:
    """W5X-001: the check is within one case - another case may attach the
    same filename, because its dataset is never this case's label."""
    _temp_env(tmp_path)

    with TestClient(app) as client:
        first_case = _make_case(client)
        second_case = _make_case(client)
        first = client.post(
            f"/cases/{first_case}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )
        second = client.post(
            f"/cases/{second_case}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )

    assert first.status_code == 201
    assert second.status_code == 201
