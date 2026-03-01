"""Pydantic schemas for CandidateStory endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CandidateOut(BaseModel):
    id: UUID
    source_type: str
    source_id: str
    source_url: str
    title: str | None = None
    excerpt: str | None = None
    created_at_source: datetime | None = None
    ingested_at: datetime
    language: str | None = None
    prefilter_flags: dict = {}
    story_score: float | None = None
    score_components: dict = {}
    category_pred: str | None = None
    category_confidence: float | None = None
    entities: dict = {}
    summary_draft: str | None = None
    tags_pred: list[str] | None = None
    status: str
    reviewer_notes: str | None = None

    model_config = {"from_attributes": True}


class CandidateListOut(BaseModel):
    items: list[CandidateOut]
    total: int
    limit: int
    offset: int


class RejectBody(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)
