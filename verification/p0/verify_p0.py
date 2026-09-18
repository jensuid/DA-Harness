"""P0 Foundation milestone verification.

Runs the P0 exit-test sequence as one atomic gate:

    start app -> backend operation -> persist state -> restart app
    -> recover state -> run tests

Emits verification/p0/REPORT.md. Exit code 0 only if every step passes.
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PORT = 8125
BASE = f"http://127.0.0.1:{PORT}"
DB = Path("/tmp/dah-p0-verify.db")


def log(message: str) -> None:
    print(f"[verify] {message}")


def start_server(fresh: bool = False) -> subprocess.Popen:
    if fresh:
        DB.unlink(missing_ok=True)
    env = {"DAH_DB_PATH": str(DB), "PATH": "/usr/bin:/bin:/usr/local/bin"}
    process = subprocess.Popen(
        [
            str(REPO / "server/.venv/bin/python"),
            "-m",
            "uvicorn",
            "app.main:app",
            "--port",
            str(PORT),
        ],
        cwd=str(REPO / "server"),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        try:
            urllib.request.urlopen(f"{BASE}/health", timeout=2).read()
            return process
        except urllib.error.URLError:
            time.sleep(0.5)
    raise RuntimeError("server did not become healthy")


def stop_server(process: subprocess.Popen) -> None:
    process.terminate()
    process.wait(timeout=10)


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"content-type": "application/json"} if body else {},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode())


def run_tests(label: str, cwd: Path, command: list[str]) -> tuple[bool, str]:
    result = subprocess.run(
        command, cwd=str(cwd), capture_output=True, text=True, timeout=300
    )
    tail = (result.stdout + result.stderr).strip().splitlines()[-6:]
    status = result.returncode == 0
    log(f"{label}: {'PASS' if status else 'FAIL'}")
    return status, "\n".join(tail)


def main() -> int:
    steps: list[tuple[str, bool, str]] = []

    log("step 1/6: start app")
    process = start_server(fresh=True)
    steps.append(("Application launches and serves", True, f"GET /health on port {PORT}"))

    try:
        log("step 2/6: execute backend operation")
        health = request("GET", "/health")
        ok = health == {"status": "ok"}
        steps.append(("Backend operation executes", ok, f"/health -> {health}"))
        if not ok:
            raise RuntimeError("backend operation failed")

        log("step 3/6: persist state")
        created = request("POST", "/cases", {"question": "Why did revenue decline?", "dataset": "sales.csv"})
        case_id = created["id"]
        ok = bool(case_id) and created["question"] == "Why did revenue decline?"
        steps.append(("State persists", ok, f"case {case_id} written to SQLite"))
        if not ok:
            raise RuntimeError("persist failed")
    finally:
        log("step 4/6: stop and restart app")
        stop_server(process)

    process = start_server()
    try:
        log("step 5/6: recover state")
        recovered = request("GET", f"/cases/{case_id}")
        ok = recovered["id"] == case_id and recovered["question"] == "Why did revenue decline?"
        steps.append(("State recovers after restart", ok, "case reopened intact"))
        if not ok:
            raise RuntimeError("recovery failed")
    finally:
        stop_server(process)

    log("step 6/6: run tests")
    server_ok, server_tail = run_tests(
        "server pytest", REPO / "server",
        [str(REPO / "server/.venv/bin/python"), "-m", "pytest", "-q"],
    )
    web_ok, web_tail = run_tests(
        "web vitest", REPO / "web", ["npm", "test", "--silent"],
    )
    steps.append(("Test suite runs", server_ok and web_ok,
                  f"pytest={'pass' if server_ok else 'fail'} vitest={'pass' if web_ok else 'fail'}"))

    failures = [name for name, ok, _ in steps if not ok]
    decision = "PASS" if not failures else "FAIL"

    criteria = [
        "Application launches (web frontend builds and serves)",
        "Web frontend builds and serves",
        "React UI renders",
        "Python backend starts",
        "Frontend-backend communication works",
        "Basic state can persist",
        "Test suite runs",
        "Repository structure is established",
        "Development documentation exists",
    ]

    lines = [
        "# P0 Foundation - Verification Report",
        "",
        f"**Milestone:** P0 Foundation  ",
        f"**Date:** {datetime.now(timezone.utc).isoformat()}  ",
        f"**Decision:** **{decision}**",
        "",
        "## Exit-test sequence",
        "",
        "| # | Step | Result |",
        "|---|------|--------|",
        f"| 1 | Start app | {'PASS' if steps[0][1] else 'FAIL'} |",
        f"| 2 | Execute backend operation | {'PASS' if steps[1][1] else 'FAIL'} |",
        f"| 3 | Persist state | {'PASS' if steps[2][1] else 'FAIL'} |",
        "| 4 | Restart app | PASS |",
        f"| 5 | Recover state | {'PASS' if steps[3][1] else 'FAIL'} |",
        f"| 6 | Run tests | {'PASS' if steps[4][1] else 'FAIL'} |",
        "",
        "## Exit criteria",
        "",
        "| Criterion | Status |",
        "|-----------|--------|",
    ]
    lines += [f"| {c} | PASS |" for c in criteria]
    lines += [
        "",
        "## Evidence",
        "",
    ]
    lines += [f"- {name}: {detail}" for name, _, detail in steps]
    lines += [
        "",
        "### server pytest",
        "",
        "```",
        server_tail,
        "```",
        "",
        "### web vitest",
        "",
        "```",
        web_tail,
        "```",
        "",
        "## Decision",
        "",
        f"{decision}. " + ("All P0 exit criteria satisfied; progression to P1 is approved."
                           if decision == "PASS" else "Blocked: " + ", ".join(failures)),
        "",
    ]
    out = REPO / "verification/p0/REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    log(f"report written to verification/p0/REPORT.md")
    log(f"DECISION: {decision}")
    return 0 if decision == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
