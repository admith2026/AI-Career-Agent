"""API routes for Application Automation service."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import JobApplication, Job, JobAnalysis, User
from shared.schemas import ApplyRequest, ApplicationOut, ApplicationStatusUpdate
from shared.events import EventBus

from .applicant import apply_to_job
from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/applications", tags=["applications"])

_event_bus: EventBus | None = None


def set_event_bus(bus: EventBus) -> None:
    global _event_bus
    _event_bus = bus


@router.post("", response_model=ApplicationOut)
async def create_application(
    req: ApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Apply to a job — generates tailored resume and sends application email."""
    if not _event_bus:
        raise HTTPException(status_code=503, detail="Event bus not initialised")
    try:
        application = await apply_to_job(current_user["user_id"], req.job_id, db, _event_bus)
        return ApplicationOut.model_validate(application)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[ApplicationOut])
async def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all applications for the current user."""
    query = (
        select(JobApplication)
        .options(joinedload(JobApplication.job))
        .where(JobApplication.user_id == current_user["user_id"])
    )
    if status:
        query = query.where(JobApplication.status == status)
    query = query.order_by(desc(JobApplication.created_at)).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.unique().scalars().all()
    return [ApplicationOut.model_validate(r) for r in rows]


@router.get("/stats/summary")
async def application_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return application statistics for the current user."""
    base = select(func.count(JobApplication.id)).where(JobApplication.user_id == current_user["user_id"])
    total = (await db.execute(base)).scalar() or 0

    by_status_q = (
        select(JobApplication.status, func.count(JobApplication.id))
        .where(JobApplication.user_id == current_user["user_id"])
        .group_by(JobApplication.status)
    )
    rows = (await db.execute(by_status_q)).all()
    by_status = {row[0]: row[1] for row in rows}

    return {"total": total, "by_status": by_status}


# Also serve /stats for frontend compatibility
@router.get("/stats")
async def application_stats_alias(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Alias for /stats/summary."""
    return await application_stats(db=db, current_user=current_user)


# ─── Auto-Apply Scheduling & Follow-up ──────────────────────────────────────


class AutoApplySettings(BaseModel):
    enabled: bool = True
    min_score: int = 70
    max_daily: int = 10
    preferred_sources: list[str] = []
    exclude_companies: list[str] = []


@router.post("/auto-apply/settings")
async def update_auto_apply_settings(
    body: AutoApplySettings,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update auto-apply preferences for the current user."""
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.auto_apply_enabled = body.enabled
    # Store extended settings in notification_preferences JSONB
    prefs = user.notification_preferences or {}
    prefs["auto_apply"] = body.model_dump()
    user.notification_preferences = prefs
    await db.commit()
    return {"status": "updated", "auto_apply": body.model_dump()}


@router.get("/auto-apply/settings")
async def get_auto_apply_settings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get current auto-apply settings."""
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    prefs = (user.notification_preferences or {}).get("auto_apply", {})
    return {
        "enabled": user.auto_apply_enabled,
        "min_score": prefs.get("min_score", settings.min_score_for_auto_apply),
        "max_daily": prefs.get("max_daily", settings.max_daily_applications),
        "preferred_sources": prefs.get("preferred_sources", []),
        "exclude_companies": prefs.get("exclude_companies", []),
    }


@router.post("/auto-apply/trigger")
async def trigger_auto_apply(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Manually trigger auto-apply: find top scoring unapplied jobs and apply."""
    if not _event_bus:
        raise HTTPException(status_code=503, detail="Event bus not initialised")

    user_id = current_user["user_id"]

    # Check daily limit
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count_q = await db.execute(
        select(func.count(JobApplication.id)).where(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= today,
        )
    )
    today_count = today_count_q.scalar() or 0
    max_daily = settings.max_daily_applications
    remaining = max(0, max_daily - today_count)

    if remaining == 0:
        return {"status": "daily_limit_reached", "applied": 0, "limit": max_daily}

    # Get already-applied job IDs
    applied_ids = (
        await db.execute(
            select(JobApplication.job_id).where(JobApplication.user_id == user_id)
        )
    ).scalars().all()

    # Find high-scoring jobs
    query = (
        select(Job)
        .join(JobAnalysis)
        .where(
            Job.is_active.is_(True),
            JobAnalysis.match_score >= settings.min_score_for_auto_apply,
        )
    )
    if applied_ids:
        query = query.where(Job.id.notin_(applied_ids))
    query = query.order_by(desc(JobAnalysis.match_score)).limit(remaining)

    jobs = (await db.execute(query)).scalars().all()

    applied = []
    for job in jobs:
        try:
            application = await apply_to_job(user_id, job.id, db, _event_bus)
            applied.append(str(job.id))
        except Exception as e:
            logger.error("Auto-apply failed for job %s: %s", job.id, e)

    return {"status": "completed", "applied": len(applied), "job_ids": applied}


@router.get("/follow-ups")
async def get_follow_ups(
    days_since: int = Query(7, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get applications that need follow-up (applied but no response after N days)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_since)
    result = await db.execute(
        select(JobApplication)
        .options(joinedload(JobApplication.job))
        .where(
            JobApplication.user_id == current_user["user_id"],
            JobApplication.applied_at <= cutoff,
            JobApplication.response_received.is_(False),
            JobApplication.status.in_(["applied", "auto_applied", "pending"]),
        )
        .order_by(JobApplication.applied_at)
    )
    rows = result.unique().scalars().all()
    return {
        "follow_ups_needed": len(rows),
        "applications": [ApplicationOut.model_validate(r) for r in rows],
    }


# ─── Parameterized routes MUST come last ─────────────────────────────────────


@router.get("/{application_id}", response_model=ApplicationOut)
async def get_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single application by ID."""
    result = await db.execute(
        select(JobApplication)
        .options(joinedload(JobApplication.job))
        .where(JobApplication.id == application_id, JobApplication.user_id == current_user["user_id"])
    )
    app = result.unique().scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationOut.model_validate(app)


@router.patch("/{application_id}", response_model=ApplicationOut)
async def update_application_status(
    application_id: UUID,
    body: ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update application status (e.g., interview, offered, rejected)."""
    result = await db.execute(
        select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == current_user["user_id"],
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = body.status
    if body.notes:
        app.notes = body.notes
    await db.commit()
    await db.refresh(app)
    return ApplicationOut.model_validate(app)
