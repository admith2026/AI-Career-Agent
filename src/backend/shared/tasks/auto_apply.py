"""Celery tasks for auto-apply scheduling & execution with self-learning thresholds."""

import json
import logging
from datetime import datetime, timezone

import redis
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from shared.celery_app import celery_app
from shared.config import BaseServiceSettings
from shared.models import User, Job, JobAnalysis, JobApplication

logger = logging.getLogger(__name__)
_settings = BaseServiceSettings()
_engine = create_engine(_settings.database_url_sync, pool_size=5, max_overflow=10)
_SessionLocal = sessionmaker(bind=_engine)

DEFAULT_MIN_SCORE = 75


def _get_adaptive_threshold() -> int:
    """Read the self-learning feedback data to adjust the auto-apply threshold."""
    try:
        r = redis.from_url(_settings.redis_url)
        raw = r.get("feedback:scoring_weights")
        r.close()
        if raw:
            feedback = json.loads(raw)
            recommended = feedback.get("recommended_min_score", DEFAULT_MIN_SCORE)
            return max(50, min(90, recommended))
    except Exception:
        pass
    return DEFAULT_MIN_SCORE


@celery_app.task(name="tasks.auto_apply.check_and_apply", queue="auto_apply")
def check_and_apply():
    """Periodic task: find high-scoring unmatched jobs using adaptive threshold."""
    db: Session = _SessionLocal()
    min_score = _get_adaptive_threshold()
    logger.info("Auto-apply using adaptive threshold: %d", min_score)
    try:
        users = db.execute(
            select(User).where(User.auto_apply_enabled.is_(True))
        ).scalars().all()

        applied_count = 0
        for user in users:
            # Get jobs with high match scores not yet applied to
            already_applied = (
                db.execute(
                    select(JobApplication.job_id).where(JobApplication.user_id == user.id)
                ).scalars().all()
            )
            query = (
                select(Job)
                .join(JobAnalysis)
                .where(
                    Job.is_active.is_(True),
                    JobAnalysis.match_score >= min_score,
                )
            )
            if already_applied:
                query = query.where(Job.id.notin_(already_applied))

            jobs = db.execute(query.order_by(JobAnalysis.match_score.desc()).limit(5)).scalars().all()

            for job in jobs:
                schedule_auto_apply.delay(str(user.id), str(job.id))
                applied_count += 1

        logger.info("Auto-apply check: queued %d applications for %d users", applied_count, len(users))
        return {"queued": applied_count, "users": len(users)}
    finally:
        db.close()


@celery_app.task(name="tasks.auto_apply.schedule_auto_apply", queue="auto_apply")
def schedule_auto_apply(user_id: str, job_id: str):
    """Apply to a specific job for a user (background)."""
    db: Session = _SessionLocal()
    try:
        existing = db.execute(
            select(JobApplication).where(
                JobApplication.user_id == user_id,
                JobApplication.job_id == job_id,
            )
        ).scalar_one_or_none()

        if existing:
            return {"status": "already_applied"}

        application = JobApplication(
            user_id=user_id,
            job_id=job_id,
            status="auto_applied",
            applied_via="auto_apply_celery",
            applied_at=datetime.now(timezone.utc),
        )
        db.add(application)
        db.commit()
        logger.info("Auto-applied user %s to job %s", user_id, job_id)
        return {"status": "applied", "user_id": user_id, "job_id": job_id}
    except Exception:
        db.rollback()
        logger.exception("Auto-apply failed for user %s job %s", user_id, job_id)
        raise
    finally:
        db.close()
