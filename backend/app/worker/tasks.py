"""Celery tasks — ingest and scoring."""

import logging

from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="ingest_reddit",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def ingest_reddit_task(self, limit_per_query: int = 20) -> dict:
    """Ingest Reddit posts into CandidateStory."""
    logger.info("Starting ingest_reddit_task (limit=%d)", limit_per_query)
    from app.collectors.reddit_collector import ingest_reddit

    stats = ingest_reddit(limit_per_query=limit_per_query)
    logger.info("ingest_reddit_task done: %s", stats)
    return stats


@celery_app.task(
    bind=True,
    name="process_candidates",
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
)
def process_candidates_task(self) -> dict:
    """Score unscored candidates."""
    logger.info("Starting process_candidates_task")
    from app.scoring.score_runner import score_unscored_candidates

    stats = score_unscored_candidates()
    logger.info("process_candidates_task done: %s", stats)
    return stats


@celery_app.task(
    bind=True,
    name="enrich_candidates",
    max_retries=2,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
)
def enrich_candidates_task(self) -> dict:
    """Enrich scored candidates above threshold."""
    logger.info("Starting enrich_candidates_task")
    from app.enrichment.enrich_runner import enrich_candidates

    stats = enrich_candidates()
    logger.info("enrich_candidates_task done: %s", stats)
    return stats
