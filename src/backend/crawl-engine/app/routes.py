"""Crawl Engine API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.models import CrawlerSource, CrawlQueueItem, CrawlLog

router = APIRouter(prefix="/api/crawl", tags=["Crawl Engine"])


@router.get("/sources")
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CrawlerSource).order_by(CrawlerSource.priority.desc())
    )
    sources = result.scalars().all()
    return [
        {
            "id": str(s.id), "name": s.name, "source_type": s.source_type,
            "url_pattern": s.url_pattern, "crawl_frequency_minutes": s.crawl_frequency_minutes,
            "priority": s.priority, "is_enabled": s.is_enabled,
            "requires_js": s.requires_js, "last_crawled_at": s.last_crawled_at,
            "success_rate": float(s.success_rate) if s.success_rate else 100.0,
        }
        for s in sources
    ]


@router.post("/sources")
async def add_source(body: dict, db: AsyncSession = Depends(get_db)):
    source = CrawlerSource(
        name=body["name"],
        source_type=body.get("source_type", "http"),
        url_pattern=body["url_pattern"],
        crawl_frequency_minutes=body.get("crawl_frequency_minutes", 60),
        priority=body.get("priority", 5),
        requires_js=body.get("requires_js", False),
        anti_bot_level=body.get("anti_bot_level", "low"),
        config=body.get("config", {}),
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return {"id": str(source.id), "name": source.name, "status": "created"}


@router.post("/trigger/{source_name}")
async def trigger_crawl(source_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CrawlerSource).where(CrawlerSource.name == source_name)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, f"Source '{source_name}' not found")

    queue_item = CrawlQueueItem(
        source_id=source.id,
        url=source.url_pattern,
        priority=10,
        status="pending",
    )
    db.add(queue_item)
    await db.commit()
    return {"status": "queued", "source": source_name}


@router.get("/queue")
async def get_queue(status: str = None, db: AsyncSession = Depends(get_db)):
    query = select(CrawlQueueItem).order_by(CrawlQueueItem.created_at.desc()).limit(50)
    if status:
        query = query.where(CrawlQueueItem.status == status)
    result = await db.execute(query)
    items = result.scalars().all()
    return [
        {
            "id": str(i.id), "url": i.url, "priority": i.priority,
            "status": i.status, "worker_id": i.worker_id,
            "attempts": i.attempts, "created_at": i.created_at,
        }
        for i in items
    ]


@router.get("/logs")
async def get_crawl_logs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CrawlLog).order_by(CrawlLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id), "source": l.source, "started_at": l.started_at,
            "completed_at": l.completed_at, "jobs_found": l.jobs_found,
            "jobs_new": l.jobs_new, "status": l.status,
        }
        for l in logs
    ]


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_sources = await db.scalar(select(func.count(CrawlerSource.id))) or 0
    active = await db.scalar(
        select(func.count(CrawlerSource.id)).where(CrawlerSource.is_enabled == True)
    ) or 0
    pending = await db.scalar(
        select(func.count(CrawlQueueItem.id)).where(CrawlQueueItem.status == "pending")
    ) or 0
    running = await db.scalar(
        select(func.count(CrawlQueueItem.id)).where(CrawlQueueItem.status == "running")
    ) or 0
    total_crawls = await db.scalar(select(func.count(CrawlLog.id))) or 0

    return {
        "total_sources": total_sources,
        "active_sources": active,
        "queue_pending": pending,
        "queue_running": running,
        "total_crawls_run": total_crawls,
    }
