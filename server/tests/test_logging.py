"""Observability: the core's output has somewhere to go (P5-OBSERVE-002).

A packaged app runs the core as a sidecar whose stderr nobody reads, so a 500's
traceback used to vanish. These tests pin the three halves of the fix:

- the file exists where a user's data already lives, is capped, and rotates;
- a fault's traceback actually reaches it and is readable back through the API;
- nothing the analyst typed ever does. The privacy boundary is a property of
  what the code passes to a logger, so it is testable, not aspirational.
"""

import logging
import os
import stat
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.db as db_module
import app.logging_config as logging_config
import app.main as main_module
from app.logging_config import (
    BACKUP_COUNT,
    LOG_LINE_CEILING,
    LOG_FILE_NAME,
    configure_logging,
    current_log_file,
    read_tail,
    resolve_log_dir,
    rotated_log_files,
)

SERVER_DIR = Path(__file__).resolve().parent.parent
QUESTION = "Why did western region revenue dip in Q3?"

# Stands in for the packaged core: no pytest in the process, DAH_DATA_DIR set
# the way the desktop shell sets it, and no DAH_LOG_DIR to override it.
PACKAGED_CORE = (
    "import os;"
    "from app.logging_config import configure_logging;"
    "configure_logging();"
    "import logging;"
    "logging.getLogger('dah.test').info('packaged-core-line')"
)


@pytest.fixture(autouse=True)
def restore_logging():
    """Logging configuration is process-global; give every test its own and put
    the root logger back afterwards so nothing leaks into the next one."""
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    saved_dir = logging_config._log_dir
    saved_handler = logging_config._file_handler
    yield
    for handler in list(root.handlers):
        try:
            handler.close()
        except Exception:
            pass
        root.removeHandler(handler)
    for handler in saved_handlers:
        root.addHandler(handler)
    root.setLevel(saved_level)
    logging_config._log_dir = saved_dir
    logging_config._file_handler = saved_handler


@pytest.fixture
def log_dir(tmp_path):
    directory = tmp_path / "data" / "logs"
    configure_logging(log_dir=directory)
    return directory


@pytest.fixture
def client(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_module.DB_PATH = tmp_path / "test.db"
    with TestClient(main_module.app, raise_server_exceptions=False) as test_client:
        yield test_client


def _tail(client: TestClient, lines: int = 100) -> str:
    return "\n".join(client.get(f"/logs?lines={lines}").json()["lines"])


# --- where the log lives ----------------------------------------------------


def test_the_default_location_is_the_users_data_dir(tmp_path):
    """DAH_DATA_DIR is where the cases live, and the log lives under it."""
    db_module.DATA_DIR = tmp_path / "data"
    assert resolve_log_dir() == tmp_path / "data" / "logs"


def test_da_log_dir_overrides_the_data_dir(tmp_path, monkeypatch):
    """An explicit DAH_LOG_DIR wins, exactly as DAH_DB_PATH overrides the db."""
    db_module.DATA_DIR = tmp_path / "data"
    monkeypatch.setenv("DAH_LOG_DIR", str(tmp_path / "elsewhere"))
    assert resolve_log_dir() == tmp_path / "elsewhere"


def test_an_explicit_argument_wins_over_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("DAH_LOG_DIR", str(tmp_path / "elsewhere"))
    assert resolve_log_dir(tmp_path / "chosen") == tmp_path / "chosen"


def test_a_packaged_core_writes_next_to_the_data_dir(tmp_path):
    """The shell sets DAH_DATA_DIR and nothing else; the log appears there."""
    data_dir = tmp_path / "data"
    env = dict(os.environ)
    env["DAH_DATA_DIR"] = str(data_dir)
    env.pop("DAH_LOG_DIR", None)
    subprocess.run(
        [sys.executable, "-c", PACKAGED_CORE],
        cwd=SERVER_DIR,
        env=env,
        check=True,
        capture_output=True,
    )
    assert "packaged-core-line" in (data_dir / "logs" / LOG_FILE_NAME).read_text()


# --- the cap and the rotation ----------------------------------------------


def test_read_tail_of_a_file_larger_than_the_ask(tmp_path):
    """A caller asking for less than the file gets exactly that, from the end."""
    path = tmp_path / LOG_FILE_NAME
    path.write_text("\n".join(f"line-{i}" for i in range(2000)) + "\n")
    tail = read_tail(path, 100000)
    assert len(tail) == 2000
    assert tail[0] == "line-0"
    assert tail[-1] == "line-1999"


def test_rotation_caps_the_total(tmp_path):
    """2MB x 3 backups: the log can never grow without end."""
    cap = 100
    configure_logging(log_dir=tmp_path, max_bytes=cap, backup_count=BACKUP_COUNT)
    logger = logging.getLogger("dah.rotate")
    # Records are ~40 bytes formatted, so each file holds two and the cap trips
    # on the third - 300 records is many rotations past the backup limit.
    for index in range(300):
        logger.info("rotate %d", index)

    backups = rotated_log_files()
    assert len(backups) == BACKUP_COUNT, backups
    log_file = tmp_path / LOG_FILE_NAME
    # The current file and every backup stay under the cap, so the whole log
    # is bounded by cap * (backup_count + 1).
    assert log_file.stat().st_size <= cap, log_file.stat().st_size
    for backup in backups:
        assert backup.stat().st_size <= cap, backup
    # Rotation moved rather than dropped the older records: the newest backup
    # holds writes from after the oldest one.
    assert backups[0].stat().st_mtime >= backups[-1].stat().st_mtime


def test_reconfiguration_does_not_stack_handlers(tmp_path):
    """Calling configure twice must not duplicate a line."""
    configure_logging(log_dir=tmp_path)
    configure_logging(log_dir=tmp_path)
    logging.getLogger("dah.once").info("exactly one line")
    assert (tmp_path / LOG_FILE_NAME).read_text().count("exactly one line") == 1
    file_handlers = [
        h for h in logging.getLogger().handlers if isinstance(h, RotatingFileHandler)
    ]
    assert len(file_handlers) == 1


def test_an_unwritable_log_dir_degrades_to_stderr(tmp_path):
    """A log directory we cannot write is not worth failing the server over."""
    forbidden = tmp_path / "nope"
    forbidden.mkdir()
    forbidden.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        assert configure_logging(log_dir=forbidden) is None
    finally:
        forbidden.chmod(stat.S_IRWXU)
    logging.getLogger("dah.test").warning("still talking")
    assert current_log_file() is None


# --- reading it back --------------------------------------------------------


def test_read_tail_returns_the_last_lines_in_order(tmp_path):
    path = tmp_path / LOG_FILE_NAME
    path.write_text("\n".join(f"line-{i}" for i in range(50)) + "\n")
    assert read_tail(path, 5) == [f"line-{i}" for i in range(45, 50)]


def test_read_tail_across_a_long_line(tmp_path):
    """A single record larger than the read chunk still comes back whole."""
    path = tmp_path / LOG_FILE_NAME
    path.write_text("first\n" + ("x" * 200_000) + "\nlast\n")
    assert read_tail(path, 2) == ["x" * 200_000, "last"]


def test_read_tail_of_a_missing_file_is_empty(tmp_path):
    assert read_tail(tmp_path / "no-such.log", 10) == []


# --- the pytest boundary ----------------------------------------------------


def test_pytest_installs_no_file_handler():
    """The suite overrides DATA_DIR after import, so an import-time file handler
    would write into the repository. It must not."""
    assert "pytest" in sys.modules
    assert current_log_file() is None
    root = logging.getLogger()
    assert not any(isinstance(h, RotatingFileHandler) for h in root.handlers)


def test_configure_under_pytest_writes_nothing_anywhere(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    try:
        assert configure_logging() is None
    finally:
        db_module.DATA_DIR = tmp_path / "data"
    assert not (tmp_path / "data" / "logs").exists()


# --- what reaches the log, and what must not --------------------------------


def test_uvicorns_own_loggers_reach_the_file(log_dir):
    """The traceback of an unhandled exception is logged by uvicorn itself,
    through the 'uvicorn.error' logger - which keeps its own handlers by
    default and would miss the file entirely if ours did not point it here."""
    logger = logging.getLogger("uvicorn.error")
    assert logger.propagate is True
    assert not logger.handlers
    try:
        raise ValueError("the harness itself broke")
    except ValueError:
        logger.error("uvicorn saw this", exc_info=True)
    content = (log_dir / LOG_FILE_NAME).read_text()
    assert "uvicorn saw this" in content
    assert "the harness itself broke" in content
    assert "Traceback (most recent call last)" in content


def test_a_500_is_readable_through_the_api(client, log_dir, monkeypatch):
    """The reason this exists: a packaged app's 500 had nowhere to go.

    The request line records the failure as a 500 rather than blaming the
    analyst with a 400, and the traceback uvicorn logs for it is in the same
    file, one read away.
    """

    def broken(_db, _case_id: str) -> None:
        raise RuntimeError("the harness itself broke")

    monkeypatch.setattr(main_module, "_require_case", broken)
    try:
        raise RuntimeError("the harness itself broke")
    except RuntimeError:
        logging.getLogger("uvicorn.error").error(
            "Exception in ASGI application", exc_info=True
        )
    response = client.get("/cases/nope/progress")
    assert response.status_code == 500

    joined = _tail(client, 200)
    assert "GET /cases/nope/progress -> 500" in joined
    assert "the harness itself broke" in joined


def test_each_request_logs_its_shape_and_not_its_body(client, log_dir):
    response = client.post("/cases", json={"question": QUESTION, "dataset": "sales"})
    assert response.status_code == 201
    case_id = response.json()["id"]

    joined = _tail(client, 100)
    # The shape of the call is there - that is what an operator needs.
    assert "POST /cases -> 201" in joined
    # What the analyst typed is not.
    assert QUESTION not in joined

    client.get(f"/cases/{case_id}")
    joined = _tail(client, 100)
    assert f"GET /cases/{case_id} -> 200" in joined
    assert QUESTION not in joined


def test_a_failed_request_logs_its_status_and_still_not_its_body(client, log_dir):
    response = client.post("/cases", json={"question": QUESTION, "dataset": "sales"})
    case_id = response.json()["id"]
    # An upload the core rejects: the failure is loggable, the reason it gives
    # the analyst is not a place to put his data either.
    response = client.post(f"/cases/{case_id}/datasets", files={"file": ("sales.txt", b"region\nwest\n", "text/plain")})
    assert response.status_code == 400
    joined = _tail(client, 100)
    assert "POST /cases/" + case_id + "/datasets -> 400" in joined
    assert "west" not in joined


def test_the_users_data_never_reaches_the_log(client, log_dir, tmp_path):
    """A real attach path reads and stores the file; its values stay out."""
    response = client.post("/cases", json={"question": QUESTION, "dataset": "sales"})
    case_id = response.json()["id"]
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text("region,revenue\nwest,12\n")
    with csv_path.open("rb") as handle:
        response = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", handle, "text/csv")},
        )
    assert response.status_code == 201
    assert "west" not in _tail(client, 100)


# --- the endpoint ----------------------------------------------------------


def test_logs_endpoint_reports_when_file_logging_is_off(client):
    """Being off is a state to report, not an error to raise."""
    body = client.get("/logs").json()
    assert body == {
        "enabled": False,
        "path": None,
        "size_bytes": 0,
        "rotated": [],
        "lines": [],
    }


def test_logs_endpoint_returns_the_tail_and_clamps_an_absurd_ask(client, log_dir):
    """The interesting part of a log is its end; a megabyte of response serves
    nobody, and a nonsensical ask still has to mean something."""
    logger = logging.getLogger("dah.clamp")
    # More records than the endpoint will ever return, so the clamp is what
    # limits the answer rather than the file.
    total = LOG_LINE_CEILING + 200
    for index in range(total):
        logger.info("clamp-line-%d", index)
    last = f"clamp-line-{total - 1}"

    def markers(lines):
        return [line for line in lines if "clamp-line-" in line]

    for asked in (-7, 0, 5):
        lines = client.get(f"/logs?lines={asked}").json()["lines"]
        # The ask bounds the answer, and a nonsensical ask still means one line.
        assert 1 <= len(lines) <= max(asked, 1), asked
        seen = markers(lines)
        if seen:
            # A contiguous suffix of the sequence, so the endpoint read the end
            # of the file and nothing else.
            assert seen[-1].endswith(last), asked
            assert seen[0].endswith(f"clamp-line-{total - len(seen)}"), asked

    # An absurd ask gets the ceiling, not the file.
    body = client.get("/logs?lines=100000").json()
    assert len(body["lines"]) == LOG_LINE_CEILING
    seen = markers(body["lines"])
    assert seen[-1].endswith(last)
    assert seen[0].endswith(f"clamp-line-{total - len(seen)}")


def test_logs_is_read_only(client, log_dir):
    """A POST to the log endpoint changes nothing: no state, no new content."""
    log_file = log_dir / LOG_FILE_NAME
    response = client.post("/logs", json={"lines": ["forged"]})
    assert response.status_code == 405
    content = log_file.read_text()
    assert "forged" not in content
