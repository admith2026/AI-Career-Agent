"""Scheduled notification reports — morning and evening daily digests."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import async_session_factory
from shared.models import User, Job, JobApplication, JobAnalysis

from .config import settings
from .dispatcher import dispatch_notification

logger = logging.getLogger(__name__)


async def _build_daily_report(db: AsyncSession) -> str:
    """Build a daily summary report body."""

    # Count new jobs in the last 24 hours
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    new_jobs = (await db.execute(
        select(func.count(Job.id)).where(Job.date_discovered >= cutoff)
    )).scalar() or 0

    # Top scored jobs
    top_q = (
        select(Job.job_title, Job.company_name, JobAnalysis.match_score)
        .join(JobAnalysis, Job.id == JobAnalysis.job_id)
        .where(Job.date_discovered >= cutoff, JobAnalysis.match_score.isnot(None))
        .order_by(JobAnalysis.match_score.desc())
        .limit(5)
    )
    top_jobs = (await db.execute(top_q)).all()

    # Recent applications
    recent_apps = (await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.created_at >= cutoff)
    )).scalar() or 0

    lines = [
        f"📊 **Daily Career Report**",
        f"",
        f"🔍 **{new_jobs}** new jobs discovered in the last 24h",
        f"📝 **{recent_apps}** applications submitted",
        f"",
    ]

    if top_jobs:
        lines.append("🏆 **Top Matches:**")
        for i, (title, company, score) in enumerate(top_jobs, 1):
            lines.append(f"  {i}. {title} @ {company or 'Unknown'} — Score: {score}")

    return "\n".join(lines)


async def _send_scheduled_reports() -> None:
    """Send daily digest to all users."""
    async with async_session_factory() as db:
        report = await _build_daily_report(db)

        users = (await db.execute(select(User))).scalars().all()
        for user in users:
            try:
                await dispatch_notification(
                    user=user,
                    subject="Daily Career Agent Report",
                    body=report,
                    db=db,
                )
            except Exception:
                logger.exception("Failed to send report to user %s", user.id)


async def scheduler_loop() -> None:
    """Run scheduled reports at configured times (morning + evening)."""
    logger.info(
        "Notification scheduler started — reports at %d:00 and %d:00 UTC",
        settings.morning_report_hour,
        settings.evening_report_hour,
    )

    while True:
        now = datetime.now(timezone.utc)
        if now.hour in (settings.morning_report_hour, settings.evening_report_hour) and now.minute == 0:
            logger.info("Triggering scheduled report at %s", now.isoformat())
            try:
                await _send_scheduled_reports()
            except Exception:
                logger.exception("Scheduled report failed")
            # Sleep past this minute to avoid double-trigger
            await asyncio.sleep(61)
        else:
            await asyncio.sleep(30)
