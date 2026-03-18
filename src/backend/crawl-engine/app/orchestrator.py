"""Distributed crawl orchestrator — manages the crawling queue and workers."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db_session
from shared.models import CrawlerSource, CrawlQueueItem, CrawlLog
from shared.events import EventBus, Exchanges

from app.config import settings
from app.crawlers.http_crawler import HttpCrawler
from app.crawlers.playwright_crawler import PlaywrightCrawler
from app.crawlers.signal_crawler import SignalCrawler
from app.crawlers.github_crawler import GitHubCrawler
from app.crawlers.reddit_crawler import RedditCrawler

logger = logging.getLogger(__name__)


CRAWLER_MAP = {
    "http": HttpCrawler,
    "browser": PlaywrightCrawler,
    "signal": SignalCrawler,
    "github": GitHubCrawler,
    "reddit": RedditCrawler,
}


class CrawlOrchestrator:
    """Manages distributed crawling: schedules, dispatches, and collects results."""

    def __init__(self):
        self.event_bus = EventBus(settings.rabbitmq_url)
        self._crawlers = {}
        self._running = False
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_crawlers)

    def _get_crawler(self, source_type: str):
        if source_type not in self._crawlers:
            cls = CRAWLER_MAP.get(source_type, HttpCrawler)
            self._crawlers[source_type] = cls()
        return self._crawlers[source_type]

    async def start(self):
        """Start the crawl orchestrator loop."""
        await self.event_bus.connect()
        self._running = True
        logger.info("Crawl orchestrator started")

        while self._running:
            try:
                await self._schedule_due_sources()
                await self._process_queue_batch()
                await asyncio.sleep(10)  # Check queue every 10s
            except Exception as e:
                logger.error(f"Orchestrator loop error: {e}")
                await asyncio.sleep(30)

    async def stop(self):
        self._running = False
        for crawler in self._crawlers.values():
            if hasattr(crawler, "close"):
                await crawler.close()

    async def _schedule_due_sources(self):
        """Check crawler_sources for those due for recrawling and enqueue them."""
        async for db in get_db_session():
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(CrawlerSource).where(
                    CrawlerSource.is_enabled == True,
                    (CrawlerSource.last_crawled_at == None) |
                    (CrawlerSource.last_crawled_at < now - timedelta(minutes=1))
                )
            )
            sources = result.scalars().all()

            for source in sources:
                last = source.last_crawled_at
                if last:
                    # Ensure both are aware for comparison
                    if last.tzinfo is None:
                        last = last.replace(tzinfo=timezone.utc)
                    if (now - last).total_seconds() < source.crawl_frequency_minutes * 60:
                        continue

                # Check if already queued
                existing = await db.execute(
                    select(CrawlQueueItem).where(
                        CrawlQueueItem.source_id == source.id,
                        CrawlQueueItem.status.in_(["pending", "running"]),
                    )
                )
                if existing.scalars().first():
                    continue

                queue_item = CrawlQueueItem(
                    source_id=source.id,
                    url=source.url_pattern,
                    priority=source.priority,
                    status="pending",
                )
                db.add(queue_item)
                logger.info(f"Enqueued crawl: {source.name} (priority={source.priority})")

            await db.commit()

    async def _process_queue_batch(self):
        """Pick up pending queue items and crawl them concurrently."""
        async for db in get_db_session():
            result = await db.execute(
                select(CrawlQueueItem).where(
                    CrawlQueueItem.status == "pending",
                    CrawlQueueItem.scheduled_at <= datetime.now(timezone.utc),
                ).order_by(
                    CrawlQueueItem.priority.desc(),
                    CrawlQueueItem.scheduled_at,
                ).limit(settings.max_concurrent_crawlers)
            )
            items = result.scalars().all()

            if not items:
                return

            tasks = [self._execute_crawl(item) for item in items]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_crawl(self, queue_item: CrawlQueueItem):
        """Execute a single crawl task with concurrency control."""
        async with self._semaphore:
            async for db in get_db_session():
                # Claim the task
                await db.execute(
                    update(CrawlQueueItem).where(
                        CrawlQueueItem.id == queue_item.id,
                    ).values(
                        status="running",
                        worker_id=settings.worker_id,
                        started_at=datetime.now(timezone.utc),
                        attempts=CrawlQueueItem.attempts + 1,
                    )
                )
                await db.commit()

                # Get source config
                source_result = await db.execute(
                    select(CrawlerSource).where(CrawlerSource.id == queue_item.source_id)
                )
                source = source_result.scalar_one_or_none()
                source_type = source.source_type if source else "http"
                source_name = source.name if source else "unknown"

                # Create crawl log
                crawl_log = CrawlLog(
                    source=source_name,
                    started_at=datetime.now(timezone.utc),
                    status="running",
                )
                db.add(crawl_log)
                await db.commit()
                await db.refresh(crawl_log)

                try:
                    crawler = self._get_crawler(source_type)
                    await asyncio.sleep(settings.request_delay_seconds)

                    items = await crawler.crawl(
                        queue_item.url,
                        source_name=source_name,
                    )

                    # Publish each item to the data pipeline
                    for item in items:
                        await self.event_bus.publish(
                            Exchanges.JOB_DISCOVERED if item.item_type == "job" else "signal.detected",
                            {
                                "item_type": item.item_type,
                                "source": item.source,
                                "url": item.url,
                                "title": item.title,
                                "extracted_data": item.extracted_data,
                                "external_id": item.external_id,
                                "content_hash": item.content_hash,
                                "date_posted": item.date_posted.isoformat() if item.date_posted else None,
                            },
                        )

                    # Update queue item
                    await db.execute(
                        update(CrawlQueueItem).where(
                            CrawlQueueItem.id == queue_item.id,
                        ).values(
                            status="completed",
                            completed_at=datetime.now(timezone.utc),
                            result_data={"items_found": len(items)},
                        )
                    )

                    # Update crawl log
                    crawl_log.completed_at = datetime.now(timezone.utc)
                    crawl_log.jobs_found = len([i for i in items if i.item_type == "job"])
                    crawl_log.status = "completed"

                    # Update source last_crawled_at
                    if source:
                        source.last_crawled_at = datetime.now(timezone.utc)

                    await db.commit()
                    logger.info(f"Crawl completed: {source_name} — {len(items)} items found")

                except Exception as e:
                    logger.error(f"Crawl failed for {source_name}: {e}")

                    if queue_item.attempts >= queue_item.max_attempts:
                        status = "failed"
                    else:
                        status = "retrying"

                    await db.execute(
                        update(CrawlQueueItem).where(
                            CrawlQueueItem.id == queue_item.id,
                        ).values(
                            status=status,
                            error_message=str(e)[:500],
                            scheduled_at=datetime.now(timezone.utc) + timedelta(minutes=5) if status == "retrying" else None,
                        )
                    )

                    crawl_log.completed_at = datetime.now(timezone.utc)
                    crawl_log.status = "failed"
                    crawl_log.error_message = str(e)[:500]

                    await db.commit()

    async def trigger_crawl(self, source_name: str) -> dict:
        """Manually trigger a crawl for a specific source."""
        async for db in get_db_session():
            result = await db.execute(
                select(CrawlerSource).where(CrawlerSource.name == source_name)
            )
            source = result.scalar_one_or_none()
            if not source:
                return {"error": f"Source '{source_name}' not found"}

            queue_item = CrawlQueueItem(
                source_id=source.id,
                url=source.url_pattern,
                priority=10,  # High priority for manual triggers
                status="pending",
            )
            db.add(queue_item)
            await db.commit()
            return {"status": "queued", "source": source_name, "queue_id": str(queue_item.id)}

    async def get_stats(self) -> dict:
        """Get crawling statistics."""
        async for db in get_db_session():
            total_sources = await db.scalar(select(func.count(CrawlerSource.id)))
            active = await db.scalar(
                select(func.count(CrawlerSource.id)).where(CrawlerSource.is_enabled == True)
            )
            queue_pending = await db.scalar(
                select(func.count(CrawlQueueItem.id)).where(CrawlQueueItem.status == "pending")
            )
            queue_running = await db.scalar(
                select(func.count(CrawlQueueItem.id)).where(CrawlQueueItem.status == "running")
            )
            return {
                "total_sources": total_sources or 0,
                "active_sources": active or 0,
                "queue_pending": queue_pending or 0,
                "queue_running": queue_running or 0,
                "worker_id": settings.worker_id,
                "max_concurrent": settings.max_concurrent_crawlers,
            }
