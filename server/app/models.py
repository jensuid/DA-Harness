"""Request/response models for Analysis Cases and datasets."""

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
