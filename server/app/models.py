"""Request/response models for Analysis Cases, datasets, profiles, and runs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CaseCreate(BaseModel):
    question: str
    dataset: str


class CaseUpdate(BaseModel):
    """Rename a case; either field may be omitted to leave it unchanged."""
    question: str | None = None
    dataset: str | None = None


class Case(BaseModel):
    id: str
    question: str
    dataset: str
    created_at: datetime
    updated_at: datetime


class Dataset(BaseModel):
    id: str
    case_id: str
    filename: str
    stored_path: str
    format: str
    created_at: datetime


class Profile(BaseModel):
    dataset_id: str
    rows: int
    columns: list[str]
    stats: dict
    duplicate_rows: int
    profiled_at: datetime


class RunCreate(BaseModel):
    sql: str


class PythonRunCreate(BaseModel):
    code: str


# A run's source is the query or the script, never both; `kind` says which.
RUN_KINDS = ("sql", "python")


class Run(BaseModel):
    id: str
    case_id: str
    dataset_id: str
    kind: str = "sql"
    sql: str | None = None
    code: str | None = None
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    executed_at: datetime


class RunSummary(BaseModel):
    id: str
    case_id: str
    dataset_id: str
    kind: str = "sql"
    sql: str | None = None
    code: str | None = None
    row_count: int
    truncated: bool
    executed_at: datetime


# Per the Master Specification quality model: a finding's support is a property
# of the evidence, not of AI confidence.
VALIDATION_STATUSES = (
    "supported",
    "partially_supported",
    "insufficient_evidence",
    "contradicted",
    "not_evaluated",
)


class FindingCreate(BaseModel):
    run_id: str
    statement: str
    interpretation: str | None = None
    caveat: str | None = None


class Finding(BaseModel):
    id: str
    case_id: str
    run_id: str
    statement: str
    interpretation: str | None
    caveat: str | None
    validation_status: str
    created_at: datetime


class EvidenceChain(BaseModel):
    """The trust chain a reviewer walks to verify a finding."""
    finding: Finding
    kind: str = "sql"
    sql: str | None = None
    code: str | None = None
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    dataset_filename: str


class ChartCreate(BaseModel):
    kind: str
    x: str
    y: str
    series: str | None = None
    title: str = ""


class Chart(BaseModel):
    id: str
    case_id: str
    run_id: str
    kind: str
    x: str
    y: str
    series: str | None
    title: str
    stored_path: str
    width: int
    height: int
    created_at: datetime


class ChartSummary(BaseModel):
    """Chart metadata without the image bytes."""
    id: str
    case_id: str
    run_id: str
    kind: str
    x: str
    y: str
    series: str | None
    title: str
    created_at: datetime


class Plan(BaseModel):
    """A structured analysis plan, persisted against a case and dataset."""
    id: str
    case_id: str
    dataset_id: str
    question: str
    plan: dict
    source: str
    created_at: datetime


class PlanSummary(BaseModel):
    """Plan metadata without the plan body."""
    id: str
    case_id: str
    dataset_id: str
    question: str
    source: str
    created_at: datetime


class ValidationCheck(BaseModel):
    """One check from the validation pass."""
    name: str
    passed: bool
    detail: str


class ValidationResult(BaseModel):
    finding_id: str
    run_id: str
    status: str
    checks: list[ValidationCheck]
    validated_at: datetime
