"""Where the core's output goes when nobody is watching it (P5-OBSERVE-002).

The desktop shell runs the core as a child process. In a checkout that child is
`uvicorn app.main:app` in a terminal the developer is reading; in a packaged app
it is a PyInstaller binary whose stderr is a pipe nothing is holding. P4 made a
500 honest by letting the exception propagate, which means uvicorn logs a
traceback - and in a packaged app that traceback vanished. A user hitting a
problem had nothing to show for it and so did support.

This module gives that output a home: a rotating file under the user's data
directory, where the cases already live, capped so it cannot grow without end,
and readable back through `GET /logs` so the shell - or a user with a terminal -
can look at the last thing that happened without hunting for a pipe.

Privacy is the other half of the design, and it is a property rather than a
promise:

- Logged: the time, the level, the logger name, one line per request holding
  only the method, the path, the status and the duration, the reason an LLM
  fell back to the deterministic engine, and the traceback of a real server
  fault.
- Not logged: request bodies and response payloads. An analyst's question, the
  SQL they wrote, the script they ran and every value in their data never reach
  the file, because nothing that holds them is ever passed to a logger.

The exception is a fault's traceback, which can quote what it was holding - an
unknown column name, a filename, a value that failed to parse. That is the
trade that makes a 500 debuggable, and it stays on the user's own machine: this
module writes locally and nowhere else, and nothing here ever transmits.
"""

import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE_NAME = "dah-core.log"
LOG_DIR_ENV = "DAH_LOG_DIR"
LEVEL_ENV = "DAH_LOG_LEVEL"
DEFAULT_LEVEL = "INFO"
MAX_BYTES = 2 * 1024 * 1024
BACKUP_COUNT = 3
# The most lines GET /logs will ever return; a larger ask is clamped down.
LOG_LINE_CEILING = 1000
LINE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s %(message)s"
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# uvicorn keeps three loggers of its own and does not propagate to the root by
# default, so a handler on the root alone would miss every request line.
UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")

_handlers_lock = threading.Lock()
_file_handler: RotatingFileHandler | None = None
_log_dir: Path | None = None


def resolve_log_dir(override: Path | None = None) -> Path:
    """Where the log file belongs.

    An explicit argument wins (tests use it against a tmp dir), then
    ``DAH_LOG_DIR``, then the data directory the shell already points at - so a
    packaged app's logs sit beside its cases with no extra wiring.
    """
    if override is not None:
        return override
    env = os.environ.get(LOG_DIR_ENV, "").strip()
    if env:
        return Path(env)
    # Read the module attribute rather than importing the constant, so a test
    # or a caller that repoints db.DATA_DIR after import is honoured.
    from app import db as db_module

    return Path(db_module.DATA_DIR) / "logs"


def _clear_handlers() -> None:
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    for name in UVICORN_LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True


def configure_logging(
    log_dir: Path | None = None,
    *,
    max_bytes: int = MAX_BYTES,
    backup_count: int = BACKUP_COUNT,
    level: str | None = None,
) -> Path | None:
    """Install the core's logging. Returns the log file, or None if file logging
    is off.

    Idempotent: a second call tears down the handlers it installed first, so
    reconfiguration never stacks handlers and never duplicates a line.

    Under pytest this installs the stderr handler only. The suite points
    ``db.DATA_DIR`` at a temporary directory *after* import, so a file handler
    bound at import time would write into the repository; a test that wants the
    file passes ``log_dir`` explicitly.
    """
    global _file_handler, _log_dir

    level_name = (level or os.environ.get(LEVEL_ENV, DEFAULT_LEVEL)).upper()
    root_level = getattr(logging, level_name, logging.INFO)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(logging.Formatter(LINE_FORMAT, TIME_FORMAT))

    file_handler = None
    target = None
    # An explicit location is honoured even under pytest - a test that asks for
    # a file is asking for a file. Without one, pytest is skipped because the
    # suite repoints the data directory after import and an import-time handler
    # would write into the repository.
    explicit = log_dir is not None or bool(os.environ.get(LOG_DIR_ENV, "").strip())
    if explicit or "pytest" not in sys.modules:
        target = resolve_log_dir(log_dir)
        try:
            target.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                target / LOG_FILE_NAME,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter(LINE_FORMAT, TIME_FORMAT))
            file_handler = handler
        except OSError as error:
            # A log directory we cannot create or write is not worth stopping
            # the server over. Say so on stderr - the one channel that still
            # works - and carry on with the console handler alone.
            target = None
            sys.stderr.write(
                f"dah-core: logging to file disabled ({error}); "
                "falling back to stderr\n"
            )

    with _handlers_lock:
        _clear_handlers()
        root = logging.getLogger()
        root.setLevel(root_level)
        root.addHandler(stderr_handler)
        if file_handler is not None:
            root.addHandler(file_handler)
        for name in UVICORN_LOGGERS:
            logger = logging.getLogger(name)
            logger.setLevel(root_level)
            logger.propagate = True
        _file_handler = file_handler
        _log_dir = target if file_handler is not None else None

    if file_handler is not None:
        # The one line a support request can start from: which core, which pid,
        # where the cases live. Paths, not contents.
        logging.getLogger("dah.core").info(
            "core started pid=%s data_dir=%s log_level=%s",
            os.getpid(),
            _log_dir.parent if _log_dir is not None else "?",
            level_name,
        )
    return (target / LOG_FILE_NAME) if target is not None else None


def current_log_file() -> Path | None:
    """The log file `GET /logs` reads, or None when file logging is off."""
    with _handlers_lock:
        if _log_dir is None or _file_handler is None:
            return None
        return _log_dir / LOG_FILE_NAME


def rotated_log_files() -> list[Path]:
    """The older backups, newest first. Empty when file logging is off."""
    with _handlers_lock:
        if _log_dir is None:
            return []
    directory = _log_dir
    found = []
    index = 1
    while True:
        candidate = directory / f"{LOG_FILE_NAME}.{index}"
        if not candidate.exists():
            break
        found.append(candidate)
        index += 1
    return found


def read_tail(path: Path, lines: int) -> list[str]:
    """The last ``lines`` records of ``path``, in the order they were written.

    Reads from the end because a support question is about the last thing that
    happened, and a log can be megabytes of history nobody asked for. Bytes are
    read backwards in chunks and reassembled, so a record larger than the chunk
    still comes back whole.

    ``lines`` is clamped to at least one; a caller asking for nothing is asking
    for the last line.
    """
    if not path.exists():
        return []
    wanted = max(1, lines)
    complete: list[bytes] = []
    partial = b""
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        position = handle.tell()
        while position > 0 and len([c for c in complete if c]) < wanted:
            read_size = min(65536, position)
            position -= read_size
            handle.seek(position)
            block = handle.read(read_size) + partial
            parts = block.split(b"\n")
            # Everything before the first newline is the back of a line whose
            # front has not been read yet - it is older than every complete
            # segment already collected, so it can only extend the window.
            partial = parts[0]
            complete = parts[1:] + complete
        if position == 0 and partial:
            complete = [partial] + complete
    if complete and complete[-1] == b"":
        # A log ending in a newline splits into a trailing empty segment, which
        # is the file's end rather than a record.
        complete.pop()
    return [line.decode("utf-8", errors="replace") for line in complete[-wanted:]]
