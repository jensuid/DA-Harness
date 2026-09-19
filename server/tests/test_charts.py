from fastapi.testclient import TestClient

from app.charts import render_chart
from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"

GROUPED_SQL = (
    "SELECT region, region AS series, SUM(revenue) AS total "
    "FROM read_csv_auto(?) GROUP BY region ORDER BY region"
)


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _case_with_run(client) -> tuple[str, str]:
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    run_id = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs",
        json={
            "sql": "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
            "GROUP BY region ORDER BY region"
        },
    ).json()["id"]
    return case_id, run_id


def test_bar_chart_persists_and_serves(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        response = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "region", "y": "total", "title": "Revenue"},
        )

    assert response.status_code == 201, response.text
    chart = response.json()
    assert chart["kind"] == "bar"
    assert chart["x"] == "region"
    assert chart["y"] == "total"
    assert chart["run_id"] == run_id
    chart_id = chart["id"]

    with TestClient(app) as client:
        image = client.get(f"/cases/{case_id}/charts/{chart_id}/image")

    assert image.status_code == 200
    assert image.headers["content-type"] == "image/svg+xml"
    assert image.content.startswith(b"<svg")
    assert b"Revenue" in image.content
    # The persisted file on disk is the served artifact, byte for byte.
    stored = next(db_module.DATA_DIR.rglob(f"chart_{chart_id}.svg"))
    assert stored.read_bytes() == image.content


def test_chart_reopens_in_new_session(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        chart_id = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "line", "x": "region", "y": "total"},
        ).json()["id"]

    with TestClient(app) as client:
        meta = client.get(f"/cases/{case_id}/charts/{chart_id}")
        listed = client.get(f"/cases/{case_id}/runs/{run_id}/charts")
        image = client.get(f"/cases/{case_id}/charts/{chart_id}/image")

    assert meta.status_code == 200
    assert meta.json()["id"] == chart_id
    assert listed.status_code == 200
    assert [c["id"] for c in listed.json()] == [chart_id]
    assert image.status_code == 200


def test_chart_is_reproducible(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        first = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "region", "y": "total", "title": "T"},
        ).json()["id"]
        second = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "region", "y": "total", "title": "T"},
        ).json()["id"]

    # Same run and same parameters must render byte-identical artifacts.
    a = next(db_module.DATA_DIR.rglob(f"chart_{first}.svg")).read_bytes()
    b = next(db_module.DATA_DIR.rglob(f"chart_{second}.svg")).read_bytes()
    assert a == b


def test_multi_series_line_chart(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        ).json()["id"]
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": GROUPED_SQL},
        ).json()["id"]
        chart_id = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "line", "x": "series", "y": "total", "series": "region"},
        ).json()["id"]
        image = client.get(f"/cases/{case_id}/charts/{chart_id}/image")

    assert image.status_code == 200
    body = image.content
    # Two series means two polylines and a legend.
    assert body.count(b"<polyline") == 2
    assert b"north" in body and b"south" in body


def test_chart_from_python_run(tmp_path) -> None:
    _temp_env(tmp_path)

    code = (
        "totals = {}\n"
        "for row in dataset.rows:\n"
        "    totals[row['region']] = totals.get(row['region'], 0) + row['revenue']\n"
        "result = [{'region': k, 'total': v} for k, v in sorted(totals.items())]\n"
    )
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        ).json()["id"]
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs/python",
            json={"code": code},
        ).json()["id"]
        response = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "region", "y": "total"},
        )

    assert response.status_code == 201, response.text
    assert response.json()["kind"] == "bar"


def test_rejects_unknown_kind(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        response = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "pie", "x": "region", "y": "total"},
        )

    assert response.status_code == 400
    assert "pie" in response.json()["detail"]


def test_rejects_unknown_column(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        response = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "region", "y": "profit"},
        )

    assert response.status_code == 400
    assert "profit" in response.json()["detail"]


def test_rejects_non_numeric_measure(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        response = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "total", "y": "region"},
        )

    assert response.status_code == 400


def test_chart_unknown_run_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()["id"]
        response = client.post(
            f"/cases/{case_id}/runs/nope/charts",
            json={"kind": "bar", "x": "a", "y": "b"},
        )
        image = client.get(f"/cases/{case_id}/charts/nope/image")

    assert response.status_code == 404
    assert image.status_code == 404


def test_render_chart_direct_is_deterministic() -> None:
    columns = ["region", "total"]
    rows = [["north", 325.0], ["south", 80.5]]
    args = ("bar", columns, rows, "region", "total")
    assert render_chart(*args) == render_chart(*args)


def test_bar_geometry_is_anchored_and_proportional() -> None:
    """Bars sit on the zero baseline and scale linearly with their values."""
    import xml.etree.ElementTree as ET

    values = [325.0, 80.5, 150.25]
    rows = [[f"cat_{i}", v] for i, v in enumerate(values)]
    svg = render_chart("bar", ["cat", "value"], rows, "cat", "value")

    root = ET.fromstring(svg)
    namespace = "{http://www.w3.org/2000/svg}"
    bars = [
        element
        for element in root.iter(namespace + "rect")
        if element.attrib.get("fill") not in ("white",) and "x" in element.attrib
    ]
    gridlines = [
        element
        for element in root.iter(namespace + "line")
        if element.attrib.get("stroke") == "#e5e7eb"
    ]

    assert len(bars) == 3
    baseline = max(float(line.attrib["y1"]) for line in gridlines)
    heights = sorted(float(bar.attrib["height"]) for bar in bars)

    # Every bar rests on the lowest gridline, which is the zero of the scale.
    for bar in bars:
        bottom = float(bar.attrib["y"]) + float(bar.attrib["height"])
        assert abs(bottom - baseline) < 1.5
    # Height is linear in value: the ratio is the same for every bar.
    ratios = [height / value for height, value in zip(heights, sorted(values))]
    assert max(ratios) - min(ratios) < 0.01
