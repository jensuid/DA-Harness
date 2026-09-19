"""Deterministic chart renderer (P2-ANALYSIS-009).

Turns a persisted run result (columns + rows) into an SVG chart that is stored
as part of the case's evidence, next to the run and the finding it supports.

SVG is rendered here rather than in the browser on purpose. A chart that is
part of a trust chain has to be an artifact: persisted, reproducible from the
stored result, and viewable without whatever frontend visits it later. The
renderer is dependency-free and deterministic - the same run plus the same
parameters always yield byte-identical output - which is also what makes it
testable without comparing pixels.

Only the essentials: `bar` and `line`, one or more series. Richer chart types,
and a raster backend, can replace this implementation behind the same
`render_chart` interface (Master Spec: visualization is a replaceable surface).
"""

from html import escape

CHART_KINDS = ("bar", "line")

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 400

_MARGIN_LEFT = 64
_MARGIN_RIGHT = 24
_MARGIN_TOP = 48
_MARGIN_BOTTOM = 56
_TICK_COUNT = 5


def _records(columns: list[str], rows: list[list]) -> list[dict]:
    return [dict(zip(columns, row)) for row in rows]


def _numeric(value) -> float | None:
    """Coerce a value to float; non-numeric and None are not plottable."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _label(value) -> str:
    """Compact, escaped axis label for a category or tick."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return escape(str(int(value)))
    return escape(str(value))


def _series_of(records, x: str, y: str, series: str | None) -> list[tuple[str, list[tuple[str, float]]]]:
    """Split the result into ordered (series name, points) pairs.

    Without a series column there is a single series named after the measure.
    With one, series keep first-appearance order so the legend is stable and
    independent of the engine's grouping order.
    """
    if series is None:
        points = [
            (_label(record.get(x)), yv)
            for record in records
            for yv in [_numeric(record.get(y))]
            if yv is not None
        ]
        return [(y, points)]

    order: list[str] = []
    by_series: dict[str, list[tuple[str, float]]] = {}
    for record in records:
        name = _label(record.get(series))
        yv = _numeric(record.get(y))
        if yv is None:
            continue
        if name not in by_series:
            by_series[name] = []
            order.append(name)
        by_series[name].append((_label(record.get(x)), yv))
    return [(name, by_series[name]) for name in order]


def _nice_scale(low: float, high: float, anchor_at_zero: bool) -> tuple[float, float, float]:
    """A scale spanning the data with round tick steps.

    Bar charts are anchored at zero so bar length always reads as magnitude;
    line charts may start above zero to use the plot area.
    """
    if anchor_at_zero and low > 0:
        low = 0.0
    if high == low:
        high = low + 1.0
    span = high - low
    # A round step near span / tick count: 1/2/5 x 10^n.
    raw = span / _TICK_COUNT
    magnitude = 10 ** int(f"{raw:.3e}".split("e")[1])
    step = next(
        candidate * magnitude
        for candidate in (1, 2, 5, 10)
        if candidate * magnitude >= raw * 0.999
    )
    low_floor = int(low // step) * step
    high_ceil = int(high // step + (1 if high % step else 0)) * step
    if high_ceil <= low_floor:
        high_ceil = low_floor + step
    return low_floor, high_ceil, step


def render_chart(
    kind: str,
    columns: list[str],
    rows: list[list],
    x: str,
    y: str,
    series: str | None = None,
    title: str = "",
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> bytes:
    """Render a persisted run result to SVG.

    Raises ValueError for anything the chart contract rejects - unknown kind,
    unknown columns, a non-numeric measure, or no plottable points - so the
    caller answers 400 rather than 500.
    """
    if kind not in CHART_KINDS:
      raise ValueError(
          f"chart kind '{kind}' is not supported (must be one of {', '.join(CHART_KINDS)})"
      )
    for column in (x, y) + ((series,) if series else ()):
        if column not in columns:
            raise ValueError(f"column '{column}' is not part of the run result")

    _anchor = kind == "bar"  # bar lengths must read as magnitude from zero
    data = _series_of(_records(columns, rows), x, y, series)
    if not data or not any(points for _, points in data):
        raise ValueError("no plottable points: the measure column may be empty or non-numeric")

    values = [value for _, points in data for _, value in points]
    low, high, step = _nice_scale(min(values), max(values), _anchor)

    plot_w = width - _MARGIN_LEFT - _MARGIN_RIGHT
    plot_h = height - _MARGIN_TOP - _MARGIN_BOTTOM
    categories = list(dict.fromkeys(cat for _, points in data for cat, _ in points))
    n = max(len(categories), 1)

    def px(category) -> float:
        return _MARGIN_LEFT + (categories.index(category) + 0.5) * (plot_w / n)

    def py(value: float) -> float:
        return _MARGIN_TOP + plot_h * (1 - (value - low) / (high - low))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}" font-family="sans-serif">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
    ]
    if title:
        parts.append(
            f'<text x="{width / 2}" y="{_MARGIN_TOP / 2}" text-anchor="middle"'
            f' font-size="16" font-weight="bold">{escape(title)}</text>'
        )

    # Gridlines and y-axis ticks.
    tick = low
    while tick <= high + 1e-9:
        y_px = py(tick)
        parts.append(
            f'<line x1="{_MARGIN_LEFT}" y1="{y_px:.1f}" x2="{width - _MARGIN_RIGHT}"'
            f' y2="{y_px:.1f}" stroke="#e5e7eb"/>'
        )
        parts.append(
            f'<text x="{_MARGIN_LEFT - 8}" y="{y_px + 4:.1f}" text-anchor="end"'
            f' font-size="11" fill="#4b5563">{_label(round(tick, 6))}</text>'
        )
        tick += step
    parts.append(
        f'<line x1="{_MARGIN_LEFT}" y1="{_MARGIN_TOP}" x2="{_MARGIN_LEFT}"'
        f' y2="{_MARGIN_TOP + plot_h}" stroke="#9ca3af"/>'
    )

    # X-axis category labels, rotated when they crowd.
    rotate = len(categories) > 6 or any(len(cat) > 8 for cat in categories)
    for category in categories:
        cx = px(category)
        if rotate:
            parts.append(
                f'<text x="{cx:.1f}" y="{_MARGIN_TOP + plot_h + 12}" text-anchor="end"'
                f' font-size="11" fill="#4b5563" transform="rotate(-35 {cx:.1f}'
                f' {_MARGIN_TOP + plot_h + 12})">{category}</text>'
            )
        else:
            parts.append(
                f'<text x="{cx:.1f}" y="{_MARGIN_TOP + plot_h + 18}" text-anchor="middle"'
                f' font-size="11" fill="#4b5563">{category}</text>'
            )
    parts.append(
        f'<text x="{_MARGIN_LEFT + plot_w / 2}" y="{height - 6}" text-anchor="middle"'
        f' font-size="12" fill="#374151">{escape(x)}</text>'
    )

    palette = ["#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed", "#db2777"]
    bar_slot = plot_w / n * 0.6

    for index, (name, points) in enumerate(data):
        color = palette[index % len(palette)]
        if kind == "bar":
            width_each = bar_slot / max(len(data), 1)
            for category, value in points:
                x0 = px(category) - bar_slot / 2 + index * width_each
                y0 = py(max(value, low))
                rect_h = abs(py(value) - py(low)) or 1.0
                parts.append(
                    f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{width_each * 0.9:.1f}"'
                    f' height="{rect_h:.1f}" fill="{color}" rx="2"/>'
                )
        else:
            line = " ".join(
                f"{px(category):.1f},{py(value):.1f}" for category, value in points
            )
            parts.append(
                f'<polyline points="{line}" fill="none" stroke="{color}"'
                f' stroke-width="2" stroke-linejoin="round"/>'
            )
            for category, value in points:
                parts.append(
                    f'<circle cx="{px(category):.1f}" cy="{py(value):.1f}" r="3"'
                    f' fill="{color}"/>'
                )

    if len(data) > 1:
        legend_x = width - _MARGIN_RIGHT - 10
        for index, (name, _) in enumerate(reversed(data)):
            ly = _MARGIN_TOP + index * 18
            parts.append(
                f'<rect x="{legend_x - 14}" y="{ly - 9}" width="10" height="10"'
                f' fill="{palette[(len(data) - 1 - index) % len(palette)]}"/>'
            )
            parts.append(
                f'<text x="{legend_x}" y="{ly}" font-size="11" fill="#374151">{name}</text>'
            )

    parts.append("</svg>")
    return "".join(parts).encode("utf-8")
