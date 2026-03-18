"""Data Pipeline API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.models import PipelineEvent, Job, HiringSignal

router = APIRouter(prefix="/api/pipeline", tags=["Data Pipeline"])


@router.get("/stats")
async def pipeline_stats(db: AsyncSession = Depends(get_db)):
    total_events = await db.scalar(select(func.count(PipelineEvent.id))) or 0
    processed = await db.scalar(
        select(func.count(PipelineEvent.id)).where(PipelineEvent.processed == True)
    ) or 0
    total_jobs = await db.scalar(select(func.count(Job.id))) or 0
    total_signals = await db.scalar(select(func.count(HiringSignal.id))) or 0

    # Events by type
    type_counts = await db.execute(
        select(PipelineEvent.event_type, func.count(PipelineEvent.id))
        .group_by(PipelineEvent.event_type)
    )
    events_by_type = {row[0]: row[1] for row in type_counts.all()}

    return {
        "total_events": total_events,
        "processed": processed,
        "pending": total_events - processed,
        "total_jobs_ingested": total_jobs,
        "total_signals_detected": total_signals,
        "events_by_type": events_by_type,
    }


@router.get("/events")
async def list_events(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PipelineEvent).order_by(PipelineEvent.created_at.desc()).limit(limit)
    )
    events = result.scalars().all()
    return [
        {
            "id": str(e.id), "event_type": e.event_type,
            "source_service": e.source_service, "payload": e.payload,
            "processed": e.processed, "created_at": e.created_at,
        }
        for e in events
    ]


@router.get("/signals")
async def list_signals(limit: int = 30, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HiringSignal).order_by(HiringSignal.detected_at.desc()).limit(limit)
    )
    signals = result.scalars().all()
    return [
        {
            "id": str(s.id), "signal_type": s.signal_type,
            "title": s.title, "description": s.description,
            "source_url": s.source_url, "source_name": s.source_name,
            "confidence": float(s.confidence) if s.confidence else 0,
            "predicted_roles": s.predicted_roles,
            "detected_at": s.detected_at,
        }
        for s in signals
    ]
