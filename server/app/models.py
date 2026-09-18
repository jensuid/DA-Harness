"""Request/response models for Analysis Cases, datasets, profiles, and runs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CaseCreate(BaseModel):
    question: str
    dataset: str


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
    profiled_at: datetime


class RunCreate(BaseModel):
    sql: str


class Run(BaseModel):
    id: str
    case_id: str
    dataset_id: str
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    executed_at: datetime


class RunSummary(BaseModel):
    id: str
    case_id: str
    dataset_id: str
    sql: str
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
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    dataset_filename: str


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
