"""Enrichment runner — enrich candidates above score threshold."""

import logging
import os

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.db.models import CandidateStory
from app.db.session import SessionLocal
from app.enrichment.provider import EnrichmentProvider

logger = logging.getLogger(__name__)

SCORE_THRESHOLD = float(os.environ.get("ENRICHMENT_SCORE_THRESHOLD", "0.65"))


def _get_provider() -> EnrichmentProvider:
    """Return OpenAI provider if key exists, else LocalProvider."""
    if os.environ.get("OPENAI_API_KEY"):
        from app.enrichment.openai_provider import OpenAIProvider

        logger.info("Using OpenAI enrichment provider")
        return OpenAIProvider()
    else:
        from app.enrichment.local_provider import LocalProvider

        logger.info("Using Local enrichment provider (no OPENAI_API_KEY)")
        return LocalProvider()


def enrich_candidates() -> dict:
    """
    Enrich candidates where:
    - story_score >= threshold
    - summary_draft is NULL (not yet enriched)

    Returns: {"enriched": int, "errors": int, "provider": str}
    """
    provider = _get_provider()
    provider_name = type(provider).__name__

    enriched = 0
    errors = 0

    db: Session = SessionLocal()
    try:
        candidates = db.execute(
            select(CandidateStory).where(
                and_(
                    CandidateStory.story_score >= SCORE_THRESHOLD,
                    CandidateStory.summary_draft.is_(None),
                )
            )
        ).scalars().all()

        logger.info(
            "Found %d candidates above threshold %.2f needing enrichment",
            len(candidates),
            SCORE_THRESHOLD,
        )

        for candidate in candidates:
            try:
                text = candidate.raw_text or candidate.title or ""
                lang = candidate.language or "en"

                # Run all enrichment steps
                summary = provider.summarize(text, lang)
                category, confidence = provider.classify_category(text, lang)
                tags = provider.extract_tags(text, lang)
                entities = provider.extract_entities(text, lang)

                # Update candidate
                candidate.summary_draft = summary
                candidate.category_pred = category
                candidate.category_confidence = confidence
                candidate.tags_pred = tags
                candidate.entities = entities

                db.commit()
                enriched += 1
                logger.debug(
                    "Enriched %s → category=%s, tags=%s",
                    candidate.id, category, tags,
                )

            except Exception:
                db.rollback()
                errors += 1
                logger.exception("Error enriching candidate %s", candidate.id)

    finally:
        db.close()

    logger.info(
        "Enrichment complete (provider=%s) — enriched: %d, errors: %d",
        provider_name, enriched, errors,
    )
    return {"enriched": enriched, "errors": errors, "provider": provider_name}
