"""The Python execution guards, tested in the process that enforces them.

The inner wall - the import allowlist, the restricted builtins, the
dunder-hardened dataset handle, the tabulation of `result` - is what the
sandboxed *child* process runs, so the suite's in-process line counter cannot
see it exercised: the lines run in a process the measurement does not
instrument, and the module's own docstring says so. Testing the guards
directly is worth more than relying on the child to reach them, because these
are the security-relevant branches (AT-36): the dunder walk to the engine's
globals, the import of a module that can open a socket, the builtins a script
may not call, and the shapes a `result` may not take.
"""

from __future__ import annotations

import csv
import io

import pytest

from app import python_exec


def _csv(tmp_path) -> str:
    path = tmp_path / "data.csv"
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["region", "revenue"])
        for index in range(5):
            writer.writerow([["north", "south"][index % 2], 100 * (index + 1)])
    return str(path)


# --------------------------------------------------------- the dunder-hardened handle

def test_the_handle_refuses_the_dunder_walk(tmp_path) -> None:
    """`dataset._path` must not reach the engine's internals."""
    handle = python_exec._DatasetHandle(_csv(tmp_path), ["region", "revenue"])
    # The public names work; the underscore-prefixed ones are the walk to the
    # engine's own globals, and the guard refuses them.
    assert handle.path.endswith("data.csv")
    with pytest.raises(AttributeError):
        handle._path
    with pytest.raises(AttributeError):
        handle._anything


def test_the_handle_exposes_query_and_rows(tmp_path) -> None:
    handle = python_exec._DatasetHandle(_csv(tmp_path), ["region", "revenue"])
    assert handle.columns == ["region", "revenue"]
    rows = handle.rows
    assert len(rows) == 5
    assert rows[0]["region"] == "north"
    result = handle.query("SELECT region, SUM(revenue) FROM read_csv_auto(?) GROUP BY region")
    assert result["columns"][0] == "region"


def test_the_query_handle_also_refuses_dunders(tmp_path) -> None:
    """The callable's own attributes are guarded the same way."""
    query = python_exec._DatasetHandle(_csv(tmp_path), []).query
    assert callable(query)
    with pytest.raises(AttributeError):
        query._path


def test_the_query_handle_runs_read_only_sql(tmp_path) -> None:
    query = python_exec._DatasetHandle(_csv(tmp_path), []).query
    with pytest.raises(ValueError):
        query("DELETE FROM read_csv_auto(?)")
    assert query("SELECT COUNT(*) AS n FROM read_csv_auto(?)")["rows"] == [[5]]


# --------------------------------------------------------------- the import wall

def test_the_import_guard_refuses_unsafe_modules() -> None:
    """`import subprocess` is refused with a sentence, whatever the path."""
    with pytest.raises(ImportError, match="not allowed"):
        python_exec._guarded_import("subprocess")
    with pytest.raises(ImportError, match="not allowed"):
        python_exec._guarded_import("os.path")
    guard = python_exec._ImportGuard()
    with pytest.raises(ImportError):
        guard.find_spec("socket")
    # An allowed module is left to the ordinary finders, not answered by us.
    assert guard.find_spec("statistics") is None


def test_the_import_guard_allows_the_whitelist() -> None:
    assert python_exec._guarded_import("statistics").mean([1, 2, 3]) == 2
    assert python_exec._guarded_import("math", fromlist=("sqrt",)) is not None


def test_the_import_restrictions_install_and_remove_the_guard() -> None:
    """The meta_path finder sits ahead of the built-ins only for the run."""
    import sys

    before = list(sys.meta_path)
    with python_exec._import_restrictions():
        assert python_exec._guard in sys.meta_path
        with pytest.raises(ImportError):
            python_exec._guarded_import("subprocess")
    assert python_exec._guard not in sys.meta_path
    assert sys.meta_path == before


# ------------------------------------------------------------- the builtin wall

def test_the_builtins_omit_the_dangerous_names() -> None:
    """Deliberately absent: open, exec, eval, compile, __import__."""
    namespace = python_exec._restricted_builtins()
    for name in ("open", "exec", "eval", "compile", "input", "globals", "type"):
        assert name not in namespace, f"{name} must not reach analysis code"
    assert namespace["__import__"] is python_exec._guarded_import
    assert namespace["sum"]([1, 2]) == 3


# ------------------------------------------------------------------ tabulation

def test_tabulation_names_dicts_columns_in_first_seen_order() -> None:
    """A row missing a late key still lands in its column."""
    table = python_exec._tabulate([{"a": 1, "b": 2}, {"a": 3}])
    assert table == {
        "columns": ["a", "b"],
        "rows": [[1, 2], [3, None]],
        "row_count": 2,
        "truncated": False,
    }


def test_tabulation_pads_short_lists_to_the_widest_row() -> None:
    table = python_exec._tabulate([[1, 2], [3]])
    assert table["columns"] == ["col_0", "col_1"]
    assert table["rows"] == [[1, 2], [3, None]]


def test_tabulation_rejects_shapes_that_are_not_rows() -> None:
    """The measurement can fail: a bad `result` is a 400, not a 500."""
    with pytest.raises(ValueError, match="must leave a list"):
        python_exec._tabulate({"not": "a list"})
    with pytest.raises(ValueError, match="dict or a list"):
        python_exec._tabulate([{"a": 1}, ["mixed", "rows"]])


def test_an_empty_result_is_an_empty_table() -> None:
    assert python_exec._tabulate([]) == {
        "columns": [], "rows": [], "row_count": 0, "truncated": False,
    }


# ------------------------------------------------------- in-process execution

def test_execute_user_code_runs_and_tabulates(tmp_path, no_cpu_limit) -> None:
    """The inner engine itself, in the process that measures it."""
    path = _csv(tmp_path)
    table = python_exec.execute_user_code(
        path,
        "result = [{'region': r['region'], 'total': r['revenue']} "
        "for r in dataset.rows]",
    )
    assert table["row_count"] == 5
    assert table["columns"] == ["region", "total"]


def test_execute_user_code_refuses_an_empty_script(tmp_path, no_cpu_limit) -> None:
    with pytest.raises(ValueError, match="empty"):
        python_exec.execute_user_code(_csv(tmp_path), "   ")


def test_execute_user_code_refuses_an_unsafe_import(tmp_path, no_cpu_limit) -> None:
    """The import wall answers a 400-shaped ValueError, in-process too."""
    with pytest.raises(ValueError, match="not allowed"):
        python_exec.execute_user_code(_csv(tmp_path), "import socket")


def test_execute_user_code_rejects_a_result_that_is_not_a_list(tmp_path, no_cpu_limit) -> None:
    with pytest.raises(ValueError, match="must leave a list"):
        python_exec.execute_user_code(_csv(tmp_path), "result = 5")


@pytest.fixture
def no_cpu_limit(monkeypatch):
    """Keep the suite's own process away from the CPU rlimit.

    `_resource_limits` sets an RLIMIT_CPU that applies to the whole process,
    and the limit is *cumulative*: in a suite that has already burned far more
    CPU seconds than one run is allowed, setting it would deliver SIGXCPU on
    the spot and kill the run. The sandboxed child is where that bound is meant
    to bite; here the setter is faked and the alarm and its handler stay real.
    """
    calls: dict = {"set": []}
    monkeypatch.setattr(
        python_exec.resource, "getrlimit", lambda which: (10, 20)
    )
    monkeypatch.setattr(
        python_exec.resource,
        "setrlimit",
        lambda which, limits: calls["set"].append((which, limits)),
    )
    return calls


def test_the_resource_limits_restore_what_they_set(no_cpu_limit) -> None:
    """The CPU bound and the SIGALRM handler are context-managed."""
    import signal

    with python_exec._resource_limits(5):
        assert signal.getsignal(signal.SIGALRM) is python_exec._alarm_handler
    # The limit is set on the way in - the soft bound to the run's budget,
    # the hard bound untouched - and the previous one restored on the way out.
    limits = [limits for _which, limits in no_cpu_limit["set"]]
    assert limits[0] == (python_exec._DEFAULT_CPU_SECONDS, 20)
    assert limits[-1] == (10, 20)
    # And the previous handler is put back.
    assert signal.getsignal(signal.SIGALRM) is not python_exec._alarm_handler


def test_the_alarm_handler_raises_the_timeout(no_cpu_limit) -> None:
    """The wall-clock guard raises, and the engine turns it into a 400."""
    import signal

    with pytest.raises(python_exec._Timeout):
        python_exec._alarm_handler(signal.SIGALRM, None)
    with pytest.raises(ValueError, match="time limit"):
        python_exec.execute_user_code(
            _csv_tmp(),
            "x = 0\nwhile x < 10 ** 12:\n    x += 1\n",
            timeout_seconds=1,
        )


def _csv_tmp() -> str:
    """A dataset for the timeout case, without pytest's tmp_path fixture."""
    import tempfile
    from pathlib import Path

    directory = Path(tempfile.mkdtemp(prefix="dah-guard-"))
    path = directory / "data.csv"
    path.write_text("region,revenue\nnorth,100\n")
    return str(path)
