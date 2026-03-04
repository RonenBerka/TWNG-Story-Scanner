"""Public scan endpoint — no Docker-backend auth required.

The frontend uses Supabase auth and can't easily get a Docker-backend JWT.
This endpoint runs the Reddit ingest locally (bypassing Reddit's cloud IP
blocks) then syncs new rows to Supabase so the frontend can read them.
"""

import json
import logging
import os
import urllib.request
import urllib.error
import time

from fastapi import APIRouter

from app.collectors.reddit_collector import ingest_reddit
from app.db.session import SessionLocal
from app.db.models import CandidateStory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public", tags=["public"])

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://wtqylorvckigssjlurwj.supabase.co",
)
SUPABASE_ANON_KEY = os.environ.get(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0cXlsb3J2Y2tpZ3Nzamx1cndqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTczNjEyNDMsImV4cCI6MjA3MjkzNzI0M30.bkD-pSp4cc3B_bj-pAjjYGj_GCs6Sepsj6G6fUwgPmo",
)


def _sync_to_supabase(rows: list[dict]) -> dict:
    """Push candidate_stories rows to Supabase via PostgREST."""
    if not rows:
        return {"synced": 0, "sync_errors": 0}

    synced = 0
    sync_errors = 0
    batch_size = 50

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        data = json.dumps(batch).encode("utf-8")

        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/candidate_stories?on_conflict=source_type,source_id",
            data=data,
            headers={
                "Content-Type": "application/json",
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                "Prefer": "resolution=ignore-duplicates,return=minimal",
            },
            method="POST",
        )

        try:
            urllib.request.urlopen(req)
            synced += len(batch)
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            logger.warning("Supabase sync error batch %d: %s %s", i, e.code, body[:200])
            sync_errors += 1

        time.sleep(0.1)

    return {"synced": synced, "sync_errors": sync_errors}


def _row_to_dict(row: CandidateStory) -> dict:
    """Convert a SQLAlchemy CandidateStory to a dict for Supabase."""
    return {
        "id": str(row.id),
        "source_type": row.source_type,
        "source_id": row.source_id,
        "source_url": row.source_url,
        "title": row.title,
        "raw_text": row.raw_text,
        "excerpt": row.excerpt,
        "created_at_source": row.created_at_source.isoformat() if row.created_at_source else None,
        "ingested_at": row.ingested_at.isoformat() if row.ingested_at else None,
        "language": row.language,
        "prefilter_flags": row.prefilter_flags or {},
        "story_score": row.story_score,
        "score_components": row.score_components or {},
        "category_pred": row.category_pred,
        "category_confidence": row.category_confidence,
        "entities": row.entities or {},
        "summary_draft": row.summary_draft,
        "tags_pred": row.tags_pred,
        "status": row.status,
        "reviewer_notes": row.reviewer_notes,
    }


@router.post("/scan-reddit")
async def scan_reddit(limit: int = 20) -> dict:
    """
    1. Ingest Reddit posts into local Docker PG
    2. Sync newly ingested rows to Supabase PG
    """
    # Step 1: Run the existing Reddit ingest (writes to Docker PG)
    stats = ingest_reddit(limit_per_query=limit)

    # Step 2: Read recent rows from Docker PG that need syncing
    # We sync all rows ingested in the last 10 minutes to catch new ones
    db = SessionLocal()
    try:
        from sqlalchemy import text

        recent = (
            db.query(CandidateStory)
            .filter(
                CandidateStory.ingested_at
                >= text("NOW() - INTERVAL '10 minutes'")
            )
            .all()
        )
        rows = [_row_to_dict(r) for r in recent]
    finally:
        db.close()

    # Step 3: Push to Supabase
    sync_stats = _sync_to_supabase(rows)

    return {
        "inserted": stats["inserted"],
        "skipped": stats["skipped"],
        "errors": stats["errors"],
        **sync_stats,
    }
