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

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="only .csv files are supported")

    content = await file.read()
    if not content.strip():
        raise HTTPException(status_code=400, detail="uploaded file is empty")

    dataset_id = str(uuid4())
    case_dir = db_module.DATA_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    stored_path = case_dir / f"{dataset_id}.csv"
    stored_path.write_bytes(content)

    dataset = Dataset(
        id=dataset_id,
        case_id=case_id,
        filename=file.filename,
        stored_path=str(stored_path),
        created_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT INTO datasets (id, case_id, filename, stored_path, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            dataset.id,
            dataset.case_id,
            dataset.filename,
            dataset.stored_path,
            dataset.created_at.isoformat(),
        ),
    )
    return dataset


@app.get("/cases/{case_id}/datasets", response_model=list[Dataset])
async def list_datasets(case_id: str, db=Depends(get_db)) -> list[Dataset]:
    """List datasets attached to an Analysis Case."""
    _require_case(db, case_id)
    rows = db.execute(
        "SELECT id, case_id, filename, stored_path, created_at FROM datasets "
        "WHERE case_id = ? ORDER BY created_at DESC",
        (case_id,),
    ).fetchall()
    return [
        Dataset(
            id=row["id"],
            case_id=row["case_id"],
            filename=row["filename"],
            stored_path=row["stored_path"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def _require_dataset(db, case_id: str, dataset_id: str) -> Dataset:
    row = db.execute(
        "SELECT id, case_id, filename, stored_path, created_at FROM datasets "
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
        profiled_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT OR REPLACE INTO profiles "
        "(dataset_id, rows, columns_json, stats_json, profiled_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            profile.dataset_id,
            profile.rows,
            json.dumps(profile.columns),
            json.dumps(profile.stats),
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
        "SELECT dataset_id, rows, columns_json, stats_json, profiled_at "
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
