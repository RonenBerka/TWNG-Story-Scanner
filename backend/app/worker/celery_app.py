"""Celery application configuration."""

import os

from celery import Celery

broker_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "twng_worker",
    broker=broker_url,
    backend=broker_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    # Serialisation
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Retry defaults
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Result expiry (1 hour)
    result_expires=3600,
)
