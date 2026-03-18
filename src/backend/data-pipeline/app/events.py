"""Event consumer for the data pipeline — subscribes to crawl output events."""

import logging

from shared.events import EventBus, Exchanges
from app.processor import DataProcessor

logger = logging.getLogger(__name__)


async def start_consumer(processor: DataProcessor):
    """Subscribe to crawl output events and process them."""

    async def on_job_discovered(data: dict):
        # Skip already-processed jobs (re-published for AI analysis)
        if "job_id" in data and "content_hash" not in data:
            logger.debug("Skipping re-published job: %s", data.get("job_id"))
            return
        logger.info("Processing crawled item: type=%s source=%s title=%s",
                     data.get("item_type"), data.get("source"), data.get("title", "")[:60])
        item_type = data.get("item_type", "job")
        if item_type == "job":
            await processor.process_job(data)
        elif item_type == "signal":
            await processor.process_signal(data)

    await processor.event_bus.subscribe(
        Exchanges.JOB_DISCOVERED,
        "data-pipeline-queue",
        on_job_discovered,
    )

    # Also subscribe to signal events
    async def on_signal_detected(data: dict):
        await processor.process_signal(data)

    try:
        await processor.event_bus.subscribe(
            "signal.detected",
            "data-pipeline-signals-queue",
            on_signal_detected,
        )
    except Exception:
        logger.info("signal.detected exchange not yet created, will be created on first publish")

    logger.info("Data pipeline event consumer started")
