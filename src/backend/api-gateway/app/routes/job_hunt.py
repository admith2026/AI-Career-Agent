"""Job Hunt pipeline — manual trigger endpoint."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from shared.tasks.job_hunt import run_pipeline, run_job_hunt

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Job Hunt"])


class JobHuntRequest(BaseModel):
    query: str = ".net full stack developer remote contract USA"
    async_mode: bool = False


class JobHuntResponse(BaseModel):
    status: str
    fetched: int = 0
    scored: int = 0
    notified: bool = False
    channels: list[str] = []
    top_match: dict | None = None
    task_id: str | None = None


@router.post("/api/run-job-hunt", response_model=JobHuntResponse)
async def trigger_job_hunt(body: JobHuntRequest = JobHuntRequest()):
    """Manually trigger the full job-hunt pipeline.

    - ``async_mode=false`` (default): runs synchronously, returns results.
    - ``async_mode=true``: dispatches to Celery and returns a task ID.
    """
    logger.info("Job hunt triggered via API (query=%s, async=%s)", body.query, body.async_mode)

    if body.async_mode:
        task = run_job_hunt.delay(body.query)
        return JobHuntResponse(status="queued", task_id=task.id)

    result = await run_pipeline(body.query)
    return JobHuntResponse(status="completed", **result)
