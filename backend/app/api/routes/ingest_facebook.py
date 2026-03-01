"""Batch ingest endpoint for Facebook group archive search results."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.core.url_utils import hash_url, is_valid_fb_post_url, normalize_fb_url
from app.db.models import CandidateStory
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ingest/facebook",
    tags=["ingest-facebook"],
    dependencies=[Depends(require_admin)],
)


# ------------------------------------------------------------------ #
#  Request / Response schemas                                         #
# ------------------------------------------------------------------ #

class FbSearchItem(BaseModel):
    source_url: str
    title: str | None = None
    excerpt: str | None = None


class FbSearchResultsPayload(BaseModel):
    group_name: str | None = None
    query: str | None = None
    captured_at: str | None = None
    items: list[FbSearchItem] = Field(..., min_length=1)


class FbIngestResponse(BaseModel):
    inserted: int
    duplicates: int
    invalid: int


# ------------------------------------------------------------------ #
#  Endpoint                                                           #
# ------------------------------------------------------------------ #

@router.post("/search-results", response_model=FbIngestResponse)
def ingest_fb_search_results(
    payload: FbSearchResultsPayload,
    db: Session = Depends(get_db),
) -> FbIngestResponse:
    """Receive captured Facebook group search results and store as CandidateStory rows."""

    inserted = 0
    duplicates = 0
    invalid = 0

    # Parse captured_at once for all items
    captured_at_str = payload.captured_at
    if not captured_at_str:
        captured_at_str = datetime.now(timezone.utc).isoformat()

    meta = {
        "fb_group_name": payload.group_name,
        "fb_query": payload.query,
        "captured_at": captured_at_str,
        "capture_method": "extension",
    }

    for item in payload.items:
        # Validate URL pattern
        if not is_valid_fb_post_url(item.source_url):
            logger.warning("Invalid FB URL skipped: %s", item.source_url[:120])
            invalid += 1
            continue

        # Normalize and hash
        normalized_url = normalize_fb_url(item.source_url)
        source_id = hash_url(normalized_url)

        # Cap excerpt at 500 chars
        excerpt = (item.excerpt or "")[:500] or None

        candidate = CandidateStory(
            source_type="facebook_group_archive",
            source_id=source_id,
            source_url=normalized_url,
            title=item.title,
            raw_text=None,
            excerpt=excerpt,
            created_at_source=None,
            language=None,
            prefilter_flags=meta,
            status="new",
        )

        try:
            db.add(candidate)
            db.flush()
            inserted += 1
        except IntegrityError:
            db.rollback()
            duplicates += 1

    if inserted:
        db.commit()

    logger.info(
        "FB archive ingest: inserted=%d, duplicates=%d, invalid=%d",
        inserted, duplicates, invalid,
    )

    return FbIngestResponse(inserted=inserted, duplicates=duplicates, invalid=invalid)
