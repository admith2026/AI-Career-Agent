"""Celery tasks for self-learning feedback loop."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session, sessionmaker

from shared.celery_app import celery_app
from shared.config import BaseServiceSettings
from shared.models import JobApplication, JobAnalysis, Job

logger = logging.getLogger(__name__)
_settings = BaseServiceSettings()
_engine = create_engine(_settings.database_url_sync, pool_size=5, max_overflow=10)
_SessionLocal = sessionmaker(bind=_engine)


@celery_app.task(name="tasks.feedback.run_feedback_cycle", queue="feedback")
def run_feedback_cycle():
    """Analyse application outcomes and adjust scoring weights.

    Examines recent applications to learn which job attributes correlate
    with positive outcomes (interview, offered) vs negative ones (rejected, no_response).
    Stores aggregated feedback data for the scoring engine to consume.
    """
    db: Session = _SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        # Get applications with outcomes
        apps = db.execute(
            select(JobApplication, JobAnalysis)
            .join(Job, JobApplication.job_id == Job.id)
            .join(JobAnalysis, JobAnalysis.job_id == Job.id)
            .where(JobApplication.updated_at >= cutoff)
            .where(JobApplication.status.in_(["interview", "offered", "rejected", "no_response"]))
        ).all()

        if not apps:
            logger.info("No recent application outcomes to learn from")
            return {"status": "no_data"}

        positive_scores = []
        negative_scores = []
        positive_techs: dict[str, int] = {}
        negative_techs: dict[str, int] = {}
        positive_companies: dict[str, int] = {}
        negative_companies: dict[str, int] = {}
        response_times: list[float] = []
        source_outcomes: dict[str, dict[str, int]] = {}

        for application, analysis in apps:
            is_positive = application.status in ("interview", "offered")
            score = analysis.match_score or 0
            techs = analysis.technologies or []

            if is_positive:
                positive_scores.append(score)
                for tech in techs:
                    positive_techs[tech] = positive_techs.get(tech, 0) + 1
            else:
                negative_scores.append(score)
                for tech in techs:
                    negative_techs[tech] = negative_techs.get(tech, 0) + 1

            # Track company success rates
            company = getattr(analysis, 'company_name', '') or ''
            if company:
                bucket = positive_companies if is_positive else negative_companies
                bucket[company] = bucket.get(company, 0) + 1

            # Track response times
            if application.applied_at and application.updated_at:
                delta = (application.updated_at - application.applied_at).total_seconds() / 86400
                if delta > 0:
                    response_times.append(delta)

            # Track by source
            source = getattr(analysis, 'source', 'unknown') or 'unknown'
            if source not in source_outcomes:
                source_outcomes[source] = {"positive": 0, "negative": 0}
            source_outcomes[source]["positive" if is_positive else "negative"] += 1

        avg_positive = sum(positive_scores) / len(positive_scores) if positive_scores else 0
        avg_negative = sum(negative_scores) / len(negative_scores) if negative_scores else 0
        avg_response_days = round(sum(response_times) / len(response_times), 1) if response_times else 0

        # Compute technology success rates
        all_techs = set(list(positive_techs.keys()) + list(negative_techs.keys()))
        tech_success_rates = {}
        for tech in all_techs:
            pos = positive_techs.get(tech, 0)
            neg = negative_techs.get(tech, 0)
            total = pos + neg
            if total >= 2:  # Only include techs with enough data
                tech_success_rates[tech] = round(pos / total, 3)

        # Compute recommended threshold with smoothing
        if avg_positive > 0 and avg_negative > 0:
            # Set threshold at the midpoint, slightly favoring positive outcomes
            recommended = int(avg_negative + (avg_positive - avg_negative) * 0.4)
        elif avg_positive > 0:
            recommended = max(50, int(avg_positive * 0.7))
        else:
            recommended = 50

        # Success rate by source
        source_success = {}
        for source, counts in source_outcomes.items():
            total = counts["positive"] + counts["negative"]
            if total > 0:
                source_success[source] = round(counts["positive"] / total, 3)

        # Store enhanced feedback in Redis
        import redis
        r = redis.from_url(_settings.redis_url)
        import json
        feedback = {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "version": 2,
            "total_outcomes": len(apps),
            "positive_count": len(positive_scores),
            "negative_count": len(negative_scores),
            "avg_positive_score": round(avg_positive, 1),
            "avg_negative_score": round(avg_negative, 1),
            "recommended_min_score": max(50, min(90, recommended)),
            "avg_response_days": avg_response_days,
            "positive_techs": dict(sorted(positive_techs.items(), key=lambda x: -x[1])[:20]),
            "negative_techs": dict(sorted(negative_techs.items(), key=lambda x: -x[1])[:20]),
            "tech_success_rates": dict(sorted(tech_success_rates.items(), key=lambda x: -x[1])[:30]),
            "source_success_rates": source_success,
            "top_companies": dict(sorted(positive_companies.items(), key=lambda x: -x[1])[:10]),
            "learning_insights": {
                "score_gap": round(avg_positive - avg_negative, 1),
                "best_techs": [t for t, r in sorted(tech_success_rates.items(), key=lambda x: -x[1])[:5]],
                "best_sources": [s for s, r in sorted(source_success.items(), key=lambda x: -x[1])[:3]],
            },
        }
        r.set("feedback:scoring_weights", json.dumps(feedback), ex=86400 * 7)  # Keep for 7 days

        # Also store historical snapshots for trend analysis
        history_key = f"feedback:history:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        r.set(history_key, json.dumps(feedback), ex=86400 * 90)  # Keep 90 days
        r.close()

        logger.info(
            "Feedback cycle v2: %d outcomes, avg positive=%.1f, avg negative=%.1f, "
            "recommended threshold=%d, %d tech success rates tracked",
            len(apps), avg_positive, avg_negative, recommended, len(tech_success_rates),
        )
        return feedback
    finally:
        db.close()
