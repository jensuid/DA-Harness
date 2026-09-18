from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from pydantic import BaseModel

import json

from app.analysis import profile_csv, run_query
import app.db as db_module
from app.db import get_connection
from app.models import (
    Case,
    CaseCreate,
    Dataset,
    Profile,
    Run,
    RunCreate,
    RunSummary,
    VALIDATION_STATUSES,
    EvidenceChain,
    Finding,
    FindingCreate,
    ValidationCheck,
    ValidationResult,
)

app = FastAPI(
    title="DAH Harness Core",
    description="Deterministic core of the Data Analysis Harness.",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. Confirms the core process is up and answering."""
    return {"status": "ok"}


def get_db() -> Iterator[object]:
    with get_connection() as connection:
        yield connection


@app.post("/cases", status_code=201, response_model=Case)
async def create_case(payload: CaseCreate, db=Depends(get_db)) -> Case:
    """Create and persist a new Analysis Case."""
    now = datetime.now(timezone.utc)
    case = Case(
        id=str(uuid4()),
        question=payload.question,
        dataset=payload.dataset,
        created_at=now,
        updated_at=now,
    )
    db.execute(
        "INSERT INTO cases (id, question, dataset, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            case.id,
            case.question,
            case.dataset,
            case.created_at.isoformat(),
            case.updated_at.isoformat(),
        ),
    )
    return case


@app.get("/cases/{case_id}", response_model=Case)
async def get_case(case_id: str, db=Depends(get_db)) -> Case:
    """Reopen a persisted Analysis Case."""
    row = db.execute(
        "SELECT id, question, dataset, created_at, updated_at FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="case not found")
    return Case(
        id=row["id"],
        question=row["question"],
        dataset=row["dataset"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@app.get("/cases", response_model=list[Case])
async def list_cases(db=Depends(get_db)) -> list[Case]:
    """List all persisted Analysis Cases."""
    rows = db.execute(
        "SELECT id, question, dataset, created_at, updated_at FROM cases "
        "ORDER BY created_at DESC"
    ).fetchall()
    return [
        Case(
            id=row["id"],
            question=row["question"],
            dataset=row["dataset"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


SUPPORTED_FORMATS = (".csv", ".parquet", ".xlsx")


def _format_for(filename: str) -> str:
    """Dataset format is the lowercased extension, without the dot."""
    return Path(filename).suffix.lower().lstrip(".")


def _require_case(db, case_id: str) -> None:
    row = db.execute("SELECT 1 FROM cases WHERE id = ?", (case_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="case not found")


@app.post(
    "/cases/{case_id}/datasets",
    status_code=201,
    response_model=Dataset,
)
async def attach_dataset(
    case_id: str,
    file: UploadFile,
    db=Depends(get_db),
) -> Dataset:
    """Attach a CSV dataset to an Analysis Case.

    The file is written to disk by the core, never by the frontend (DEC-001).
    """
    _require_case(db, case_id)

    if not file.filename or not file.filename.lower().endswith(SUPPORTED_FORMATS):
        raise HTTPException(
            status_code=400, detail="only .csv, .parquet, and .xlsx files are supported"
        )

    content = await file.read()
    if not content.strip():
        raise HTTPException(status_code=400, detail="uploaded file is empty")

    dataset_id = str(uuid4())
    case_dir = db_module.DATA_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    stored_path = case_dir / f"{dataset_id}.{_format_for(file.filename)}"
    stored_path.write_bytes(content)

    dataset = Dataset(
        id=dataset_id,
        case_id=case_id,
        filename=file.filename,
        stored_path=str(stored_path),
        format=_format_for(file.filename),
        created_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT INTO datasets (id, case_id, filename, stored_path, format, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            dataset.id,
            dataset.case_id,
            dataset.filename,
            dataset.stored_path,
            dataset.format,
            dataset.created_at.isoformat(),
        ),
    )
    return dataset


@app.get("/cases/{case_id}/datasets", response_model=list[Dataset])
async def list_datasets(case_id: str, db=Depends(get_db)) -> list[Dataset]:
    """List datasets attached to an Analysis Case."""
    _require_case(db, case_id)
    rows = db.execute(
        "SELECT id, case_id, filename, stored_path, format, created_at FROM datasets "
        "WHERE case_id = ? ORDER BY created_at DESC",
        (case_id,),
    ).fetchall()
    return [
        Dataset(
            id=row["id"],
            case_id=row["case_id"],
            filename=row["filename"],
            stored_path=row["stored_path"],
            format=row["format"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def _require_dataset(db, case_id: str, dataset_id: str) -> Dataset:
    row = db.execute(
        "SELECT id, case_id, filename, stored_path, format, created_at FROM datasets "
        "WHERE id = ? AND case_id = ?",
        (dataset_id, case_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    return Dataset(
        id=row["id"],
        case_id=row["case_id"],
        filename=row["filename"],
        stored_path=row["stored_path"],
        format=row["format"],
        created_at=row["created_at"],
    )


@app.post(
    "/cases/{case_id}/datasets/{dataset_id}/profile",
    status_code=201,
    response_model=Profile,
)
async def profile_dataset(
    case_id: str,
    dataset_id: str,
    db=Depends(get_db),
) -> Profile:
    """Profile an attached dataset with DuckDB and persist the result.

    The profile is deterministic - no LLM involved (DEC-001).
    """
    dataset = _require_dataset(db, case_id, dataset_id)

    raw = profile_csv(dataset.stored_path)
    profile = Profile(
        dataset_id=dataset_id,
        rows=raw["rows"],
        columns=raw["columns"],
        stats=raw["stats"],
        duplicate_rows=raw["duplicate_rows"],
        profiled_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT OR REPLACE INTO profiles "
        "(dataset_id, rows, columns_json, stats_json, duplicate_rows, profiled_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            profile.dataset_id,
            profile.rows,
            json.dumps(profile.columns),
            json.dumps(profile.stats),
            profile.duplicate_rows,
            profile.profiled_at.isoformat(),
        ),
    )
    return profile


@app.get(
    "/cases/{case_id}/datasets/{dataset_id}/profile",
    response_model=Profile,
)
async def get_profile(
    case_id: str,
    dataset_id: str,
    db=Depends(get_db),
) -> Profile:
    """Retrieve the stored profile for an attached dataset."""
    _require_dataset(db, case_id, dataset_id)
    row = db.execute(
        "SELECT dataset_id, rows, columns_json, stats_json, duplicate_rows, profiled_at "
        "FROM profiles WHERE dataset_id = ?",
        (dataset_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="profile not found")
    return Profile(
        dataset_id=row["dataset_id"],
        rows=row["rows"],
        columns=json.loads(row["columns_json"]),
        stats=json.loads(row["stats_json"]),
        duplicate_rows=row["duplicate_rows"],
        profiled_at=row["profiled_at"],
    )


@app.post(
    "/cases/{case_id}/datasets/{dataset_id}/runs",
    status_code=201,
    response_model=Run,
)
async def create_run(
    case_id: str,
    dataset_id: str,
    payload: RunCreate,
    db=Depends(get_db),
) -> Run:
    """Run user SQL against an attached dataset and persist the result.

    The query is a placeholder-free string bound to the dataset path by the
    engine; the read-only check in run_query gates what may execute. Results
    are capped (default 1000 rows) and marked truncated when they exceed it.
    """
    dataset = _require_dataset(db, case_id, dataset_id)

    try:
        result = run_query(dataset.stored_path, payload.sql)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"query failed: {error}")

    run = Run(
        id=str(uuid4()),
        case_id=case_id,
        dataset_id=dataset_id,
        sql=payload.sql,
        columns=result["columns"],
        rows=result["rows"],
        row_count=result["row_count"],
        truncated=result["truncated"],
        executed_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT INTO runs (id, case_id, dataset_id, sql, columns_json, rows_json, "
        "row_count, truncated, executed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run.id,
            run.case_id,
            run.dataset_id,
            run.sql,
            json.dumps(run.columns),
            json.dumps(run.rows),
            run.row_count,
            1 if run.truncated else 0,
            run.executed_at.isoformat(),
        ),
    )
    return run


@app.get("/cases/{case_id}/runs", response_model=list[RunSummary])
async def list_runs(case_id: str, db=Depends(get_db)) -> list[RunSummary]:
    """List analysis runs for a case, without the heavy result rows."""
    _require_case(db, case_id)
    rows = db.execute(
        "SELECT id, case_id, dataset_id, sql, row_count, truncated, executed_at "
        "FROM runs WHERE case_id = ? ORDER BY executed_at DESC",
        (case_id,),
    ).fetchall()
    return [
        RunSummary(
            id=row["id"],
            case_id=row["case_id"],
            dataset_id=row["dataset_id"],
            sql=row["sql"],
            row_count=row["row_count"],
            truncated=bool(row["truncated"]),
            executed_at=row["executed_at"],
        )
        for row in rows
    ]


@app.get("/cases/{case_id}/runs/{run_id}", response_model=Run)
async def get_run(case_id: str, run_id: str, db=Depends(get_db)) -> Run:
    """Reopen a persisted analysis run, including its result rows."""
    _require_case(db, case_id)
    row = db.execute(
        "SELECT id, case_id, dataset_id, sql, columns_json, rows_json, row_count, "
        "truncated, executed_at FROM runs WHERE id = ? AND case_id = ?",
        (run_id, case_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    return Run(
        id=row["id"],
        case_id=row["case_id"],
        dataset_id=row["dataset_id"],
        sql=row["sql"],
        columns=json.loads(row["columns_json"]),
        rows=json.loads(row["rows_json"]),
        row_count=row["row_count"],
        truncated=bool(row["truncated"]),
        executed_at=row["executed_at"],
    )


def _require_run(db, case_id: str, run_id: str) -> None:
    row = db.execute(
        "SELECT 1 FROM runs WHERE id = ? AND case_id = ?", (run_id, case_id)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")


@app.post(
    "/cases/{case_id}/findings",
    status_code=201,
    response_model=Finding,
)
async def create_finding(
    case_id: str,
    payload: FindingCreate,
    db=Depends(get_db),
) -> Finding:
    """Record a finding against a specific analysis run.

    The finding starts not_evaluated: support is established by validation
    (P1-VALID-005), never assumed at creation.
    """
    _require_case(db, case_id)
    _require_run(db, case_id, payload.run_id)

    finding = Finding(
        id=str(uuid4()),
        case_id=case_id,
        run_id=payload.run_id,
        statement=payload.statement,
        interpretation=payload.interpretation,
        caveat=payload.caveat,
        validation_status="not_evaluated",
        created_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT INTO findings (id, case_id, run_id, statement, interpretation, "
        "caveat, validation_status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            finding.id,
            finding.case_id,
            finding.run_id,
            finding.statement,
            finding.interpretation,
            finding.caveat,
            finding.validation_status,
            finding.created_at.isoformat(),
        ),
    )
    return finding


@app.get("/cases/{case_id}/findings", response_model=list[Finding])
async def list_findings(case_id: str, db=Depends(get_db)) -> list[Finding]:
    """List findings recorded against a case."""
    _require_case(db, case_id)
    rows = db.execute(
        "SELECT id, case_id, run_id, statement, interpretation, caveat, "
        "validation_status, created_at FROM findings WHERE case_id = ? "
        "ORDER BY created_at DESC",
        (case_id,),
    ).fetchall()
    return [
        Finding(
            id=row["id"],
            case_id=row["case_id"],
            run_id=row["run_id"],
            statement=row["statement"],
            interpretation=row["interpretation"],
            caveat=row["caveat"],
            validation_status=row["validation_status"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@app.get("/cases/{case_id}/findings/{finding_id}", response_model=Finding)
async def get_finding(case_id: str, finding_id: str, db=Depends(get_db)) -> Finding:
    """Reopen a single finding."""
    _require_case(db, case_id)
    row = db.execute(
        "SELECT id, case_id, run_id, statement, interpretation, caveat, "
        "validation_status, created_at FROM findings WHERE id = ? AND case_id = ?",
        (finding_id, case_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="finding not found")
    return Finding(
        id=row["id"],
        case_id=row["case_id"],
        run_id=row["run_id"],
        statement=row["statement"],
        interpretation=row["interpretation"],
        caveat=row["caveat"],
        validation_status=row["validation_status"],
        created_at=row["created_at"],
    )


@app.get(
    "/cases/{case_id}/findings/{finding_id}/evidence",
    response_model=EvidenceChain,
)
async def get_evidence_chain(
    case_id: str,
    finding_id: str,
    db=Depends(get_db),
) -> EvidenceChain:
    """Trace a finding back to its computation and dataset.

    Walks finding -> run -> dataset so a reviewer can answer
    "where did this conclusion come from?" (Master Spec section 10.4).
    """
    finding = await get_finding(case_id, finding_id, db)

    run_row = db.execute(
        "SELECT id, case_id, dataset_id, sql, columns_json, rows_json, row_count, "
        "truncated, executed_at FROM runs WHERE id = ?",
        (finding.run_id,),
    ).fetchone()
    if run_row is None:
        raise HTTPException(status_code=500, detail="referenced run is missing")

    dataset_row = db.execute(
        "SELECT filename FROM datasets WHERE id = ?", (run_row["dataset_id"],)
    ).fetchone()
    if dataset_row is None:
        raise HTTPException(status_code=500, detail="referenced dataset is missing")

    return EvidenceChain(
        finding=finding,
        sql=run_row["sql"],
        columns=json.loads(run_row["columns_json"]),
        rows=json.loads(run_row["rows_json"]),
        row_count=run_row["row_count"],
        truncated=bool(run_row["truncated"]),
        dataset_filename=dataset_row["filename"],
    )


@app.patch(
    "/cases/{case_id}/findings/{finding_id}/validation",
    response_model=Finding,
)
async def set_validation_status(
    case_id: str,
    finding_id: str,
    status: str,
    db=Depends(get_db),
) -> Finding:
    """Set a finding's validation status by explicit decision only."""
    if status not in VALIDATION_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of {', '.join(VALIDATION_STATUSES)}",
        )
    finding = await get_finding(case_id, finding_id, db)
    db.execute(
        "UPDATE findings SET validation_status = ? WHERE id = ?",
        (status, finding.id),
    )
    finding.validation_status = status
    return finding


@app.post(
    "/cases/{case_id}/findings/{finding_id}/validate",
    status_code=200,
    response_model=ValidationResult,
)
async def validate_finding(
    case_id: str,
    finding_id: str,
    db=Depends(get_db),
) -> ValidationResult:
    """Reproduce a finding's computation and check its support.

    The trust loop closes here: the stored SQL is rerun against the stored
    dataset and compared to the persisted result. A finding is `supported`
    only if the numbers still reproduce (Master Spec section 10.5).
    """
    finding = await get_finding(case_id, finding_id, db)

    run_row = db.execute(
        "SELECT id, case_id, dataset_id, sql, columns_json, rows_json, "
        "row_count, truncated FROM runs WHERE id = ?",
        (finding.run_id,),
    ).fetchone()
    if run_row is None:
        raise HTTPException(status_code=500, detail="referenced run is missing")

    dataset_row = db.execute(
        "SELECT id, stored_path FROM datasets WHERE id = ?",
        (run_row["dataset_id"],),
    ).fetchone()
    if dataset_row is None:
        raise HTTPException(status_code=500, detail="referenced dataset is missing")

    checks: list[ValidationCheck] = []

    # 1. Reproducibility: rerun the stored SQL and compare to the stored rows.
    try:
        rerun = run_query(dataset_row["stored_path"], run_row["sql"])
        reproduced = rerun["rows"] == json.loads(run_row["rows_json"])
    except ValueError as error:
        checks.append(
            ValidationCheck(
                name="reproducibility", passed=False, detail=f"query rejected: {error}"
            )
        )
        reproduced = False
    else:
        checks.append(
            ValidationCheck(
                name="reproducibility",
                passed=reproduced,
                detail="rerun matches stored result" if reproduced else "rerun differs",
            )
        )

    # 2. Denominator: a null-free basis for any aggregate claim.
    profile_row = db.execute(
        "SELECT stats_json FROM profiles WHERE dataset_id = ?",
        (dataset_row["id"],),
    ).fetchone()
    if profile_row is None:
        checks.append(
            ValidationCheck(
                name="missing_data", passed=True,
                detail="no profile recorded - skipped",
            )
        )
        null_total = 0
    else:
        stats = json.loads(profile_row["stats_json"])
        null_total = sum(c.get("null_count", 0) for c in stats.values())
        null_free = null_total == 0
        checks.append(
            ValidationCheck(
                name="missing_data",
                passed=null_free,
                detail=f"{null_total} null value(s) across profiled columns",
            )
        )

    # 3. Evidence integrity: the run still belongs to this case's dataset.
    owned = run_row["case_id"] == case_id
    checks.append(
        ValidationCheck(
            name="evidence_integrity",
            passed=owned,
            detail="run belongs to this case" if owned else "run is foreign to this case",
        )
    )

    passed_all = reproduced and owned and null_total == 0
    status = "supported" if passed_all else "insufficient_evidence"
    if reproduced and not passed_all:
        status = "partially_supported"

    db.execute(
        "UPDATE findings SET validation_status = ? WHERE id = ?",
        (status, finding.id),
    )

    return ValidationResult(
        finding_id=finding.id,
        run_id=finding.run_id,
        status=status,
        checks=checks,
        validated_at=datetime.now(timezone.utc),
    )
