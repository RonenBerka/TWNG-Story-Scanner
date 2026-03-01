"""TWNGStoryRecord endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.models import TWNGStoryRecord
from app.db.session import get_db
from app.schemas.records import RecordListOut

router = APIRouter(prefix="/records", tags=["records"], dependencies=[Depends(require_admin)])


@router.get("", response_model=RecordListOut)
def list_records(
    category: str | None = Query(None),
    visibility: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> RecordListOut:
    query = db.query(TWNGStoryRecord)

    if category is not None:
        query = query.filter(TWNGStoryRecord.category == category)
    if visibility is not None:
        query = query.filter(TWNGStoryRecord.visibility == visibility)

    total = query.count()
    items = (
        query.order_by(TWNGStoryRecord.published_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return RecordListOut(items=items, total=total, limit=limit, offset=offset)
