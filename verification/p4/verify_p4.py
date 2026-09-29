"""P4 Production Candidate verification.

P3 proved the loop is *useful*. P4 proves it is *safe to hand to someone else*.
Where the earlier gates walked the happy path, this one walks the edges a
controlled external user actually hits - and asserts the system stays honest at
every one:

    a dataset larger than the result cap -> the cap holds and says so
    -> an aggregation over the whole set is still exact (the cap loses nothing)
    -> bad SQL answers 400 with the engine's own message, and persists nothing
    -> a sandbox escape is refused and leaves nothing behind
    -> a fault *inside the harness* answers 500 instead of blaming the analyst
    -> a misbehaving LLM degrades to the deterministic engine, never blocks
    -> the assistant still proposes and still writes nothing
    -> a finding on an unordered result validates identically every time
    -> the case moves elsewhere and reproduces
    -> the suite runs green

The two properties that make this a P4 gate rather than a P3 re-run are the
error taxonomy (P4-RELIABILITY-002) and rerun determinism (P4-VALID-005). Both
are invisible on the happy path and both are what "production candidate" means:
a user who gives bad input is told what to fix, and a user who validates the
same finding twice gets the same answer.

Emits verification/p4/REPORT.md. Exit code 0 only if every step passes.
"""

import io
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

# Environment variables that turn an assistant engine into a live LLM caller.
# The gate's own journey must be reproducible without a network, so these are
# scrubbed from this process before any assistant call (see main). The test
# suite the gate spawns gets the same treatment. One step deliberately sets a
# dummy key and breaks the LLM on purpose, to prove the fallback contract.
_LLM_ENV_VARS = frozenset(
    {"DAH_LLM_API_KEY", "OPENAI_API_KEY", "DAH_LLM_BASE_URL", "DAH_LLM_MODEL"}
)

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "server"))

import app.main as main_module  # noqa: E402
import app.planner as planner_module  # noqa: E402
from app.db import get_connection  # noqa: E402
from app.main import app, get_db  # noqa: E402
import app.db as db_module  # noqa: E402

# Scrub as early as possible: app.main loaded server/.env at import (this is a
# script, not a pytest module), and every assistant engine reads these at call
# time. Removing them makes the journey deterministic - no live call per
# assistant step.
for _var in _LLM_ENV_VARS:
    os.environ.pop(_var, None)

# Large enough to exceed the 1000-row result cap, small enough to keep the gate
# fast. Every value is a closed function of the row index so the expectations
# below are analytically known rather than measured.
ROWS = 5000
REGIONS = ["north", "south", "east", "west", "central"]
RATES = {"north": 100.0, "south": 80.0, "east": 60.0, "west": 40.0, "central": 20.0}
GROUPS = 1000  # rows per region: ROWS // len(REGIONS)


def _large_csv() -> bytes:
    """A deterministic dataset whose aggregates are known by construction.

    revenue depends only on the region, so each region's sum is exactly its
    rate times the group size - no floating-point accumulation surprises.
    """
    out = io.StringIO()
    out.write("id,region,revenue\n")
    for i in range(1, ROWS + 1):
        region = REGIONS[(i - 1) % len(REGIONS)]
        out.write(f"{i},{region},{RATES[region]:.1f}\n")
    return out.getvalue().encode()


# The unordered query that exposed the validation flake (P4-VALID-005): no
# ORDER BY, so DuckDB may answer with its groups in any order across
# connections. Reproduction must treat the result as a bag of rows.
UNORDERED_SQL = (
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region"
)
EXPECTED_TOTALS = {region: RATES[region] * GROUPS for region in REGIONS}
GRAND_TOTAL = sum(EXPECTED_TOTALS.values())

# A write the read-only gate must refuse.
WRITE_SQL = "DELETE FROM read_csv_auto(?)"

# A script that reaches outside its scratch directory. The kernel denies it
# under sandbox-exec; on a host without the OS sandbox the in-process guards
# deny it, so the answer is a 400 either way.
SANDBOX_PROBE = (
    "with open('/tmp/dah_p4_gate_probe.txt', 'w') as probe:\n"
    "    probe.write('the sandbox did not stop this write')\n"
    "result = [{'escaped': True}]\n"
)


class _Boom:
    """A harness-side fault: not the input's fault, so never a 400."""

    def __call__(self, *args, **kwargs):
        raise KeyError("the harness itself broke")


class _BrokenLLM:
    """An LLM that always fails - the fallback contract must still hold."""

    def __init__(self, *args, **kwargs):
        pass

    def plan(self, question, profile, context=None):
        raise RuntimeError("the LLM endpoint is unreachable")


def log(message: str) -> None:
    print(f"[verify] {message}")


def main() -> int:
    work = Path(tempfile.mkdtemp())
    db_module.DATA_DIR = work / "data"
    db_path = work / "p4.db"

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    steps: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        steps.append((name, ok, detail))
        log(f"{name}: {'PASS' if ok else 'FAIL'} ({detail})")

    with TestClient(app) as client:
        # 1. A case phrased the way an external user would phrase it
        case = client.post(
            "/cases",
            json={
                "question": "Which regions carry the most revenue?",
                "dataset": "regional_sales.csv",
            },
        )
        ok = case.status_code == 201
        case_id = case.json()["id"] if ok else ""
        record("Create case", ok, f"HTTP {case.status_code}")

        # 2. A dataset deliberately larger than the result cap
        attach = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("regional_sales.csv", _large_csv(), "text/csv")},
        )
        ok = attach.status_code == 201
        dataset_id = attach.json()["id"] if ok else ""
        record(
            "Attach a dataset larger than the result cap",
            ok,
            f"HTTP {attach.status_code}, {ROWS} rows",
        )

        # 3. Profiling is correct at scale - the P4-PERF-006 change read the
        # description with LIMIT 0 and folded the row total into one pass, so
        # a profile whose counts depend on that plumbing is the regression guard
        profile = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        profile_body = profile.json() if profile.status_code == 201 else {}
        stats = profile_body.get("stats", {})
        record(
            "Profile is correct at scale",
            profile.status_code == 201
            and profile_body.get("rows") == ROWS
            and profile_body.get("columns") == ["id", "region", "revenue"]
            and stats.get("region", {}).get("distinct_count") == len(REGIONS)
            and stats.get("revenue", {}).get("min") == 20.0
            and stats.get("revenue", {}).get("max") == 100.0
            and profile_body.get("duplicate_rows") == 0,
            f"rows={profile_body.get('rows')}, "
            f"distinct regions={stats.get('region', {}).get('distinct_count')}",
        )

        # 4. The cap holds: a full scan is truncated and says so, never
        # unbounded memory
        full_scan = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT * FROM read_csv_auto(?)"},
        )
        scan_body = full_scan.json() if full_scan.status_code == 201 else {}
        record(
            "A full scan is capped and flagged",
            full_scan.status_code == 201
            and scan_body.get("row_count") == 1000
            and scan_body.get("truncated") is True
            and len(scan_body.get("rows", [])) == 1000,
            f"row_count={scan_body.get('row_count')}, "
            f"truncated={scan_body.get('truncated')}",
        )

        # 5. The cap costs nothing for aggregates: an aggregation over the whole
        # dataset reads every row, not just the first capped page
        aggregate = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT COUNT(*) AS n, SUM(revenue) AS total"
                        " FROM read_csv_auto(?)"},
        )
        agg_body = aggregate.json() if aggregate.status_code == 201 else {}
        record(
            "An aggregation reads every row, not the capped page",
            aggregate.status_code == 201
            and agg_body.get("rows") == [[ROWS, GRAND_TOTAL]]
            and agg_body.get("truncated") is False,
            f"rows={agg_body.get('rows')}",
        )

        # 6. Bad SQL is the input's fault: 400 with the engine's own message,
        # and nothing persisted
        runs_before = len(client.get(f"/cases/{case_id}/runs").json())
        bad = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT * FROM read_csv_auto(?) WHERE"},
        )
        bad_body = bad.json() if bad.status_code == 400 else {}
        runs_after_bad = len(client.get(f"/cases/{case_id}/runs").json())
        record(
            "Bad SQL answers 400 with the engine's message",
            bad.status_code == 400
            and bool(bad_body.get("detail"))
            and runs_after_bad == runs_before,
            f"HTTP {bad.status_code}, detail={str(bad_body.get('detail'))[:48]}",
        )

        # 7. A write attempt is refused by the read-only gate, still no run
        write = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": WRITE_SQL},
        )
        record(
            "A write query is refused",
            write.status_code == 400
            and len(client.get(f"/cases/{case_id}/runs").json()) == runs_before,
            f"HTTP {write.status_code}",
        )

        # 8. The hard sandbox refuses an escape and leaves nothing behind
        probe = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs/python",
            json={"code": SANDBOX_PROBE},
        )
        record(
            "A sandbox escape is refused and persists nothing",
            probe.status_code == 400
            and len(client.get(f"/cases/{case_id}/runs").json()) == runs_before,
            f"HTTP {probe.status_code}",
        )

        # 9. A fault inside the harness answers 500, never a 400 that blames the
        # analyst (P4-RELIABILITY-002). Observed with a client that does not
        # re-raise, the only way a 500 is visible in process.
        original_run_query = main_module.run_query
        main_module.run_query = _Boom()
        try:
            with TestClient(app, raise_server_exceptions=False) as fault_client:
                fault = fault_client.post(
                    f"/cases/{case_id}/datasets/{dataset_id}/runs",
                    json={"sql": "SELECT * FROM read_csv_auto(?)"},
                )
        finally:
            main_module.run_query = original_run_query
        record(
            "A harness fault answers 500, not 400",
            fault.status_code == 500,
            f"HTTP {fault.status_code} "
            f"(a 400 here would blame the analyst for our own bug)",
        )

        # 10. A misbehaving LLM degrades to the deterministic engine instead of
        # blocking the loop. The key is set on purpose; the LLM is broken on
        # purpose; the answer must still be a plan.
        os.environ["DAH_LLM_API_KEY"] = "gate-dummy-key"
        original_llm = planner_module.LLMPlanner
        planner_module.LLMPlanner = _BrokenLLM
        try:
            plan = client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")
        finally:
            planner_module.LLMPlanner = original_llm
            os.environ.pop("DAH_LLM_API_KEY", None)
        plan_body = plan.json().get("plan", {}) if plan.status_code == 201 else {}
        # A configured LLM that fails must still answer with a plan, and the
        # source must say it fell back - a silent "deterministic" here would
        # hide the degradation FIX-TIMEOUT-006 made visible.
        record(
            "A broken LLM degrades instead of blocking",
            plan.status_code == 201
            and plan.json().get("source") == planner_module.SOURCE_DETERMINISTIC_FALLBACK
            and bool(plan_body.get("sub_questions")),
            f"source={plan.json().get('source')}, "
            f"sub_questions={len(plan_body.get('sub_questions', []))}",
        )

        # 11. The run the finding will stand on - deliberately unordered
        unordered = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": UNORDERED_SQL},
        )
        ok = unordered.status_code == 201
        unordered_body = unordered.json() if ok else {}
        unordered_id = unordered_body.get("id", "") if ok else ""
        totals = {
            row[0]: row[1]
            for row in unordered_body.get("rows", [])
        }
        record(
            "Run the unordered aggregation",
            ok
            and totals == EXPECTED_TOTALS
            and unordered_body.get("truncated") is False,
            f"row_count={unordered_body.get('row_count')}, totals={totals}",
        )

        # 12. The assistant drafts the finding the result supports - and still
        # creates nothing
        draft = client.post(f"/cases/{case_id}/runs/{unordered_id}/draft-finding")
        draft_body = draft.json() if draft.status_code == 200 else {}
        findings_empty = client.get(f"/cases/{case_id}/findings").json() == []
        record(
            "The assistant drafts a finding, writes nothing",
            draft.status_code == 200
            and bool(draft_body.get("statement"))
            and bool(draft_body.get("grounds"))
            and findings_empty,
            f"source={draft_body.get('source')}, "
            f"grounds={len(draft_body.get('grounds', []))}",
        )

        # 13. The human accepts through the only endpoint that writes
        finding = client.post(
            f"/cases/{case_id}/findings",
            json={
                "run_id": unordered_id,
                "statement": draft_body.get(
                    "statement", "north carries the most revenue"
                ),
                "interpretation": draft_body.get("interpretation"),
                "caveat": draft_body.get("caveat"),
            },
        )
        ok = finding.status_code == 201
        finding_id = finding.json()["id"] if ok else ""
        record("Accept the draft as a finding", ok, f"HTTP {finding.status_code}")

        # 14. The P4 property: validating the same finding repeatedly must
        # always agree. An unordered result can come back with its rows in a
        # different order per connection; before P4-VALID-005 that flipped the
        # verdict between supported and insufficient_evidence.
        verdicts = set()
        for _ in range(8):
            response = client.post(
                f"/cases/{case_id}/findings/{finding_id}/validate"
            )
            if response.status_code == 200:
                verdicts.add(response.json()["status"])
        record(
            "Validation is deterministic across reruns",
            verdicts == {"supported"},
            f"verdicts={verdicts} (a flake would show more than one)",
        )

        # 15. Evidence completes the stage the workflow waits on: a finding plus
        # a chart rendered from the same run
        chart = client.post(
            f"/cases/{case_id}/runs/{unordered_id}/charts",
            json={
                "kind": "bar",
                "x": "region",
                "y": "total",
                "title": "Total revenue by region",
                "format": "png",
            },
        )
        ok = chart.status_code == 201
        chart_id = chart.json()["id"] if ok else ""
        image = (
            client.get(f"/cases/{case_id}/charts/{chart_id}/image") if chart_id else None
        )
        record(
            "Render the chart the evidence stage needs",
            ok
            and image is not None
            and image.status_code == 200
            and image.content.startswith(b"\x89PNG\r\n\x1a\n"),
            f"HTTP {chart.status_code}, image bytes={len(image.content) if image else 0}",
        )

        # 16. The workflow closes on a large dataset too
        progress = client.get(f"/cases/{case_id}/progress")
        progress_body = progress.json() if progress.status_code == 200 else {}
        record(
            "The loop closes at scale",
            progress.status_code == 200
            and progress_body.get("stage") == "validated"
            and progress_body.get("loop_closed") is True,
            f"stage={progress_body.get('stage')}, "
            f"loop_closed={progress_body.get('loop_closed')}",
        )

        # 17. The case moves elsewhere and reproduces
        export = client.get(f"/cases/{case_id}/export")
        package = export.json() if export.status_code == 200 else {}
        imported = client.post("/cases/import", json=package)
        ok = imported.status_code == 201
        imported_id = imported.json()["id"] if ok else ""
        restored = (
            {
                item["filename"]: item["id"]
                for item in client.get(f"/cases/{imported_id}/datasets").json()
            }
            if ok
            else {}
        )
        rerun = (
            client.post(
                f"/cases/{imported_id}/runs",
                json={
                    "sql": UNORDERED_SQL,
                    "dataset_ids": [
                        restored["regional_sales.csv"],
                    ],
                },
            )
            if restored
            else None
        )
        rerun_totals = (
            {row[0]: row[1] for row in rerun.json()["rows"]}
            if rerun is not None and rerun.status_code == 201
            else {}
        )
        record(
            "The case reproduces elsewhere",
            ok
            and rerun is not None
            and rerun.status_code == 201
            and rerun_totals == EXPECTED_TOTALS,
            f"totals={rerun_totals}",
        )

    # 18. The test suite runs green. -rf names every failing test so a single
    # flake is diagnosable from the report. The LLM credentials are scrubbed
    # from the subprocess on purpose (see the block near the imports).
    suite_env = {
        name: value for name, value in os.environ.items()
        if name not in _LLM_ENV_VARS
    }
    tests = subprocess.run(
        [str(REPO / "server/.venv/bin/python"), "-m", "pytest", "-q", "-rf"],
        cwd=str(REPO / "server"),
        env=suite_env,
        capture_output=True,
        text=True,
    )
    suite_ok = tests.returncode == 0
    summary = [line for line in tests.stdout.splitlines() if "passed" in line]
    failed_tests = [
        line.strip() for line in tests.stdout.splitlines() if line.startswith("FAILED")
    ]
    detail = summary[-1].strip() if summary else f"exit {tests.returncode}"
    if failed_tests:
        detail = detail + " | " + "; ".join(failed_tests)
    record("Test suite runs", suite_ok, detail)

    failures = [name for name, ok, _ in steps if not ok]
    decision = "PASS" if not failures else "FAIL"

    lines = [
        "# P4 Production Candidate Verification",
        "",
        f"Run: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Journey under test",
        "",
        "```",
        "attach a dataset larger than the result cap -> profile is exact at scale",
        "-> a full scan is capped and flagged (never unbounded)",
        "-> an aggregation still reads every row (the cap costs nothing)",
        "-> bad SQL answers 400 with the engine's message, persists nothing",
        "-> a write is refused -> a sandbox escape is refused",
        "-> a harness fault answers 500 instead of blaming the analyst",
        "-> a broken LLM degrades to deterministic, never blocks",
        "-> the assistant drafts a finding and writes nothing",
        "-> the human accepts -> validation agrees across reruns",
        "-> the loop closes at scale -> the case reproduces elsewhere",
        "```",
        "",
        "P3 proved the loop is useful; this gate proves it is safe to hand to",
        "someone else. The two properties that make it P4 rather than a P3 re-run",
        "- the error taxonomy and rerun determinism - are invisible on the happy",
        "path, and both are what 'production candidate' has to mean.",
        "",
        "## Steps",
        "",
        "| Step | Result | Detail |",
        "|------|--------|--------|",
    ]
    lines += [f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |" for name, ok, detail in steps]
    lines += [
        "",
        "## Exit criteria (P4 gate: error semantics, determinism, scale,",
        "the read-only and sandbox boundaries, graceful degradation)",
        "",
        "| Criterion | Status |",
        "|-----------|--------|",
    ]
    criteria = [
        ("Bad input is the input's fault, with a message and no side effects",
         "Bad SQL answers 400 with the engine's message"),
        ("A harness fault is never reported as the user's fault",
         "A harness fault answers 500, not 400"),
        ("Read-only and OS-sandbox boundaries hold and persist nothing",
         "A sandbox escape is refused and persists nothing"),
        ("A failure of the LLM degrades rather than blocking",
         "A broken LLM degrades instead of blocking"),
        ("Results are bounded but aggregates stay exact",
         "An aggregation reads every row, not the capped page"),
        ("Profiling is correct at scale",
         "Profile is correct at scale"),
        ("The same finding validates the same way every time",
         "Validation is deterministic across reruns"),
        ("The assistant proposes and never decides",
         "The assistant drafts a finding, writes nothing"),
        ("The loop closes on a large dataset",
         "The loop closes at scale"),
        ("A case moves elsewhere and reproduces",
         "The case reproduces elsewhere"),
    ]
    for label, step_name in criteria:
        status = "PASS" if any(n == step_name and ok for n, ok, _ in steps) else "FAIL"
        lines.append(f"| {label} | {status} |")
    lines += [
        "",
        "## Decision",
        "",
        f"{decision}. "
        + (
            "The harness behaves correctly at every edge a controlled external "
            "user can reach: bad input is answered with the engine's own message "
            "and leaves nothing behind, a fault in the harness is reported as "
            "the server's problem instead of the analyst's, an unavailable LLM "
            "degrades rather than blocking, results are capped without losing "
            "aggregates, and validating the same finding twice always agrees. "
            "P4 is done and the project is ready for the production-grade track "
            "(distribution, observability, signing)."
            if decision == "PASS"
            else "Blocked: " + ", ".join(failures)
        ),
        "",
    ]
    out = REPO / "verification/p4/REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    log(f"report written to verification/p4/REPORT.md")
    log(f"DECISION: {decision}")
    return 0 if decision == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
