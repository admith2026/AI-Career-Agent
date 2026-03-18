"""Recruiter Intelligence routes — CRUD + ranking for recruiter contacts."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import RecruiterContact, JobApplication, Job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recruiters", tags=["recruiters"])


# ─── Schemas ─────────────────────────────────────────────────────────────────


class RecruiterCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    linkedin_url: str | None = None
    source: str | None = None
    notes: str | None = None
    specializations: list[str] = []


class RecruiterUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    notes: str | None = None
    specializations: list[str] | None = None


class RecruiterInteraction(BaseModel):
    interaction_type: str  # "email_sent", "call", "response_received", "placement"
    notes: str | None = None


# ─── CRUD ────────────────────────────────────────────────────────────────────


@router.get("")
async def list_recruiters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company: str | None = None,
    search: str | None = None,
    sort_by: str = Query("intelligence_score", regex="^(intelligence_score|response_rate|last_contacted|name)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List recruiters with optional filtering and intelligent sorting."""
    query = select(RecruiterContact)

    if company:
        query = query.where(RecruiterContact.company.ilike(f"%{company}%"))
    if search:
        query = query.where(
            or_(
                RecruiterContact.name.ilike(f"%{search}%"),
                RecruiterContact.email.ilike(f"%{search}%"),
                RecruiterContact.company.ilike(f"%{search}%"),
            )
        )

    # Sort
    sort_col = getattr(RecruiterContact, sort_by, RecruiterContact.intelligence_score)
    query = query.order_by(desc(sort_col))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "data": [_recruiter_to_dict(r) for r in rows],
    }


@router.post("")
async def create_recruiter(
    body: RecruiterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new recruiter contact."""
    recruiter = RecruiterContact(
        name=body.name,
        email=body.email,
        phone=body.phone,
        company=body.company,
        linkedin_url=body.linkedin_url,
        source=body.source or "manual",
        notes=body.notes,
        specializations=body.specializations,
    )
    db.add(recruiter)
    await db.commit()
    await db.refresh(recruiter)
    return _recruiter_to_dict(recruiter)


@router.get("/{recruiter_id}")
async def get_recruiter(
    recruiter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single recruiter with intelligence data."""
    result = await db.execute(select(RecruiterContact).where(RecruiterContact.id == recruiter_id))
    recruiter = result.scalar_one_or_none()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    return _recruiter_to_dict(recruiter)


@router.put("/{recruiter_id}")
async def update_recruiter(
    recruiter_id: UUID,
    body: RecruiterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update recruiter contact details."""
    result = await db.execute(select(RecruiterContact).where(RecruiterContact.id == recruiter_id))
    recruiter = result.scalar_one_or_none()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(recruiter, field, value)
    await db.commit()
    await db.refresh(recruiter)
    return _recruiter_to_dict(recruiter)


@router.delete("/{recruiter_id}")
async def delete_recruiter(
    recruiter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a recruiter contact."""
    result = await db.execute(select(RecruiterContact).where(RecruiterContact.id == recruiter_id))
    recruiter = result.scalar_one_or_none()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    await db.delete(recruiter)
    await db.commit()
    return {"status": "deleted", "id": str(recruiter_id)}


# ─── Intelligence & Ranking ─────────────────────────────────────────────────


@router.post("/{recruiter_id}/interaction")
async def record_interaction(
    recruiter_id: UUID,
    body: RecruiterInteraction,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record an interaction with a recruiter (updates intelligence score)."""
    result = await db.execute(select(RecruiterContact).where(RecruiterContact.id == recruiter_id))
    recruiter = result.scalar_one_or_none()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")

    recruiter.total_interactions = (recruiter.total_interactions or 0) + 1
    recruiter.last_contacted = datetime.now(timezone.utc)

    if body.interaction_type == "response_received":
        recruiter.last_response_at = datetime.now(timezone.utc)
        # Update response rate
        total = recruiter.total_interactions or 1
        recruiter.response_rate = min(100, ((recruiter.response_rate or 0) * (total - 1) + 100) / total)

    if body.interaction_type == "placement":
        recruiter.successful_placements = (recruiter.successful_placements or 0) + 1

    if body.notes:
        existing_notes = recruiter.notes or ""
        recruiter.notes = f"{existing_notes}\n[{datetime.now(timezone.utc).isoformat()}] {body.notes}".strip()

    # Recalculate intelligence score
    recruiter.intelligence_score = _calculate_intelligence_score(recruiter)

    await db.commit()
    await db.refresh(recruiter)
    return _recruiter_to_dict(recruiter)


@router.get("/ranking/top")
async def top_recruiters(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get top-ranked recruiters by intelligence score."""
    result = await db.execute(
        select(RecruiterContact)
        .where(RecruiterContact.intelligence_score > 0)
        .order_by(desc(RecruiterContact.intelligence_score))
        .limit(limit)
    )
    rows = result.scalars().all()
    return {"recruiters": [_recruiter_to_dict(r) for r in rows]}


@router.get("/stats/summary")
async def recruiter_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Recruiter network statistics."""
    total = (await db.execute(select(func.count(RecruiterContact.id)))).scalar() or 0
    avg_score = (await db.execute(select(func.avg(RecruiterContact.intelligence_score)))).scalar() or 0
    by_company = (await db.execute(
        select(RecruiterContact.company, func.count(RecruiterContact.id))
        .where(RecruiterContact.company.isnot(None))
        .group_by(RecruiterContact.company)
        .order_by(desc(func.count(RecruiterContact.id)))
        .limit(10)
    )).all()

    return {
        "total_recruiters": total,
        "avg_intelligence_score": round(float(avg_score), 1),
        "top_companies": {row[0]: row[1] for row in by_company},
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _calculate_intelligence_score(recruiter: RecruiterContact) -> int:
    """Calculate a 0-100 intelligence/ranking score for a recruiter."""
    score = 0.0

    # Response rate (0-40 points)
    rate = float(recruiter.response_rate or 0)
    score += min(40, rate * 0.4)

    # Interaction frequency (0-20 points)
    interactions = recruiter.total_interactions or 0
    score += min(20, interactions * 2)

    # Successful placements (0-25 points)
    placements = recruiter.successful_placements or 0
    score += min(25, placements * 5)

    # Recency bonus (0-15 points)
    if recruiter.last_response_at:
        days_since = (datetime.now(timezone.utc) - recruiter.last_response_at).days
        if days_since <= 7:
            score += 15
        elif days_since <= 30:
            score += 10
        elif days_since <= 90:
            score += 5

    return min(100, int(score))


def _recruiter_to_dict(r: RecruiterContact) -> dict:
    return {
        "id": str(r.id),
        "name": r.name,
        "email": r.email,
        "phone": r.phone,
        "company": r.company,
        "linkedin_url": r.linkedin_url,
        "source": r.source,
        "notes": r.notes,
        "last_contacted": r.last_contacted.isoformat() if r.last_contacted else None,
        "intelligence_score": r.intelligence_score or 0,
        "response_rate": float(r.response_rate or 0),
        "total_interactions": r.total_interactions or 0,
        "successful_placements": r.successful_placements or 0,
        "specializations": r.specializations or [],
        "last_response_at": r.last_response_at.isoformat() if r.last_response_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
