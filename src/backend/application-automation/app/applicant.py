"""Applies to jobs — generates resume via resume-generator service, then sends email."""

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.events import EventBus, Exchanges
from shared.models import Job, JobApplication, GeneratedResume, User, UserProfile

from .config import settings
from .email_sender import send_application_email

logger = logging.getLogger(__name__)


async def apply_to_job(
    user_id: UUID,
    job_id: UUID,
    db: AsyncSession,
    event_bus: EventBus,
) -> JobApplication:
    """Full apply flow: generate resume → send email → record application."""

    # Load user + profile
    user = await db.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    # Load job
    job = await db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    # Check for duplicate application
    dup = await db.execute(
        select(JobApplication).where(
            JobApplication.user_id == user_id,
            JobApplication.job_id == job_id,
        )
    )
    if dup.scalar_one_or_none():
        raise ValueError("Already applied to this job")

    # Generate tailored resume via Resume Generator service
    resume_payload = {
        "user_id": str(user_id),
        "job_id": str(job_id),
        "job_title": job.job_title,
        "company_name": job.company_name or "",
        "job_description": job.job_description or "",
        "technologies": [],
        "user_name": user.full_name,
        "user_summary": profile.summary if profile else "",
        "user_skills": profile.skills if profile else [],
        "user_experience_years": profile.experience_years if profile else 0,
        "base_resume": profile.resume_base if profile else "",
    }

    resume_data = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{settings.resume_generator_url}/api/generate-resume",
                json=resume_payload,
            )
            resp.raise_for_status()
            resume_data = resp.json()
        except Exception:
            logger.exception("Resume generation failed — will apply without tailored resume")

    # Persist generated resume
    resume_id = None
    if resume_data:
        resume = GeneratedResume(
            id=uuid4(),
            user_id=user_id,
            job_id=job_id,
            resume_content=resume_data.get("resume_content", ""),
            cover_letter=resume_data.get("cover_letter", ""),
            outreach_email=resume_data.get("outreach_email", ""),
            format="markdown",
        )
        db.add(resume)
        await db.flush()
        resume_id = resume.id

    # Send email if recruiter email is available
    applied_via = "manual"
    if job.recruiter_email and resume_data:
        outreach = resume_data.get("outreach_email", "")
        subject = f"Application for {job.job_title} — {user.full_name}"
        sent = await send_application_email(
            to_email=job.recruiter_email,
            subject=subject,
            body_html=f"<pre>{outreach}</pre>",
            body_text=outreach,
        )
        if sent:
            applied_via = "email"

    # Record application
    application = JobApplication(
        id=uuid4(),
        user_id=user_id,
        job_id=job_id,
        resume_id=resume_id,
        status="applied" if applied_via == "email" else "pending",
        applied_via=applied_via,
        applied_at=datetime.now(timezone.utc) if applied_via == "email" else None,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    # Publish event
    await event_bus.publish(
        Exchanges.APPLICATION_SUBMITTED,
        {
            "application_id": str(application.id),
            "user_id": str(user_id),
            "job_id": str(job_id),
            "job_title": job.job_title,
            "company_name": job.company_name,
            "status": application.status,
            "applied_via": applied_via,
        },
    )

    return application
