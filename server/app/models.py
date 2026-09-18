"""Request/response models for Analysis Cases."""

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
