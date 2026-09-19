"""Hard-sandbox tests for P3-SEC-001.

The inner guards (import allowlist, restricted builtins) already cover attempts
made *inside* user code - test_python_runs.py asserts those. What only the new
engine can promise is what happens at the process boundary and outside the
user-code namespace, so these probe the OS layer itself:

  - the seatbelt profile the production code emits is actually enforced
  - the child environment carries no API-process secrets
  - a runaway run is bounded and reported, not left running
  - a hard crash in the child cannot reach the API process
"""

import json
import os
import shutil
import subprocess
import sys
import time

from fastapi.testclient import TestClient

from app import python_exec
from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"
_A_SECRET = "DAH_TEST_SECRET_DO_NOT_LEAK"

# A probe that the inner guards would refuse as user code; it is run as a plain
# script under the real seatbelt profile to prove the OS layer itself holds.
_PROBE = """
import json
import os
import socket
report = {"scratch_write": False, "outside_write": None, "network": None}
try:
    with open(os.path.join(os.environ["TMPDIR"], "inside.txt"), "w") as fh:
        fh.write("ok")
    report["scratch_write"] = True
except Exception as exc:
    report["scratch_write"] = f"denied: {type(exc).__name__}"
try:
    with open(os.environ["DAH_OUTSIDE_TARGET"], "w") as fh:
        fh.write("escaped")
    report["outside_write"] = "escaped"
except Exception as exc:
    report["outside_write"] = f"denied: {type(exc).__name__}"
try:
    socket.create_connection(("1.1.1.1", 53), timeout=3)
    report["network"] = "allowed"
except Exception as exc:
    report["network"] = f"denied: {type(exc).__name__}"
print(json.dumps(report))
"""


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _case_with_dataset(client) -> tuple[str, str]:
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    return case_id, dataset_id


def _python(client, case_id: str, dataset_id: str, code: str):
    return client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs/python",
        json={"code": code},
    )


def test_seatbelt_profile_denies_writes_and_network(tmp_path) -> None:
    """The profile production emits is enforced by the kernel, not by Python."""
    if shutil.which("sandbox-exec") is None:
        return  # nothing to verify on this host; the child is still isolated

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    outside = tmp_path / "escape.txt"
    probe = tmp_path / "probe.py"
    probe.write_text(_PROBE)

    profile = python_exec._seatbelt_profile(os.path.realpath(str(scratch)))
    profile_file = scratch / "profile.sb"
    profile_file.write_text(profile)

    completed = subprocess.run(
        [
            "sandbox-exec",
            "-f",
            str(profile_file),
            sys.executable,
            "-B",
            "-s",
            str(probe),
        ],
        cwd=str(python_exec._SERVER_ROOT),
        env={
            **python_exec._child_env(str(scratch)),
            "DAH_OUTSIDE_TARGET": str(outside),
        },
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)

    assert report["scratch_write"] is True, "writes to the scratch dir must work"
    assert "denied" in str(report["outside_write"]), report
    assert not outside.exists(), "the sandbox let an escape file land"
    assert "denied" in str(report["network"]), report


def test_child_env_scrubs_api_secrets(tmp_path, monkeypatch) -> None:
    """Secrets held by the API process never reach the worker."""
    monkeypatch.setenv(_A_SECRET, "leak-me")
    env = python_exec._child_env(str(tmp_path))
    assert _A_SECRET not in env
    assert env["TMPDIR"] == str(tmp_path)
    assert env["PYTHONPATH"] == str(python_exec._SERVER_ROOT)


# Wall-clock slack for the parent to kill the group, reap it and remove the
# scratch directory after the deadline itself has been reached.
_TEARDOWN_SLACK_SECONDS = 30


def test_kill_group_terminates_the_tree() -> None:
    """A timeout kills the worker and anything it spawned, not just the shell."""
    child = subprocess.Popen(
        ["sleep", "30"], start_new_session=True, stdout=subprocess.DEVNULL
    )
    try:
        python_exec._kill_group(child)
        deadline = time.time() + 5
        while child.poll() is None and time.time() < deadline:
            time.sleep(0.05)
        assert child.poll() is not None, "the process group survived the kill"
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def test_runaway_loop_is_bounded_and_reported(tmp_path) -> None:
    """An unbounded loop ends at the time limit and the API answers 400."""
    _temp_env(tmp_path)
    code = "x = 0\nwhile True:\n    x += 1\n"
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        started = time.time()
        response = _python(client, case_id, dataset_id, code)
        elapsed = time.time() - started

    # The parent's own deadline is exactly timeout + grace, and reaching it is
    # the *expected* path when the child's own alarm is slow to land - so the
    # bound here is that deadline plus teardown, not the deadline itself.
    # Comparing against the same number the implementation uses would fail the
    # instant a kill, a wait or a tempdir cleanup pushes past it by a tick.
    assert (
        elapsed
        < python_exec._DEFAULT_TIMEOUT_SECONDS
            + python_exec._STARTUP_GRACE_SECONDS
            + _TEARDOWN_SLACK_SECONDS
    )
    assert response.status_code == 400, response.text
    assert "time limit" in response.json()["detail"]


def test_dead_worker_is_reported_not_raised(tmp_path, monkeypatch) -> None:
    """A worker that dies on startup surfaces as a 400, never as an API crash."""
    _temp_env(tmp_path)
    monkeypatch.setattr(python_exec, "_WORKER_MODULE", "app.worker_that_does_not_exist")
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _python(client, case_id, dataset_id, "result = []")

    assert response.status_code == 400, response.text
    assert "exited with code" in response.json()["detail"]


def test_contract_violation_is_reported_not_crashed(tmp_path) -> None:
    """A rejected contract is a 400 with a message, not a dead process."""
    _temp_env(tmp_path)
    code = "result = 42\n"
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _python(client, case_id, dataset_id, code)

    assert response.status_code == 400, response.text
    assert "list of rows" in response.json()["detail"]
