"""The analytical golden suite (P8-GOLDEN-005): measurement, not assertion.

Two numbers the PRD asks for and nothing previously computed:

    AT-40 - 100% of deterministic reference calculations match expected results
    AT-01 - >= 95% of scripted workflow attempts complete the full loop,
            over >= 20 runs and >= 3 datasets

Both are measured against a real server over real HTTP, the pattern
verify_e2e.py established: a fresh uvicorn on a free port, an isolated data
dir, and the LLM env vars scrubbed from the server's subprocess so the
deterministic engines answer and the run needs no network. Nothing is mocked,
and no golden value is the engine's own output - see reference.py for how the
expectations are derived and independently recomputed before this runner asks
the engine anything.

The two measurements are one journey, not two passes: each scripted run walks
the whole loop (create, question, attach, profile, plan, run, interpret,
draft, accept, validate, reopen) *and* the run it makes is the reference query,
so the same execution answers both numbers. A run counts complete when every
stage produced its artifact and the case reopens with it; a verdict of
`insufficient_evidence` is still a complete run, because a finding that the
evidence does not support is a finished analysis, not a failed one.

    server/.venv/bin/python verification/golden/verify_golden.py

Exit 0 only when both thresholds hold; the report is written to
verification/golden/REPORT.md either way, and the same two numbers are
asserted in server/tests/test_golden.py so a regression fails a test rather
than a report nobody reads.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SERVER = REPO / "server"
VENV_PYTHON = SERVER / ".venv" / "bin" / "python"
REPORT_PATH = REPO / "verification" / "golden" / "REPORT.md"

# Run from the repo root; make the package importable when it is not.
sys.path.insert(0, str(REPO))

from verification.golden.reference import (
    AT40_SHAPES,
    CHECKS,
    DATASETS_DIR,
    GoldenCheck,
    recompute,
)

# Turning any of these on makes the planner/generator/interpreter/drafter call
# a live LLM. A golden run must be reproducible without a network, so they are
# emptied in the server's environment exactly as verify_e2e.py does.
LLM_ENV_VARS = frozenset(
    {"DAH_LLM_API_KEY", "OPENAI_API_KEY", "DAH_LLM_BASE_URL", "DAH_LLM_MODEL"}
)

# The thresholds the PRD names. A reference calculation must match every time;
# a workflow attempt is allowed to fail sometimes, but not often.
REFERENCE_THRESHOLD = 1.0
COMPLETION_THRESHOLD = 0.95
MIN_WORKFLOW_RUNS = 20
MIN_DATASETS = 3

# A workflow stage that produced nothing of its own is a failure the report
# names; the loop itself is the ordered contract AT-01 spells out.
STAGES = (
    "create",
    "attach",
    "profile",
    "plan",
    "run",
    "interpret",
    "draft",
    "accept",
    "validate",
    "reopen",
)


def log(message: str) -> None:
    print(f"[golden] {message}", flush=True)


def rows_match(actual: list[list], expected: list[list], tolerance: float) -> bool:
    """Do the engine's rows equal the golden rows?

    Counts and labels compare exactly; two numerics compare within the check's
    stated tolerance, because an integer column and a float one are the same
    answer in different clothes (a week's `spend` is 100 either way) and a
    real like a correlation or a mean carries no last bit that matters. Order
    is part of the expectation - every reference query carries an ORDER BY, so
    a different order is a different computation, not a reshuffling.
    """
    if len(actual) != len(expected):
        return False
    for actual_row, expected_row in zip(actual, expected):
        if len(actual_row) != len(expected_row):
            return False
        for left, right in zip(actual_row, expected_row):
            left_numeric = isinstance(left, (int, float)) and not isinstance(left, bool)
            right_numeric = isinstance(right, (int, float)) and not isinstance(
                right, bool
            )
            if left_numeric and right_numeric:
                if abs(left - right) > tolerance:
                    return False
            elif left != right:
                return False
    return True


@dataclass
class CheckResult:
    check_id: str
    dataset: str
    shape: str
    reference_ok: bool
    workflow_ok: bool
    failed_stage: str = ""
    detail: str = ""
    verdict: str = ""


@dataclass
class GoldenReport:
    reference_passed: int
    reference_total: int
    workflow_completed: int
    workflow_total: int
    datasets: int
    results: list[CheckResult] = field(default_factory=list)

    @property
    def reference_rate(self) -> float:
        return self.reference_passed / self.reference_total if self.reference_total else 0.0

    @property
    def completion_rate(self) -> float:
        return self.workflow_completed / self.workflow_total if self.workflow_total else 0.0

    @property
    def ok(self) -> bool:
        return (
            self.reference_rate >= REFERENCE_THRESHOLD
            and self.completion_rate >= COMPLETION_THRESHOLD
            and self.workflow_total >= MIN_WORKFLOW_RUNS
            and self.datasets >= MIN_DATASETS
        )


class Server:
    """A real uvicorn server on a free port, isolated to a temp data dir."""

    def __init__(self) -> None:
        self.data_dir = tempfile.mkdtemp(prefix="dah-golden-")
        self.db_path = Path(self.data_dir) / "golden.db"

        env = dict(os.environ)
        # The server loads server/.env on a plain uvicorn start; an empty value
        # here wins over the file and the engines treat an empty key as absent,
        # so the deterministic engines answer and the run needs no network.
        for var in LLM_ENV_VARS:
            env[var] = ""
        env["DAH_DATA_DIR"] = self.data_dir
        env["DAH_DB_PATH"] = str(self.db_path)

        self.proc = subprocess.Popen(
            [
                str(VENV_PYTHON),
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self._free_port()),
            ],
            cwd=str(SERVER),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # The server logs every request. Left undrained, the pipe's kernel
        # buffer fills (~64KB on macOS), the server then blocks writing its
        # next log line, and every request after that hangs - the client waits
        # on a server that is waiting on nobody. A reader thread keeps the pipe
        # empty and the last lines available for a post-mortem.
        self.log_lines: list[str] = []
        self._drain = threading.Thread(
            target=self._pump_stdout, daemon=True, name="dah-golden-server-log"
        )
        self._drain.start()
        self.port = self._wait_for_health()

    def _pump_stdout(self) -> None:
        """Keep the server's stdout pipe empty; cap the history we keep."""
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.log_lines.append(line)
            if len(self.log_lines) > 500:
                del self.log_lines[:200]

    def server_log_tail(self, lines: int = 20) -> str:
        """The server's own last words, for a failure that is not ours."""
        return "".join(self.log_lines[-lines:])

    @staticmethod
    def _free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _wait_for_health(self, timeout: float = 60.0) -> int:
        # The pump thread owns proc.stdout - reading it here too is a race the
        # pump usually wins, and a readline() that never sees the announcement
        # blocks past this loop's deadline with no timeout of its own. The
        # announcement is read from the pump's captured history instead.
        deadline = time.time() + timeout
        port: int | None = None
        while time.time() < deadline and port is None:
            if self.proc.poll() is not None:
                raise RuntimeError(
                    f"server exited early:\n{self.server_log_tail(40)}"
                )
            for line in list(self.log_lines):
                if "Uvicorn running on" in line:
                    port = int(line.rsplit(":", 1)[-1].split()[0])
                    break
            if port is None:
                time.sleep(0.1)
        if port is None:
            raise RuntimeError("server did not announce a port in time")
        while time.time() < deadline:
            if self._get(port, "/health").get("status") == "ok":
                return port
            time.sleep(0.25)
        raise RuntimeError("server never answered /health")

    def _get(self, port: int, path: str) -> dict:
        with urllib.request.urlopen(
            urllib.request.Request(f"http://127.0.0.1:{port}{path}"), timeout=120
        ) as res:
            body = res.read()
            return json.loads(body) if body else {}

    def get(self, path: str) -> dict:
        return self._get(self.port, path)

    def post(self, path: str, payload: dict | str | None = None) -> tuple[int, dict]:
        data = (
            json.dumps(payload).encode()
            if isinstance(payload, dict)
            else (payload.encode() if isinstance(payload, str) else b"")
        )
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as res:
                body = res.read()
                return res.status, (json.loads(body) if body else {})
        except urllib.error.HTTPError as err:
            body = err.read()
            try:
                return err.code, json.loads(body)
            except json.JSONDecodeError:
                return err.code, {"raw": body.decode(errors="replace")}

    def upload(self, path: str, filename: str, content: str) -> dict:
        boundary = "dah-golden-boundary"
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
        with urllib.request.urlopen(req, timeout=180) as res:
            return json.loads(res.read())

    def stop(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


def _journey_fault(server: Server, stage: str, err: Exception) -> str:
    """A failure we did not expect, with the server's own log for context."""
    return (
        f"{type(err).__name__} at {stage}: {err}\n"
        f"server log tail:\n{server.server_log_tail()}"
    )


def _run_one(server: Server, check: GoldenCheck) -> CheckResult:
    """One scripted journey: the workflow loop, carrying the reference check.

    Every stage that produces nothing returns with `failed_stage` set, so a
    failure in the report names the step rather than the whole run being a
    mystery. The reference comparison happens on the run the loop made.
    """
    failed = ""
    detail = ""
    verdict = ""
    reference_ok = False

    # create + question
    status, case = server.post(
        "/cases", {"question": check.question, "dataset": check.dataset}
    )
    if status != 201:
        return CheckResult(
            check.check_id, check.dataset, check.shape, False, False, "create",
            f"HTTP {status}: {str(case)[:120]}",
        )
    case_id = case["id"]

    # attach (a real multipart upload, the surface a user touches)
    fixture = (DATASETS_DIR / check.dataset).read_text(encoding="utf-8")
    dataset = server.upload(
        f"/cases/{case_id}/datasets", check.dataset, fixture
    )
    if "id" not in dataset:
        return CheckResult(
            check.check_id, check.dataset, check.shape, False, False, "attach",
            f"upload answered no id: {str(dataset)[:120]}",
        )
    dataset_id = dataset["id"]

    # profile
    _, profile = server.post(
        f"/cases/{case_id}/datasets/{dataset_id}/profile"
    )
    if not profile.get("columns"):
        failed = "profile"
        detail = "the profile produced no columns"

    # plan (the deterministic planner, no LLM)
    _, plan = server.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")
    if not failed and plan.get("source") != "deterministic":
        failed = "plan"
        detail = f"source={plan.get('source')!r}, expected deterministic"

    # run - the reference query itself, and the loop's analysis step
    if not failed:
        status, run = server.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", {"sql": check.sql}
        )
        if status != 201 or run.get("row_count", 0) < 1:
            failed = "run"
            detail = f"HTTP {status}, row_count={run.get('row_count')}"
        else:
            # The reference measurement: the engine's rows against the golden
            # value, compared only after hand and independent paths agreed.
            reference_ok = rows_match(run["rows"], check.expected, check.tolerance)
            if not reference_ok:
                detail = (
                    f"rows {json.dumps(run['rows'])} do not match "
                    f"{json.dumps(check.expected)} within {check.tolerance}"
                )

    # interpret (a plain-language read of the result)
    if not failed:
        run_id = run["id"]
        _, interpretation = server.post(
            f"/cases/{case_id}/runs/{run_id}/interpret"
        )
        if interpretation.get("source") != "deterministic":
            failed = "interpret"
            detail = f"source={interpretation.get('source')!r}"

    # draft + accept - the drafter proposes, a human disposes
    if not failed:
        _, draft = server.post(f"/cases/{case_id}/runs/{run_id}/draft-finding")
        if not draft.get("statement"):
            failed = "draft"
            detail = "the drafter produced no statement"
        else:
            status, finding = server.post(
                f"/cases/{case_id}/findings",
                {
                    "statement": draft["statement"],
                    "interpretation": draft["interpretation"],
                    "caveat": draft["caveat"],
                    "grounds": draft["grounds"],
                    "run_id": run_id,
                },
            )
            if status != 201:
                failed = "accept"
                detail = f"HTTP {status}: {str(finding)[:120]}"

    # validate - the verdict is recomputed, never assumed
    if not failed:
        status, validation = server.post(
            f"/cases/{case_id}/findings/{finding['id']}/validate"
        )
        verdict = validation.get("status", "")
        if status != 200 or verdict not in (
            "supported",
            "partially_supported",
            "insufficient_evidence",
        ):
            failed = "validate"
            detail = f"HTTP {status}, status={verdict!r}"
        elif check.shape == "validation":
            # The validation shape has teeth: a finding quoting the golden
            # figures must reproduce them, so the calculation check passes
            # rather than the verdict merely being a recognised word.
            checks = {c["name"]: c for c in validation.get("checks", [])}
            if not checks.get("calculation", {}).get("passed"):
                failed = "validate"
                detail = (
                    "a validation-shape finding did not reproduce its "
                    f"calculation: {checks.get('calculation', {}).get('detail', '')}"
                )

    # reopen - the case still exists and still carries what the loop made
    if not failed:
        reopened = server.get(f"/cases/{case_id}")
        findings = server.get(f"/cases/{case_id}/findings")
        if reopened.get("id") != case_id or not any(
            f.get("id") == finding["id"] for f in findings
        ):
            failed = "reopen"
            detail = "the reopened case is missing the finding it accepted"

    return CheckResult(
        check_id=check.check_id,
        dataset=check.dataset,
        shape=check.shape,
        reference_ok=reference_ok,
        workflow_ok=not failed,
        failed_stage=failed,
        detail=detail,
        verdict=verdict,
    )


def verify_expectations(checks: tuple[GoldenCheck, ...] = CHECKS) -> None:
    """The fixture's own audit: hand-computed against independently recomputed.

    This runs before the engine is asked anything, because comparing the engine
    against a wrong fixture would measure nothing. A disagreement here means the
    *fixture* is wrong, not the engine.
    """
    for check in checks:
        independent = recompute(check)
        if not rows_match(independent, check.expected, check.tolerance):
            raise RuntimeError(
                f"{check.check_id}: the hand-computed expectation "
                f"{check.expected} disagrees with the independent "
                f"recomputation {independent}; the fixture is wrong"
            )


def run_golden(server: Server | None = None, write_report: bool = True) -> GoldenReport:
    """Measure the two numbers. Owns the server it starts unless given one."""
    owns_server = server is None
    if server is None:
        server = Server()
    try:
        log(f"server live on 127.0.0.1:{server.port} (data: {server.data_dir})")
        verify_expectations()
        log(f"{len(CHECKS)} expectations verified two ways before running")

        results = [_run_one(server, check) for check in CHECKS]
        for result in results:
            outcome = "PASS" if result.workflow_ok and result.reference_ok else "FAIL"
            log(
                f"{result.check_id}: {outcome} "
                f"(shape={result.shape}, workflow="
                f"{'complete' if result.workflow_ok else 'failed at ' + result.failed_stage}"
                f", reference={'match' if result.reference_ok else 'mismatch'}"
                f"{', verdict=' + result.verdict if result.verdict else ''})"
            )
            if result.detail:
                log(f"    {result.detail[:200]}")

        report = GoldenReport(
            reference_passed=sum(1 for r in results if r.reference_ok),
            reference_total=len(results),
            workflow_completed=sum(1 for r in results if r.workflow_ok),
            workflow_total=len(results),
            datasets=len({r.dataset for r in results}),
            results=results,
        )
        log(
            f"reference {report.reference_passed}/{report.reference_total} "
            f"({report.reference_rate:.1%}); workflow "
            f"{report.workflow_completed}/{report.workflow_total} "
            f"({report.completion_rate:.1%}) over {report.datasets} dataset(s)"
        )
        if write_report:
            write_report_file(report)
        return report
    finally:
        if owns_server:
            server.stop()


def write_report_file(report: GoldenReport) -> None:
    by_shape: dict[str, list[CheckResult]] = {shape: [] for shape in AT40_SHAPES}
    for result in report.results:
        by_shape[result.shape].append(result)

    lines = [
        "# Golden Suite Report (P8-GOLDEN-005)",
        "",
        "Measured against a real server over HTTP, isolated to a temporary data",
        "dir, with the LLM variables empty so the deterministic engines answer.",
        "Every expectation was verified two ways - hand-computed and",
        "independently recomputed from the fixture - before the engine ran.",
        "",
        "## The two numbers",
        "",
        f"- **AT-40 reference calculations:** {report.reference_passed}/"
        f"{report.reference_total} match within a stated tolerance "
        f"(**{report.reference_rate:.1%}**, threshold 100%)",
        f"- **AT-01 workflow completion:** {report.workflow_completed}/"
        f"{report.workflow_total} scripted runs complete the full loop "
        f"(**{report.completion_rate:.1%}**, threshold 95%)",
        f"- **Datasets:** {report.datasets} (minimum 3); "
        f"runs: {report.workflow_total} (minimum 20)",
        "",
        "## Coverage of AT-40's ten shapes",
        "",
        "| Shape | Checks | All match |",
        "|-------|--------|-----------|",
    ]
    for shape in AT40_SHAPES:
        results = by_shape[shape]
        matched = sum(1 for r in results if r.reference_ok)
        lines.append(
            f"| {shape} | {len(results)} | "
            f"{'yes' if matched == len(results) and results else 'n/a' if not results else 'no'} |"
        )
    lines += [
        "",
        "## Runs",
        "",
        "| Check | Dataset | Shape | Reference | Workflow | Verdict |",
        "|-------|---------|-------|-----------|----------|---------|",
    ]
    for result in report.results:
        lines.append(
            f"| {result.check_id} | {result.dataset} | {result.shape} | "
            f"{'match' if result.reference_ok else 'MISMATCH'} | "
            f"{'complete' if result.workflow_ok else 'failed at ' + result.failed_stage} | "
            f"{result.verdict or '-'} |"
        )
    failures = [r for r in report.results if not (r.reference_ok and r.workflow_ok)]
    if failures:
        lines += ["", "## Failures", ""]
        for result in failures:
            lines.append(f"- **{result.check_id}** ({result.shape}): {result.detail}")
    else:
        lines += ["", "No failures.", ""]

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"report written to {REPORT_PATH}")


def main() -> int:
    if not VENV_PYTHON.exists():
        print(f"[golden] server venv not found at {VENV_PYTHON}", file=sys.stderr)
        return 2
    started = time.time()
    report = run_golden()
    log(f"elapsed {time.time() - started:.1f}s")
    if report.ok:
        log("BOTH THRESHOLDS HOLD")
        return 0
    log(
        "THRESHOLD MISSED: reference "
        f"{report.reference_rate:.1%} (needs 100%), workflow "
        f"{report.completion_rate:.1%} (needs 95%), "
        f"{report.datasets} dataset(s) (needs 3), "
        f"{report.workflow_total} runs (needs 20)"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
