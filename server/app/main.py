import logging
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4


def load_env_config(env_path: Path) -> bool:
    """Load a local .env into the process environment.

    Returns True when a file was found and loaded. Existing environment
    variables win - `load_dotenv` does not override them - so a variable
    exported in the shell or injected by a container always beats the file.
    """
    from dotenv import load_dotenv

    return load_dotenv(env_path)


# A plain `uvicorn app.main:app` start picks up server/.env without the caller
# sourcing it first. Skipped under pytest so a developer with a real LLM key
# configured does not make live calls from the test suite.
if "pytest" not in sys.modules:
    load_env_config(Path(__file__).resolve().parent.parent / ".env")


from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import json

from app.analysis import profile_csv, run_query, run_query_multi
from app.errors import INPUT_ERROR_TYPES
from app.eda import EDA_OPS, run_eda
from app.evidence import build_evidence_graph
from app.history import build_case_history
from app.logging_config import (
    LOG_LINE_CEILING,
    configure_logging,
    current_log_file,
    read_tail,
    rotated_log_files,
)
from app.supervisor import start_parent_watchdog
from app.python_exec import run_python
from app.workflow import STAGES, case_progress
from app.charts import render_chart, CHART_KINDS, CHART_FORMATS
from app.charts import DEFAULT_WIDTH, DEFAULT_HEIGHT
from app.planner import create_plan as create_plan_module, validate_plan
from app.interpreter import create_interpretation as create_interpretation_module
from app.drafter import create_draft as create_draft_module
from app.generator import create_code as create_code_module
from app.assistant import create_answer as create_answer_module, summarize_case
from app.exporter import export_case, import_package, PACKAGE_FORMAT, PACKAGE_VERSION
from app import agent as agent_module
import app.db as db_module
from app.db import get_connection
from app.models import (
    Case,
    CaseCreate,
    CaseFromTemplate,
    CaseHistory,
    CaseProgress,
    CaseUpdate,
    EdaCreate,
    EdaResult,
    EvidenceGraph,
    EvidenceNode,
    EvidenceEdge,
    ClaimTrace,
    WorkflowStage,
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
    Template,
    TemplateCreate,
    Interpretation,
    DraftFinding,
    LogView,
    GenerateCodeRequest,
    GeneratedCode,
    ChatRequest,
    ConversationTurn,
    AgentStep,
    AgentState,
    AgentApproval,
)

# Give the core's output somewhere to go. Under the desktop shell the core is a
# child process whose stderr nobody is reading, so a 500's traceback needs a
# file. Writes under DAH_DATA_DIR/logs, nowhere else, and nothing under pytest
# (see app/logging_config). Called before the watchdog so that a supervised
# exit is the last line in the log rather than an unwritten one.
configure_logging()

# Under the desktop shell, end this process when the shell is gone (see
# app.supervisor). No-op for a hand-started server and under pytest.
start_parent_watchdog()


app = FastAPI(
    title="DAH Harness Core",
    description="Deterministic core of the Data Analysis Harness.",
    version="0.1.0",
)


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """A fault in the harness answers 500 as JSON, with an id (P5-RELIABILITY-003).

    Two jobs, and the second is the one that is easy to lose: catching the
    exception means uvicorn never sees it, so the traceback P5-OBSERVE-002 made
    recoverable would stop reaching the log. It is recorded here, under the id
    the response carries, so "I have error <id>" finds the traceback in the
    file.

    The body deliberately says less than the log. A fault's message can quote
    what it was holding - an unknown column, a filename, a value that failed to
    parse - so only the id and a fixed message leave the process. The detail
    stays local.

    HTTPException has its own handler, so a 400 or a 404 never reaches here and
    keeps answering with its own `detail`.
    """
    request_id = uuid4().hex
    logging.getLogger("dah.core").exception(
        "unhandled error request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "internal error", "request_id": request_id},
    )


@app.middleware("http")
async def log_request(request: Request, call_next):
    """One line per request, holding only the shape of the call.

    Method, path, status and duration are what an operator needs to see a slow
    or failing endpoint. The body is deliberately absent: an analyst's question,
    the SQL they wrote and every value in their data never reach the log.
    """
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        logging.getLogger("dah.request").info(
            "%s %s -> %s in %.0fms",
            request.method,
            request.url.path,
            status_code,
            (time.perf_counter() - started) * 1000,
        )


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. Confirms the core process is up and answering."""
    return {"status": "ok"}


@app.get("/logs", response_model=LogView)
def recent_logs(lines: int = 200) -> LogView:
    """The tail of what the core has been doing.

    Read-only by construction - GET only, no body accepted, nothing the caller
    supplies is written anywhere. `lines` defaults to 200 and is clamped to 1000,
    because the interesting part of a log is its end and a megabyte of history
    in a response serves nobody.
    """
    log_file = current_log_file()
    if log_file is None:
        return LogView(
            enabled=False,
            path=None,
            size_bytes=0,
            rotated=[],
            lines=[],
        )
    tail = read_tail(log_file, min(max(lines, 1), LOG_LINE_CEILING))
    return LogView(
        enabled=True,
        path=str(log_file),
        size_bytes=log_file.stat().st_size if log_file.exists() else 0,
        rotated=[path.name for path in rotated_log_files()],
        lines=tail,
    )


def get_db() -> Iterator[object]:
    with get_connection() as connection:
        yield connection


def _insert_case(db, question: str, dataset: str) -> Case:
    """Persist a fresh case row and return it (P3-CASE-007).

    Shared by direct creation and creation from a template, so the two paths
    cannot diverge on defaults like `updated_at`.
    """
    now = datetime.now(timezone.utc)
    case = Case(
        id=str(uuid4()),
        question=question,
        dataset=dataset,
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


@app.post("/cases", status_code=201, response_model=Case)
async def create_case(payload: CaseCreate, db=Depends(get_db)) -> Case:
    """Create and persist a new Analysis Case."""
    return _insert_case(db, payload.question, payload.dataset)


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


@app.get(
    "/cases/{case_id}/progress",
    response_model=CaseProgress,
)
async def get_case_progress(case_id: str, db=Depends(get_db)) -> CaseProgress:
    """Where this case stands in the guided workflow (P3-FLOW-004).

    The stage is derived from the case's artifacts rather than stored, so the
    answer always matches the data: attach a dataset and the `data` stage
    closes; delete it and the case moves back. The response names the single
    action that advances, and the endpoint that performs it.
    """
    _require_case(db, case_id)
    progress = case_progress(db, case_id)
    completed = set(progress["completed"])
    return CaseProgress(
        case_id=case_id,
        stage=progress["stage"],
        completed=progress["completed"],
        stages=[
            WorkflowStage(name=stage, completed=stage in completed)
            for stage in STAGES
        ],
        next_action=progress["next_action"],
        next_hint=progress["next_hint"],
        next_endpoint=progress["next_endpoint"],
        loop_closed=progress["loop_closed"],
        counts=progress["counts"],
    )


def _like_pattern(term: str) -> str:
    """Turn a search term into a literal-substring LIKE pattern (P3-CASE-007).

    LIKE wildcards in the term are escaped so `q1_1` does not match `q1a1` and
    `50%` stays a literal percent sign; backslash is the escape character.
    """
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@app.get("/cases", response_model=list[Case])
async def list_cases(q: str | None = None, db=Depends(get_db)) -> list[Case]:
    """List all persisted Analysis Cases.

    `q` filters case-insensitively on the question and the dataset label; an
    absent or empty `q` lists everything (P3-CASE-007).
    """
    if q and q.strip():
        pattern = _like_pattern(q.strip().lower())
        rows = db.execute(
            "SELECT id, question, dataset, created_at, updated_at FROM cases "
            "WHERE LOWER(question) LIKE ? ESCAPE '\\' "
            "OR LOWER(dataset) LIKE ? ESCAPE '\\' "
            "ORDER BY created_at DESC",
            (pattern, pattern),
        ).fetchall()
    else:
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

    for item in db.execute(
        "SELECT id, run_id, summary, observations_json, caveats_json, source, "
        "created_at FROM interpretations WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        db.execute(
            "INSERT INTO interpretations (id, run_id, case_id, summary, "
            "observations_json, caveats_json, source, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid4()),
                run_ids.get(item["run_id"]),
                new_case_id,
                item["summary"],
                item["observations_json"],
                item["caveats_json"],
                item["source"],
                item["created_at"],
            ),
        )

    # The agent's audit trail travels with the case it belongs to (P6-AGENT-002):
    # a duplicate whose findings were agent-proposed keeps the approvals that
    # let those proposals run, so the copy is as inspectable as the original.
    # Payload ids are remapped to the copy's own artifacts, exactly as above.
    for step in db.execute(
        "SELECT kind, payload_json, source, status, note, created_at, decided_at "
        "FROM agent_steps WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        remapped = json.loads(step["payload_json"])
        for key, mapping in (
            ("dataset_id", dataset_ids),
            ("run_id", run_ids),
        ):
            if isinstance(remapped.get(key), str):
                remapped[key] = mapping.get(remapped[key], remapped[key])
        db.execute(
            "INSERT INTO agent_steps (id, case_id, kind, payload_json, source, "
            "status, note, created_at, decided_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid4()),
                new_case_id,
                step["kind"],
                json.dumps(remapped),
                step["source"],
                step["status"],
                step["note"] or "",
                step["created_at"],
                step["decided_at"],
            ),
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
    db.execute("DELETE FROM interpretations WHERE case_id = ?", (case_id,))
    db.execute("DELETE FROM conversations WHERE case_id = ?", (case_id,))
    db.execute("DELETE FROM agent_steps WHERE case_id = ?", (case_id,))
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


@app.delete("/cases/{case_id}/datasets/{dataset_id}", status_code=204)
async def delete_dataset(case_id: str, dataset_id: str, db=Depends(get_db)) -> None:
    """Remove one dataset from a case, leaving the case itself standing.

    The dataset row, its profile, its plans and its on-disk file go together.
    It refuses while any run still binds the dataset: a run is the evidence a
    finding or a chart stands on - the evidence chain runs
    finding -> run -> dataset - so deleting the dataset underneath would leave
    a dangling trace. Delete the blocking run(s) first; that is also what makes
    the derived workflow stage move backwards (P3-FLOW-004).
    """
    dataset = _require_dataset(db, case_id, dataset_id)

    blocking = _runs_touching_dataset(db, case_id, dataset_id)
    if blocking:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{len(blocking)} run(s) still bind this dataset, and a finding "
                "or chart may stand on that evidence - delete the run(s) first"
            ),
        )

    db.execute("DELETE FROM profiles WHERE dataset_id = ?", (dataset_id,))
    db.execute("DELETE FROM plans WHERE dataset_id = ?", (dataset_id,))
    db.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))

    stored = Path(dataset.stored_path)
    if stored.is_file():
        stored.unlink()


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


def _runs_touching_dataset(db, case_id: str, dataset_id: str) -> list[str]:
    """IDs of the runs that bind this dataset, newest-independent order.

    A run binds a dataset either as its primary (runs.dataset_id) or as one of
    several (runs.dataset_ids_json, P3-DATA-003); a legacy run has no JSON list,
    so the primary column is checked on its own. This is the set a dataset
    deletion would undercut, and it is why deletion refuses while it is alive.
    """
    touching: set[str] = set()
    rows = db.execute(
        "SELECT id, dataset_id, dataset_ids_json FROM runs WHERE case_id = ?",
        (case_id,),
    ).fetchall()
    for row in rows:
        if row["dataset_id"] == dataset_id:
            touching.add(row["id"])
            continue
        bound = _dataset_ids_of(row)
        if bound and dataset_id in bound:
            touching.add(row["id"])
    return sorted(touching)


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
    except INPUT_ERROR_TYPES as error:
        # A join's SQL is the analyst's too: duckdb.Error for a bad statement,
        # ValueError for a placeholder or read-only-gate violation.
        raise HTTPException(status_code=400, detail=str(error))

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
    "/cases/{case_id}/datasets/{dataset_id}/eda",
    response_model=EdaResult,
)
async def run_exploratory_analysis(
    case_id: str,
    dataset_id: str,
    payload: EdaCreate,
    db=Depends(get_db),
) -> EdaResult:
    """Run one exploratory operation over an attached dataset (P3-ANALYSIS-005).

    Segmentation, correlation, and distribution summaries compile to read-only
    DuckDB and run under the same gate and row cap as a hand-written query. EDA
    is exploration rather than evidence, so the result is returned, not
    persisted: a finding must anchor on a query the analyst wrote.
    """
    dataset = _require_dataset(db, case_id, dataset_id)
    try:
        result = run_eda(dataset.stored_path, payload.op, payload.model_dump())
    except INPUT_ERROR_TYPES as error:
        # EDA compiles to DuckDB, so its failures are the same two families.
        raise HTTPException(status_code=400, detail=str(error))

    return EdaResult(
        op=payload.op,
        columns=result["columns"],
        rows=result["rows"],
        row_count=result["row_count"],
        truncated=result["truncated"],
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
    except INPUT_ERROR_TYPES as error:
        # Bad SQL - a syntax error, an unknown column - reaches here as a
        # duckdb.Error rather than a ValueError; both are the input's fault and
        # answer 400. Anything else is a server fault and propagates as a 500.
        raise HTTPException(status_code=400, detail=str(error))

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
    except INPUT_ERROR_TYPES as error:
        # run_python normalises every sandbox rejection to ValueError; a fault
        # in the harness itself is not one and may not answer 400.
        raise HTTPException(status_code=400, detail=str(error))

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


@app.get(
    "/cases/{case_id}/evidence-graph",
    response_model=EvidenceGraph,
)
async def get_evidence_graph(case_id: str, db=Depends(get_db)) -> EvidenceGraph:
    """Every claim in the case and what it rests on (P3-EVIDENCE-006).

    The graph is projected from the persisted rows, never stored, so it cannot
    drift from what is on disk. Each trace walks one finding out to the dataset
    it stands on; a finding that reaches no dataset is an orphan.
    """
    _require_case(db, case_id)
    try:
        graph = build_evidence_graph(db, case_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    def node(item: dict) -> EvidenceNode:
        return EvidenceNode(
            id=item["id"],
            kind=item["kind"],
            label=item["label"],
            detail=item.get("detail"),
            created_at=item.get("created_at"),
        )

    return EvidenceGraph(
        case_id=case_id,
        nodes=[node(item) for item in graph["nodes"]],
        edges=[
            EvidenceEdge(
                source=edge["source"], target=edge["target"], relation=edge["relation"]
            )
            for edge in graph["edges"]
        ],
        traces=[
            ClaimTrace(
                finding_id=trace["finding_id"],
                statement=trace["statement"],
                validation_status=trace["validation_status"],
                hops=[node(hop) for hop in trace["hops"]],
                reaches_source=trace["reaches_source"],
            )
            for trace in graph["traces"]
        ],
        orphan_findings=graph["orphan_findings"],
        counts=graph["counts"],
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


def _record_repro(checks, reproduced, detail_ok, detail_bad) -> bool:
    """Append the reproducibility check and report whether it passed."""
    checks.append(
        ValidationCheck(
            name="reproducibility",
            passed=reproduced,
            detail=detail_ok if reproduced else detail_bad,
        )
    )
    return reproduced


def _row_key(row) -> str:
    """A canonical sort key for one result row.

    DuckDB does not promise a row order for unordered results: a GROUP BY can
    return its groups in a different order on a different connection, so the
    same query rerun against the same data can persist its rows in another
    order and a positional comparison would call that a drift it is not. An SQL
    result set is a bag of rows; only ORDER BY makes it a sequence, and when the
    query asks for one DuckDB honours it, so sorting both sides is a no-op there
    and a correction everywhere else. JSON-encoding the row keeps the key
    type-aware and deterministic.
    """
    return json.dumps(row)


def _reproduce_sql(run_row, dataset_ids, by_id, checks) -> bool:
    """Rerun the stored SQL and compare it to the persisted rows.

    A multi-dataset run re-binds every placeholder in order. A query that no
    longer binds against the stored data - a renamed column, a changed schema
    - is a failed check, not a server error. Rows are compared as a multiset
    (see _row_key): a query that never asked for an order must not fail
    reproduction for having got a different one.
    """
    try:
        if len(dataset_ids) > 1:
            rerun = run_query_multi(
                [by_id[dataset_id]["stored_path"] for dataset_id in dataset_ids],
                run_row["sql"],
            )
        else:
            rerun = run_query(by_id[dataset_ids[0]]["stored_path"], run_row["sql"])
        stored = json.loads(run_row["rows_json"])
        matches = sorted(rerun["rows"], key=_row_key) == sorted(stored, key=_row_key)
    except (ValueError, Exception) as error:
        return _record_repro(checks, False, "", f"query rejected: {error}")
    return _record_repro(checks, matches, "rerun matches stored result", "rerun differs")


def _reproduce_python(run_row, dataset_row, checks) -> bool:
    """Re-execute the stored script and compare the whole tabulated result.

    Both columns and rows are compared: the tabulator names columns in
    first-seen order, so a script whose result shape drifted shows up as a
    column change even when the values happen to line up.
    """
    try:
        rerun = run_python(dataset_row["stored_path"], run_row["code"])
        matches = (
            rerun["columns"] == json.loads(run_row["columns_json"])
            and rerun["rows"] == json.loads(run_row["rows_json"])
        )
    except (ValueError, Exception) as error:
        return _record_repro(checks, False, "", f"script rejected: {error}")
    return _record_repro(checks, matches, "rerun matches stored result", "rerun differs")


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

    The trust loop closes here: the stored computation is rerun against the
    stored dataset and compared to the persisted result - SQL since P1, and
    Python since P3-SEC-001 made re-executing user script safe (it runs in a
    separate OS-sandboxed process, so validating costs no more trust than the
    original run did). A finding is `supported` only if the numbers still
    reproduce (Master Spec section 10.5).
    """
    finding = await get_finding(case_id, finding_id, db)

    run_row = db.execute(
        "SELECT id, case_id, dataset_id, kind, sql, code, dataset_ids_json, "
        "columns_json, rows_json, row_count, truncated FROM runs WHERE id = ?",
        (finding.run_id,),
    ).fetchone()
    if run_row is None:
        raise HTTPException(status_code=500, detail="referenced run is missing")

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

    # 1. Reproducibility: rerun the stored computation - SQL or Python - and
    # compare it to the stored rows.
    if run_row["kind"] == "python":
        reproduced = _reproduce_python(run_row, dataset_row, checks)
    else:
        reproduced = _reproduce_sql(run_row, dataset_ids, by_id, checks)

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
    "/cases/{case_id}/runs/{run_id}/interpret",
    status_code=201,
    response_model=Interpretation,
)
async def create_interpretation(
    case_id: str,
    run_id: str,
    db=Depends(get_db),
) -> Interpretation:
    """Say what a persisted result shows, in the language of the case question.

    The run's own columns and rows, the question, the SQL or Python that
    produced them, and the dataset profile go to the interpreter. The LLM reads
    them when it is configured and degrades to a deterministic read of the same
    numbers on any failure, so an interpretation is always returned and the
    persisted `source` says which engine spoke (P3-AI-011).
    """
    _require_run(db, case_id, run_id)
    row = db.execute(
        "SELECT kind, sql, code, columns_json, rows_json, row_count, truncated, "
        "dataset_id FROM runs WHERE id = ? AND case_id = ?",
        (run_id, case_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")

    case = db.execute("SELECT question FROM cases WHERE id = ?", (case_id,)).fetchone()
    profile_row = db.execute(
        "SELECT columns_json, stats_json FROM profiles WHERE dataset_id = ?",
        (row["dataset_id"],),
    ).fetchone()
    profile = (
        {
            "columns": json.loads(profile_row["columns_json"]),
            "stats": json.loads(profile_row["stats_json"]),
        }
        if profile_row is not None
        else None
    )

    interpretation, source = create_interpretation_module(
        question=case["question"] if case else "",
        kind=row["kind"],
        source_text=row["sql"] if row["kind"] == "sql" else row["code"],
        columns=json.loads(row["columns_json"]),
        rows=json.loads(row["rows_json"]),
        profile=profile,
        truncated=bool(row["truncated"]),
    )

    interpretation_id = str(uuid4())
    now = datetime.now(timezone.utc)
    db.execute(
        "INSERT INTO interpretations (id, run_id, case_id, summary, "
        "observations_json, caveats_json, source, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            interpretation_id,
            run_id,
            case_id,
            interpretation["summary"],
            json.dumps(interpretation.get("observations", [])),
            json.dumps(interpretation.get("caveats", [])),
            source,
            now.isoformat(),
        ),
    )
    return Interpretation(
        id=interpretation_id,
        run_id=run_id,
        case_id=case_id,
        summary=interpretation["summary"],
        observations=interpretation.get("observations", []),
        caveats=interpretation.get("caveats", []),
        source=source,
        created_at=now,
    )


def _interpretation_of(row) -> Interpretation:
    return Interpretation(
        id=row["id"],
        run_id=row["run_id"],
        case_id=row["case_id"],
        summary=row["summary"],
        observations=json.loads(row["observations_json"]),
        caveats=json.loads(row["caveats_json"]),
        source=row["source"],
        created_at=row["created_at"],
    )


@app.get(
    "/cases/{case_id}/runs/{run_id}/interpret",
    response_model=Interpretation,
)
async def get_interpretation(case_id: str, run_id: str, db=Depends(get_db)) -> Interpretation:
    """The latest reading of this run's result."""
    _require_run(db, case_id, run_id)
    row = db.execute(
        "SELECT id, run_id, case_id, summary, observations_json, caveats_json, "
        "source, created_at FROM interpretations WHERE run_id = ? AND case_id = ? "
        "ORDER BY created_at DESC LIMIT 1",
        (run_id, case_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="no interpretation recorded for this run")
    return _interpretation_of(row)


@app.get(
    "/cases/{case_id}/runs/{run_id}/interpretations",
    response_model=list[Interpretation],
)
async def list_interpretations(
    case_id: str, run_id: str, db=Depends(get_db)
) -> list[Interpretation]:
    """Every reading of this run's result, newest first."""
    _require_run(db, case_id, run_id)
    rows = db.execute(
        "SELECT id, run_id, case_id, summary, observations_json, caveats_json, "
        "source, created_at FROM interpretations WHERE run_id = ? AND case_id = ? "
        "ORDER BY created_at DESC",
        (run_id, case_id),
    ).fetchall()
    return [_interpretation_of(row) for row in rows]


@app.post(
    "/cases/{case_id}/runs/{run_id}/draft-finding",
    status_code=200,
    response_model=DraftFinding,
)
async def draft_finding(
    case_id: str,
    run_id: str,
    db=Depends(get_db),
) -> DraftFinding:
    """Draft the finding a result would support, without writing anything.

    A finding is the trust artifact - the evidence chain, validation and export
    all stand on it - so this stops one step short of creating one. The drafter
    reads the same inputs an interpretation reads (the run's own columns and
    rows, the case question, the SQL or Python that produced them, the dataset
    profile) and returns a candidate: a statement, what it means, its caveat and
    the grounds it stands on. The LLM proposes when it is configured; an invented
    magnitude or any other failure degrades to a deterministic draft of the same
    numbers, so a draft is always returned and `source` says which engine spoke.

    Drafting is stateless by design (P3-AI-012): nothing is persisted, and
    nothing is created until a human POSTs the statement to /findings - the only
    path that writes a finding, which keeps the human-owns-the-finding property
    structural instead of a flag.
    """
    _require_run(db, case_id, run_id)
    row = db.execute(
        "SELECT kind, sql, code, columns_json, rows_json, row_count, truncated, "
        "dataset_id FROM runs WHERE id = ? AND case_id = ?",
        (run_id, case_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")

    case = db.execute("SELECT question FROM cases WHERE id = ?", (case_id,)).fetchone()
    profile_row = db.execute(
        "SELECT columns_json, stats_json FROM profiles WHERE dataset_id = ?",
        (row["dataset_id"],),
    ).fetchone()
    profile = (
        {
            "columns": json.loads(profile_row["columns_json"]),
            "stats": json.loads(profile_row["stats_json"]),
        }
        if profile_row is not None
        else None
    )

    draft, source = create_draft_module(
        question=case["question"] if case else "",
        kind=row["kind"],
        source_text=row["sql"] if row["kind"] == "sql" else row["code"],
        columns=json.loads(row["columns_json"]),
        rows=json.loads(row["rows_json"]),
        profile=profile,
        truncated=bool(row["truncated"]),
    )
    return DraftFinding(
        run_id=run_id,
        case_id=case_id,
        statement=draft["statement"],
        interpretation=draft["interpretation"],
        caveat=draft["caveat"],
        grounds=draft.get("grounds", []),
        source=source,
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
        # render_chart validates everything it is given and raises ValueError
        # for it; a drawing failure underneath is a server fault, not bad input.
        raise HTTPException(status_code=400, detail=str(error))

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
    "/cases/{case_id}/chat",
    status_code=201,
    response_model=ConversationTurn,
)
async def chat_about_case(
    case_id: str,
    payload: ChatRequest,
    db=Depends(get_db),
) -> ConversationTurn:
    """Answer a question about the case, and remember the exchange.

    The case's own artifacts - datasets with their profiles, runs, findings,
    plans, charts and the derived workflow stage - are the things the answer may
    draw on, plus what *previous* cases found: memory is derived from the other
    cases on disk against this question, so an answer may cite a prior finding
    instead of re-deriving it (P6-MEMORY-001). `grounds` cites the artifact
    behind each claim so a reviewer can check it, and a citation that does not
    resolve to a real row - in this case or any other - is rejected. The LLM
    answers when it is configured, with the recent turns as context (that is the
    conversation memory), and degrades to a deterministic answer of the same
    facts on any failure - unavailable, malformed, or citing an artifact that
    does not exist - so an answer is always returned and `source` says which
    engine spoke (P3-AI-014).
    """
    _require_case(db, case_id)

    facts = summarize_case(db, case_id, payload.message)
    history = [
        {"message": row["message"], "answer": row["answer"]}
        for row in db.execute(
            "SELECT message, answer FROM conversations WHERE case_id = ? "
            "ORDER BY created_at",
            (case_id,),
        ).fetchall()
    ]

    turn, source = create_answer_module(payload.message, history, facts)
    turn_id = str(uuid4())
    now = datetime.now(timezone.utc)
    db.execute(
        "INSERT INTO conversations (id, case_id, message, answer, grounds_json, "
        "source, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            turn_id,
            case_id,
            payload.message,
            turn["answer"],
            json.dumps(turn.get("grounds", [])),
            source,
            now.isoformat(),
        ),
    )
    return ConversationTurn(
        id=turn_id,
        case_id=case_id,
        message=payload.message,
        answer=turn["answer"],
        grounds=turn.get("grounds", []),
        source=source,
        created_at=now,
    )


def _agent_step_of(row) -> AgentStep:
    return AgentStep(
        id=row["id"],
        case_id=row["case_id"],
        kind=row["kind"],
        payload=json.loads(row["payload_json"]),
        source=row["source"],
        status=row["status"],
        note=row["note"] or "",
        created_at=row["created_at"],
        decided_at=row["decided_at"],
    )


def _agent_state(db, case_id: str) -> AgentState:
    state = agent_module.state(db, case_id)
    return AgentState(
        case_id=case_id,
        pending=_agent_step_of(state["pending"]) if state["pending"] else None,
        history=[_agent_step_of(row) for row in state["history"]],
    )


@app.get(
    "/cases/{case_id}/agent",
    response_model=AgentState,
)
async def get_agent_state(case_id: str, db=Depends(get_db)) -> AgentState:
    """Where the agent stands on a case: the pending proposal and the audit trail.

    Read-only and idempotent. Nothing is proposed here - a GET that wrote would
    mean a page refresh commits work - so this is the safe thing to poll while a
    human is deciding.
    """
    _require_case(db, case_id)
    return _agent_state(db, case_id)


@app.post(
    "/cases/{case_id}/agent",
    response_model=AgentState,
    status_code=200,
    summary="Start or advance the case's agent",
    description=(
        "Derive and record the case's next step, if there is one. The step is "
        "*proposed*, not taken: its payload is settled now so the human approves "
        "something concrete, but the write waits for an approval. Idempotent - a "
        "pending step is returned unchanged, so two calls never yield two writes. "
        "A GET on the same path is the read-only state and never proposes."
    ),
)
async def propose_agent_step(case_id: str, db=Depends(get_db)) -> AgentState:
    """Start or advance the agent: derive and record the case's next step.

    A POST that performed the write would be autonomous, so this proposes and
    stops; the write happens on /approve. The payload is settled at proposal
    time, so the human approves something concrete rather than a promise.
    """
    _require_case(db, case_id)
    agent_module.propose(db, case_id)
    return _agent_state(db, case_id)


@app.post(
    "/cases/{case_id}/agent/approve",
    response_model=AgentState,
)
async def approve_agent_step(
    case_id: str,
    payload: AgentApproval,
    db=Depends(get_db),
) -> AgentState:
    """The human's yes. The step's write runs, and the next step is proposed.

    The approval must name the case's *current* pending step - an id from a
    stale page is a 409, never a second write of an old proposal. Every write
    goes through the endpoint that owns it, so the agent earns no privilege a
    hand-written call lacks: the same read-only gate, the same row cap, the
    same single path that creates a finding.
    """
    _require_case(db, case_id)
    try:
        step = agent_module.approve(db, case_id, payload.step_id)
    except agent_module.PendingStepError as error:
        raise HTTPException(
            status_code=409,
            detail={
                "detail": "the step id is not this case's pending step",
                "expected": error.expected,
                "given": error.given,
            },
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))

    note = await _apply_agent_step(db, case_id, step)
    agent_module.settle(db, step["id"], note)
    # The next proposal is part of the approval's answer, so a human approving
    # their way down the loop needs no second call to see what comes next.
    agent_module.propose(db, case_id)
    return _agent_state(db, case_id)


@app.post(
    "/cases/{case_id}/agent/reject",
    response_model=AgentState,
)
async def reject_agent_step(
    case_id: str,
    payload: AgentApproval,
    db=Depends(get_db),
) -> AgentState:
    """The human's no, with their reason recorded on the step.

    Rejection never writes case state: the proposal is marked rejected and the
    next step is derived, so refusing a draft leaves no finding behind and
    refusing a query leaves no run behind.
    """
    _require_case(db, case_id)
    try:
        agent_module.reject(db, case_id, payload.step_id, payload.reason or "")
    except agent_module.PendingStepError as error:
        raise HTTPException(
            status_code=409,
            detail={
                "detail": "the step id is not this case's pending step",
                "expected": error.expected,
                "given": error.given,
            },
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))
    agent_module.propose(db, case_id)
    return _agent_state(db, case_id)


async def _apply_agent_step(db, case_id: str, step: dict) -> str:
    """Run one approved step through the endpoint that owns the write.

    The agent has no write path of its own. Each kind awaits the same async
    endpoint a manual request would, which is what keeps the read-only gate, the
    row cap, the honesty budgets and the single-creation-path invariants in
    force for an agent-run case exactly as they are for a hand-run one.
    """
    kind = step["kind"]
    body = step["payload"]

    if kind == "profile":
        profile = await profile_dataset(case_id, body["dataset_id"], db)
        return f"profiled {body['filename']}: {profile.rows} row(s)"

    if kind == "plan":
        plan = await create_plan(case_id, body["dataset_id"], db)
        return f"planned from {plan.source}"

    if kind == "analyze":
        run = await create_run(
            case_id, body["dataset_id"], RunCreate(sql=body["code"]), db
        )
        return (
            f"ran {body['kind']} variant {body.get('variant', 0)}: "
            f"{run.row_count} row(s)"
        )

    if kind == "interpret":
        interpretation = await create_interpretation(
            case_id, body["run_id"], db
        )
        return f"interpreted from {interpretation.source}"

    if kind == "accept":
        finding = await create_finding(
            case_id,
            FindingCreate(
                run_id=body["run_id"],
                statement=body["statement"],
                interpretation=body.get("interpretation"),
                caveat=body.get("caveat"),
            ),
            db,
        )
        return f"accepted the draft as finding {finding.id}"

    if kind == "chart":
        chart = await create_chart(
            case_id,
            body["run_id"],
            ChartCreate(
                kind=body["kind"],
                x=body["x"],
                y=body["y"],
                title=body.get("title", ""),
            ),
            db,
        )
        return f"rendered {chart.kind} chart {chart.id}"

    if kind == "validate":
        result = await validate_finding(case_id, body["finding_id"], db)
        return f"validated: {result.status}"

    raise HTTPException(status_code=500, detail=f"unknown agent step kind {kind}")


@app.get(
    "/cases/{case_id}/chat",
    response_model=list[ConversationTurn],
)
async def list_chat(case_id: str, db=Depends(get_db)) -> list[ConversationTurn]:
    """The case's conversation, oldest first, so a reopened case resumes."""
    _require_case(db, case_id)
    rows = db.execute(
        "SELECT id, case_id, message, answer, grounds_json, source, created_at "
        "FROM conversations WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall()
    return [
        ConversationTurn(
            id=row["id"],
            case_id=row["case_id"],
            message=row["message"],
            answer=row["answer"],
            grounds=json.loads(row["grounds_json"]),
            source=row["source"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@app.post(
    "/cases/{case_id}/datasets/{dataset_id}/generate-code",
    status_code=200,
    response_model=GeneratedCode,
)
async def generate_code(
    case_id: str,
    dataset_id: str,
    payload: GenerateCodeRequest,
    db=Depends(get_db),
) -> GeneratedCode:
    """Propose the read-only computation that would answer a question.

    The dataset's own profile - its columns, types and nulls - goes to the
    generator alongside the question, and what comes back is a proposal: the
    code, what it does, and the columns it reads. The LLM writes it when it is
    configured and degrades to a deterministic proposal of the same structure on
    any failure - unavailable, malformed, not read-only, or reading a column the
    dataset does not have - so a proposal is always returned and `source` says
    which engine wrote it.

    Generation is stateless by design (P3-AI-013): nothing is persisted, and
    nothing runs until a human POSTs the code to the runs endpoint - the only
    path that persists a run, which keeps the human in charge of what executes.
    """
    _require_dataset(db, case_id, dataset_id)

    profile_row = db.execute(
        "SELECT rows, columns_json, stats_json FROM profiles WHERE dataset_id = ?",
        (dataset_id,),
    ).fetchone()
    # Without a profile there is nothing structural to generate from, so the
    # call names the missing step rather than writing code against an unknown
    # dataset.
    if profile_row is None:
        raise HTTPException(
            status_code=400,
            detail="profile the dataset before generating code",
        )
    profile = {
        "rows": profile_row["rows"],
        "columns": json.loads(profile_row["columns_json"]),
        "stats": json.loads(profile_row["stats_json"]),
    }

    proposal, source = create_code_module(
        question=payload.question, profile=profile, kind=payload.kind
    )
    return GeneratedCode(
        dataset_id=dataset_id,
        case_id=case_id,
        kind=proposal["kind"],
        code=proposal["code"],
        explanation=proposal["explanation"],
        columns_used=proposal.get("columns_used", []),
        source=source,
    )


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


@app.get(
    "/cases/{case_id}/history",
    response_model=CaseHistory,
)
async def get_case_history(case_id: str, db=Depends(get_db)) -> CaseHistory:
    """Everything that happened in a case, in order (P3-CASE-007).

    A read-side projection: the timeline is derived from each artifact's own
    timestamp, so it cannot drift from the persisted rows. A just-created case
    has a single event; validation has no timestamp of its own, so a finding's
    status rides along as its event's detail.
    """
    try:
        history = build_case_history(db, case_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="case not found")
    return CaseHistory(**history)


@app.post(
    "/cases/{case_id}/template",
    status_code=201,
    response_model=Template,
)
async def promote_template(
    case_id: str,
    payload: TemplateCreate,
    db=Depends(get_db),
) -> Template:
    """Promote a case into a reusable template (P3-CASE-007).

    The template keeps the case's question and dataset label - the skeleton a
    new case starts from - and nothing else: data, runs and findings stay with
    the case. Templates are not case children, so outliving their source case
    is the point.
    """
    case = db.execute(
        "SELECT id, question, dataset FROM cases WHERE id = ?", (case_id,)
    ).fetchone()
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")

    name = (payload.name or case["question"]).strip()
    if not name:
        raise HTTPException(status_code=400, detail="name must not be empty")

    template = Template(
        id=str(uuid4()),
        name=name,
        question=case["question"],
        dataset=case["dataset"],
        created_at=datetime.now(timezone.utc),
    )
    db.execute(
        "INSERT INTO templates (id, name, question, dataset, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (template.id, template.name, template.question, template.dataset,
         template.created_at.isoformat()),
    )
    return template


@app.get("/templates", response_model=list[Template])
async def list_templates(db=Depends(get_db)) -> list[Template]:
    """List every saved template, newest first (P3-CASE-007)."""
    rows = db.execute(
        "SELECT id, name, question, dataset, created_at FROM templates "
        "ORDER BY created_at DESC"
    ).fetchall()
    return [
        Template(
            id=row["id"],
            name=row["name"],
            question=row["question"],
            dataset=row["dataset"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@app.post("/cases/from-template", status_code=201, response_model=Case)
async def create_case_from_template(
    payload: CaseFromTemplate,
    db=Depends(get_db),
) -> Case:
    """Start a new case from a saved template (P3-CASE-007).

    The template's question and dataset label seed the case; either may be
    overridden inline. Only the skeleton is copied - no data, runs or findings -
    so every case from a template starts clean.
    """
    template = db.execute(
        "SELECT id, name, question, dataset FROM templates WHERE id = ?",
        (payload.template_id,),
    ).fetchone()
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")

    question = payload.question if payload.question is not None else template["question"]
    dataset = payload.dataset if payload.dataset is not None else template["dataset"]
    return _insert_case(db, question, dataset)


@app.delete("/templates/{template_id}", status_code=204)
async def delete_template(template_id: str, db=Depends(get_db)) -> None:
    """Remove a template. Cases created from it are unaffected (P3-CASE-007)."""
    row = db.execute("SELECT 1 FROM templates WHERE id = ?", (template_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="template not found")
    db.execute("DELETE FROM templates WHERE id = ?", (template_id,))
