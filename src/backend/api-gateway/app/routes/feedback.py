"""Self-Learning Feedback Loop routes.

Provides endpoints for:
- Viewing feedback/learning data from application outcomes
- Recording explicit user feedback on job matches
- Getting personalized score adjustments
"""

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.cache import get_redis
from shared.database import get_db
from shared.models import JobApplication, JobAnalysis, Job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


# ─── Schemas ─────────────────────────────────────────────────────────────────


class JobFeedback(BaseModel):
    job_id: UUID
    feedback_type: str  # "thumbs_up", "thumbs_down", "not_relevant", "too_junior", "too_senior", "great_match"
    notes: str | None = None


class ScoreAdjustmentRequest(BaseModel):
    preferred_min_score: int | None = None
    preferred_technologies: list[str] | None = None
    avoid_companies: list[str] | None = None
    prefer_remote: bool | None = None


# ─── Feedback Endpoints ──────────────────────────────────────────────────────


@router.post("/job")
async def submit_job_feedback(
    body: JobFeedback,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit explicit feedback on a job match to improve future recommendations."""
    r = await get_redis()
    user_id = str(current_user["user_id"])

    # Store feedback in Redis for the learning engine
    feedback_key = f"feedback:user:{user_id}:jobs"
    feedback_entry = {
        "job_id": str(body.job_id),
        "type": body.feedback_type,
        "notes": body.notes,
    }
    await r.lpush(feedback_key, json.dumps(feedback_entry))
    await r.ltrim(feedback_key, 0, 499)  # Keep last 500 feedback entries

    # Update per-user preference counters
    counter_key = f"feedback:user:{user_id}:counters"
    await r.hincrby(counter_key, body.feedback_type, 1)
    await r.expire(counter_key, 86400 * 90)  # 90 days

    return {"status": "recorded", "feedback_type": body.feedback_type}


@router.get("/insights")
async def get_feedback_insights(
    current_user: dict = Depends(get_current_user),
):
    """Get insights derived from the feedback loop (global + personal)."""
    r = await get_redis()
    user_id = str(current_user["user_id"])

    # Global feedback summary (from Celery task)
    global_data = await r.get("feedback:scoring_weights")
    global_insights = json.loads(global_data) if global_data else None

    # Personal counters
    counter_key = f"feedback:user:{user_id}:counters"
    personal = await r.hgetall(counter_key)

    # Personal recent feedback
    feedback_key = f"feedback:user:{user_id}:jobs"
    recent = await r.lrange(feedback_key, 0, 9)
    recent_list = [json.loads(f) for f in recent] if recent else []

    return {
        "global_insights": global_insights,
        "personal_feedback": {
            "counters": {k: int(v) for k, v in personal.items()} if personal else {},
            "recent": recent_list,
        },
    }


@router.get("/learning-stats")
async def learning_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get stats on how the system is learning from application outcomes."""
    user_id = current_user["user_id"]

    # Count outcomes by status
    result = await db.execute(
        select(JobApplication.status, func.count(JobApplication.id))
        .where(JobApplication.user_id == user_id)
        .group_by(JobApplication.status)
    )
    outcomes = {row[0]: row[1] for row in result.all()}

    # Average match score for positive vs negative outcomes
    positive_avg = (await db.execute(
        select(func.avg(JobAnalysis.match_score))
        .join(Job, JobAnalysis.job_id == Job.id)
        .join(JobApplication, JobApplication.job_id == Job.id)
        .where(
            JobApplication.user_id == user_id,
            JobApplication.status.in_(["interview", "offered"]),
        )
    )).scalar()

    negative_avg = (await db.execute(
        select(func.avg(JobAnalysis.match_score))
        .join(Job, JobAnalysis.job_id == Job.id)
        .join(JobApplication, JobApplication.job_id == Job.id)
        .where(
            JobApplication.user_id == user_id,
            JobApplication.status.in_(["rejected", "no_response"]),
        )
    )).scalar()

    # Top technologies from successful applications
    successful_techs = (await db.execute(
        select(func.unnest(JobAnalysis.technologies), func.count())
        .join(Job, JobAnalysis.job_id == Job.id)
        .join(JobApplication, JobApplication.job_id == Job.id)
        .where(
            JobApplication.user_id == user_id,
            JobApplication.status.in_(["interview", "offered"]),
        )
        .group_by(func.unnest(JobAnalysis.technologies))
        .order_by(desc(func.count()))
        .limit(10)
    )).all()

    return {
        "outcomes": outcomes,
        "avg_score_positive": round(float(positive_avg), 1) if positive_avg else None,
        "avg_score_negative": round(float(negative_avg), 1) if negative_avg else None,
        "successful_technologies": [{"tech": row[0], "count": row[1]} for row in successful_techs],
        "recommendation": _generate_recommendation(outcomes, positive_avg, negative_avg),
    }


def _generate_recommendation(outcomes: dict, pos_avg, neg_avg) -> str:
    """Generate a human-readable recommendation based on learning data."""
    total = sum(outcomes.values())
    if total == 0:
        return "Start applying to jobs to help the system learn your preferences."

    positive = outcomes.get("interview", 0) + outcomes.get("offered", 0)
    rate = positive / total * 100

    parts = [f"Success rate: {rate:.0f}% ({positive}/{total})."]

    if pos_avg and neg_avg and pos_avg > neg_avg:
        parts.append(f"Higher-scored jobs (avg {pos_avg:.0f}) perform better than lower ones (avg {neg_avg:.0f}).")
        parts.append(f"Consider setting minimum score to {int(neg_avg) + 5}+.")

    return " ".join(parts)
