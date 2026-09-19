import json

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n4,,south\n"
SQL = "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region ORDER BY region"


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _full_case(client) -> str:
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    run_id = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
    ).json()["id"]
    client.post(
        f"/cases/{case_id}/findings",
        json={"run_id": run_id, "statement": "north leads revenue"},
    )
    client.post(
        f"/cases/{case_id}/runs/{run_id}/charts",
        json={"kind": "bar", "x": "region", "y": "total", "title": "Revenue"},
    )
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")
    return case_id


def test_export_contains_every_section(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _full_case(client)
        response = client.get(f"/cases/{case_id}/export")

    assert response.status_code == 200, response.text
    package = response.json()
    assert package["format"] == "dah-case-package"
    assert package["version"] == 1
    assert package["case"]["question"] == "Why did revenue decline?"
    for section in ("datasets", "profiles", "runs", "findings", "charts", "plans"):
        assert len(package[section]) == 1, section

    dataset = package["datasets"][0]
    assert dataset["filename"] == "sales.csv"
    # The raw bytes are embedded, so the package needs no external files.
    import base64

    assert base64.b64decode(dataset["data_base64"]) == CSV
    assert package["runs"][0]["sql"] == SQL
    assert package["runs"][0]["columns"] == ["region", "total"]
    assert package["findings"][0]["statement"] == "north leads revenue"
    assert package["charts"][0]["svg"].startswith("<svg")
    assert package["plans"][0]["source"] == "deterministic"


def test_export_unknown_case_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        response = client.get("/cases/nope/export")

    assert response.status_code == 404


def test_round_trip_restores_the_case(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _full_case(client)
        package = client.get(f"/cases/{case_id}/export").json()
        response = client.post("/cases/import", json=package)

    assert response.status_code == 201, response.text
    imported = response.json()
    assert imported["id"] != case_id
    assert imported["question"] == "Why did revenue decline?"

    with TestClient(app) as client:
        restored = client.get(f"/cases/{imported['id']}/export").json()
        original = client.get(f"/cases/{case_id}/export").json()

    # State round-trips losslessly: same shape, same content, new IDs.
    assert restored["case"]["question"] == original["case"]["question"]
    assert len(restored["datasets"]) == len(original["datasets"])
    assert restored["datasets"][0]["data_base64"] == original["datasets"][0]["data_base64"]
    assert restored["runs"][0]["sql"] == original["runs"][0]["sql"]
    assert restored["runs"][0]["rows"] == original["runs"][0]["rows"]
    assert restored["findings"][0]["statement"] == original["findings"][0]["statement"]
    assert restored["charts"][0]["svg"] == original["charts"][0]["svg"]
    assert restored["plans"][0]["plan"] == original["plans"][0]["plan"]


def test_round_trip_relinks_references_and_serves_artifacts(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _full_case(client)
        package = client.get(f"/cases/{case_id}/export").json()
        imported_id = client.post("/cases/import", json=package).json()["id"]

        restored = client.get(f"/cases/{imported_id}/export").json()
        # References still point at entities inside the restored case.
        run_id = restored["runs"][0]["id"]
        dataset_id = restored["datasets"][0]["id"]
        assert restored["findings"][0]["run_id"] == run_id
        assert restored["charts"][0]["run_id"] == run_id
        assert restored["profiles"][0]["dataset_id"] == dataset_id

        # The restored artifacts are live, not just data: the chart is served.
        chart_id = restored["charts"][0]["id"]
        image = client.get(f"/cases/{imported_id}/charts/{chart_id}/image")
        assert image.status_code == 200
        assert image.content.startswith(b"<svg")

        # And the imported dataset can be queried again through the engine.
        rerun = client.post(
            f"/cases/{imported_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT COUNT(*) AS n FROM read_csv_auto(?)"},
        )
        assert rerun.status_code == 201
        assert rerun.json()["rows"] == [[4]]


def test_import_rejects_bad_package(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        assert client.post("/cases/import", json={"nope": 1}).status_code == 400
        wrong_format = {"format": "something-else", "version": 1, "case": {}}
        assert client.post("/cases/import", json=wrong_format).status_code == 400
        wrong_version = {
            "format": "dah-case-package",
            "version": 99,
            "case": {},
        }
        assert client.post("/cases/import", json=wrong_version).status_code == 400

        # Right shape but no question.
        empty = {
            "format": "dah-case-package",
            "version": 1,
            "case": {"question": ""},
            "datasets": [],
            "profiles": [],
            "runs": [],
            "findings": [],
            "charts": [],
            "plans": [],
        }
        assert client.post("/cases/import", json=empty).status_code == 400
