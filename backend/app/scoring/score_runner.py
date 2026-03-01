"""Score runner — batch-score unscored CandidateStory rows."""

import logging

from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import CandidateStory
from app.scoring.story_score import story_score

logger = logging.getLogger(__name__)


def score_unscored_candidates() -> dict:
    """
    Query all CandidateStory rows where story_score IS NULL,
    compute scores, and persist results.

    Returns:
        {"scored": int, "errors": int}
    """
    scored = 0
    errors = 0

    db = SessionLocal()
    try:
        candidates = db.execute(
            select(CandidateStory).where(CandidateStory.story_score.is_(None))
        ).scalars().all()

        logger.info("Found %d unscored candidates", len(candidates))

        for candidate in candidates:
            try:
                text = candidate.raw_text or ""
                score, components, flags = story_score(text)

                candidate.story_score = score
                candidate.score_components = components
                candidate.prefilter_flags = flags
                db.commit()
                scored += 1
                logger.info(
                    "Scored candidate %s → %.4f", candidate.id, score
                )
            except Exception:
                db.rollback()
                errors += 1
                logger.exception(
                    "Error scoring candidate %s", candidate.id
                )
    finally:
        db.close()

    return {"scored": scored, "errors": errors}
