"""Background scheduler that triggers crawl cycles on an interval."""

import asyncio
import logging

from shared.database import async_session_factory
from shared.events import EventBus

from .config import settings
from .orchestrator import run_crawl_cycle

logger = logging.getLogger(__name__)


async def crawl_scheduler(event_bus: EventBus) -> None:
    """Run crawl cycles forever on the configured interval."""
    interval = settings.interval_hours * 3600
    logger.info("Crawl scheduler started — interval=%dh", settings.interval_hours)

    while True:
        try:
            async with async_session_factory() as db:
                await run_crawl_cycle(db, event_bus)
        except Exception:
            logger.exception("Crawl cycle error")
        await asyncio.sleep(interval)
