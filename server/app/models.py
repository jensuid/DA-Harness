"""Request/response models for Analysis Cases, datasets, and profiles."""

from datetime import datetime

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
