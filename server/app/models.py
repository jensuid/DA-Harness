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
