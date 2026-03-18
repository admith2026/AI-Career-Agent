"""Decision Engine event consumer — reacts to analyzed jobs."""

import logging
from uuid import UUID

from shared.events import EventBus, Exchanges
from shared.database import get_db_session
from app.engine import DecisionEngine

logger = logging.getLogger(__name__)


async def start_consumer(engine: DecisionEngine):
    """Subscribe to JOB_ANALYZED and auto-evaluate new jobs."""

    async def on_job_analyzed(data: dict):
        job_id = data.get("job_id")
        user_id = data.get("user_id")
        if not job_id or not user_id:
            return
        try:
            async for db in get_db_session():
                await engine.evaluate_job(UUID(job_id), UUID(user_id), db)
        except Exception:
            logger.exception("Failed to evaluate job %s for user %s", job_id, user_id)

    try:
        await engine.event_bus.subscribe(
            Exchanges.JOB_ANALYZED,
            "decision-engine-queue",
            on_job_analyzed,
        )
        logger.info("Decision engine event consumer started")
    except Exception:
        logger.info("JOB_ANALYZED exchange not ready yet")
