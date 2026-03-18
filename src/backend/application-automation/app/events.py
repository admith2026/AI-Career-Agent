"""Event consumer — listens for job.analyzed events and auto-applies if criteria are met."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import async_session_factory
from shared.events import EventBus, Exchanges
from shared.models import User, JobAnalysis

from .config import settings
from .applicant import apply_to_job

logger = logging.getLogger(__name__)


async def _handle_job_analyzed(data: dict, event_bus: EventBus) -> None:
    """If a job scores high enough and user has auto-apply enabled, apply automatically."""
    job_id_str = data.get("job_id")
    if not job_id_str:
        return

    try:
        job_id = UUID(job_id_str)
    except ValueError:
        return

    async with async_session_factory() as db:
        # Check if score meets threshold
        analysis = await db.execute(
            select(JobAnalysis).where(JobAnalysis.job_id == job_id)
        )
        analysis_row = analysis.scalar_one_or_none()
        if not analysis_row or (analysis_row.match_score or 0) < settings.min_score_for_auto_apply:
            return

        # Find users with auto-apply enabled
        users_result = await db.execute(
            select(User).where(User.auto_apply_enabled.is_(True))
        )
        users = users_result.scalars().all()

        for user in users:
            try:
                await apply_to_job(user.id, job_id, db, event_bus)
                logger.info("Auto-applied user %s to job %s", user.id, job_id)
            except ValueError as e:
                logger.info("Skipped auto-apply for user %s: %s", user.id, e)
            except Exception:
                logger.exception("Auto-apply failed for user %s, job %s", user.id, job_id)


async def start_consumer(event_bus: EventBus) -> None:
    """Subscribe to job.analyzed events for auto-apply processing."""
    async def handler(data: dict) -> None:
        await _handle_job_analyzed(data, event_bus)

    await event_bus.subscribe(
        Exchanges.JOB_ANALYZED,
        "application-automation.job-analyzed",
        handler,
    )
    logger.info("Application automation consumer started")
