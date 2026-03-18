"""Crawl orchestrator — runs all crawlers, deduplicates, persists, and publishes events."""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.events import EventBus, Exchanges
from shared.models import Job, CrawlLog

from .config import settings
from .crawlers.base import BaseCrawler, CrawledJob
from .crawlers.remoteok import RemoteOKCrawler
from .crawlers.weworkremotely import WeWorkRemotelyCrawler
from .crawlers.linkedin import LinkedInCrawler
from .crawlers.indeed import IndeedCrawler
from .crawlers.dice import DiceCrawler

logger = logging.getLogger(__name__)


def _build_crawlers() -> list[BaseCrawler]:
    return [
        RemoteOKCrawler(delay_seconds=settings.request_delay_seconds, user_agent=settings.user_agent),
        WeWorkRemotelyCrawler(delay_seconds=settings.request_delay_seconds, user_agent=settings.user_agent),
        LinkedInCrawler(delay_seconds=settings.request_delay_seconds, user_agent=settings.user_agent),
        IndeedCrawler(delay_seconds=settings.request_delay_seconds, user_agent=settings.user_agent),
        DiceCrawler(delay_seconds=settings.request_delay_seconds, user_agent=settings.user_agent),
    ]


async def _run_single_crawler(
    crawler: BaseCrawler, keywords: list[str], semaphore: asyncio.Semaphore
) -> list[CrawledJob]:
    async with semaphore:
        try:
            results = await crawler.crawl(keywords)
            logger.info("%s returned %d jobs", crawler.source, len(results))
            return results
        except Exception:
            logger.exception("Crawler %s failed", crawler.source)
            return []
        finally:
            await crawler.close()


async def run_crawl_cycle(db: AsyncSession, event_bus: EventBus) -> dict:
    """Execute one full crawl cycle across all job boards."""

    crawlers = _build_crawlers()
    semaphore = asyncio.Semaphore(settings.max_concurrent_crawlers)
    keywords = settings.search_keywords

    cycle_start = datetime.now(timezone.utc)
    logger.info("Starting crawl cycle with %d crawlers", len(crawlers))

    # Run crawlers concurrently (bounded by semaphore)
    tasks = [_run_single_crawler(c, keywords, semaphore) for c in crawlers]
    results = await asyncio.gather(*tasks)

    all_jobs: list[CrawledJob] = []
    for batch in results:
        all_jobs.extend(batch)

    # Deduplicate within this batch by (external_id)
    seen: set[str] = set()
    unique_jobs: list[CrawledJob] = []
    for j in all_jobs:
        if j.external_id not in seen:
            seen.add(j.external_id)
            unique_jobs.append(j)

    # Persist new jobs to the database
    new_count = 0
    for cj in unique_jobs:
        exists = await db.execute(
            select(Job).where(Job.external_id == cj.external_id, Job.source == cj.source)
        )
        if exists.scalar_one_or_none():
            continue

        job = Job(
            id=uuid4(),
            external_id=cj.external_id,
            source=cj.source,
            job_title=cj.job_title,
            company_name=cj.company_name,
            vendor_name=cj.vendor_name,
            recruiter_name=cj.recruiter_name,
            recruiter_email=cj.recruiter_email,
            phone_number=cj.phone_number,
            job_description=cj.job_description,
            job_link=cj.job_link,
            salary_or_rate=cj.salary_or_rate,
            location=cj.location,
            is_remote=cj.is_remote,
            contract_type=cj.contract_type,
            date_posted=cj.date_posted,
            date_discovered=datetime.now(timezone.utc),
            raw_data=cj.raw_data,
        )
        db.add(job)
        new_count += 1

        # Publish discovery event
        await event_bus.publish(
            Exchanges.JOB_DISCOVERED,
            {
                "job_id": str(job.id),
                "source": cj.source,
                "job_title": cj.job_title,
                "company_name": cj.company_name,
                "job_link": cj.job_link,
                "job_description": cj.job_description or "",
            },
        )

    await db.commit()

    # Write crawl log
    cycle_end = datetime.now(timezone.utc)
    duration = (cycle_end - cycle_start).total_seconds()

    log_entry = CrawlLog(
        id=uuid4(),
        source="all",
        status="completed",
        jobs_found=len(all_jobs),
        jobs_new=new_count,
        started_at=cycle_start,
        completed_at=cycle_end,
    )
    db.add(log_entry)
    await db.commit()

    summary = {
        "total_found": len(all_jobs),
        "unique": len(unique_jobs),
        "new_saved": new_count,
        "duration_seconds": round(duration, 2),
    }
    logger.info("Crawl cycle complete: %s", summary)

    # Publish crawl-completed event
    await event_bus.publish(Exchanges.CRAWL_COMPLETED, summary)
    return summary
