"""Exploratory analysis operations (P3-ANALYSIS-005).

Segmentation, correlation, and distribution summaries over an attached dataset.
These are the "what should I look at first" steps that sit between profiling and
a hand-written query.

Every op compiles to a read-only DuckDB statement and runs through the same
`run_query` the SQL endpoint uses - one engine, one read-only gate, one row cap
(DEC-001). That keeps EDA deterministic and its output in the standard result
shape, so a chart can be rendered from it the same way as any run.

EDA is exploration, not evidence: results are not persisted as runs, because a
finding must be anchored on a reproducible query the analyst wrote (Master Spec
section 10). When an interesting segment or correlation turns up, the analyst
runs the equivalent query to make it evidence.
"""

from app.analysis import run_query

EDA_OPS = ("segment", "correlate", "distribution")

_MAX_CATEGORIES = 20


def _quote(column: str) -> str:
    """Quote an identifier defensively; a quote in the name is refused.

    Column names come from the request, not from the file, so they are never
    interpolated raw.
    """
    if not column or '"' in column:
        raise ValueError(f"column name '{column}' is not usable")
    return f'"{column}"'


def _columns_of(path: str) -> list[str]:
    return run_query(path, "SELECT * FROM read_csv_auto(?) LIMIT 0")["columns"]


def _require(path: str, *names: str) -> None:
    present = _columns_of(path)
    for name in names:
        if name not in present:
            raise ValueError(f"column '{name}' is not part of the dataset")


def _segment(path: str, by: str, measure: str) -> dict:
    """Group the measure by a categorical column, with spread and centre."""
    _require(path, by, measure)
    sql = (
        f"SELECT {_quote(by)} AS segment, COUNT(*) AS rows, "
        f"AVG({_quote(measure)}) AS mean, MEDIAN({_quote(measure)}) AS median, "
        f"MIN({_quote(measure)}) AS min, MAX({_quote(measure)}) AS max, "
        f"STDDEV_SAMP({_quote(measure)}) AS stddev "
        f"FROM read_csv_auto(?) GROUP BY {_quote(by)} ORDER BY {_quote(by)}"
    )
    return run_query(path, sql)


def _correlate(path: str, x: str, y: str) -> dict:
    """Pearson correlation between two numeric columns."""
    _require(path, x, y)
    sql = (
        f"SELECT CORR({_quote(x)}, {_quote(y)}) AS pearson_r, "
        f"COUNT(*) AS paired_rows FROM read_csv_auto(?)"
    )
    result = run_query(path, sql)
    if result["rows"] and result["rows"][0][0] is None:
        raise ValueError(
            f"no paired numeric values in '{x}' and '{y}' to correlate"
        )
    return result


def _column_types(path: str) -> dict[str, str]:
    """DuckDB's own type for each column, so EDA picks the right summary."""
    described = run_query(path, "DESCRIBE SELECT * FROM read_csv_auto(?)")
    return {
        row[0]: str(row[1])
        for row in described["rows"]
    }


def _is_numeric(type_name: str) -> bool:
    upper = type_name.upper()
    return any(
        upper.startswith(family)
        for family in (
            "TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT",
            "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT",
            "FLOAT", "DOUBLE", "REAL", "DECIMAL",
        )
    )


def _distribution(path: str, column: str) -> dict:
    """A numeric spread summary, or the most common values for a category."""
    _require(path, column)
    numeric = _is_numeric(_column_types(path).get(column, ""))
    if not numeric:
        # Non-numeric: the useful summary is which values dominate.
        sql = (
            f"SELECT {_quote(column)} AS value, COUNT(*) AS rows "
            f"FROM read_csv_auto(?) WHERE {_quote(column)} IS NOT NULL "
            f"GROUP BY {_quote(column)} ORDER BY rows DESC, value ASC "
            f"LIMIT {_MAX_CATEGORIES}"
        )
        return run_query(path, sql)
    sql = (
        f"SELECT COUNT(*) AS rows, "
        f"MIN({_quote(column)}) AS min, MAX({_quote(column)}) AS max, "
        f"AVG({_quote(column)}) AS mean, MEDIAN({_quote(column)}) AS median, "
        f"QUANTILE_CONT({_quote(column)}, 0.25) AS q1, "
        f"QUANTILE_CONT({_quote(column)}, 0.75) AS q3, "
        f"STDDEV_SAMP({_quote(column)}) AS stddev "
        f"FROM read_csv_auto(?) WHERE {_quote(column)} IS NOT NULL"
    )
    return run_query(path, sql)


def run_eda(path: str, op: str, params: dict) -> dict:
    """Run one EDA op. Raises ValueError for anything the contract rejects."""
    if op not in EDA_OPS:
        raise ValueError(
            f"eda op '{op}' is not supported "
            f"(must be one of {', '.join(EDA_OPS)})"
        )
    if op == "segment":
        for key in ("by", "measure"):
            if not params.get(key):
                raise ValueError(f"eda '{op}' needs a '{key}' column")
        return _segment(path, params["by"], params["measure"])
    if op == "correlate":
        for key in ("x", "y"):
            if not params.get(key):
                raise ValueError(f"eda '{op}' needs a '{key}' column")
        return _correlate(path, params["x"], params["y"])
    if not params.get("column"):
        raise ValueError("eda 'distribution' needs a 'column'")
    return _distribution(path, params["column"])
