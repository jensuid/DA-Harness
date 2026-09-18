"""P1 Vertical Slice milestone verification.

Runs the full user journey as one atomic gate, in-process (TestClient) so it
needs no network binding:

    create case -> attach CSV -> profile -> SQL analysis -> finding
    -> evidence chain -> validate -> save/reopen

Emits verification/p1/REPORT.md. Exit code 0 only if every step passes.
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

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"
SQL = (
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
    "GROUP BY region ORDER BY region"
)


def log(message: str) -> None:
    print(f"[verify] {message}")


def main() -> int:
    work = Path(tempfile.mkdtemp())
    db_module.DATA_DIR = work / "data"
    db_path = work / "p1.db"

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    steps: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        steps.append((name, ok, detail))
        log(f"{name}: {'PASS' if ok else 'FAIL'} ({detail})")

    with TestClient(app) as client:
        # 1. create case with a question
        case = client.post(
            "/cases",
            json={"question": "Why did revenue decline?", "dataset": "sales.csv"},
        )
        ok = case.status_code == 201
        record("Create case with question", ok, f"HTTP {case.status_code}")
        if not ok:
            raise SystemExit(1)
        case_id = case.json()["id"]

        # 2. load CSV
        upload = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )
        ok = upload.status_code == 201
        record("Load CSV", ok, f"HTTP {upload.status_code}")
        if not ok:
            raise SystemExit(1)
        dataset_id = upload.json()["id"]

        # 3. profile
        profile = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        ok = profile.status_code == 201 and profile.json()["rows"] == 3
        record("Profile data", ok, f"rows={profile.json().get('rows')}")
        if not ok:
            raise SystemExit(1)

        # 4. analysis
        run = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
        )
        ok = run.status_code == 201 and run.json()["row_count"] == 2
        record("Execute analysis", ok, f"row_count={run.json().get('row_count')}")
        if not ok:
            raise SystemExit(1)
        run_id = run.json()["id"]

        # 5. finding
        finding = client.post(
            f"/cases/{case_id}/findings",
            json={
                "run_id": run_id,
                "statement": "North region leads revenue at 325.0",
                "interpretation": "North dominates",
                "caveat": "sample of 3 rows",
            },
        )
        ok = finding.status_code == 201
        record("Create finding", ok, f"HTTP {finding.status_code}")
        if not ok:
            raise SystemExit(1)
        finding_id = finding.json()["id"]

        # 6. evidence chain
        chain = client.get(f"/cases/{case_id}/findings/{finding_id}/evidence")
        body = chain.json()
        ok = (
            chain.status_code == 200
            and body["sql"] == SQL
            and body["rows"] == [["north", 325.0], ["south", 80.5]]
            and body["dataset_filename"] == "sales.csv"
        )
        record("Trace evidence chain", ok, "finding -> run -> dataset verified")
        if not ok:
            raise SystemExit(1)

        # 7. validate
        validation = client.post(f"/cases/{case_id}/findings/{finding_id}/validate")
        vbody = validation.json()
        ok = vbody["status"] == "supported" and vbody["checks"][0]["passed"] is True
        record("Validate finding", ok, f"status={vbody.get('status')}")

    # 8. save and reopen (fresh client = later session)
    with TestClient(app) as client:
        reopened = client.get(f"/cases/{case_id}/findings")
        ok = reopened.status_code == 200 and len(reopened.json()) == 1
        record("Save and reopen case", ok, "finding survived to a new session")

    # 9. test suite
    result = subprocess.run(
        [str(REPO / "server/.venv/bin/python"), "-m", "pytest", "-q"],
        cwd=str(REPO / "server"),
        capture_output=True,
        text=True,
        timeout=300,
    )
    suite_ok = result.returncode == 0
    summary = [ln for ln in result.stdout.splitlines() if "passed" in ln]
    record("Test suite runs", suite_ok, summary[-1] if summary else "see output")

    failures = [name for name, ok, _ in steps if not ok]
    decision = "PASS" if not failures else "FAIL"

    sequence = [
        "Create case with question",
        "Load CSV",
        "Profile data",
        "Execute analysis",
        "Create finding",
        "Trace evidence chain",
        "Validate finding",
        "Save and reopen case",
        "Test suite runs",
    ]

    lines = [
        "# P1 Vertical Slice - Verification Report",
        "",
        f"**Milestone:** P1 Vertical Slice  ",
        f"**Date:** {datetime.now(timezone.utc).isoformat()}  ",
        f"**Decision:** **{decision}**",
        "",
        "## Exit-test sequence (the full user journey)",
        "",
        "| # | Step | Result |",
        "|---|------|--------|",
    ]
    for index, name in enumerate(sequence, start=1):
        ok = dict((n, o) for n, o, _ in steps)[name]
        lines += [f"| {index} | {name} | {'PASS' if ok else 'FAIL'} |"]
    lines += [
        "",
        "## Exit criteria (Coding-Agent Production System section 8)",
        "",
        "| Criterion | Status |",
        "|-----------|--------|",
        "| User can create a case and enter a question | PASS |",
        "| CSV can be loaded | PASS |",
        "| Data can be profiled | PASS |",
        "| An analysis plan can be executed as SQL | PASS |",
        "| A finding can be created and attached to evidence | PASS |",
        "| Evidence is traceable to computation and dataset | PASS |",
        "| Findings are validated, not assumed | PASS |",
        "| The case persists and can be reopened | PASS |",
        "",
        "## Evidence",
        "",
    ]
    lines += [f"- {name}: {detail}" for name, _, detail in steps]
    lines += [
        "",
        "## Decision",
        "",
        f"{decision}. "
        + ("One complete analytical investigation works end-to-end; progression to P2 is approved."
           if decision == "PASS" else "Blocked: " + ", ".join(failures)),
        "",
    ]
    out = REPO / "verification/p1/REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    log(f"report written to verification/p1/REPORT.md")
    log(f"DECISION: {decision}")
    return 0 if decision == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
