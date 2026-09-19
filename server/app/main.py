import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4


from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

import json

from app.analysis import profile_csv, run_query, run_query_multi
from app.python_exec import run_python
from app.charts import render_chart, CHART_KINDS, CHART_FORMATS
from app.charts import DEFAULT_WIDTH, DEFAULT_HEIGHT
from app.planner import create_plan as create_plan_module, validate_plan
from app.exporter import export_case, import_package, PACKAGE_FORMAT, PACKAGE_VERSION
import app.db as db_module
from app.db import get_connection
from app.models import (
    Case,
    CaseCreate,
    CaseUpdate,
    Dataset,
    Profile,
    Run,
    MultiRunCreate,
    RunCreate,
    PythonRunCreate,
    RunSummary,
    RUN_KINDS,
    VALIDATION_STATUSES,
    EvidenceChain,
    Finding,
    FindingCreate,
    ValidationCheck,
    ValidationResult,
    Chart,
    ChartSummary,
    ChartCreate,
    Plan,
    PlanSummary,
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


@app.patch("/cases/{case_id}", response_model=Case)
async def update_case(
    case_id: str,
    payload: CaseUpdate,
    db=Depends(get_db),
) -> Case:
    """Rename a case: its question and/or dataset label.

    Omitted fields are left as they are. `updated_at` moves so a rename is
    visible as case activity.
    """
    row = db.execute(
        "SELECT id, question, dataset, created_at, updated_at FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="case not found")

    question = payload.question if payload.question is not None else row["question"]
    dataset = payload.dataset if payload.dataset is not None else row["dataset"]
    now = datetime.now(timezone.utc)
    db.execute(
        "UPDATE cases SET question = ?, dataset = ?, updated_at = ? WHERE id = ?",
        (question, dataset, now.isoformat(), case_id),
    )
    return Case(
        id=row["id"],
        question=question,
        dataset=dataset,
        created_at=row["created_at"],
        updated_at=now,
    )


@app.post(
    "/cases/{case_id}/duplicate",
    status_code=201,
    response_model=Case,
)
async def duplicate_case(
    case_id: str,
    db=Depends(get_db),
) -> Case:
    """Deep-copy a case with new IDs throughout.

    Copies datasets (bytes on disk), profiles, runs, findings and charts, so the
    duplicate is a self-contained case in its own right and mutations to it
    never touch the original (P2-CASE-010).
    """
    source = db.execute(
        "SELECT id, question, dataset, created_at, updated_at FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()
    if source is None:
        raise HTTPException(status_code=404, detail="case not found")

    new_case_id = str(uuid4())
    now = datetime.now(timezone.utc)
    new_case = Case(
        id=new_case_id,
        question=source["question"],
        dataset=source["dataset"],
        created_at=now,
        updated_at=now,
    )
    db.execute(
        "INSERT INTO cases (id, question, dataset, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (new_case.id, new_case.question, new_case.dataset,
         new_case.created_at.isoformat(), new_case.updated_at.isoformat()),
    )

    case_dir = db_module.DATA_DIR / new_case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    # Datasets: copy the stored bytes, keep an old->new id map for the children
    # that reference a dataset (profiles and runs).
    dataset_ids: dict[str, str] = {}
    for dataset in db.execute(
        "SELECT id, filename, stored_path, format, created_at FROM datasets "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        new_dataset_id = str(uuid4())
        dataset_ids[dataset["id"]] = new_dataset_id
        source_path = Path(dataset["stored_path"])
        stored_path = case_dir / f"{new_dataset_id}.{dataset['format']}"
        if source_path.is_file():
            stored_path.write_bytes(source_path.read_bytes())
        db.execute(
            "INSERT INTO datasets (id, case_id, filename, stored_path, format, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (new_dataset_id, new_case_id, dataset["filename"], str(stored_path),
             dataset["format"], now.isoformat()),
        )

    for profile in db.execute(
        "SELECT dataset_id, rows, columns_json, stats_json, duplicate_rows, profiled_at "
        "FROM profiles WHERE dataset_id IN (SELECT id FROM datasets WHERE case_id = ?)",
        (case_id,),
    ).fetchall():
        db.execute(
            "INSERT OR REPLACE INTO profiles (dataset_id, rows, columns_json, stats_json, "
            "duplicate_rows, profiled_at) VALUES (?, ?, ?, ?, ?, ?)",
            (dataset_ids.get(profile["dataset_id"]), profile["rows"],
             profile["columns_json"], profile["stats_json"],
             profile["duplicate_rows"], profile["profiled_at"]),
        )

    # Runs: remap dataset; keep an old->new id map for findings and charts.
    run_ids: dict[str, str] = {}
    for run in db.execute(
        "SELECT id, dataset_id, kind, sql, code, dataset_ids_json, columns_json, "
        "rows_json, row_count, "
        "truncated, executed_at FROM runs WHERE case_id = ? ORDER BY executed_at",
        (case_id,),
    ).fetchall():
        new_run_id = str(uuid4())
        run_ids[run["id"]] = new_run_id
        db.execute(
            "INSERT INTO runs (id, case_id, dataset_id, kind, sql, code, "
            "dataset_ids_json, columns_json, rows_json, row_count, truncated, "
            "executed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (new_run_id, new_case_id, dataset_ids.get(run["dataset_id"]), run["kind"],
             run["sql"], run["code"],
             _remap_dataset_ids(run["dataset_ids_json"], dataset_ids),
             run["columns_json"],
             run["rows_json"], run["row_count"], run["truncated"], run["executed_at"]),
        )

    for finding in db.execute(
        "SELECT id, run_id, statement, interpretation, caveat, validation_status, created_at "
        "FROM findings WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        db.execute(
            "INSERT INTO findings (id, case_id, run_id, statement, interpretation, "
            "caveat, validation_status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid4()), new_case_id, run_ids.get(finding["run_id"]),
             finding["statement"], finding["interpretation"], finding["caveat"],
             finding["validation_status"], finding["created_at"]),
        )

    for chart in db.execute(
        "SELECT id, run_id, kind, x, y, series, title, stored_path, width, height, created_at "
        "FROM charts WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        new_chart_id = str(uuid4())
        source_path = Path(chart["stored_path"])
        chart_suffix = Path(chart["stored_path"]).suffix or ".svg"
        stored_path = case_dir / f"chart_{new_chart_id}{chart_suffix}"
        if source_path.is_file():
            stored_path.write_bytes(source_path.read_bytes())
        db.execute(
            "INSERT INTO charts (id, case_id, run_id, kind, x, y, series, title, "
            "stored_path, width, height, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (new_chart_id, new_case_id, run_ids.get(chart["run_id"]), chart["kind"],
             chart["x"], chart["y"], chart["series"], chart["title"],
             str(stored_path), chart["width"], chart["height"], chart["created_at"]),
        )

    for plan in db.execute(
        "SELECT id, dataset_id, question, plan_json, source, created_at FROM plans "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        db.execute(
            "INSERT INTO plans (id, case_id, dataset_id, question, plan_json, source, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid4()), new_case_id, dataset_ids.get(plan["dataset_id"]),
             plan["question"], plan["plan_json"], plan["source"], plan["created_at"]),
        )

    return new_case


@app.delete("/cases/{case_id}", status_code=204)
async def delete_case(case_id: str, db=Depends(get_db)) -> None:
    """Delete a case and everything attached to it.

    Children are removed before the case row, and the case's on-disk directory
    goes with it, so a deleted case leaves no orphaned state behind.
    """
    row = db.execute("SELECT 1 FROM cases WHERE id = ?", (case_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="case not found")

    # Order matters for the declared foreign keys: charts and findings
    # reference runs; profiles are keyed by dataset, not by case.
    db.execute("DELETE FROM charts WHERE case_id = ?", (case_id,))
    db.execute("DELETE FROM findings WHERE case_id = ?", (case_id,))
    db.execute("DELETE FROM runs WHERE case_id = ?", (case_id,))
    db.execute(
        "DELETE FROM profiles WHERE dataset_id IN "
        "(SELECT id FROM datasets WHERE case_id = ?)",
        (case_id,),
    )
    db.execute("DELETE FROM plans WHERE case_id = ?", (case_id,))
    db.execute("DELETE FROM datasets WHERE case_id = ?", (case_id,))
    db.execute("DELETE FROM cases WHERE id = ?", (case_id,))

    case_dir = db_module.DATA_DIR / case_id
    if case_dir.is_dir():
        shutil.rmtree(case_dir)


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


def _dataset_ids_of(row) -> list[str] | None:
    """The datasets a run touches; None means an unknown (legacy) set.

    Older runs predate the column, and single-dataset runs record [dataset_id]
    so the response always tells the caller what the query bound.
    """
    raw = row["dataset_ids_json"] if "dataset_ids_json" in row.keys() else None
    if not raw:
        return None
    try:
        ids = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return [str(item) for item in ids] if ids else None


@app.post(
    "/cases/{case_id}/runs",
    status_code=201,
    response_model=Run,
)
async def create_multi_dataset_run(
    case_id: str,
    payload: MultiRunCreate,
    db=Depends(get_db),
) -> Run:
    """Run user SQL across several attached datasets (P3-DATA-003).

    Placeholders bind positionally to the datasets in the order listed, so a
    query can join files of any supported format:

        SELECT a.region, b.target
        FROM read_csv_auto(?) a JOIN read_parquet(?) b ON a.id = b.id

    One placeholder per dataset; a mismatch is a 400. The first dataset is the
    run's primary, which keeps the evidence chain and old code paths working.
    """
    _require_case(db, case_id)
    if not payload.dataset_ids:
        raise HTTPException(status_code=400, detail="at least one dataset is required")
    if len(set(payload.dataset_ids)) != len(payload.dataset_ids):
        raise HTTPException(status_code=400, detail="dataset_ids must be unique")

    placeholders = ", ".join("?" * len(payload.dataset_ids))
    rows = db.execute(
        f"SELECT id, stored_path FROM datasets WHERE case_id = ? AND id IN "
        f"({placeholders})",
        (case_id, *payload.dataset_ids),
    ).fetchall()
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(payload.dataset_ids):
        missing = [i for i in payload.dataset_ids if i not in by_id]
        raise HTTPException(
            status_code=404,
            detail=f"dataset(s) not found in this case: {', '.join(missing)}",
        )

    paths = [by_id[dataset_id]["stored_path"] for dataset_id in payload.dataset_ids]
    try:
        result = run_query_multi(paths, payload.sql)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"query failed: {error}")

    run = Run(
        id=str(uuid4()),
        case_id=case_id,
        dataset_id=payload.dataset_ids[0],
        kind="sql",
        sql=payload.sql,
        dataset_ids=list(payload.dataset_ids),
        columns=result["columns"],
        rows=result["rows"],
        row_count=result["row_count"],
        truncated=result["truncated"],
        executed_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT INTO runs (id, case_id, dataset_id, kind, sql, code, "
        "dataset_ids_json, columns_json, rows_json, row_count, truncated, "
        "executed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run.id,
            run.case_id,
            run.dataset_id,
            run.kind,
            run.sql,
            None,
            json.dumps(run.dataset_ids),
            json.dumps(run.columns),
            json.dumps(run.rows),
            run.row_count,
            1 if run.truncated else 0,
            run.executed_at.isoformat(),
        ),
    )
    return run


def _remap_dataset_ids(raw: str | None, dataset_ids: dict[str, str]) -> str:
    """Repoint a duplicated run's dataset list at the copy's own datasets."""
    if not raw:
        return json.dumps(list(dataset_ids.values())[:1]) if dataset_ids else "[]"
    try:
        listed = json.loads(raw)
    except json.JSONDecodeError:
        return json.dumps(list(dataset_ids.values())[:1]) if dataset_ids else "[]"
    return json.dumps([dataset_ids.get(item) for item in listed])


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
        kind="sql",
        sql=payload.sql,
        columns=result["columns"],
        rows=result["rows"],
        row_count=result["row_count"],
        truncated=result["truncated"],
        executed_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT INTO runs (id, case_id, dataset_id, kind, sql, code, "
        "dataset_ids_json, columns_json, rows_json, row_count, truncated, "
        "executed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run.id,
            run.case_id,
            run.dataset_id,
            run.kind,
            run.sql,
            run.code,
            json.dumps([run.dataset_id]),
            json.dumps(run.columns),
            json.dumps(run.rows),
            run.row_count,
            1 if run.truncated else 0,
            run.executed_at.isoformat(),
        ),
    )
    return run


@app.post(
    "/cases/{case_id}/datasets/{dataset_id}/runs/python",
    status_code=201,
    response_model=Run,
)
async def create_python_run(
    case_id: str,
    dataset_id: str,
    payload: PythonRunCreate,
    db=Depends(get_db),
) -> Run:
    """Run user Python against an attached dataset and persist the result.

    The code executes in a restricted read-only workspace (no filesystem
    writes, no imports outside the allowlist, bounded CPU and memory) with a
    `dataset` handle for read-only access. Its `result` becomes the run's
    columns and rows, persisted exactly like a SQL run (P2-ANALYSIS-008).
    """
    dataset = _require_dataset(db, case_id, dataset_id)

    try:
        result = run_python(dataset.stored_path, payload.code)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"analysis failed: {error}")

    run = Run(
        id=str(uuid4()),
        case_id=case_id,
        dataset_id=dataset_id,
        kind="python",
        code=payload.code,
        columns=result["columns"],
        rows=result["rows"],
        row_count=result["row_count"],
        truncated=result["truncated"],
        executed_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT INTO runs (id, case_id, dataset_id, kind, sql, code, "
        "dataset_ids_json, columns_json, rows_json, row_count, truncated, "
        "executed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run.id,
            run.case_id,
            run.dataset_id,
            run.kind,
            run.sql,
            run.code,
            json.dumps([run.dataset_id]),
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
        "SELECT id, case_id, dataset_id, kind, sql, code, dataset_ids_json, "
        "row_count, truncated, executed_at FROM runs "
        "WHERE case_id = ? ORDER BY executed_at DESC",
        (case_id,),
    ).fetchall()
    return [
        RunSummary(
            id=row["id"],
            case_id=row["case_id"],
            dataset_id=row["dataset_id"],
            kind=row["kind"],
            sql=row["sql"],
            code=row["code"],
            dataset_ids=_dataset_ids_of(row),
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
        "SELECT id, case_id, dataset_id, kind, sql, code, dataset_ids_json, "
        "columns_json, rows_json, row_count, truncated, executed_at "
        "FROM runs WHERE id = ? AND case_id = ?",
        (run_id, case_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    return Run(
        id=row["id"],
        case_id=row["case_id"],
        dataset_id=row["dataset_id"],
        kind=row["kind"],
        sql=row["sql"],
        code=row["code"],
        dataset_ids=_dataset_ids_of(row),
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
        "SELECT id, case_id, dataset_id, kind, sql, code, columns_json, rows_json, "
        "row_count, truncated, executed_at FROM runs WHERE id = ?",
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
        kind=run_row["kind"],
        sql=run_row["sql"],
        code=run_row["code"],
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
        "SELECT id, case_id, dataset_id, kind, sql, dataset_ids_json, "
        "columns_json, rows_json, row_count, truncated FROM runs WHERE id = ?",
        (finding.run_id,),
    ).fetchone()
    if run_row is None:
        raise HTTPException(status_code=500, detail="referenced run is missing")

    if run_row["kind"] != "sql":
        # Reproducing a Python run means re-executing its script; that gate is
        # not part of this task, so it is reported rather than faked.
        raise HTTPException(
            status_code=400,
            detail="validation of Python runs is not supported yet",
        )

    dataset_ids = _dataset_ids_of(run_row) or [run_row["dataset_id"]]
    dataset_rows = db.execute(
        "SELECT id, stored_path FROM datasets WHERE id IN "
        f"({', '.join('?' * len(dataset_ids))})",
        dataset_ids,
    ).fetchall()
    by_id = {row["id"]: row for row in dataset_rows}
    if len(by_id) != len(dataset_ids):
        raise HTTPException(status_code=500, detail="referenced dataset is missing")
    dataset_row = by_id[dataset_ids[0]]

    checks: list[ValidationCheck] = []

    # 1. Reproducibility: rerun the stored SQL and compare to the stored rows.
    # A multi-dataset run re-binds every placeholder in order.
    try:
        if len(dataset_ids) > 1:
            rerun = run_query_multi(
                [by_id[dataset_id]["stored_path"] for dataset_id in dataset_ids],
                run_row["sql"],
            )
        else:
            rerun = run_query(dataset_row["stored_path"], run_row["sql"])
        reproduced = rerun["rows"] == json.loads(run_row["rows_json"])
    except (ValueError, Exception) as error:
        # A query that no longer binds against the stored data - a renamed
        # column, a changed schema - is a failed check, not a server error.
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


@app.post(
    "/cases/{case_id}/runs/{run_id}/charts",
    status_code=201,
    response_model=Chart,
)
async def create_chart(
    case_id: str,
    run_id: str,
    payload: ChartCreate,
    db=Depends(get_db),
) -> Chart:
    """Render a chart from a persisted run result and store it with the case.

    The chart is an evidence artifact: it is rendered from the stored result,
    not from a live query, so it stays reproducible after the run. SVG is
    written to the case directory and its metadata to SQLite (P2-ANALYSIS-009).
    """
    _require_run(db, case_id, run_id)
    row = db.execute(
        "SELECT columns_json, rows_json FROM runs WHERE id = ? AND case_id = ?",
        (run_id, case_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")

    columns = json.loads(row["columns_json"])
    rows = json.loads(row["rows_json"])

    fmt = payload.format if payload.format in CHART_FORMATS else "svg"
    try:
        image = render_chart(
            payload.kind,
            columns,
            rows,
            payload.x,
            payload.y,
            payload.series,
            payload.title,
            fmt=fmt,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"chart failed: {error}")

    chart_id = str(uuid4())
    case_dir = db_module.DATA_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    stored_path = case_dir / f"chart_{chart_id}.{fmt}"
    stored_path.write_bytes(image)

    chart = Chart(
        id=chart_id,
        case_id=case_id,
        run_id=run_id,
        kind=payload.kind,
        x=payload.x,
        y=payload.y,
        series=payload.series,
        title=payload.title,
        stored_path=str(stored_path),
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        created_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT INTO charts (id, case_id, run_id, kind, x, y, series, title, "
        "stored_path, width, height, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            chart.id,
            chart.case_id,
            chart.run_id,
            chart.kind,
            chart.x,
            chart.y,
            chart.series,
            chart.title,
            chart.stored_path,
            chart.width,
            chart.height,
            chart.created_at.isoformat(),
        ),
    )
    return chart


def _chart_row_to_summary(row) -> ChartSummary:
    return ChartSummary(
        id=row["id"],
        case_id=row["case_id"],
        run_id=row["run_id"],
        kind=row["kind"],
        x=row["x"],
        y=row["y"],
        series=row["series"],
        title=row["title"],
        created_at=row["created_at"],
    )


@app.get(
    "/cases/{case_id}/runs/{run_id}/charts",
    response_model=list[ChartSummary],
)
async def list_charts(case_id: str, run_id: str, db=Depends(get_db)) -> list[ChartSummary]:
    """List the charts rendered from one run, without the image bytes."""
    _require_run(db, case_id, run_id)
    rows = db.execute(
        "SELECT id, case_id, run_id, kind, x, y, series, title, created_at "
        "FROM charts WHERE case_id = ? AND run_id = ? ORDER BY created_at DESC",
        (case_id, run_id),
    ).fetchall()
    return [_chart_row_to_summary(row) for row in rows]


def _require_chart(db, case_id: str, chart_id: str):
    row = db.execute(
        "SELECT id, case_id, run_id, kind, x, y, series, title, stored_path, "
        "width, height, created_at FROM charts WHERE id = ? AND case_id = ?",
        (chart_id, case_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="chart not found")
    return row


@app.get("/cases/{case_id}/charts/{chart_id}", response_model=Chart)
async def get_chart(case_id: str, chart_id: str, db=Depends(get_db)) -> Chart:
    """Retrieve a chart's metadata."""
    row = _require_chart(db, case_id, chart_id)
    return Chart(
        id=row["id"],
        case_id=row["case_id"],
        run_id=row["run_id"],
        kind=row["kind"],
        x=row["x"],
        y=row["y"],
        series=row["series"],
        title=row["title"],
        stored_path=row["stored_path"],
        width=row["width"],
        height=row["height"],
        created_at=row["created_at"],
    )


@app.get(
    "/cases/{case_id}/charts/{chart_id}/image",
    response_class=FileResponse,
)
async def get_chart_image(case_id: str, chart_id: str, db=Depends(get_db)) -> FileResponse:
    """Serve the persisted chart image itself."""
    row = _require_chart(db, case_id, chart_id)
    path = Path(row["stored_path"])
    if not path.is_file():
        raise HTTPException(status_code=404, detail="chart image is missing from disk")
    return FileResponse(path, media_type=_chart_media_type(path), filename=path.name)


def _chart_media_type(path: Path) -> str:
    """The artifact's content type, sniffed from its stored bytes.

    Charts created before P3-CHART-002 are SVG; newer ones may be PNG. Sniffing
    keeps old rows correct without a schema migration.
    """
    try:
        with path.open("rb") as handle:
            head = handle.read(8)
    except OSError:
        return "image/svg+xml"
    return "image/png" if head.startswith(b"\x89PNG\r\n\x1a\n") else "image/svg+xml"


@app.post(
    "/cases/{case_id}/datasets/{dataset_id}/plan",
    status_code=201,
    response_model=Plan,
)
async def create_plan(
    case_id: str,
    dataset_id: str,
    db=Depends(get_db),
) -> Plan:
    """Plan an analysis from the case question and the dataset profile.

    The plan is context-specific, not a whole-case dump (Master Spec section
    18): question plus profile in, structured plan out. The LLM is preferred
    when configured and its output is schema-validated here; otherwise the
    deterministic planner derives the plan from the profile's structure. The
    `source` field records which engine produced it (P2-AI-011).
    """
    dataset = _require_dataset(db, case_id, dataset_id)

    case_row = db.execute(
        "SELECT question FROM cases WHERE id = ?", (case_id,)
    ).fetchone()
    if case_row is None:
        raise HTTPException(status_code=404, detail="case not found")

    profile_row = db.execute(
        "SELECT rows, columns_json, stats_json, duplicate_rows FROM profiles "
        "WHERE dataset_id = ?",
        (dataset_id,),
    ).fetchone()
    # Without a profile there is nothing structural to plan from, so the call
    # names the missing step rather than planning against an empty dataset.
    if profile_row is None:
        raise HTTPException(
            status_code=400,
            detail="profile the dataset before planning",
        )

    profile = {
        "rows": profile_row["rows"],
        "columns": json.loads(profile_row["columns_json"]),
        "stats": json.loads(profile_row["stats_json"]),
        "duplicate_rows": profile_row["duplicate_rows"],
    }

    plan_body, source = create_plan_module(case_row["question"], profile)
    # An LLM plan is re-validated on the way in; schema violations never reach
    # the database.
    problems = validate_plan(plan_body)
    if problems:
        raise HTTPException(
            status_code=500,
            detail=f"plan failed validation: {'; '.join(problems[:3])}",
        )

    plan = Plan(
        id=str(uuid4()),
        case_id=case_id,
        dataset_id=dataset_id,
        question=case_row["question"],
        plan=plan_body,
        source=source,
        created_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT INTO plans (id, case_id, dataset_id, question, plan_json, source, "
        "created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (plan.id, plan.case_id, plan.dataset_id, plan.question,
         json.dumps(plan.plan), plan.source, plan.created_at.isoformat()),
    )
    return plan


@app.get(
    "/cases/{case_id}/datasets/{dataset_id}/plan",
    response_model=Plan,
)
async def get_plan(case_id: str, dataset_id: str, db=Depends(get_db)) -> Plan:
    """Retrieve the latest plan for a case's dataset."""
    _require_dataset(db, case_id, dataset_id)
    row = db.execute(
        "SELECT id, case_id, dataset_id, question, plan_json, source, created_at "
        "FROM plans WHERE case_id = ? AND dataset_id = ? "
        "ORDER BY created_at DESC LIMIT 1",
        (case_id, dataset_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="plan not found")
    return Plan(
        id=row["id"],
        case_id=row["case_id"],
        dataset_id=row["dataset_id"],
        question=row["question"],
        plan=json.loads(row["plan_json"]),
        source=row["source"],
        created_at=row["created_at"],
    )


@app.get(
    "/cases/{case_id}/datasets/{dataset_id}/plans",
    response_model=list[PlanSummary],
)
async def list_plans(
    case_id: str, dataset_id: str, db=Depends(get_db)
) -> list[PlanSummary]:
    """Every plan recorded for a case's dataset, newest first."""
    _require_dataset(db, case_id, dataset_id)
    rows = db.execute(
        "SELECT id, case_id, dataset_id, question, source, created_at FROM plans "
        "WHERE case_id = ? AND dataset_id = ? ORDER BY created_at DESC",
        (case_id, dataset_id),
    ).fetchall()
    return [
        PlanSummary(
            id=row["id"],
            case_id=row["case_id"],
            dataset_id=row["dataset_id"],
            question=row["question"],
            source=row["source"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@app.get(
    "/cases/{case_id}/export",
    response_model=dict,
)
async def export_case_package(case_id: str, db=Depends(get_db)) -> dict:
    """Export a case as one self-contained JSON package.

    The package carries the datasets' bytes, the runs' results, the chart
    artifacts, and every finding and plan, so it needs neither the database nor
    the data directory to be understood or restored (P2-CASE-012).
    """
    package = export_case(db, case_id)
    if package is None:
        raise HTTPException(status_code=404, detail="case not found")
    return package


@app.post(
    "/cases/import",
    status_code=201,
    response_model=Case,
)
async def import_case_package(payload: dict, db=Depends(get_db)) -> Case:
    """Reconstruct a case from an exported package.

    The inverse of export: entities are recreated with fresh IDs and remapped
    references, so a restored package stands on its own and never collides with
    existing IDs.
    """
    if len(json.dumps(payload)) > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="package is too large")
    try:
        case = import_package(db, payload, db_module.DATA_DIR)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return Case(
        id=case["id"],
        question=case["question"],
        dataset=case["dataset"],
        created_at=case["created_at"],
        updated_at=case["updated_at"],
    )
