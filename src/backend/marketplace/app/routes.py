"""Job Marketplace API routes — recruiter portal and candidate matching."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import (
    RecruiterProfile, MarketplaceJob, CandidateMatch,
    User, UserProfile,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


# ─── Recruiter Profile ──────────────────────────────────────────────────────

@router.post("/recruiter/register")
async def register_recruiter(
    company_name: str,
    company_website: str = "",
    industry: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Register as a recruiter."""
    existing = await db.execute(
        select(RecruiterProfile).where(RecruiterProfile.user_id == current_user["user_id"])
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already registered as recruiter")

    profile = RecruiterProfile(
        user_id=current_user["user_id"],
        company_name=company_name,
        company_website=company_website,
        industry=industry,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return {"id": str(profile.id), "company_name": company_name, "status": "registered"}


@router.get("/recruiter/profile")
async def get_recruiter_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get current user's recruiter profile."""
    result = await db.execute(
        select(RecruiterProfile).where(RecruiterProfile.user_id == current_user["user_id"])
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Not registered as recruiter")
    return {
        "id": str(profile.id),
        "company_name": profile.company_name,
        "company_website": profile.company_website,
        "industry": profile.industry,
        "plan": profile.plan,
        "verified": profile.verified,
        "jobs_posted": profile.jobs_posted,
        "total_hires": profile.total_hires,
    }


# ─── Job Posting ─────────────────────────────────────────────────────────────

@router.post("/jobs")
async def post_job(
    title: str,
    description: str,
    company_name: str = "",
    location: str = "",
    is_remote: bool = True,
    contract_type: str = "full-time",
    salary_min: float = 0,
    salary_max: float = 0,
    required_skills: list[str] = [],
    experience_level: str = "mid",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Post a new job to the marketplace."""
    recruiter_q = await db.execute(
        select(RecruiterProfile).where(RecruiterProfile.user_id == current_user["user_id"])
    )
    recruiter = recruiter_q.scalar_one_or_none()
    if not recruiter:
        raise HTTPException(status_code=403, detail="Must register as recruiter first")

    job = MarketplaceJob(
        recruiter_id=recruiter.id,
        title=title,
        description=description,
        company_name=company_name or recruiter.company_name,
        location=location,
        is_remote=is_remote,
        contract_type=contract_type,
        salary_min=salary_min,
        salary_max=salary_max,
        required_skills=required_skills,
        experience_level=experience_level,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(job)
    recruiter.jobs_posted = (recruiter.jobs_posted or 0) + 1
    await db.commit()
    await db.refresh(job)
    return {"id": str(job.id), "title": title, "status": job.status}


@router.get("/jobs")
async def list_marketplace_jobs(
    status_filter: str | None = None,
    skills: str | None = None,
    experience: str | None = None,
    is_remote: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List marketplace jobs (public endpoint — no auth required for browsing)."""
    query = select(MarketplaceJob)
    if status_filter:
        query = query.where(MarketplaceJob.status == status_filter)
    else:
        query = query.where(MarketplaceJob.status == "active")
    if is_remote is not None:
        query = query.where(MarketplaceJob.is_remote == is_remote)
    if experience:
        query = query.where(MarketplaceJob.experience_level == experience)
    query = query.order_by(desc(MarketplaceJob.created_at)).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    jobs = result.scalars().all()
    return {"jobs": [
        {
            "id": str(j.id),
            "title": j.title,
            "company_name": j.company_name,
            "location": j.location,
            "is_remote": j.is_remote,
            "contract_type": j.contract_type,
            "salary_min": float(j.salary_min) if j.salary_min else None,
            "salary_max": float(j.salary_max) if j.salary_max else None,
            "required_skills": j.required_skills or [],
            "experience_level": j.experience_level,
            "applications_count": j.applications_count,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]}


@router.get("/jobs/{job_id}")
async def get_marketplace_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get marketplace job details."""
    result = await db.execute(select(MarketplaceJob).where(MarketplaceJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Increment view count
    job.views_count = (job.views_count or 0) + 1
    await db.commit()

    return {
        "id": str(job.id),
        "title": job.title,
        "description": job.description,
        "company_name": job.company_name,
        "location": job.location,
        "is_remote": job.is_remote,
        "contract_type": job.contract_type,
        "salary_min": float(job.salary_min) if job.salary_min else None,
        "salary_max": float(job.salary_max) if job.salary_max else None,
        "required_skills": job.required_skills or [],
        "experience_level": job.experience_level,
        "status": job.status,
        "views_count": job.views_count,
        "applications_count": job.applications_count,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "expires_at": job.expires_at.isoformat() if job.expires_at else None,
    }


@router.patch("/jobs/{job_id}")
async def update_job_status(
    job_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update job status (recruiter only)."""
    recruiter_q = await db.execute(
        select(RecruiterProfile).where(RecruiterProfile.user_id == current_user["user_id"])
    )
    recruiter = recruiter_q.scalar_one_or_none()
    if not recruiter:
        raise HTTPException(status_code=403, detail="Not a recruiter")

    result = await db.execute(
        select(MarketplaceJob).where(MarketplaceJob.id == job_id, MarketplaceJob.recruiter_id == recruiter.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = status
    await db.commit()
    return {"id": str(job.id), "status": status}


# ─── Candidate Matching ─────────────────────────────────────────────────────

@router.post("/jobs/{job_id}/match")
async def match_candidates(
    job_id: UUID,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """AI-match candidates to a marketplace job based on skills overlap."""
    result = await db.execute(select(MarketplaceJob).where(MarketplaceJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch candidate profiles with skills
    profiles_q = await db.execute(
        select(UserProfile).where(UserProfile.skills.isnot(None)).limit(limit * 3)
    )
    profiles = profiles_q.scalars().all()
    required = set(s.lower() for s in (job.required_skills or []))

    scored = []
    for p in profiles:
        user_skills = set(s.lower() for s in (p.skills or []))
        if not required:
            score = 0.5
            reasons = ["no_specific_requirements"]
        else:
            overlap = required & user_skills
            score = len(overlap) / len(required) if required else 0
            reasons = [f"skill_match:{s}" for s in overlap]
        if score > 0.1:
            scored.append((p, score, reasons))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:limit]

    matches_created = []
    for profile, score, reasons in top:
        # Check if match already exists
        existing = await db.execute(
            select(CandidateMatch).where(
                CandidateMatch.job_id == job_id, CandidateMatch.user_id == profile.user_id
            )
        )
        if existing.scalar_one_or_none():
            continue
        match = CandidateMatch(
            job_id=job_id,
            user_id=profile.user_id,
            match_score=round(score * 100, 2),
            match_reasons=reasons,
        )
        db.add(match)
        matches_created.append({"user_id": str(profile.user_id), "score": round(score * 100, 2), "reasons": reasons})

    await db.commit()
    return {"job_id": str(job_id), "candidates_matched": len(matches_created), "matches": matches_created}


@router.get("/jobs/{job_id}/candidates")
async def get_candidates(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get ranked candidates for a marketplace job."""
    result = await db.execute(
        select(CandidateMatch)
        .where(CandidateMatch.job_id == job_id)
        .order_by(desc(CandidateMatch.match_score))
    )
    matches = result.scalars().all()

    candidates = []
    for m in matches:
        user_q = await db.execute(select(User).where(User.id == m.user_id))
        user = user_q.scalar_one_or_none()
        candidates.append({
            "id": str(m.id),
            "user_id": str(m.user_id),
            "name": user.full_name if user else "Unknown",
            "email": user.email if user else "",
            "match_score": float(m.match_score) if m.match_score else 0,
            "match_reasons": m.match_reasons or [],
            "status": m.status,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })

    return {"job_id": str(job_id), "candidates": candidates}


@router.patch("/candidates/{match_id}")
async def update_candidate_status(
    match_id: UUID,
    status: str,
    recruiter_notes: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update candidate match status (shortlist, contact, hire, reject)."""
    result = await db.execute(select(CandidateMatch).where(CandidateMatch.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    match.status = status
    if recruiter_notes:
        match.recruiter_notes = recruiter_notes
    await db.commit()
    return {"id": str(match.id), "status": status}


# ─── Stats ───────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get marketplace stats."""
    total_jobs_q = await db.execute(select(func.count(MarketplaceJob.id)))
    total_jobs = total_jobs_q.scalar() or 0

    active_jobs_q = await db.execute(
        select(func.count(MarketplaceJob.id)).where(MarketplaceJob.status == "active")
    )
    active_jobs = active_jobs_q.scalar() or 0

    total_matches_q = await db.execute(select(func.count(CandidateMatch.id)))
    total_matches = total_matches_q.scalar() or 0

    total_recruiters_q = await db.execute(select(func.count(RecruiterProfile.id)))
    total_recruiters = total_recruiters_q.scalar() or 0

    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_matches": total_matches,
        "total_recruiters": total_recruiters,
    }
