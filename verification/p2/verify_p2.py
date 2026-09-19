"""P2 MVP milestone verification.

Runs the full P2 user journey as one atomic gate, in-process (TestClient) so it
needs no network binding:

    real question -> load data -> profile -> SQL run -> Python run
    -> chart -> AI plan -> finding -> validation
    -> case management (rename, duplicate, delete)
    -> export -> import round trip -> reproducibility

Emits verification/p2/REPORT.md. Exit code 0 only if every step passes.
"""

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "server"))

import app.db as db_module  # noqa: E402
from app.db import get_connection  # noqa: E402
from app.main import app, get_db  # noqa: E402

# Deliberately messier than P1's: a null, a duplicate row, and a categorical
# split, so the P2 capabilities have something real to work on.
CSV = (
    b"order_id,revenue,region\n"
    b"1,125.0,north\n"
    b"2,80.5,south\n"
    b"3,200.0,north\n"
    b"4,,south\n"
    b"2,80.5,south\n"
)
SQL = (
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
    "GROUP BY region ORDER BY region"
)
PYTHON = (
    "totals = {}\n"
    "for row in dataset.rows:\n"
    "    totals[row['region']] = totals.get(row['region'], 0) + (row['revenue'] or 0)\n"
    "result = [{'region': k, 'total': v} for k, v in sorted(totals.items())]\n"
)


def log(message: str) -> None:
    print(f"[verify] {message}")


def main() -> int:
    work = Path(tempfile.mkdtemp())
    db_module.DATA_DIR = work / "data"
    db_path = work / "p2.db"

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    steps: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        steps.append((name, ok, detail))
        log(f"{name}: {'PASS' if ok else 'FAIL'} ({detail})")

    with TestClient(app) as client:
        # 1. A real analytical question
        case = client.post(
            "/cases",
            json={"question": "Why did revenue decline in the south?", "dataset": "sales.csv"},
        )
        ok = case.status_code == 201
        case_id = case.json()["id"] if ok else ""
        record("Create case with a real question", ok, f"HTTP {case.status_code}")

        # 2. Load data
        dataset = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )
        ok = dataset.status_code == 201
        dataset_id = dataset.json()["id"] if ok else ""
        record("Load CSV", ok, f"HTTP {dataset.status_code}")

        # 3. Profile - the deterministic basis for everything downstream
        profile = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        body = profile.json() if profile.status_code == 201 else {}
        record(
            "Profile data",
            profile.status_code == 201 and body.get("rows") == 5,
            f"rows={body.get('rows')}, duplicate_rows={body.get('duplicate_rows')}",
        )

        # 4. SQL analysis
        run = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
        )
        ok = run.status_code == 201
        run_id = run.json()["id"] if ok else ""
        record(
            "Execute SQL analysis",
            ok and run.json().get("row_count") == 2,
            f"row_count={run.json().get('row_count') if ok else '-'}",
        )

        # 5. Python analysis - the other engine, same persisted shape
        py_run = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs/python",
            json={"code": PYTHON},
        )
        ok = py_run.status_code == 201
        record(
            "Execute Python analysis",
            ok and py_run.json().get("columns") == ["region", "total"],
            f"columns={py_run.json().get('columns') if ok else '-'}",
        )

        # 6. Visualize - a chart artifact rendered from the stored result
        chart = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "region", "y": "total", "title": "Revenue by region"},
        )
        ok = chart.status_code == 201
        chart_id = chart.json()["id"] if ok else ""
        record("Create chart from run result", ok, f"HTTP {chart.status_code}")

        # 7. AI plan - structured output from question + profile
        plan = client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")
        ok = plan.status_code == 201
        plan_body = plan.json().get("plan", {}) if ok else {}
        record(
            "Generate AI plan",
            ok and bool(plan_body.get("hypotheses")) and bool(plan_body.get("sub_questions")),
            f"source={plan.json().get('source')}, "
            f"hypotheses={len(plan_body.get('hypotheses', []))}",
        )

        # 8. Finding attached to evidence
        finding = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "north leads revenue"},
        )
        ok = finding.status_code == 201
        finding_id = finding.json()["id"] if ok else ""
        record("Create finding", ok, f"HTTP {finding.status_code}")

        # 9. Evidence chain
        chain = client.get(f"/cases/{case_id}/findings/{finding_id}/evidence")
        ok = chain.status_code == 200
        chain_body = chain.json() if ok else {}
        record(
            "Trace evidence chain",
            ok and chain_body.get("dataset_filename") == "sales.csv",
            "finding -> run -> dataset verified"
            if ok and chain_body.get("sql")
            else "link missing",
        )

        # 10. Validation - the finding must reproduce
        validation = client.post(
            f"/cases/{case_id}/findings/{finding_id}/validate"
        )
        record(
            "Validate finding",
            # This dataset deliberately contains a null, so an honest validator
            # reports partially_supported - the missing_data check actually
            # fired rather than rubber-stamping the finding.
            validation.status_code == 200
            and validation.json().get("status") == "partially_supported"
            and any(
                check["name"] == "missing_data" and not check["passed"]
                for check in validation.json().get("checks", [])
            ),
            f"status={validation.json().get('status') if validation.status_code == 200 else '-'}"
            ", missing_data check fired",
        )

        # 11. Case management
        renamed = client.patch(
            f"/cases/{case_id}",
            json={"question": "Why did Q3 revenue decline in the south?"},
        )
        record(
            "Rename case",
            renamed.status_code == 200
            and renamed.json()["question"].startswith("Why did Q3"),
            f"HTTP {renamed.status_code}",
        )

        duplicate = client.post(f"/cases/{case_id}/duplicate")
        duplicate_id = duplicate.json().get("id") if duplicate.status_code == 201 else ""
        copy_runs = (
            client.get(f"/cases/{duplicate_id}/runs").json()
            if duplicate_id
            else []
        )
        record(
            "Duplicate case",
            duplicate.status_code == 201
            and len(copy_runs) == 2
            and all(r["id"] != run_id for r in copy_runs),
            f"copy has {len(copy_runs)} run(s), all with fresh IDs",
        )

        delete = client.delete(f"/cases/{duplicate_id}")
        record(
            "Delete case",
            delete.status_code == 204
            and client.get(f"/cases/{duplicate_id}").status_code == 404,
            f"HTTP {delete.status_code}, then 404",
        )

        # 12. Export - a self-contained package
        export = client.get(f"/cases/{case_id}/export")
        package = export.json() if export.status_code == 200 else {}
        record(
            "Export case package",
            export.status_code == 200 and len(package.get("charts", [])) == 1,
            f"sections={sorted(k for k in package if k not in ('format', 'version', 'exported_at'))}",
        )

        # 13. Import - the package stands on its own elsewhere
        imported = client.post("/cases/import", json=package)
        ok = imported.status_code == 201
        imported_id = imported.json()["id"] if ok else ""
        restored_runs = (
            client.get(f"/cases/{imported_id}/runs").json() if imported_id else []
        )
        record(
            "Import package round trip",
            ok and len(restored_runs) == 2 and restored_runs[0]["id"] not in (run_id,),
            f"{len(restored_runs)} run(s) restored with fresh IDs",
        )

        # 14. Reproducibility - the restored data answers the same question
        restored_dataset = (
            client.get(f"/cases/{imported_id}/datasets").json() if imported_id else []
        )
        rerun = (
            client.post(
                f"/cases/{imported_id}/datasets/{restored_dataset[0]['id']}/runs",
                json={"sql": SQL},
            )
            if restored_dataset
            else None
        )
        record(
            "Reproduce analysis on restored data",
            rerun is not None
            and rerun.status_code == 201
            and rerun.json()["rows"] == [["north", 325.0], ["south", 161.0]],
            f"rows={rerun.json()['rows'] if rerun and rerun.status_code == 201 else '-'}",
        )

        # 15. Chart from the restored case is served
        restored_charts = [
            chart
            for run_summary in restored_runs
            for chart in client.get(
                f"/cases/{imported_id}/runs/{run_summary['id']}/charts"
            ).json()
        ]
        image = (
            client.get(
                f"/cases/{imported_id}/charts/{restored_charts[0]['id']}/image"
            )
            if restored_charts
            else None
        )
        record(
            "Serve restored chart artifact",
            image is not None
            and image.status_code == 200
            and image.content.startswith(b"<svg"),
            f"HTTP {image.status_code if image else '-'}",
        )

    # 16. The test suite runs green
    tests = subprocess.run(
        [str(REPO / "server/.venv/bin/python"), "-m", "pytest", "-q"],
        cwd=str(REPO / "server"),
        capture_output=True,
        text=True,
    )
    suite_ok = tests.returncode == 0
    summary = [line for line in tests.stdout.splitlines() if "passed" in line]
    record(
        "Test suite runs",
        suite_ok,
        summary[-1].strip() if summary else f"exit {tests.returncode}",
    )

    failures = [name for name, ok, _ in steps if not ok]
    decision = "PASS" if not failures else "FAIL"

    lines = [
        "# P2 MVP Milestone Verification",
        "",
        f"Run: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Journey under test",
        "",
        "```",
        "real question -> load data -> profile -> SQL -> Python -> chart -> AI plan",
        "-> finding -> evidence -> validation -> rename/duplicate/delete",
        "-> export -> import -> reproduce -> serve restored artifact",
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
        "## Exit criteria (P2 gate: real problem, data, SQL/Python, visualization,",
        "AI, evidence, validation, export, reproducibility)",
        "",
        "| Criterion | Status |",
        "|-----------|--------|",
    ]
    criteria = [
        ("A real analytical problem can be framed as a case", "Create case with a real question"),
        ("Supported data loads and profiles", "Profile data"),
        ("Both engines analyse it (SQL and Python)", "Execute Python analysis"),
        ("Analysis results are visualized and persisted", "Create chart from run result"),
        ("AI produces a structured plan", "Generate AI plan"),
        ("Findings carry a traceable evidence chain", "Trace evidence chain"),
        ("Findings are validated, not assumed", "Validate finding"),
        ("Cases can be renamed, duplicated, and deleted", "Delete case"),
        ("A case exports as a self-contained package", "Export case package"),
        ("The package imports and reproduces elsewhere", "Reproduce analysis on restored data"),
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
            "The MVP loop is complete and reproducible end to end; P2 is done and "
            "the project is ready for the V1 hardening track (hard sandbox, "
            "raster charts, LLM key configuration, desktop shell)."
            if decision == "PASS"
            else "Blocked: " + ", ".join(failures)
        ),
        "",
    ]
    out = REPO / "verification/p2/REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    log(f"report written to verification/p2/REPORT.md")
    log(f"DECISION: {decision}")
    return 0 if decision == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
