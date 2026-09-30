"""Visual verification: the shell against a REAL core, in a REAL browser.

The gates drive the app in-process (jsdom, Starlette's TestClient), which
proves the contract but renders nothing - so a restyle can be green and still
look wrong. This is the complement: an isolated core, a seeded case, the Vite
dev server, and headless Chrome over the DevTools protocol. It serves two
modes, both in drive_chrome.js:

    shots  - captures the list and the workspace as PNGs
    verify - reads the browser's COMPUTED styles, which is what a restyle
             actually changed; a source claim about a token is worth nothing
             next to `getComputedStyle`

    server/.venv/bin/python verification/visual/verify_visual.py [shots|verify]

Nothing is mocked, and no LLM key is used: the LLM env vars are scrubbed from
the core's subprocess so the deterministic engines answer, which makes a run
reproducible offline.

Two things this script is careful about, because both cost a session once:

  * The running desktop app owns port 8123 with the analyst's real case
    store. This core binds 8124 to an ephemeral data dir, and the dev server's
    /api proxy is pointed at it with DAH_CORE_PORT. Do not aim this at 8123 -
    a seeded case lands in the user's database.
  * Chrome binds its debug port on IPv6 and answers `localhost`, not
    127.0.0.1, and a second Chrome needs its own --user-data-dir or it exits
    silently. Both are handled in drive_chrome.js.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SERVER = REPO / "server"
VENV_PYTHON = SERVER / ".venv" / "bin" / "python"
HERE = Path(__file__).resolve().parent
DRIVE = HERE / "drive_chrome.js"

CORE_PORT = "8124"
DEV_PORT = "5274"
CHROME_DEBUG_PORT = "9333"
API = f"http://127.0.0.1:{CORE_PORT}"


def wait_for(url: str, timeout: float = 40.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def post(path: str, data: dict | None = None, files: dict | None = None,
         json_body: bool = False):
    boundary = "----dahboundary" + uuid.uuid4().hex[:8]
    if json_body:
        req = urllib.request.Request(
            API + path, data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    body = b""
    if data:
        for k, v in data.items():
            body += (f"--{boundary}\r\nContent-Disposition: form-data; "
                     f'name="{k}"\r\n\r\n{v}\r\n').encode()
    if files:
        for name, (fname, content) in files.items():
            body += (
                f"--{boundary}\r\nContent-Disposition: form-data; "
                f'name="{name}"; filename="{fname}"\r\n'
                f"Content-Type: text/csv\r\n\r\n"
            ).encode() + content + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        API + path, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def port_free(port: int) -> bool:
    import socket
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "shots"
    if mode not in ("shots", "verify"):
        print(f"unknown mode {mode!r} (shots | verify)")
        return 2

    # Refuse to start if the port is taken: a core already listening would
    # answer the health check and a seeded case would land in its store.
    if not port_free(int(CORE_PORT)):
        print(f"port {CORE_PORT} is already in use - the isolated core would "
              f"not be the one answering the health check. Free it (or check "
              f"whether a previous run leaked) and retry.")
        return 1

    data_dir = Path(tempfile.mkdtemp(prefix="dah-visual-"))
    db_path = data_dir / "dah.db"
    env = {**os.environ}
    for k in ("DAH_LLM_API_KEY", "DAH_LLM_BASE_URL", "DAH_LLM_MODEL", "OPENAI_API_KEY"):
        env[k] = ""
    env["DAH_DATA_DIR"] = str(data_dir)
    env["DAH_DB_PATH"] = str(db_path)

    print(f"starting isolated core on {CORE_PORT}...")
    core = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", CORE_PORT],
        cwd=str(SERVER), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    try:
        if not wait_for(API + "/health"):
            print("CORE FAILED TO START:")
            print(core.stdout.read().decode()[-3000:])
            return 1
        print("  core up")

        # One case with a dataset carrying a planted null, so the workspace
        # renders the rail, the overview and the panels a restyle touches.
        csv = (
            "region,month,revenue,tickets\n"
            "north,jan,4200,31\n"
            "north,feb,3900,28\n"
            "south,jan,5100,40\n"
            "south,feb,,41\n"
            "east,jan,3800,22\n"
            "east,feb,4100,25\n"
            "west,jan,4700,33\n"
            "west,feb,4400,30\n"
        )
        case = post("/cases", {
            "question": "Which region's support load is rising fastest against its revenue?",
            "dataset": "regional_support_q1.csv",
        }, json_body=True)
        post(f"/cases/{case['id']}/datasets",
             files={"file": ("regional_support_q1.csv", csv.encode())})
        print(f"  case {case['id'][:8]}")

        print(f"starting vite dev server on {DEV_PORT}...")
        venv = {
            **os.environ,
            "DAH_DEV_PORT": DEV_PORT,
            # The proxy's target is otherwise the app's own core on 8123.
            "DAH_CORE_PORT": CORE_PORT,
        }
        vite = subprocess.Popen(
            ["npm", "run", "dev"], cwd=str(REPO / "web"),
            env=venv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        try:
            # Vite binds localhost (not 127.0.0.1), so this is the URL that
            # reaches it.
            if not wait_for(f"http://localhost:{DEV_PORT}/", 40.0):
                print("VITE FAILED:")
                print(vite.stdout.read().decode()[-3000:])
                return 1
            print("  vite up")
            r = subprocess.run(
                ["node", str(DRIVE), mode],
                cwd=str(REPO), check=True,
                env={**venv,
                     "DAH_SHOTS_PORT": DEV_PORT,
                     "DAH_CHROME_DEBUG_PORT": CHROME_DEBUG_PORT},
            )
            return r.returncode
        finally:
            vite.terminate()
            try:
                vite.wait(timeout=10)
            except subprocess.TimeoutExpired:
                vite.kill()
    finally:
        core.terminate()
        try:
            core.wait(timeout=10)
        except subprocess.TimeoutExpired:
            core.kill()
        shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
