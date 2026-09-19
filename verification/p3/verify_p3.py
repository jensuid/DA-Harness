"""P3 V1 milestone verification.

Runs the full P3 user journey as one atomic gate, in-process (TestClient) so it
needs no network binding. Where P2 proved the loop with one dataset and one
analyst-written query, P3 proves *repeated real-world use*: several datasets
joined in one run, an OS-level sandbox around generated code, an assistant that
proposes at every step without ever deciding, and a case that can be found,
replayed, templated and moved elsewhere.

    real question -> attach two datasets (CSV + Parquet) -> profile both
    -> assistant proposes the query (writes nothing)
    -> plan -> join run -> hard sandbox blocks an escape attempt
    -> assistant reads the result and drafts a finding (writes nothing)
    -> human accepts the finding -> raster chart -> validation closes the loop
    -> evidence graph covers both datasets -> workflow reports the loop closed
    -> assistant answers with citations -> EDA without a query
    -> history -> search -> template outlives the case
    -> dataset deletion blocked by its own evidence
    -> export -> import -> the join reproduces elsewhere

Emits verification/p3/REPORT.md. Exit code 0 only if every step passes.
"""

import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

# Environment variables that turn an assistant engine into a live LLM caller.
# The gate's own journey must be reproducible without a network, so these are
# scrubbed from this process before any assistant call (see main()). The test
# suite the gate spawns gets the same treatment, for the same reason.
_LLM_ENV_VARS = frozenset(
    {"DAH_LLM_API_KEY", "OPENAI_API_KEY", "DAH_LLM_BASE_URL", "DAH_LLM_MODEL"}
)

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "server"))

import app.db as db_module  # noqa: E402
from app.db import get_connection  # noqa: E402
from app.main import app, get_db  # noqa: E402

# Scrub as early as possible: app.main loaded server/.env at import (this is a
# script, not a pytest module), and every assistant engine reads these at call
# time. Removing them makes the journey deterministic - no live call per
# assistant step, so the gate is neither slow nor timing-dependent. The LLM
# paths stay covered by the suite (they test both engines explicitly).
for _var in _LLM_ENV_VARS:
    os.environ.pop(_var, None)

# Clean data on purpose: P2's gate used a null and a duplicate to make the
# validator work, so this gate's finding must reach a clean `supported` to prove
# the *join* validates, not that a messy one was tolerated.
ORDERS_CSV = (
    b"order_id,revenue,region\n"
    b"1,125.0,north\n"
    b"2,80.5,south\n"
    b"3,200.0,north\n"
    b"4,60.0,east\n"
    b"5,90.0,south\n"
)
TARGETS_CSV = (
    b"region,target\n"
    b"north,300.0\n"
    b"south,250.0\n"
    b"east,100.0\n"
)
# A join across two files of different formats: the first placeholder binds to
# the CSV, the second to the Parquet, positionally (P3-DATA-003).
JOIN_SQL = (
    "SELECT a.region, SUM(a.revenue) AS total, b.target AS target "
    "FROM read_csv_auto(?) a "
    "JOIN read_parquet(?) b ON a.region = b.region "
    "GROUP BY a.region, b.target "
    "ORDER BY a.region"
)
JOIN_ROWS = [
    ["east", 60.0, 100.0],
    ["north", 325.0, 300.0],
    ["south", 170.5, 250.0],
]
# A script that reaches outside its scratch directory. The kernel denies it
# under sandbox-exec; on a host without the OS sandbox the in-process guards
# deny it, so the answer is a 400 either way - never a persisted "escaped" run.
SANDBOX_PROBE = (
    "with open('/tmp/dah_gate_probe.txt', 'w') as probe:\n"
    "    probe.write('the sandbox did not stop this write')\n"
    "result = [{'escaped': True}]\n"
)


def log(message: str) -> None:
    print(f"[verify] {message}")


def build_parquet(work: Path) -> bytes:
    """Write the targets table as Parquet, so the join mixes formats."""
    import duckdb

    csv_path = work / "targets_src.csv"
    csv_path.write_bytes(TARGETS_CSV)
    parquet_path = work / "targets.parquet"
    duckdb.execute(
        f"COPY (SELECT * FROM read_csv_auto('{csv_path}')) "
        f"TO '{parquet_path}' (FORMAT PARQUET)"
    )
    return parquet_path.read_bytes()


def main() -> int:
    work = Path(tempfile.mkdtemp())
    db_module.DATA_DIR = work / "data"
    db_path = work / "p3.db"

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    steps: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        steps.append((name, ok, detail))
        log(f"{name}: {'PASS' if ok else 'FAIL'} ({detail})")

    with TestClient(app) as client:
        # 1. A real analytical question that needs two datasets to answer
        case = client.post(
            "/cases",
            json={
                "question": "Which regions missed their revenue target?",
                "dataset": "orders.csv",
            },
        )
        ok = case.status_code == 201
        case_id = case.json()["id"] if ok else ""
        record("Create case with a real question", ok, f"HTTP {case.status_code}")

        # 2-3. Two attached datasets, in different formats
        orders = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("orders.csv", ORDERS_CSV, "text/csv")},
        )
        ok = orders.status_code == 201
        orders_id = orders.json()["id"] if ok else ""
        record("Attach CSV dataset", ok, f"HTTP {orders.status_code}")

        targets = client.post(
            f"/cases/{case_id}/datasets",
            files={
                "file": (
                    "targets.parquet",
                    build_parquet(work),
                    "application/octet-stream",
                )
            },
        )
        ok = targets.status_code == 201
        targets_id = targets.json()["id"] if ok else ""
        record("Attach Parquet dataset", ok, f"HTTP {targets.status_code}")

        # 4. Profiling - the basis the assistant reads before proposing anything
        profiled = []
        for label, dataset_id in (("orders", orders_id), ("targets", targets_id)):
            response = client.post(
                f"/cases/{case_id}/datasets/{dataset_id}/profile"
            )
            body = response.json() if response.status_code == 201 else {}
            profiled.append(
                response.status_code == 201
                and body.get("rows") == (5 if label == "orders" else 3)
            )
        record(
            "Profile both datasets",
            all(profiled) and len(profiled) == 2,
            f"profiled={sum(profiled)} of {len(profiled)}",
        )

        # 5. The assistant proposes the computation and creates nothing
        proposal = client.post(
            f"/cases/{case_id}/datasets/{orders_id}/generate-code",
            json={"question": "total revenue per region", "kind": "sql"},
        )
        proposal_body = proposal.json() if proposal.status_code == 200 else {}
        columns_used = proposal_body.get("columns_used", [])
        no_runs_yet = client.get(f"/cases/{case_id}/runs").json() == []
        record(
            "Assistant proposes query, writes nothing",
            proposal.status_code == 200
            and bool(proposal_body.get("code"))
            and set(columns_used) <= {"order_id", "revenue", "region"}
            and no_runs_yet,
            f"source={proposal_body.get('source')}, "
            f"columns_used={columns_used}, runs_created={not no_runs_yet}",
        )

        # 6. A plan, so the workflow's plan stage closes
        plan = client.post(f"/cases/{case_id}/datasets/{orders_id}/plan")
        ok = plan.status_code == 201
        plan_body = plan.json().get("plan", {}) if ok else {}
        record(
            "Generate analysis plan",
            ok and bool(plan_body.get("sub_questions")) and bool(plan_body.get("hypotheses")),
            f"source={plan.json().get('source')}, "
            f"sub_questions={len(plan_body.get('sub_questions', []))}",
        )

        # 7. One SQL run joining both attached files
        join = client.post(
            f"/cases/{case_id}/runs",
            json={"sql": JOIN_SQL, "dataset_ids": [orders_id, targets_id]},
        )
        ok = join.status_code == 201
        join_body = join.json() if ok else {}
        join_id = join_body.get("id", "") if ok else ""
        record(
            "Join two datasets in one run",
            ok and join_body.get("rows") == JOIN_ROWS,
            f"row_count={join_body.get('row_count') if ok else '-'}, "
            f"datasets={len(join_body.get('dataset_ids') or [])}",
        )

        # 8. The hard sandbox: an escape attempt is refused, never persisted
        runs_before = len(client.get(f"/cases/{case_id}/runs").json())
        probe = client.post(
            f"/cases/{case_id}/datasets/{orders_id}/runs/python",
            json={"code": SANDBOX_PROBE},
        )
        runs_after = len(client.get(f"/cases/{case_id}/runs").json())
        record(
            "Hard sandbox blocks an escape attempt",
            probe.status_code == 400 and runs_after == runs_before,
            f"HTTP {probe.status_code}, runs before={runs_before} after={runs_after}",
        )

        # 9. The assistant reads what the join shows
        interpretation = client.post(
            f"/cases/{case_id}/runs/{join_id}/interpret"
        )
        interpretation_body = (
            interpretation.json() if interpretation.status_code == 201 else {}
        )
        record(
            "Assistant reads the result",
            interpretation.status_code == 201
            and bool(interpretation_body.get("summary"))
            and bool(interpretation_body.get("observations")),
            f"source={interpretation_body.get('source')}, "
            f"observations={len(interpretation_body.get('observations', []))}",
        )

        # 10. The assistant drafts the finding the result would support, and
        # still creates nothing - acceptance is a separate human action
        draft = client.post(f"/cases/{case_id}/runs/{join_id}/draft-finding")
        draft_body = draft.json() if draft.status_code == 200 else {}
        findings_empty = client.get(f"/cases/{case_id}/findings").json() == []
        record(
            "Assistant drafts a finding, writes nothing",
            draft.status_code == 200
            and bool(draft_body.get("statement"))
            and bool(draft_body.get("grounds"))
            and findings_empty,
            f"source={draft_body.get('source')}, "
            f"grounds={len(draft_body.get('grounds', []))}, findings={not findings_empty}",
        )

        # 11. The human accepts the draft through the only endpoint that writes
        finding = client.post(
            f"/cases/{case_id}/findings",
            json={
                "run_id": join_id,
                "statement": draft_body.get("statement", "north exceeded target"),
                "interpretation": draft_body.get("interpretation"),
                "caveat": draft_body.get("caveat"),
            },
        )
        ok = finding.status_code == 201
        finding_id = finding.json()["id"] if ok else ""
        record("Accept the draft as a finding", ok, f"HTTP {finding.status_code}")

        # 12. A raster chart rendered from the stored join result
        chart = client.post(
            f"/cases/{case_id}/runs/{join_id}/charts",
            json={
                "kind": "bar",
                "x": "region",
                "y": "total",
                "title": "Revenue against target by region",
                "format": "png",
            },
        )
        ok = chart.status_code == 201
        chart_id = chart.json()["id"] if ok else ""
        image = (
            client.get(f"/cases/{case_id}/charts/{chart_id}/image") if chart_id else None
        )
        record(
            "Render raster chart from run result",
            ok
            and image is not None
            and image.status_code == 200
            and image.content.startswith(b"\x89PNG\r\n\x1a\n"),
            f"HTTP {chart.status_code}, image bytes={len(image.content) if image else 0}",
        )

        # 13. Validation closes the trust loop on a join run
        validation = client.post(
            f"/cases/{case_id}/findings/{finding_id}/validate"
        )
        validation_body = validation.json() if validation.status_code == 200 else {}
        repro = [
            check
            for check in validation_body.get("checks", [])
            if check["name"] == "reproducibility"
        ]
        record(
            "Validate the finding closes the loop",
            validation.status_code == 200
            and validation_body.get("status") == "supported"
            and bool(repro)
            and repro[0]["passed"],
            f"status={validation_body.get('status') if validation.status_code == 200 else '-'}"
            ", reproducibility passed",
        )

        # 14. The evidence graph covers every artifact, and the claim reaches
        # both datasets the join bound
        graph = client.get(f"/cases/{case_id}/evidence-graph")
        graph_body = graph.json() if graph.status_code == 200 else {}
        counts = graph_body.get("counts", {})
        trace = next(iter(graph_body.get("traces", [])), {})
        trace_datasets = [
            hop["label"] for hop in trace.get("hops", []) if hop["kind"] == "dataset"
        ]
        record(
            "Evidence graph traces claim to both datasets",
            graph.status_code == 200
            and counts.get("datasets") == 2
            and counts.get("findings") == 1
            and trace.get("reaches_source") is True
            and len(trace_datasets) == 2
            and not graph_body.get("orphan_findings"),
            f"counts={counts}, reached={trace_datasets}",
        )

        # 15. The workflow derives its stage from the artifacts, not from a flag
        progress = client.get(f"/cases/{case_id}/progress")
        progress_body = progress.json() if progress.status_code == 200 else {}
        record(
            "Workflow reports the loop closed",
            progress.status_code == 200
            and progress_body.get("stage") == "validated"
            and progress_body.get("loop_closed") is True
            and progress_body.get("next_action") is None,
            f"stage={progress_body.get('stage')}, "
            f"loop_closed={progress_body.get('loop_closed')}",
        )

        # 16. The assistant answers about the case and cites its evidence
        chat = client.post(
            f"/cases/{case_id}/chat",
            json={"message": "How many datasets does this case have?"},
        )
        chat_body = chat.json() if chat.status_code == 201 else {}
        grounds = chat_body.get("grounds", [])
        dataset_names = {"orders.csv", "targets.parquet", orders_id, targets_id}
        cited = all(
            isinstance(ground, str) and ":" in ground for ground in grounds
        )
        cites_case = any(
            ground.split(":", 1)[1] in dataset_names for ground in grounds
        )
        replay = client.get(f"/cases/{case_id}/chat")
        record(
            "Assistant answers with citations",
            chat.status_code == 201
            and bool(chat_body.get("answer"))
            and cited
            and cites_case
            and replay.status_code == 200
            and len(replay.json()) == 1,
            f"source={chat_body.get('source')}, grounds={grounds}",
        )

        # 17. EDA answers a question without the analyst writing a query
        segment = client.post(
            f"/cases/{case_id}/datasets/{orders_id}/eda",
            json={"op": "segment", "by": "region", "measure": "revenue"},
        )
        segment_body = segment.json() if segment.status_code == 200 else {}
        record(
            "Explore data without a query",
            segment.status_code == 200
            and segment_body.get("row_count") == 3
            and not segment_body.get("truncated"),
            f"op=segment, row_count={segment_body.get('row_count') if segment.status_code == 200 else '-'}",
        )

        # 18. The case's own timeline, one event per artifact in the order it
        # happened, derived from each artifact's own timestamp
        history = client.get(f"/cases/{case_id}/history")
        history_body = history.json() if history.status_code == 200 else {}
        events = history_body.get("events", [])
        kinds = [event["kind"] for event in events]
        ordered = all(
            events[i]["timestamp"] <= events[i + 1]["timestamp"]
            for i in range(len(events) - 1)
        )
        record(
            "Replay the case history",
            history.status_code == 200
            and {
                "case_created",
                "dataset_attached",
                "run_executed",
                "finding_recorded",
                "chart_rendered",
            } <= set(kinds)
            and ordered
            and kinds[0] == "case_created",
            f"events={len(events)}, ordered={ordered}",
        )

        # 19. A case can be found again
        search = client.get("/cases", params={"q": "revenue target"})
        record(
            "Search finds the case",
            search.status_code == 200
            and any(item["id"] == case_id for item in search.json()),
            f"matches={len(search.json()) if search.status_code == 200 else '-'}",
        )

        # 20. A template outlives the case it came from
        template = client.post(
            f"/cases/{case_id}/template",
            json={"name": "Regional target gap analysis"},
        )
        ok = template.status_code == 201
        template_id = template.json()["id"] if ok else ""
        from_template = client.post(
            "/cases/from-template",
            json={
                "template_id": template_id,
                "question": "Which regions missed target in Q4?",
            },
        )
        listed = client.get("/templates").json()
        retired = client.delete(f"/templates/{template_id}")
        still_listed = any(item["id"] == template_id for item in client.get("/templates").json())
        record(
            "Template outlives its source case",
            ok
            and from_template.status_code == 201
            and any(item["id"] == template_id for item in listed)
            and retired.status_code == 204
            and not still_listed
            and client.get(f"/cases/{case_id}").status_code == 200,
            f"templated={ok}, from_template HTTP {from_template.status_code}, "
            f"retired HTTP {retired.status_code}",
        )

        # 21. Evidence protects its dataset: deletion is refused while a run
        # stands on it - for the primary and for a join's other member
        blocked_primary = client.delete(f"/cases/{case_id}/datasets/{orders_id}")
        blocked_member = client.delete(f"/cases/{case_id}/datasets/{targets_id}")
        record(
            "Dataset deletion blocked by its evidence",
            blocked_primary.status_code == 400
            and blocked_member.status_code == 400
            and len(client.get(f"/cases/{case_id}/datasets").json()) == 2,
            f"primary HTTP {blocked_primary.status_code}, "
            f"join member HTTP {blocked_member.status_code}",
        )

        # 22. The case exports as one self-contained package, join included
        export = client.get(f"/cases/{case_id}/export")
        package = export.json() if export.status_code == 200 else {}
        packaged_runs = package.get("runs", [])
        record(
            "Export package carries the join",
            export.status_code == 200
            and len(packaged_runs) == 1
            and len(packaged_runs[0].get("dataset_ids", [])) == 2,
            f"sections={sorted(k for k in package if k not in ('format', 'version', 'exported_at'))}",
        )

        # 23. The package stands on its own elsewhere and reproduces
        imported = client.post("/cases/import", json=package)
        ok = imported.status_code == 201
        imported_id = imported.json()["id"] if ok else ""
        restored = (
            {item["filename"]: item["id"] for item in client.get(f"/cases/{imported_id}/datasets").json()}
            if ok
            else {}
        )
        rerun = (
            client.post(
                f"/cases/{imported_id}/runs",
                json={
                    "sql": JOIN_SQL,
                    "dataset_ids": [restored["orders.csv"], restored["targets.parquet"]],
                },
            )
            if restored
            else None
        )
        record(
            "Import reproduces the join elsewhere",
            ok
            and rerun is not None
            and rerun.status_code == 201
            and rerun.json()["rows"] == JOIN_ROWS,
            f"rows={rerun.json()['rows'] if rerun and rerun.status_code == 201 else '-'}",
        )

    # 24. The test suite runs green. -rf names every failing test so a single
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
        "# P3 V1 Milestone Verification",
        "",
        f"Run: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Journey under test",
        "",
        "```",
        "real question -> attach CSV + Parquet -> profile both",
        "-> assistant proposes the query (writes nothing) -> plan",
        "-> join run -> hard sandbox refuses an escape attempt",
        "-> assistant reads the result and drafts a finding (writes nothing)",
        "-> human accepts the finding -> raster chart -> validation closes the loop",
        "-> evidence graph reaches both datasets -> workflow reports the loop closed",
        "-> assistant answers with citations -> EDA without a query",
        "-> history -> search -> template outlives the case",
        "-> dataset deletion blocked by its own evidence",
        "-> export -> import -> the join reproduces elsewhere",
        "```",
        "",
        "## Steps",
        "",
        "| Step | Result | Detail |",
        "|------|--------|--------|",
    ]
    lines += [f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |" for name, ok, detail in steps]
    lines += [
        "",
        "## Exit criteria (P3 gate: multi-dataset joins, hard sandbox, the four",
        "assistant slices, raster charts, validation, evidence, workflow, reuse)",
        "",
        "| Criterion | Status |",
        "|-----------|--------|",
    ]
    criteria = [
        ("Several datasets attach to one case in different formats", "Attach Parquet dataset"),
        ("One run can join them", "Join two datasets in one run"),
        ("Generated Python runs under an OS-level sandbox", "Hard sandbox blocks an escape attempt"),
        ("A question yields the computation that would answer it", "Assistant proposes query, writes nothing"),
        ("A result yields a plain-language reading", "Assistant reads the result"),
        ("A result yields the candidate finding it supports", "Assistant drafts a finding, writes nothing"),
        ("A case answers questions about itself with citations", "Assistant answers with citations"),
        ("Charts render as raster behind the same interface", "Render raster chart from run result"),
        ("A finding on a join run validates", "Validate the finding closes the loop"),
        ("Every claim traces to the data it stands on", "Evidence graph traces claim to both datasets"),
        ("The workflow stage is derived and the loop closes", "Workflow reports the loop closed"),
        ("EDA answers without a written query", "Explore data without a query"),
        ("A case can be found, replayed and templated", "Template outlives its source case"),
        ("Evidence protects the data it stands on", "Dataset deletion blocked by its evidence"),
        ("A case moves elsewhere and reproduces", "Import reproduces the join elsewhere"),
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
            "The V1 loop is complete for repeated real-world use: multi-dataset "
            "joins, a hard sandbox around generated code, an assistant that "
            "proposes at every step and decides at none, and a case that "
            "survives search, templating and a move to another harness. P3 is "
            "done and the project is ready for the production-candidate track "
            "(reliability, UX, performance, observability)."
            if decision == "PASS"
            else "Blocked: " + ", ".join(failures)
        ),
        "",
    ]
    out = REPO / "verification/p3/REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    log(f"report written to verification/p3/REPORT.md")
    log(f"DECISION: {decision}")
    return 0 if decision == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
