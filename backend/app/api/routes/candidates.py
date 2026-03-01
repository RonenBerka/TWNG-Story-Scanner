"""Candidate curation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.models import AuditLog, CandidateStory, TWNGStoryRecord
from app.db.session import get_db
from app.schemas.candidates import CandidateListOut, CandidateOut, RejectBody

router = APIRouter(prefix="/candidates", tags=["candidates"], dependencies=[Depends(require_admin)])


@router.get("", response_model=CandidateListOut)
def list_candidates(
    status: str = Query("new"),
    min_score: float | None = Query(None),
    source: str | None = Query(None),
    lang: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> CandidateListOut:
    query = db.query(CandidateStory).filter(CandidateStory.status == status)

    if min_score is not None:
        query = query.filter(CandidateStory.story_score >= min_score)
    if source is not None:
        query = query.filter(CandidateStory.source_type == source)
    if lang is not None:
        query = query.filter(CandidateStory.language == lang)
    if q is not None:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                CandidateStory.title.ilike(pattern),
                CandidateStory.excerpt.ilike(pattern),
                CandidateStory.summary_draft.ilike(pattern),
            )
        )

    total = query.count()
    items = (
        query.order_by(CandidateStory.ingested_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return CandidateListOut(items=items, total=total, limit=limit, offset=offset)


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
) -> CandidateOut:
    candidate = db.get(CandidateStory, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("/{candidate_id}/approve", response_model=CandidateOut)
def approve_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
) -> CandidateOut:
    candidate = db.get(CandidateStory, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status == "approved":
        raise HTTPException(status_code=409, detail="Candidate already approved")

    # Create TWNGStoryRecord from candidate
    record = TWNGStoryRecord(
        candidate_id=candidate.id,
        source_url=candidate.source_url,
        source_type=candidate.source_type,
        summary_final=candidate.summary_draft or candidate.excerpt or candidate.title or "",
        category=candidate.category_pred,
        tags=candidate.tags_pred,
        language=candidate.language,
    )
    db.add(record)

    candidate.status = "approved"

    # Audit log
    db.add(
        AuditLog(
            actor="admin",
            action="approve",
            target_type="candidate_story",
            target_id=candidate.id,
        )
    )

    db.commit()
    db.refresh(candidate)
    return candidate


@router.post("/{candidate_id}/reject", response_model=CandidateOut)
def reject_candidate(
    candidate_id: UUID,
    body: RejectBody | None = None,
    db: Session = Depends(get_db),
) -> CandidateOut:
    candidate = db.get(CandidateStory, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status == "rejected":
        raise HTTPException(status_code=409, detail="Candidate already rejected")

    candidate.status = "rejected"
    if body and body.reason:
        candidate.reviewer_notes = body.reason

    # Audit log
    db.add(
        AuditLog(
            actor="admin",
            action="reject",
            target_type="candidate_story",
            target_id=candidate.id,
            details={"reason": body.reason if body else None},
        )
    )

    db.commit()
    db.refresh(candidate)
    return candidate
