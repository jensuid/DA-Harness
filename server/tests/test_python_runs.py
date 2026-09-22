from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _case_with_dataset(client) -> tuple[str, str]:
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    return case_id, dataset_id


def _python(client, case_id: str, dataset_id: str, code: str):
    return client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs/python",
        json={"code": code},
    )


def test_python_run_persists_and_reopens(tmp_path) -> None:
    _temp_env(tmp_path)

    code = (
        "totals = {}\n"
        "for row in dataset.rows:\n"
        "    totals[row['region']] = totals.get(row['region'], 0) + row['revenue']\n"
        "result = [{'region': k, 'total': v} for k, v in sorted(totals.items())]\n"
    )
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _python(client, case_id, dataset_id, code)

    assert response.status_code == 201, response.text
    run = response.json()
    assert run["kind"] == "python"
    assert run["code"] == code
    assert run["sql"] is None
    assert run["columns"] == ["region", "total"]
    assert run["row_count"] == 2
    assert run["rows"] == [["north", 325.0], ["south", 80.5]]
    run_id = run["id"]

    # Reopen in a fresh client - the run and its rows must survive.
    with TestClient(app) as client:
        stored = client.get(f"/cases/{case_id}/runs/{run_id}")

    assert stored.status_code == 200
    stored_run = stored.json()
    assert stored_run["kind"] == "python"
    assert stored_run["rows"] == run["rows"]
    assert stored_run["code"] == code


def test_python_run_via_duckdb_query(tmp_path) -> None:
    _temp_env(tmp_path)

    code = (
        "table = dataset.query(\n"
        "    'SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) '\n"
        "    'GROUP BY region ORDER BY region'\n"
        ")\n"
        "result = [\n"
        "    {'region': r['region'], 'total': r['total']}\n"
        "    for r in [dict(zip(table['columns'], row)) for row in table['rows']]\n"
        "]\n"
    )
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _python(client, case_id, dataset_id, code)

    assert response.status_code == 201, response.text
    run = response.json()
    assert run["columns"] == ["region", "total"]
    assert run["rows"] == [["north", 325.0], ["south", 80.5]]


def test_python_run_listed_alongside_sql(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT COUNT(*) FROM read_csv_auto(?)"},
        )
        _python(
            client, case_id, dataset_id, "result = [{'n': len(dataset.rows)}]"
        )
        listed = client.get(f"/cases/{case_id}/runs").json()

    assert len(listed) == 2
    kinds = {run["kind"] for run in listed}
    assert kinds == {"sql", "python"}
    for summary in listed:
        assert "rows" not in summary
        assert (summary["code"] is None) == (summary["kind"] == "sql")


def test_python_rejects_write_query_through_handle(tmp_path) -> None:
    _temp_env(tmp_path)

    code = "result = dataset.query('COPY (SELECT 1) TO /tmp/escape.txt')"
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _python(client, case_id, dataset_id, code)

    assert response.status_code == 400


def test_python_rejects_blocked_import(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _python(
            client, case_id, dataset_id, "import subprocess\nresult = []"
        )

    assert response.status_code == 400
    assert "subprocess" in response.json()["detail"]


def test_python_allows_safe_import(tmp_path) -> None:
    _temp_env(tmp_path)

    code = (
        "import statistics\n"
        "values = [row['revenue'] for row in dataset.rows]\n"
        "result = [{'mean': statistics.mean(values), 'count': len(values)}]\n"
    )
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _python(client, case_id, dataset_id, code)

    assert response.status_code == 201, response.text
    run = response.json()
    assert run["columns"] == ["mean", "count"]
    assert run["rows"] == [[(125.0 + 80.5 + 200.0) / 3, 3]]


def test_python_rejects_filesystem_write(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        target = tmp_path / "written.txt"
        response = _python(
            client,
            case_id,
            dataset_id,
            f"open('{target}', 'w').write('nope')\nresult = []",
        )

    assert response.status_code in (400, 500)
    assert not target.exists()


def test_python_rejects_dunder_escape(tmp_path) -> None:
    _temp_env(tmp_path)

    code = "leaked = dataset.query.__globals__\nresult = [{'g': len(leaked)}]"
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _python(client, case_id, dataset_id, code)

    assert response.status_code == 400


def test_python_rejects_missing_result(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _python(client, case_id, dataset_id, "x = 1")

    assert response.status_code == 400
    assert "result" in response.json()["detail"]


def test_python_rejects_empty_code(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _python(client, case_id, dataset_id, "   ")

    assert response.status_code == 400


def test_python_run_unknown_dataset_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()["id"]
        response = _python(
            client, case_id, "nope", "result = [{'a': 1}]"
        )

    assert response.status_code == 404


def test_evidence_chain_works_for_python_run(tmp_path) -> None:
    _temp_env(tmp_path)

    code = "result = [{'region': r['region'], 'revenue': r['revenue']} for r in dataset.rows]"
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        run_id = _python(client, case_id, dataset_id, code).json()["id"]

        finding_id = client.post(
            f"/cases/{case_id}/findings",
            json={
                "run_id": run_id,
                "statement": "north leads revenue in every row",
            },
        ).json()["id"]

        chain = client.get(f"/cases/{case_id}/findings/{finding_id}/evidence")

    assert chain.status_code == 200, chain.text
    evidence = chain.json()
    assert evidence["kind"] == "python"
    assert evidence["sql"] is None
    assert evidence["code"] == code
    assert evidence["columns"] == ["region", "revenue"]
    assert evidence["dataset_filename"] == "sales.csv"

    # A Python-backed finding validates like a SQL one (P3-VALID-010): the
    # stored script is re-executed in the sandbox and its table compared.
    verdict = client.post(
        f"/cases/{case_id}/findings/{finding_id}/validate"
    )
    assert verdict.status_code == 200, verdict.text
    assert verdict.json()["status"] == "supported"
    checks = {c["name"]: c for c in verdict.json()["checks"]}
    assert checks["calculation"]["passed"] is True
