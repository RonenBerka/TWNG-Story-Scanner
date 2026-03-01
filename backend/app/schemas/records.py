"""Pydantic schemas for TWNGStoryRecord endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RecordOut(BaseModel):
    id: UUID
    candidate_id: UUID | None = None
    source_url: str
    source_type: str
    credit_text: str | None = None
    summary_final: str
    category: str | None = None
    tags: list[str] | None = None
    language: str | None = None
    published_at: datetime
    visibility: str
    takedown_status: str

    model_config = {"from_attributes": True}


class RecordListOut(BaseModel):
    items: list[RecordOut]
    total: int
    limit: int
    offset: int
