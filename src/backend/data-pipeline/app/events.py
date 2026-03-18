"""Event consumer for the data pipeline — subscribes to crawl output events."""

import json
import logging

from shared.events import EventBus, Exchanges
from app.processor import DataProcessor

logger = logging.getLogger(__name__)


async def start_consumer(processor: DataProcessor):
    """Subscribe to crawl output events and process them."""

    async def on_job_discovered(message):
        async with message.process():
            data = json.loads(message.body.decode())
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
    async def on_signal_detected(message):
        async with message.process():
            data = json.loads(message.body.decode())
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
