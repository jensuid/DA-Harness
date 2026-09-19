"""Restricted Python execution engine for the Analysis Workspace (P2-ANALYSIS-008).

This is the Python counterpart to analysis.run_query: user Python runs against an
attached dataset and yields a table that persists in the same `runs` store, so
findings, evidence, and validation treat SQL and Python runs identically.

The user code is handed a `dataset` handle with read-only access to the attached
file:

    result = [
        {"region": row["region"], "share": row["revenue"] / total}
        for row in dataset.rows
    ]

`dataset.query(sql)` runs a read-only DuckDB query under the same gate as the SQL
engine; `dataset.rows` is the whole table as a list of dicts (row-capped, like
every other result in this system). The script leaves its answer in `result`; a
list of dicts (or a list of lists) becomes the run's columns and rows.

Threat posture (Master Spec section on external engines; Verification plan,
"Python" risks: filesystem access, process execution, network, exhaustion):

    blocked   - filesystem writes (no `open`, no os/shutil/pathlib imports),
                process execution and network egress (import allowlist),
                resource exhaustion (wall-clock and CPU limits).
    also      - dunder access on the injected handle is refused, so casual
                escapes like `dataset.query.__globals__` do not reach the engine.

This is a *soft* sandbox suited to a local-first single-user tool: it stops
accidental writes and runaway AI-generated code, not a hostile user who already
owns the machine. A hard OS-level sandbox (separate process under sandbox-exec /
landlock) is the V1 follow-up and is tracked as such.
"""

import builtins
import resource
import signal
import sys
import threading
from contextlib import contextmanager
from typing import Any, Iterator

from app.analysis import run_query

# Modules the user code may import. Everything else - subprocess, socket, os,
# ctypes, multiprocessing, urllib, http, importlib - is refused by the import
# hook. openpyxl/pyarrow are included because the dataset reader needs them when
# the attached file is xlsx; both are read-only data readers.
_SAFE_MODULES = frozenset(
    {
        "math",
        "statistics",
        "json",
        "re",
        "collections",
        "itertools",
        "functools",
        "operator",
        "string",
        "unicodedata",
        "datetime",
        "decimal",
        "fractions",
        "html",
        "textwrap",
        "openpyxl",
        "pyarrow",
    }
)

# Builtins the user code may call. Deliberately absent: open, exec, eval,
# compile, __import__, input, breakpoint, globals, locals, vars, dir, getattr,
# hasattr, setattr, delattr, type, super, property, memoryview, object.
_ALLOWED_BUILTINS = frozenset(
    {
        "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
        "chr", "complex", "dict", "divmod", "enumerate", "filter", "float",
        "format", "frozenset", "hex", "int", "isinstance", "iter", "len",
        "list", "map", "max", "min", "next", "oct", "ord", "pow", "print",
        "range", "repr", "reversed", "round", "set", "slice", "sorted", "str",
        "sum", "tuple", "zip", "True", "False", "None",
        "BaseException", "Exception", "ArithmeticError", "AssertionError",
        "AttributeError", "FloatingPointError", "ImportError", "IndexError",
        "KeyError", "LookupError", "NameError", "NotImplementedError",
        "OverflowError", "RuntimeError", "StopIteration", "TypeError",
        "UnboundLocalError", "ValueError", "ZeroDivisionError",
    }
)

# Wall-clock and CPU seconds for one run, and the address-space ceiling.
_DEFAULT_TIMEOUT_SECONDS = 30
_DEFAULT_CPU_SECONDS = _DEFAULT_TIMEOUT_SECONDS + 5


class _DatasetQuery:
    """A bound, dunder-hardened callable that runs read-only SQL on the file.

    Attribute lookups for names starting with "_" are refused so user code
    cannot walk from the handle to the engine's own globals. Calling still
    works: `obj(...)` resolves `__call__` on the type, not the instance.
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def __call__(self, sql: str) -> dict:
        return run_query(self.path, sql)

    def __getattribute__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return object.__getattribute__(self, name)


class _DatasetHandle:
    """The read-only view of an attached dataset that user code receives."""

    def __init__(self, path: str, columns: list[str]) -> None:
        self.path = path
        self.columns = columns

    @property
    def query(self) -> _DatasetQuery:
        return _DatasetQuery(self.path)

    @property
    def rows(self) -> list[dict]:
        return _rows_as_dicts(self.path)

    def __getattribute__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return object.__getattribute__(self, name)


def _dataset_columns(path: str) -> list[str]:
    """Column names of the attached file, without materialising any rows."""
    return run_query(path, "SELECT * FROM read_csv_auto(?) LIMIT 0")["columns"]


def _rows_as_dicts(path: str) -> list[dict]:
    """The attached file as a list of row dicts, under the standard row cap."""
    result = run_query(path, "SELECT * FROM read_csv_auto(?)")
    return [dict(zip(result["columns"], row)) for row in result["rows"]]


class _Timeout(Exception):
    """Raised in the signal handler when a run exceeds its wall clock."""


def _alarm_handler(signum, frame) -> None:
    raise _Timeout("analysis exceeded the time limit")


class _ImportGuard:
    """A sys.meta_path finder that refuses everything outside the allowlist.

    Installed only for the duration of a run. Sitting ahead of the built-in
    finders means even frozen modules (sys, _io, _thread) are refused.
    """

    def find_spec(self, fullname: str, path=None, target=None) -> None:
        root = fullname.split(".", 1)[0]
        if root not in _SAFE_MODULES:
            raise ImportError(f"module '{fullname}' is not allowed in analysis code")
        return None


_install_lock = threading.Lock()
_install_count = 0
_guard = _ImportGuard()


@contextmanager
def _import_restrictions() -> Iterator[None]:
    """Install the import guard, refcounting so concurrent runs stay covered."""
    global _install_count
    with _install_lock:
        if _install_count == 0:
            sys.meta_path.insert(0, _guard)
        _install_count += 1
    try:
        yield
    finally:
        with _install_lock:
            _install_count -= 1
            if _install_count == 0 and _guard in sys.meta_path:
                sys.meta_path.remove(_guard)


@contextmanager
def _resource_limits(timeout_seconds: int) -> Iterator[None]:
    """Bound wall clock and CPU time, restoring both afterwards.

    Address space is deliberately not capped: on macOS the process already
    maps far more virtual memory than a useful limit allows, so an RLIMIT_AS
    bound rejects the run outright rather than restraining it. A real memory
    bound needs a separate process, which arrives with the V1 hard sandbox.
    """
    prev_cpu = resource.getrlimit(resource.RLIMIT_CPU)
    resource.setrlimit(resource.RLIMIT_CPU, (_DEFAULT_CPU_SECONDS, prev_cpu[1]))

    in_main_thread = threading.current_thread() is threading.main_thread()
    prev_handler = None
    if in_main_thread:
        # Signal handlers can only be registered on the main thread; worker
        # threads still get the CPU bound.
        prev_handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(timeout_seconds)
    try:
        yield
    finally:
        if in_main_thread:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, prev_handler)
        resource.setrlimit(resource.RLIMIT_CPU, prev_cpu)


def _restricted_builtins() -> dict:
    """The builtins namespace user code sees."""
    namespace = {
        name: getattr(builtins, name)
        for name in _ALLOWED_BUILTINS
        if hasattr(builtins, name)
    }
    # The import statement resolves through __import__, so a guarded copy is
    # what makes `import statistics` work while `import subprocess` is
    # refused with a message the caller can understand. The meta_path guard
    # covers any import path that reaches the machinery another way.
    namespace["__import__"] = _guarded_import
    return namespace


_real_import = builtins.__import__


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".", 1)[0]
    if root not in _SAFE_MODULES:
        raise ImportError(f"module '{name}' is not allowed in analysis code")
    return _real_import(name, globals, locals, fromlist, level)


def _tabulate(result: Any) -> dict:
    """Turn the script's `result` into the columns/rows shape runs persist.

    A list of dicts names its own columns; a list of lists gets positional
    names. Anything else is rejected with a message the caller can surface.
    """
    if not isinstance(result, list):
        raise ValueError("analysis code must leave a list of rows in `result`")

    if not result:
        return {"columns": [], "rows": [], "row_count": 0, "truncated": False}

    if all(isinstance(row, dict) for row in result):
        # Column order is the order keys first appear in, so a row missing a
        # late key still lands in the right place.
        columns: list[str] = []
        for row in result:
            for key in row:
                if key not in columns:
                    columns.append(key)
        rows = [[row.get(column) for column in columns] for row in result]
    elif all(isinstance(row, (list, tuple)) for row in result):
        width = max(len(row) for row in result)
        columns = [f"col_{i}" for i in range(width)]
        rows = [list(row) + [None] * (width - len(row)) for row in result]
    else:
        raise ValueError(
            "every row in `result` must be a dict or a list/tuple of values"
        )
    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": False,
    }


def run_python(
    path: str,
    source: str,
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """Execute user Python against one attached dataset and tabulate `result`.

    Raises ValueError for anything the analysis contract rejects - unsafe
    imports, missing `result`, the wrong row shape - so the caller can answer
    400 rather than 500.
    """
    if not source.strip():
        raise ValueError("analysis code is empty")

    handle = _DatasetHandle(path, _dataset_columns(path))
    namespace = {
        "__builtins__": _restricted_builtins(),
        "dataset": handle,
        "result": None,
    }

    with _import_restrictions(), _resource_limits(timeout_seconds):
        try:
            exec(compile(source, "<analysis>", "exec"), namespace)
        except _Timeout as error:
            raise ValueError(str(error)) from error
        except ImportError as error:
            raise ValueError(str(error)) from error

    return _tabulate(namespace.get("result"))
