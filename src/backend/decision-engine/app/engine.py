"""Decision Engine scoring and decision logic."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Job, JobAnalysis, HiringSignal, DecisionLog, UserProfile
from shared.events import EventBus, Exchanges
from app.config import settings

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Evaluates jobs, computes scores, and makes autonomous decisions."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def score_job(self, job: Job, analysis: JobAnalysis | None, db: AsyncSession) -> dict:
        """Compute a composite relevance score for a job."""
        score = 0
        breakdown = {}

        # Base match score from analysis (0-100)
        if analysis and analysis.match_score is not None:
            base = min(analysis.match_score, 100)
            score += base
            breakdown["base_match"] = base
        else:
            score += 50
            breakdown["base_match"] = 50

        # Remote bonus
        if job.is_remote:
            score += 5
            breakdown["remote_bonus"] = 5

        # Hiring signal boost — company actively hiring
        if job.company_name:
            result = await db.execute(
                select(func.count(HiringSignal.id)).where(
                    HiringSignal.company_name == job.company_name
                )
            )
            signal_count = result.scalar() or 0
            signal_boost = min(signal_count * 3, settings.signal_boost_max)
            score += signal_boost
            breakdown["signal_boost"] = signal_boost

        # Recency bonus — jobs posted in last 24h
        if job.date_posted and (datetime.utcnow() - job.date_posted.replace(tzinfo=None)).days < 1:
            score += 5
            breakdown["recency_bonus"] = 5

        # Technology match depth (from analysis)
        if analysis and analysis.technologies:
            tech_count = len(analysis.technologies)
            tech_bonus = min(tech_count * 2, 10)
            score += tech_bonus
            breakdown["tech_depth_bonus"] = tech_bonus

        # Seniority alignment bonus
        if analysis and analysis.seniority_level:
            if analysis.seniority_level.lower() in ("senior", "lead", "staff"):
                score += 5
                breakdown["seniority_bonus"] = 5

        # Cap at 100
        final_score = min(score, 100)
        return {"score": final_score, "breakdown": breakdown}

    def decide(self, score: int, user_auto_apply: bool) -> tuple[str, str]:
        """Make a decision based on score and user preferences.

        Returns (decision, reason).
        """
        if score >= settings.auto_apply_min_score and user_auto_apply:
            return "auto_apply", f"Score {score} >= {settings.auto_apply_min_score} with auto-apply enabled"
        elif score >= settings.auto_apply_min_score:
            return "recommend_apply", f"Score {score} >= {settings.auto_apply_min_score} — strong match"
        elif score >= settings.outreach_min_score:
            return "outreach", f"Score {score} >= {settings.outreach_min_score} — suggest networking"
        else:
            return "skip", f"Score {score} below threshold"

    async def evaluate_job(self, job_id: UUID, user_id: UUID, db: AsyncSession) -> dict:
        """Full evaluation pipeline: score → decide → log → act."""
        job = await db.get(Job, job_id)
        if not job:
            return {"error": "Job not found"}

        analysis = None
        if job.analysis:
            analysis = job.analysis
        else:
            result = await db.execute(
                select(JobAnalysis).where(JobAnalysis.job_id == job_id)
            )
            analysis = result.scalar_one_or_none()

        # Get user preferences
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        score_data = await self.score_job(job, analysis, db)
        score = score_data["score"]

        from shared.models import User
        user = await db.get(User, user_id)
        user_auto_apply = user.auto_apply_enabled if user else False

        decision, reason = self.decide(score, user_auto_apply)

        # Log the decision
        log_entry = DecisionLog(
            user_id=user_id,
            job_id=job_id,
            decision_type="job_evaluation",
            decision=decision,
            reason=reason,
            score_data=score_data,
        )
        db.add(log_entry)
        await db.commit()

        # Publish decision event
        await self.event_bus.publish(
            Exchanges.JOB_SCORED,
            {
                "job_id": str(job_id),
                "user_id": str(user_id),
                "score": score,
                "decision": decision,
                "reason": reason,
            },
        )

        return {
            "job_id": str(job_id),
            "score": score,
            "breakdown": score_data["breakdown"],
            "decision": decision,
            "reason": reason,
        }

    async def batch_evaluate(self, user_id: UUID, db: AsyncSession, limit: int = 50) -> list[dict]:
        """Evaluate all un-scored jobs for a user."""
        # Find jobs that don't have decision logs yet for this user
        sub = select(DecisionLog.job_id).where(DecisionLog.user_id == user_id)
        result = await db.execute(
            select(Job.id)
            .where(Job.is_active.is_(True))
            .where(Job.id.notin_(sub))
            .order_by(Job.date_discovered.desc())
            .limit(limit)
        )
        job_ids = result.scalars().all()

        results = []
        for jid in job_ids:
            try:
                r = await self.evaluate_job(jid, user_id, db)
                results.append(r)
            except Exception:
                logger.exception("Failed to evaluate job %s", jid)
        return results
