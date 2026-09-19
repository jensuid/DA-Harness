"""Restricted Python execution engine for the Analysis Workspace.

The Python counterpart to analysis.run_query: user Python runs against an
attached dataset and yield a table that persists in the same `runs` store, so
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

    outer wall - the code runs in a *separate process* under an OS-level
                sandbox. On macOS that is sandbox-exec (seatbelt) with a
                profile that denies every filesystem write outside the run's
                scratch directory and denies all network access. On hosts
                without sandbox-exec the separate process still isolates the
                server: a crash, an infinite loop, or a wild allocation ends
                in the child, not in the API process.
    inner wall - the child keeps the in-process guards (import allowlist,
                restricted builtins, dunder-hardened handle, CPU and wall-clock
                limits). Even on a host with no OS sandbox the inner wall still
                refuses unsafe imports and filesystem writes; on a host with
                one, it is defense in depth.

Timeouts are enforced three ways, outermost first: the parent kills the child's
process group after the limit plus startup grace; the child's CPU rlimit bounds
burning loops; the child's SIGALRM bounds wall clock inside user code.

Validation of Python runs (reproducing the result by re-execution) is reported
as unsupported (a clear 400) rather than faked; that gate is future work.
"""

import builtins
import json
import os
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.analysis import run_query

# Modules the user code may import. Everything else - subprocess, socket, os,
# shutil, pathlib, ctypes, multiprocessing, urllib, http, importlib - is
# refused by the import hook. openpyxl/pyarrow are included because the dataset
# reader needs them when the attached file is xlsx; both are read-only readers.
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

# Wall-clock and CPU seconds for one run.
_DEFAULT_TIMEOUT_SECONDS = 30
_DEFAULT_CPU_SECONDS = _DEFAULT_TIMEOUT_SECONDS + 5

# Interpreter startup plus teardown on top of the user-code budget.
_STARTUP_GRACE_SECONDS = 20

_SERVER_ROOT = Path(__file__).resolve().parent.parent
_WORKER_MODULE = "app.python_worker"
_MAX_RESULT_BYTES = 64 * 1024 * 1024

# macOS seatbelt is the only OS sandbox wired up today; elsewhere the separate
# process plus the inner guards still apply. `which` is cheap, so it is checked
# per run rather than cached - a PATH change mid-process is rare but harmless.
_SANDBOX_BINARY = "sandbox-exec"


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

    Address space is deliberately not capped here: the hard sandbox's separate
    process is what carries memory risk, and on macOS an RLIMIT_AS bound
    rejects ordinary runs because the interpreter maps far more VM than a
    useful limit allows.
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


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".", 1)[0]
    if root not in _SAFE_MODULES:
        raise ImportError(f"module '{name}' is not allowed in analysis code")
    return builtins.__import__(name, globals, locals, fromlist, level)


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


def execute_user_code(
    path: str,
    source: str,
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """Run user code in this process under the inner guards.

    Used by the sandboxed worker; `run_python` is what the API calls. Raises
    ValueError for anything the analysis contract rejects - unsafe imports,
    missing `result`, the wrong row shape - so the caller can answer 400
    rather than 500.
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


def _seatbelt_profile(scratch_real: str) -> str:
    """The macOS sandbox-exec profile for one run.

    Reads are unrestricted (the interpreter, the stdlib, and the attached
    dataset all have to load). Writes are denied everywhere except the run's
    own scratch directory, and the network is denied outright.
    """
    return (
        "(version 1)\n"
        "(deny default)\n"
        "(allow process*)\n"
        "(allow file-read*)\n"
        "(deny file-write*)\n"
        f'(allow file-write* (subpath "{scratch_real}"))\n'
        "(deny network*)\n"
    )


def _child_env(scratch: str) -> dict[str, str]:
    """The minimal environment the worker inherits.

    The API process may carry DAH_LLM_API_KEY and other secrets; the worker
    never sees them, so user code cannot reach them even past the inner wall.
    """
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONPATH": str(_SERVER_ROOT),
        "TMPDIR": scratch,
        "LC_ALL": "C.UTF-8",
        "LANG": "C.UTF-8",
    }
    return {key: value for key, value in env.items() if value}


def _kill_group(process: subprocess.Popen) -> None:
    """Kill the worker and anything it spawned (sandbox-exec sits in between)."""
    try:
        group = os.getpgid(process.pid)
    except ProcessLookupError:
        return
    try:
        os.killpg(group, signal.SIGKILL)
    except ProcessLookupError:
        return
    except PermissionError:
        process.kill()


def run_python(
    path: str,
    source: str,
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """Execute user Python in a separate, OS-sandboxed process and tabulate it.

    Raises ValueError for anything the analysis contract rejects - unsafe
    imports, missing `result`, the wrong row shape, exceeding the time limit -
    so the caller can answer 400 rather than 500.
    """
    if not source.strip():
        raise ValueError("analysis code is empty")

    scratch = tempfile.mkdtemp(prefix="dah-exec-")
    job = {
        "dataset_path": path,
        "code": source,
        "timeout_seconds": timeout_seconds,
    }
    job_path = os.path.join(scratch, "job.json")
    with open(job_path, "w", encoding="utf-8") as handle:
        json.dump(job, handle)

    command = [sys.executable, "-B", "-s", "-m", _WORKER_MODULE, job_path]
    profile_path: str | None = None
    if shutil.which(_SANDBOX_BINARY) is not None:
        profile_path = os.path.join(scratch, "profile.sb")
        with open(profile_path, "w", encoding="utf-8") as handle:
            handle.write(_seatbelt_profile(os.path.realpath(scratch)))
        command = [_SANDBOX_BINARY, "-f", profile_path, *command]

    deadline = timeout_seconds + _STARTUP_GRACE_SECONDS
    process = subprocess.Popen(
        command,
        cwd=str(_SERVER_ROOT),
        env=_child_env(scratch),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=deadline)
    except subprocess.TimeoutExpired:
        _kill_group(process)
        process.wait()
        return _failure("analysis exceeded the time limit", scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    if process.returncode != 0:
        detail = (stderr or b"").decode("utf-8", "replace").strip()
        return _failure(
            f"analysis process exited with code {process.returncode}"
            + (f": {detail[-800:]}" if detail else ""),
            scratch,
        )

    try:
        payload = json.loads(stdout.decode("utf-8"))
    except json.JSONDecodeError as error:
        detail = (stderr or b"").decode("utf-8", "replace").strip()
        return _failure(
            f"analysis produced an unreadable result: {error}"
            + (f": {detail[-800:]}" if detail else ""),
            scratch,
        )

    if "error" in payload:
        return _failure(payload["error"], scratch)

    return {
        "columns": payload["columns"],
        "rows": payload["rows"],
        "row_count": payload["row_count"],
        "truncated": payload.get("truncated", False),
    }


def _failure(message: str, scratch: str) -> dict:
    """Turn a sandbox-layer rejection into the ValueError the API answers 400."""
    shutil.rmtree(scratch, ignore_errors=True)
    raise ValueError(message)
