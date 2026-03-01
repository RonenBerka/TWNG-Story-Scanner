"""Admin endpoints for triggering async tasks."""

from celery.result import AsyncResult
from fastapi import APIRouter, Depends

from app.core.security import require_admin
from app.worker.celery_app import celery_app
from app.worker.tasks import ingest_reddit_task, process_candidates_task

router = APIRouter(
    prefix="/admin/tasks",
    tags=["tasks"],
    dependencies=[Depends(require_admin)],
)


@router.post("/ingest-reddit")
async def trigger_ingest(limit: int = 20) -> dict:
    """Enqueue Reddit ingest task."""
    result = ingest_reddit_task.delay(limit_per_query=limit)
    return {"task_id": result.id, "status": "queued", "task": "ingest_reddit"}


@router.post("/process-candidates")
async def trigger_process() -> dict:
    """Enqueue candidate scoring task."""
    result = process_candidates_task.delay()
    return {"task_id": result.id, "status": "queued", "task": "process_candidates"}


@router.get("/status/{task_id}")
async def task_status(task_id: str) -> dict:
    """Check task status by ID."""
    result = AsyncResult(task_id, app=celery_app)
    response = {"task_id": task_id, "status": result.status}
    if result.ready():
        response["result"] = result.result
    return response
