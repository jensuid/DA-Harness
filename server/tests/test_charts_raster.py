"""Raster chart tests for P3-CHART-002.

The SVG backend is dependency-free and stays the default; PNG is an opt-in
format behind the same `render_chart` interface. These check that the raster
output is a real, decodable image, that the geometry the SVG tests already
assert is carried over, and that the API round trip stores and serves bytes of
the right type.
"""

import io

from fastapi.testclient import TestClient

from app.charts import render_chart
from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"region,revenue\nnorth,300.0\nsouth,120.0\neast,80.0\nwest,200.0\n"
ROWS = [
    ["north", 300.0],
    ["south", 120.0],
    ["east", 80.0],
    ["west", 200.0],
]
COLUMNS = ["region", "revenue"]


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
        "/cases", json={"question": "Where is revenue concentrated?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    response = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs",
        json={
            "sql": "SELECT region, SUM(revenue) AS revenue FROM read_csv_auto(?) "
            "GROUP BY region ORDER BY region"
        },
    )
    assert response.status_code == 201, response.text
    return case_id, response.json()["id"]


def _decodable(png: bytes):
    from PIL import Image

    return Image.open(io.BytesIO(png)).convert("RGB")


def test_png_is_a_real_image() -> None:
    png = render_chart("bar", COLUMNS, ROWS, "region", "revenue", fmt="png")
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    image = _decodable(png)
    assert image.size == (800, 400)


def test_png_is_deterministic() -> None:
    args = ("line", COLUMNS, ROWS, "region", "revenue")
    assert render_chart(*args, fmt="png") == render_chart(*args, fmt="png")


def _is_ink(pixel) -> bool:
    """Saturated color: bars and lines, but not near-white gridlines."""
    red, green, blue = pixel[:3]
    return max(red, green, blue) - min(red, green, blue) > 40


def test_png_bar_is_drawn_and_anchored_at_zero() -> None:
    """A taller bar reaches higher up the plot, and bars sit on the baseline."""
    from app.charts import ChartModel

    model = ChartModel("bar", COLUMNS, ROWS, "region", "revenue", None, "", 800, 400)
    baseline = int(model.py(model.low))
    png = render_chart("bar", COLUMNS, ROWS, "region", "revenue", fmt="png")
    image = _decodable(png)
    width, height = image.size

    def column_ink(x: int, from_top: bool = True) -> int:
        ys = range(height) if from_top else range(height - 1, -1, -1)
        return next(y for y in ys if _is_ink(image.getpixel((x, y))))

    # Category centres: north (300) at the first, east (80) at the third.
    north_x = int(model.px("north"))
    east_x = int(model.px("east"))
    assert north_x < east_x
    # A taller bar tops out higher up the image.
    assert column_ink(north_x) < column_ink(east_x)
    # Bars are anchored: the foot of a bar is the zero baseline, not a
    # floating midpoint (downsampling can shift an edge by a pixel).
    assert abs(column_ink(east_x, from_top=False) - baseline) <= 1


def test_png_supports_multiple_series_and_title() -> None:
    rows = [
        ["north", "2024", 100.0],
        ["north", "2025", 150.0],
        ["south", "2024", 60.0],
        ["south", "2025", 90.0],
    ]
    png = render_chart(
        "line", ["region", "year", "revenue"], rows, "year", "revenue",
        series="region", title="Revenue by year", fmt="png",
    )
    image = _decodable(png)
    colors = {
        image.getpixel((x, y))
        for y in range(0, image.size[1], 3)
        for x in range(0, image.size[0], 3)
    }
    assert len({c for c in colors if c != (255, 255, 255)}) >= 2, "two series colors expected"


def test_png_rejects_unknown_kind() -> None:
    try:
        render_chart("pie", COLUMNS, ROWS, "region", "revenue", fmt="png")
    except ValueError as error:
        assert "pie" in str(error)
    else:
        raise AssertionError("an unknown chart kind was accepted")


def test_unknown_format_is_rejected() -> None:
    try:
        render_chart("bar", COLUMNS, ROWS, "region", "revenue", fmt="gif")
    except ValueError as error:
        assert "gif" in str(error)
    else:
        raise AssertionError("an unknown chart format was accepted")


def test_svg_stays_the_default_and_dependency_free() -> None:
    svg = render_chart("bar", COLUMNS, ROWS, "region", "revenue")
    assert svg.startswith(b"<svg")


def test_png_chart_round_trips_through_the_api(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        created = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={
                "kind": "bar",
                "x": "region",
                "y": "revenue",
                "title": "Revenue by region",
                "format": "png",
            },
        )
        assert created.status_code == 201, created.text
        chart_id = created.json()["id"]

        served = client.get(f"/cases/{case_id}/charts/{chart_id}/image")
        assert served.status_code == 200
        assert served.headers["content-type"] == "image/png"
        assert served.content.startswith(b"\x89PNG\r\n\x1a\n")

        exported = client.get(f"/cases/{case_id}/export").json()
        assert exported["charts"][0]["format"] == "png"
        assert exported["charts"][0]["image_b64"]

        imported_id = client.post("/cases/import", json=exported).json()["id"]
        restored = client.get(f"/cases/{imported_id}/export").json()
        restored_image = client.get(
            f"/cases/{imported_id}/charts/{restored['charts'][0]['id']}/image"
        )
        assert restored_image.status_code == 200
        assert restored_image.headers["content-type"] == "image/png"
        assert restored_image.content == served.content


def test_svg_chart_still_round_trips(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        created = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "region", "y": "revenue"},
        )
        assert created.status_code == 201, created.text
        served = client.get(
            f"/cases/{case_id}/charts/{created.json()['id']}/image"
        )
        assert served.headers["content-type"] == "image/svg+xml"
        assert served.content.startswith(b"<svg")
