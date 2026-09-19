"""Deterministic chart renderer (P2-ANALYSIS-009, P3-CHART-002).

Turns a persisted run result (columns + rows) into a chart that is stored as
part of the case's evidence, next to the run and the finding it supports.

The chart is rendered server-side rather than in the browser on purpose. A chart
that is part of a trust chain has to be an artifact: persisted, reproducible
from the stored result, and viewable without whatever frontend visits it later.
The SVG backend is dependency-free and deterministic - the same run plus the
same parameters always yield byte-identical output - which is also what makes it
testable without comparing pixels. The PNG backend (P3-CHART-002) rasterises the
same geometry behind the same interface for consumers that need a bitmap;
Pillow is an optional dependency, so the core loop never needs it.

Only the essentials: `bar` and `line`, one or more series. Richer chart types
can replace this implementation behind the same `render_chart` interface
(Master Spec: visualization is a replaceable surface).
"""

import io
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


CHART_FORMATS = ("svg", "png")

_PALETTE = ["#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed", "#db2777"]

# PNG is drawn at this multiple of the target size and downscaled, which is what
# gives anti-aliased lines and text with Pillow's built-in bitmap font.
_PNG_SUPERSAMPLE = 2


class ChartModel:
    """A computed chart: geometry plus the data both renderers need.

    Everything device-independent lives here so the SVG and PNG backends cannot
    drift apart - one scale, one category order, one bar geometry.
    """

    def __init__(
        self,
        kind: str,
        columns: list[str],
        rows: list[list],
        x: str,
        y: str,
        series: str | None,
        title: str,
        width: int,
        height: int,
    ) -> None:
        if kind not in CHART_KINDS:
            raise ValueError(
                f"chart kind '{kind}' is not supported "
                f"(must be one of {', '.join(CHART_KINDS)})"
            )
        for column in (x, y) + ((series,) if series else ()):
            if column not in columns:
                raise ValueError(f"column '{column}' is not part of the run result")

        self.kind = kind
        self.x = x
        self.y = y
        self.series = series
        self.title = title
        self.width = width
        self.height = height
        self.anchor_at_zero = kind == "bar"  # bar length reads as magnitude

        data = _series_of(_records(columns, rows), x, y, series)
        if not data or not any(points for _, points in data):
            raise ValueError(
                "no plottable points: the measure column may be empty or non-numeric"
            )
        values = [value for _, points in data for _, value in points]
        self.low, self.high, self.step = _nice_scale(
            min(values), max(values), self.anchor_at_zero
        )

        self.categories = list(
            dict.fromkeys(cat for _, points in data for cat, _ in points)
        )
        self.series_data = [
            (name, _PALETTE[index % len(_PALETTE)], points)
            for index, (name, points) in enumerate(data)
        ]
        self.rotate_labels = len(self.categories) > 6 or any(
            len(cat) > 8 for cat in self.categories
        )

        self.plot_w = width - _MARGIN_LEFT - _MARGIN_RIGHT
        self.plot_h = height - _MARGIN_TOP - _MARGIN_BOTTOM

    @property
    def ticks(self) -> list[float]:
        """Y-axis tick values from low to high."""
        result = []
        tick = self.low
        while tick <= self.high + 1e-9:
            result.append(tick)
            tick += self.step
        return result

    def px(self, category) -> float:
        n = max(len(self.categories), 1)
        return _MARGIN_LEFT + (self.categories.index(category) + 0.5) * (self.plot_w / n)

    def py(self, value: float) -> float:
        return _MARGIN_TOP + self.plot_h * (1 - (value - self.low) / (self.high - self.low))

    def bar_slot(self) -> float:
        n = max(len(self.categories), 1)
        return self.plot_w / n * 0.6


def _validate_format(fmt: str) -> str:
    if fmt not in CHART_FORMATS:
        raise ValueError(
            f"chart format '{fmt}' is not supported "
            f"(must be one of {', '.join(CHART_FORMATS)})"
        )
    return fmt


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
    fmt: str = "svg",
) -> bytes:
    """Render a persisted run result to SVG (default) or PNG.

    Raises ValueError for anything the chart contract rejects - unknown kind or
    format, unknown columns, a non-numeric measure, or no plottable points - so
    the caller answers 400 rather than 500.
    """
    _validate_format(fmt)
    model = ChartModel(kind, columns, rows, x, y, series, title, width, height)
    if fmt == "png":
        return _render_png(model)
    return _render_svg(model)


def _render_svg(model: ChartModel) -> bytes:
    width, height = model.width, model.height
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}" font-family="sans-serif">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
    ]
    if model.title:
        parts.append(
            f'<text x="{width / 2}" y="{_MARGIN_TOP / 2}" text-anchor="middle"'
            f' font-size="16" font-weight="bold">{escape(model.title)}</text>'
        )

    # Gridlines and y-axis ticks.
    for tick in model.ticks:
        y_px = model.py(tick)
        parts.append(
            f'<line x1="{_MARGIN_LEFT}" y1="{y_px:.1f}" x2="{width - _MARGIN_RIGHT}"'
            f' y2="{y_px:.1f}" stroke="#e5e7eb"/>'
        )
        parts.append(
            f'<text x="{_MARGIN_LEFT - 8}" y="{y_px + 4:.1f}" text-anchor="end"'
            f' font-size="11" fill="#4b5563">{_label(round(tick, 6))}</text>'
        )
    parts.append(
        f'<line x1="{_MARGIN_LEFT}" y1="{_MARGIN_TOP}" x2="{_MARGIN_LEFT}"'
        f' y2="{_MARGIN_TOP + model.plot_h}" stroke="#9ca3af"/>'
    )

    # X-axis category labels, rotated when they crowd.
    for category in model.categories:
        cx = model.px(category)
        if model.rotate_labels:
            parts.append(
                f'<text x="{cx:.1f}" y="{_MARGIN_TOP + model.plot_h + 12}" text-anchor="end"'
                f' font-size="11" fill="#4b5563" transform="rotate(-35 {cx:.1f}'
                f' {_MARGIN_TOP + model.plot_h + 12})">{category}</text>'
            )
        else:
            parts.append(
                f'<text x="{cx:.1f}" y="{_MARGIN_TOP + model.plot_h + 18}"'
                f' text-anchor="middle" font-size="11" fill="#4b5563">{category}</text>'
            )
    parts.append(
        f'<text x="{_MARGIN_LEFT + model.plot_w / 2}" y="{height - 6}"'
        f' text-anchor="middle" font-size="12" fill="#374151">{escape(model.x)}</text>'
    )

    bar_slot = model.bar_slot()
    for series_index, (name, color, points) in enumerate(model.series_data):
        if model.kind == "bar":
            width_each = bar_slot / max(len(model.series_data), 1)
            for category, value in points:
                x0 = model.px(category) - bar_slot / 2 + series_index * width_each
                y0 = model.py(max(value, model.low))
                rect_h = abs(model.py(value) - model.py(model.low)) or 1.0
                parts.append(
                    f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{width_each * 0.9:.1f}"'
                    f' height="{rect_h:.1f}" fill="{color}" rx="2"/>'
                )
        else:
            line = " ".join(
                f"{model.px(category):.1f},{model.py(value):.1f}"
                for category, value in points
            )
            parts.append(
                f'<polyline points="{line}" fill="none" stroke="{color}"'
                f' stroke-width="2" stroke-linejoin="round"/>'
            )
            for category, value in points:
                parts.append(
                    f'<circle cx="{model.px(category):.1f}" cy="{model.py(value):.1f}"'
                    f' r="3" fill="{color}"/>'
                )

    if len(model.series_data) > 1:
        legend_x = width - _MARGIN_RIGHT - 10
        for index, (name, color) in enumerate(
            [(n, c) for n, c, _ in reversed(model.series_data)]
        ):
            ly = _MARGIN_TOP + index * 18
            parts.append(
                f'<rect x="{legend_x - 14}" y="{ly - 9}" width="10" height="10"'
                f' fill="{color}"/>'
            )
            parts.append(
                f'<text x="{legend_x}" y="{ly}" font-size="11" fill="#374151">'
                f'{escape(name)}</text>'
            )

    parts.append("</svg>")
    return "".join(parts).encode("utf-8")


def _hex_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _render_png(model: ChartModel) -> bytes:
    """Rasterise the same geometry the SVG backend draws.

    Pillow is an optional dependency (`pip install dah-server[charts]`); the
    SVG backend stays dependency-free so the core loop never needs it. Drawing
    happens at 2x and is downscaled with LANCZOS, which is what makes lines and
    the bitmap font look smooth.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:
        raise ValueError(
            "raster charts require the 'charts' extra "
            "(pip install dah-server[charts]): pillow is not installed"
        ) from error

    scale = _PNG_SUPERSAMPLE
    width = model.width * scale
    height = model.height * scale
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    def font(size: int):
        return ImageFont.load_default(size=size * scale)

    def px(category) -> float:
        return model.px(category) * scale

    def py(value: float) -> float:
        return model.py(value) * scale

    if model.title:
        draw.text(
            (width / 2, _MARGIN_TOP * scale / 2),
            model.title,
            fill=(17, 24, 39),
            font=font(16),
            anchor="mm",
        )

    # Gridlines and y-axis ticks.
    for tick in model.ticks:
        y_px = py(tick)
        draw.line(
            [(_MARGIN_LEFT * scale, y_px), ((model.width - _MARGIN_RIGHT) * scale, y_px)],
            fill=(229, 231, 235),
        )
        draw.text(
            ((_MARGIN_LEFT - 8) * scale, y_px),
            _label(round(tick, 6)),
            fill=(75, 85, 99),
            font=font(11),
            anchor="rm",
        )
    draw.line(
        [(_MARGIN_LEFT * scale, _MARGIN_TOP * scale),
         (_MARGIN_LEFT * scale, (_MARGIN_TOP + model.plot_h) * scale)],
        fill=(156, 163, 175),
    )

    # X-axis category labels, rotated when they crowd.
    baseline = (_MARGIN_TOP + model.plot_h) * scale
    for category in model.categories:
        cx = model.px(category) * scale
        if model.rotate_labels:
            draw.text(
                (cx, baseline + 12 * scale),
                category,
                fill=(75, 85, 99),
                font=font(11),
                anchor="rs",
            )
        else:
            draw.text(
                (cx, baseline + 18 * scale),
                category,
                fill=(75, 85, 99),
                font=font(11),
                anchor="ms",
            )
    draw.text(
        ((_MARGIN_LEFT + model.plot_w / 2) * scale, (model.height - 12) * scale),
        model.x,
        fill=(55, 65, 81),
        font=font(12),
        anchor="mm",
    )

    bar_slot = model.bar_slot() * scale
    for series_index, (name, color, points) in enumerate(model.series_data):
        rgb = _hex_rgb(color)
        if model.kind == "bar":
            width_each = bar_slot / max(len(model.series_data), 1)
            for category, value in points:
                x0 = px(category) - bar_slot / 2 + series_index * width_each
                y0 = py(max(value, model.low))
                rect_h = abs(py(value) - py(model.low)) or 1.0
                draw.rectangle(
                    [x0, y0, x0 + width_each * 0.9, y0 + rect_h],
                    fill=rgb,
                )
        else:
            line = [
                (px(category), py(value)) for category, value in points
            ]
            draw.line(line, fill=rgb, width=2 * scale, joint="curve")
            for cx, cy in line:
                draw.ellipse([cx - 3 * scale, cy - 3 * scale, cx + 3 * scale, cy + 3 * scale], fill=rgb)

    if len(model.series_data) > 1:
        legend_x = (model.width - _MARGIN_RIGHT - 10) * scale
        for index, (name, color) in enumerate(
            [(n, c) for n, c, _ in reversed(model.series_data)]
        ):
            ly = (_MARGIN_TOP + index * 18) * scale
            draw.rectangle([legend_x - 14 * scale, ly - 9 * scale, legend_x - 4 * scale, ly + scale],
                           fill=_hex_rgb(color))
            draw.text((legend_x, ly), name, fill=(55, 65, 81), font=font(11), anchor="lm")

    downscaled = image.resize((model.width, model.height), Image.LANCZOS)
    buffer = io.BytesIO()
    downscaled.save(buffer, format="PNG")
    return buffer.getvalue()
