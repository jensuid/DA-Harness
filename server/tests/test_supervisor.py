"""The core must not outlive the desktop shell that started it.

These tests pin the guarantee at the process level: a core whose shell has died
terminates on its own, and a core with no shell supervising it is untouched.
That is what keeps a crashed or force-killed shell from leaving a server holding
port 8123, which would make the next launch fail to bind and look dead.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

from app.supervisor import parent_pid, pid_alive, start_parent_watchdog

SERVER_DIR = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

# A process that does nothing but stay alive, to stand in for the shell.
SITTER = [PYTHON, "-c", "import time; time.sleep(300)"]

# A process that starts the watchdog and then stays alive, as the core would.
WATCHDOG_CORE = (
    "from app.supervisor import start_parent_watchdog;"
    "started = start_parent_watchdog();"
    "import time; print('started', started, flush=True); time.sleep(300)"
)


def _run(cmd, env_extra):
    env = dict(os.environ)
    # Clear anything inherited first - a caller's explicit value must win.
    env.pop("DAH_PARENT_PID", None)
    env.update(env_extra)
    return subprocess.Popen(cmd, cwd=SERVER_DIR, env=env, stdout=subprocess.PIPE)


def _wait_for_exit(proc, timeout):
    deadline = time.time() + timeout
    while proc.poll() is None and time.time() < deadline:
        time.sleep(0.1)
    return proc.poll()


def test_parent_pid_reads_the_environment(monkeypatch):
    monkeypatch.setenv("DAH_PARENT_PID", "4242")
    assert parent_pid() == 4242


def test_parent_pid_is_absent_for_an_unsupervised_core(monkeypatch):
    monkeypatch.delenv("DAH_PARENT_PID", raising=False)
    assert parent_pid() is None


def test_parent_pid_rejects_junk(monkeypatch):
    for junk in ("", "not-a-pid", "0", "-1"):
        monkeypatch.setenv("DAH_PARENT_PID", junk)
        assert parent_pid() is None, f"{junk!r} should not supervise anything"


def test_pid_alive_tracks_a_real_process():
    sitter = subprocess.Popen(SITTER)
    try:
        assert pid_alive(sitter.pid) is True
    finally:
        sitter.kill()
        sitter.wait()
    assert pid_alive(sitter.pid) is False


def test_watchdog_kills_the_core_when_its_shell_dies():
    # A shell exists...
    shell = subprocess.Popen(SITTER)
    try:
        # ...and a core is started under its supervision.
        core = _run([PYTHON, "-c", WATCHDOG_CORE], {"DAH_PARENT_PID": str(shell.pid)})
        assert _read_started(core) is True, "the core should have started a watchdog"

        # The shell dies. The core has to follow it - not hang, not orphan.
        shell.kill()
        shell.wait()
        assert _wait_for_exit(core, 30) is not None, "the core outlived its shell"
    finally:
        _terminate(shell)
        _terminate(core)


def test_unsupervised_core_is_left_alone():
    # No DAH_PARENT_PID: nothing to watch, so a dying stranger must not touch it.
    stranger = subprocess.Popen(SITTER)
    try:
        core = _run([PYTHON, "-c", WATCHDOG_CORE], {})
        assert _read_started(core) is False, "no pid means no watchdog"

        stranger.kill()
        stranger.wait()
        assert _wait_for_exit(core, 3) is None, "an unsupervised core was killed anyway"
    finally:
        _terminate(stranger)
        _terminate(core)


def test_start_parent_watchdog_is_a_noop_without_a_pid(monkeypatch):
    monkeypatch.delenv("DAH_PARENT_PID", raising=False)
    assert start_parent_watchdog() is False


def _read_started(proc):
    """The core prints `started True|False`; None if it never spoke."""
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            return None
        line = proc.stdout.readline()
        text = line.decode().strip()
        if text.startswith("started "):
            return text.split()[-1] == "True"
        time.sleep(0.05)
    return None


def _terminate(proc):
    if proc.poll() is None:
        proc.kill()
        proc.wait()
