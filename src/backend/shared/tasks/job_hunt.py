"""Celery task — Autonomous Job Hunt Pipeline.

Flow: fetch jobs (JSearch, multi-role queries) → score with AI (OpenAI, dynamic profile) → filter → notify.
Runs on Celery beat schedule (9 AM / 6 PM UTC) and via /api/run-job-hunt endpoint.

Supports ALL technical roles — queries are dynamically built from user profiles.
"""

import asyncio
import logging
from datetime import datetime, timezone

from shared.celery_app import celery_app
from shared.services.job_fetcher import fetch_jobs, fetch_jobs_multi_query, DEFAULT_QUERY, ParsedJob
from shared.services.ai_scorer import score_job, MatchResult
from shared.services.skill_engine import get_search_queries_for_skills, ROLE_TEMPLATES
from shared.services.notifier import (
    send_telegram_alert,
    send_email_alert,
    send_whatsapp_alert,
)
from shared.config import BaseServiceSettings

logger = logging.getLogger(__name__)

SCORE_THRESHOLD = 70


def _build_alert_text(scored: list[tuple[ParsedJob, MatchResult]]) -> str:
    """Build a plain-text summary for Telegram / WhatsApp."""
    lines = [f"🎯 *Job Hunt Results — {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}*\n"]
    lines.append(f"Found *{len(scored)}* jobs scoring above {SCORE_THRESHOLD}:\n")

    for idx, (job, match) in enumerate(scored, 1):
        lines.append(
            f"{idx}. *{job.title}* @ {job.company}\n"
            f"   Score: {match.score}/100\n"
            f"   {match.explanation}\n"
            f"   Apply: {job.apply_link}\n"
        )
    return "\n".join(lines)


def _build_alert_html(scored: list[tuple[ParsedJob, MatchResult]]) -> str:
    """Build an HTML summary for email."""
    rows = ""
    for job, match in scored:
        rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee"><strong>{job.title}</strong><br>{job.company}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;font-size:1.2em;
                color:{'#22c55e' if match.score >= 85 else '#eab308'}">{match.score}/100</td>
            <td style="padding:8px;border-bottom:1px solid #eee">{match.explanation}</td>
            <td style="padding:8px;border-bottom:1px solid #eee"><a href="{job.apply_link}">Apply</a></td>
        </tr>"""

    return f"""
    <h2>🎯 Job Hunt Results — {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}</h2>
    <p>Found <strong>{len(scored)}</strong> jobs scoring above {SCORE_THRESHOLD}.</p>
    <table style="border-collapse:collapse;width:100%;font-family:sans-serif">
        <tr style="background:#f3f4f6">
            <th style="padding:8px;text-align:left">Job</th>
            <th style="padding:8px">Score</th>
            <th style="padding:8px;text-align:left">Why</th>
            <th style="padding:8px">Link</th>
        </tr>
        {rows}
    </table>"""


async def _run_pipeline(
    query: str = DEFAULT_QUERY,
    queries: list[str] | None = None,
    profile: str | None = None,
) -> dict:
    """Async core: fetch (multi-query) → score (dynamic profile) → filter → notify."""
    settings = BaseServiceSettings()

    # ── 1. Fetch ──────────────────────────────────────────────────────────────
    if queries and len(queries) > 0:
        logger.info("🔍 Multi-query fetch: %s", queries)
        jobs = await fetch_jobs_multi_query(queries)
    else:
        logger.info("🔍 Fetching jobs: %s", query)
        jobs = await fetch_jobs(query=query)

    if not jobs:
        logger.warning("No jobs returned from JSearch")
        return {"fetched": 0, "scored": 0, "notified": False}

    # ── 2. Score (dynamic profile) ─────────────────────────────────────────────
    score_profile = profile or None
    logger.info("🤖 Scoring %d jobs against %s …", len(jobs),
                "custom profile" if score_profile else "default profile")
    scored: list[tuple[ParsedJob, MatchResult]] = []
    for job in jobs:
        match = await score_job(
            title=job.title,
            company=job.company,
            description=job.description,
            **({"profile": score_profile} if score_profile else {}),
        )
        if match.score >= SCORE_THRESHOLD:
            scored.append((job, match))

    scored.sort(key=lambda x: x[1].score, reverse=True)
    logger.info("✅ %d / %d jobs scored above threshold (%d)", len(scored), len(jobs), SCORE_THRESHOLD)

    if not scored:
        return {"fetched": len(jobs), "scored": 0, "notified": False}

    # ── 3. Notify ─────────────────────────────────────────────────────────────
    text = _build_alert_text(scored)
    html = _build_alert_html(scored)
    subject = f"🎯 {len(scored)} High-Match Jobs Found"
    channels_sent: list[str] = []

    # Telegram
    telegram_chat_id = settings.telegram_bot_token and "default"
    if settings.telegram_bot_token:
        # Use the TELEGRAM_CHAT_ID env var if available; fall back gracefully
        chat_id = getattr(settings, "telegram_chat_id", "")
        if chat_id and await send_telegram_alert(chat_id, text):
            channels_sent.append("telegram")

    # Email
    if settings.email_user and settings.email_pass:
        if await send_email_alert(settings.email_user, subject, html):
            channels_sent.append("email")

    # Twilio WhatsApp
    if settings.twilio_account_sid and settings.twilio_auth_token:
        whatsapp_to = getattr(settings, "whatsapp_to_number", "")
        if whatsapp_to and await send_whatsapp_alert(whatsapp_to, text):
            channels_sent.append("whatsapp")

    logger.info("📬 Notifications sent via: %s", channels_sent or ["none — no channels configured"])

    return {
        "fetched": len(jobs),
        "scored": len(scored),
        "notified": bool(channels_sent),
        "channels": channels_sent,
        "top_match": {
            "title": scored[0][0].title,
            "company": scored[0][0].company,
            "score": scored[0][1].score,
        } if scored else None,
    }


# ── Celery task (sync wrapper around the async pipeline) ─────────────────────

@celery_app.task(name="tasks.job_hunt.run_job_hunt", queue="intelligence")
def run_job_hunt(
    query: str = DEFAULT_QUERY,
    queries: list[str] | None = None,
    profile: str | None = None,
) -> dict:
    """Celery-compatible sync entry point — runs the async pipeline."""
    logger.info("⚡ Job hunt pipeline triggered (query=%s, multi=%s)", query, bool(queries))
    return asyncio.run(_run_pipeline(query=query, queries=queries, profile=profile))


# ── Expose the async version for direct FastAPI use ──────────────────────────
run_pipeline = _run_pipeline
