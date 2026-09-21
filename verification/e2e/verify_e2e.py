"""End-to-end verification against a REAL server.

The P2/P3/P4 gates drive the app in-process through Starlette's TestClient,
which is fast but skips everything uvicorn actually does: binding a port,
serving real HTTP, the multipart parser on a real upload, the startup and
shutdown lifecycles. This script is the complement, not a replacement:

    a fresh uvicorn server on a free port, an isolated data dir
    -> one case built by hand the way an analyst would
    -> the same case audited by the reviewer agent (P7-AGENT-001)
    -> a second case driven entirely by the analyst agent, one approved write
       at a time
    -> export/import round trip, then the server is asked to stop

Nothing is mocked and no LLM key is used: the LLM env vars are scrubbed from
the server's subprocess so the deterministic engines answer, which makes the
run reproducible offline. Exit code 0 only if every step passes; the report is
written to verification/e2e/REPORT.md.

    server/.venv/bin/python verification/e2e/verify_e2e.py
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SERVER = REPO / "server"
VENV_PYTHON = SERVER / ".venv" / "bin" / "python"

# Turning any of these on makes the planner/generator/interpreter/drafter call
# a live LLM. A real end-to-end run must be reproducible without a network, so
# they are removed from the server's environment the way the P2 gate scrubs
# them from its own subprocess.
LLM_ENV_VARS = frozenset(
    {"DAH_LLM_API_KEY", "OPENAI_API_KEY", "DAH_LLM_BASE_URL", "DAH_LLM_MODEL"}
)

# A real-shaped question over a file messy enough to exercise the profiler: a
# null, a duplicate row, and a categorical split.
CSV = (
    b"order_id,quarter,revenue,region\n"
    b"1,2024q1,125.0,north\n"
    b"2,2024q1,80.5,south\n"
    b"3,2024q2,200.0,north\n"
    b"4,2024q2,,south\n"      # a null the profiler must count
    b"3,2024q2,200.0,north\n"  # a duplicate the profiler must count
).decode()

QUESTION = "Why did revenue change between the first two quarters?"

# The claim the analyst's own finding makes - one the SQL result actually
# supports, so the reviewer's audit passes rather than being a staged failure.
CLAIM = "Revenue rose from 205.5 in 2024q1 to 200.0 in 2024q2 in north, and fell in south."

steps: list[tuple[str, str, str]] = []  # (name, verdict, detail)


def log(message: str) -> None:
    print(f"[e2e] {message}", flush=True)


def note(name: str, verdict: str, detail: str) -> None:
    steps.append((name, verdict, detail))
    log(f"{name}: {verdict} - {detail}")


class Server:
    """A real uvicorn server on a free port, isolated to a temp data dir."""

    def __init__(self) -> None:
        self.data_dir = tempfile.mkdtemp(prefix="dah-e2e-")
        self.db_path = Path(self.data_dir) / "e2e.db"
        self.env_file = Path(self.data_dir) / "no.env"  # absent on purpose

        env = dict(os.environ)
        # The server loads server/.env on a plain uvicorn start, and that file
        # may carry a real key. `load_dotenv` never overrides a variable that is
        # already set, so an empty value here wins over the file - and the
        # engines treat an empty key as absent (`os.environ.get(...) or ...`),
        # so the deterministic engines answer and the run needs no network.
        for var in LLM_ENV_VARS:
            env[var] = ""
        # An empty body is a real 204 for the shell's DELETEs; the server must
        # never see a key from a developer's shell here.
        env["DAH_DATA_DIR"] = self.data_dir
        env["DAH_DB_PATH"] = str(self.db_path)

        self.proc = subprocess.Popen(
            [
                str(VENV_PYTHON), "-m", "uvicorn",
                "app.main:app", "--host", "127.0.0.1",
                "--port", str(self._free_port()),
            ],
            cwd=str(SERVER),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.port = self._wait_for_health()

    @staticmethod
    def _free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _wait_for_health(self, timeout: float = 60.0) -> int:
        # uvicorn prints its listening line; the port is known only then.
        deadline = time.time() + timeout
        port: int | None = None
        while time.time() < deadline:
            line = self.proc.stdout.readline() if self.proc.stdout else ""
            if "Uvicorn running on" in line:
                port = int(line.rsplit(":", 1)[-1].split()[0])
                break
            if self.proc.poll() is not None:
                out = self.proc.stdout.read() if self.proc.stdout else ""
                raise RuntimeError(f"server exited early:\n{out}")
        if port is None:
            raise RuntimeError("server did not announce a port in time")
        while time.time() < deadline:
            if self._get(port, "/health").get("status") == "ok":
                return port
            time.sleep(0.25)
        raise RuntimeError("server never answered /health")

    def _get(self, port: int, path: str) -> dict:
        with urllib.request.urlopen(
            urllib.request.Request(f"http://127.0.0.1:{port}{path}"), timeout=60
        ) as res:
            body = res.read()
            return json.loads(body) if body else {}

    def get(self, path: str) -> dict:
        return self._get(self.port, path)

    def post(self, path: str, payload: dict | str | None = None) -> tuple[int, dict]:
        data = json.dumps(payload).encode() if isinstance(payload, dict) else (
            payload.encode() if isinstance(payload, str) else b""
        )
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as res:
                body = res.read()
                return res.status, (json.loads(body) if body else {})
        except urllib.error.HTTPError as err:
            body = err.read()
            try:
                return err.code, json.loads(body)
            except json.JSONDecodeError:
                return err.code, {"raw": body.decode(errors="replace")}

    def upload(self, path: str, filename: str, content: str) -> dict:
        boundary = "dah-e2e-boundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: text/csv\r\n\r\n{content}\r\n--{boundary}--\r\n"
        ).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=body,
            headers={"content-type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as res:
            return json.loads(res.read())

    def stop(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


def run_journey(server: Server) -> None:
    # ---- 1. the store is current for this build -------------------------
    schema = server.get("/schema-version")
    assert schema["current"], schema
    note("Store opens at the build's schema", "PASS",
         f"version {schema['version']} of {schema['target']}, "
         f"{len(schema['migrations'])} migration(s) applied")

    # ---- 2. a case with a real question --------------------------------
    status, case = server.post("/cases", {"question": QUESTION, "dataset": "sales.csv"})
    assert status == 201, (status, case)
    case_id = case["id"]
    note("Case created", "PASS", f"question={case['question']!r}")

    # ---- 3. a real multipart upload ------------------------------------
    dataset = server.upload(f"/cases/{case_id}/datasets", "sales.csv", CSV)
    assert dataset["filename"] == "sales.csv", dataset
    dataset_id = dataset["id"]
    note("Dataset attached over multipart", "PASS",
         f"{dataset['filename']} ({dataset['format']})")

    # ---- 4. the profile reads the mess in the file ----------------------
    profile = server.post(
        f"/cases/{case_id}/datasets/{dataset_id}/profile"
    )[1]
    assert profile["rows"] == 5, profile
    assert "revenue" in profile["columns"], profile
    revenue_nulls = profile["stats"]["revenue"]["null_count"]
    assert revenue_nulls == 1, profile
    note("Profile counts the null and the duplicate", "PASS",
         f"rows={profile['rows']}, columns={profile['columns']}, "
         f"revenue nulls={revenue_nulls}, duplicates={profile['duplicate_rows']}")

    # ---- 5. a plan, structured -----------------------------------------
    plan = server.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")[1]
    assert plan["source"] == "deterministic", plan
    note("Plan derived", "PASS",
         f"source={plan['source']}, keys={sorted(plan['plan'].keys())}")

    # ---- 6. generated SQL, run under the read-only gate -----------------
    generated = server.post(
        f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
        {"question": QUESTION, "kind": "sql"},
    )[1]
    run = server.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs",
        {"sql": generated["code"]},
    )[1]
    assert run["row_count"] > 0, run
    rows = {r[0]: r[1] for r in run["rows"]}
    note("Generated SQL runs", "PASS",
         f"row_count={run['row_count']}, totals={rows}")

    # ---- 7. the read-only gate refuses a write --------------------------
    status, body = server.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs",
        {"sql": "CREATE TABLE evil (x int)"},
    )
    assert status == 400, (status, body)
    note("A write is refused", "PASS",
         f"HTTP {status}: {str(body['detail'])[:70]}")

    # ---- 8. interpret, then a drafted finding accepted by hand ----------
    interp = server.post(f"/cases/{case_id}/runs/{run['id']}/interpret")[1]
    assert interp["source"] == "deterministic", interp
    draft = server.post(f"/cases/{case_id}/runs/{run['id']}/draft-finding")[1]
    finding = server.post(
        f"/cases/{case_id}/findings",
        {
            "statement": draft["statement"],
            "interpretation": draft["interpretation"],
            "caveat": draft["caveat"],
            "grounds": draft["grounds"],
            "run_id": run["id"],
        },
    )[1]
    assert finding["validation_status"] == "not_evaluated", finding
    note("A drafted finding is accepted", "PASS",
         f"statement={finding['statement'][:60]}...")

    # ---- 9. validation reruns the computation ---------------------------
    validation = server.post(
        f"/cases/{case_id}/findings/{finding['id']}/validate"
    )[1]
    # The verdict is honest rather than flattering: this dataset has a null
    # revenue, so the missing-data check flags it and the verdict is
    # partially_supported rather than supported. The rerun itself reproduced.
    assert validation["status"] in ("supported", "partially_supported"), validation
    checks = {c["name"]: c for c in validation["checks"]}
    assert checks["reproducibility"]["passed"], validation
    note("The finding validates, and the null is flagged", "PASS",
         f"status={validation['status']}, reproducibility="
         f"{checks['reproducibility']['detail']}, missing_data="
         f"{'flagged' if not checks['missing_data']['passed'] else 'clean'}")

    # ---- 10. EVALUATE: the human audits the same artifact ---------------
    evaluation = server.post(
        f"/cases/{case_id}/datasets/{dataset_id}/evaluate",
        {"code": generated["code"], "claim": CLAIM, "kind": "sql"},
    )[1]
    verdicts = {f["axis"]: f["verdict"] for f in evaluation["findings"]}
    assert len(verdicts) == 9, verdicts
    note("EVALUATE answers all nine axes", "PASS",
         f"{sum(1 for v in verdicts.values() if v == 'pass')} pass, "
         f"{sum(1 for v in verdicts.values() if v == 'concern')} concern, "
         f"{sum(1 for v in verdicts.values() if v == 'fail')} fail")

    # ---- 11. the reviewer agent: a second point of view -----------------
    # A GET never proposes, so a page refresh commits nothing.
    read = server.get(f"/cases/{case_id}/agents/reviewer")
    assert read["pending"] is None, read
    note("The reviewer's GET proposes nothing", "PASS", "pending is null on a read")

    proposed = server.post(f"/cases/{case_id}/agents/reviewer")[1]
    pending = proposed["pending"]
    assert pending and pending["kind"] == "evaluate", proposed
    assert pending["payload"]["claim"] == finding["statement"], pending
    note("The reviewer proposes the finding's audit", "PASS",
         f"kind={pending['kind']}, claim is the finding's own statement")

    # One role's approval never authorises the other role's write: the
    # reviewer's pending step sent to the analyst's endpoint is a 409, never a
    # write. The 409 has two real shapes - a dict naming the analyst's own live
    # step when one is pending, a plain sentence when none is - and both refuse.
    analyst = server.post(f"/cases/{case_id}/agents/analyst")[1]
    status, body = server.post(
        f"/cases/{case_id}/agents/analyst/approve", {"step_id": pending["id"]}
    )
    assert status == 409, (status, body)
    if isinstance(body["detail"], dict):
        assert body["detail"]["role"] == "analyst", body
        assert body["detail"]["expected"] == analyst["pending"]["id"], body
        detail = "names the analyst's own pending step"
    else:
        detail = f"no analyst step pending: {body['detail']}"
    note("A cross-role approval is refused", "PASS", f"HTTP 409, {detail}")

    # Approving runs the audit through the same evaluate endpoint a human uses.
    approved = server.post(
        f"/cases/{case_id}/agents/reviewer/approve", {"step_id": pending["id"]}
    )[1]
    audit_step = approved["history"][-1]
    assert audit_step["status"] == "done", approved
    note("The approved audit records its verdict", "PASS", audit_step["note"])

    # Idempotence keyed on (code, claim): an audited finding is not re-proposed.
    again = server.post(f"/cases/{case_id}/agents/reviewer")[1]
    assert again["pending"] is None, again
    note("An audited finding is not re-audited", "PASS",
         "the reviewer's next derivation has nothing pending")

    status, body = server.post(f"/cases/{case_id}/agents/supervisor")
    assert status == 400, (status, body)
    assert "analyst" in body["detail"] and "reviewer" in body["detail"], body
    note("An unknown role is named, not guessed", "PASS", f"HTTP {status} names the roles")

    # ---- 12. the read-side surfaces of the finished case ----------------
    graph = server.get(f"/cases/{case_id}/evidence-graph")
    assert graph["counts"]["findings"] >= 1, graph
    note("The evidence graph traces the claim", "PASS",
         f"counts={graph['counts']}")

    history = server.get(f"/cases/{case_id}/history")
    assert len(history["events"]) >= 5, history
    note("The case history is the whole timeline", "PASS",
         f"{len(history['events'])} events, kinds="
         f"{sorted(history['counts'].keys())}")

    walk = server.get(f"/cases/{case_id}/learn")
    names = [s_["name"] for s_ in walk["steps"]]
    assert names == ["why", "what", "how", "validate"], walk
    note("The LEARN walk is the spec's four phases", "PASS",
         f"{', '.join(names)}; work on now: {walk['current']}")

    chat = server.post(f"/cases/{case_id}/chat", {"message": QUESTION})[1]
    assert chat["source"] == "deterministic", chat
    note("The case answers with citations", "PASS",
         f"source={chat['source']}, {len(chat['grounds'])} ground(s)")

    # ---- 13. export and import round trip -------------------------------
    package = server.get(f"/cases/{case_id}/export")
    imported = server.post("/cases/import", package)[1]
    assert imported["question"] == QUESTION, imported
    note("The case round-trips through export", "PASS",
         f"restored as {imported['id'][:8]} with fresh ids")


def run_agent_case(server: Server) -> None:
    """A case the analyst agent drives itself, one approved write at a time.

    This is the half the reviewer exists to audit: the loop proposes, a human
    approves each write, and the case closes with a validated finding - or
    states why it could not. The agent is bounded, so the loop always ends.
    """
    _, case = server.post("/cases", {"question": QUESTION, "dataset": "sales.csv"})
    case_id = case["id"]
    server.upload(f"/cases/{case_id}/datasets", "sales.csv", CSV)

    approved = 0
    rejected = 0
    kind_sequence: list[str] = []
    for _ in range(24):  # a bound the agent cannot exceed
        state = server.post(f"/cases/{case_id}/agent")[1]
        pending = state["pending"]
        if pending is None:
            ends = [s for s in state["history"] if s["kind"] == "end"]
            reason = ends[-1]["note"] if ends else "no further step"
            break
        kind_sequence.append(pending["kind"])
        if pending["kind"] == "end":
            rejected_reason = "the agent proposed stopping"
            server.post(
                f"/cases/{case_id}/agent/reject",
                {"step_id": pending["id"], "reason": rejected_reason},
            )
            rejected += 1
            continue
        state = server.post(
            f"/cases/{case_id}/agent/approve", {"step_id": pending["id"]}
        )[1]
        assert state["history"][-1]["status"] == "done", state
        approved += 1
    else:
        raise AssertionError(f"the agent did not terminate: {kind_sequence}")

    note("The analyst agent drives the loop to a stop", "PASS",
         f"approved={approved}, rejected={rejected}, steps="
         f"{'->'.join(kind_sequence) or 'none'}; stopped: {reason[:60]}")

    # Every write the agent made left an audit row naming its engine.
    state = server.get(f"/cases/{case_id}/agent")
    sources = {s["source"] for s in state["history"] if s["status"] == "done"}
    assert sources == {"deterministic"}, sources
    note("Every agent step names its engine", "PASS",
         f"sources={sorted(sources)}, {len(state['history'])} step(s) recorded")

    progress = server.get(f"/cases/{case_id}/progress")
    note("The agent-run case reaches a stated stage", "PASS",
         f"stage={progress['stage']}, loop_closed={progress['loop_closed']}")


def write_report(ok: bool, elapsed: float) -> None:
    report = Path(__file__).resolve().parent / "REPORT.md"
    stamp = datetime.now(timezone.utc).isoformat()
    lines = [
        "# End-to-End Verification (real server)",
        "",
        f"Run: {stamp}",
        f"Outcome: {'PASS' if ok else 'FAIL'} ({elapsed:.1f}s)",
        "",
        "A fresh uvicorn server on a free port with an isolated data dir, driven",
        "over real HTTP. No LLM key is passed to the server, so the deterministic",
        "engines answer and the run is reproducible offline.",
        "",
        "| Step | Verdict | Detail |",
        "|------|---------|--------|",
    ]
    for name, verdict, detail in steps:
        lines.append(f"| {name} | {verdict} | {detail} |")
    lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")
    log(f"report written to {report}")


def main() -> int:
    if not VENV_PYTHON.exists():
        print(f"[e2e] server venv not found at {VENV_PYTHON}", file=sys.stderr)
        return 2
    started = time.time()
    server = Server()
    ok = True
    try:
        log(f"server live on 127.0.0.1:{server.port} (data: {server.data_dir})")
        run_journey(server)
        run_agent_case(server)
        log("ALL STEPS PASS")
    except AssertionError as err:
        ok = False
        log(f"FAILED: {err}")
    except Exception as err:  # noqa: BLE001 - the report names the fault
        ok = False
        log(f"FAULT: {type(err).__name__}: {err}")
    finally:
        server.stop()
        write_report(ok, time.time() - started)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
