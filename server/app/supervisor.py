"""Parent-process supervision for the desktop shell.

The Tauri shell is the only reason the core process exists. When the shell goes
away - a normal quit, a crash, or the OS killing it outright - the core should go
with it, not linger and keep holding port 8123 so the next launch cannot bind it.

The shell passes its own pid as ``DAH_PARENT_PID``. This module polls that pid and
terminates the core when it is gone. It is deliberately not the *only* cleanup
path: the shell also signals the core's process group on window close and on app
exit. This is the guarantee for the ways the shell can die without running any
code of its own - a ``SIGKILL`` reaches no destructor and no event handler.

Nothing here runs unless ``DAH_PARENT_PID`` is set, so a server started by hand or
by the test suite never watches a parent it does not have.
"""

import os
import threading
import time

POLL_INTERVAL = 1.0
_WATCHDOG_THREAD_NAME = "dah-parent-watchdog"


def parent_pid() -> int | None:
    """The pid the shell asked this core to outlive, or None if not supervised."""
    raw = os.environ.get("DAH_PARENT_PID", "").strip()
    if not raw:
        return None
    try:
        pid = int(raw)
    except ValueError:
        return None
    # 0 and negatives are not real pids; -1 would be "every process" to os.kill.
    return pid if pid > 0 else None


def pid_alive(pid: int) -> bool:
    """Whether ``pid`` is currently a running process."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Exists, but belongs to another user - not the shell that started us.
        return False
    except OSError:
        return False
    return True


def start_parent_watchdog() -> bool:
    """Start a daemon thread that ends this process when the shell is gone.

    Returns True only when a watchdog actually started, so a caller can tell a
    supervised core from a standalone one.
    """
    pid = parent_pid()
    if pid is None:
        return False

    def watch() -> None:
        while True:
            if not pid_alive(pid):
                # The shell is gone; there is nobody left to serve and nobody to
                # shut us down gracefully. Exit immediately - a live port is the
                # only thing that could make the next launch look broken.
                os._exit(0)
            time.sleep(POLL_INTERVAL)

    thread = threading.Thread(target=watch, daemon=True, name=_WATCHDOG_THREAD_NAME)
    thread.start()
    return True
