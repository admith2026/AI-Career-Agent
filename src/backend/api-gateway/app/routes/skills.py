"""Saved searches & skill profile routes."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import SavedSearch, UserProfile
from shared.services.skill_engine import (
    ROLE_TEMPLATES,
    SKILL_CATEGORIES,
    get_search_queries_for_skills,
    build_dynamic_profile,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/skills", tags=["Skills & Saved Searches"])


# ─── Skill Engine Endpoints ──────────────────────────────────────────────────


@router.get("/taxonomy")
async def get_skill_taxonomy():
    """Return the full skill taxonomy for the UI skill selector."""
    return {
        "categories": SKILL_CATEGORIES,
        "role_templates": {
            key: {"label": val["label"], "core_skills": val["core_skills"]}
            for key, val in ROLE_TEMPLATES.items()
        },
    }


@router.get("/role-templates")
async def get_role_templates():
    """Return available role templates with their search queries and core skills."""
    return [
        {
            "key": key,
            "label": val["label"],
            "core_skills": val["core_skills"],
            "search_queries": val["search_queries"],
        }
        for key, val in ROLE_TEMPLATES.items()
    ]


class GenerateQueriesRequest(BaseModel):
    skills: list[str] = []
    preferred_roles: list[str] = []
    location: str = "USA"


@router.post("/generate-queries")
async def generate_search_queries(body: GenerateQueriesRequest):
    """Generate JSearch queries based on user skills and preferred roles."""
    queries = get_search_queries_for_skills(
        skills=body.skills,
        preferred_roles=body.preferred_roles,
        location=body.location,
    )
    return {"queries": queries}


@router.get("/profile-preview")
async def preview_dynamic_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview the dynamic AI scoring profile that will be used for job matching."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user["user_id"])
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found — create your profile first")

    profile_str = build_dynamic_profile(
        headline=profile.headline,
        skills=profile.skills or [],
        experience_years=profile.experience_years or 0,
        preferred_technologies=profile.preferred_technologies or [],
        preferred_contract_types=profile.preferred_contract_types or [],
        summary=profile.summary,
    )

    queries = get_search_queries_for_skills(
        skills=profile.skills or [],
        preferred_roles=profile.preferred_roles or [],
    )

    return {
        "scoring_profile": profile_str,
        "generated_queries": queries,
        "skills_count": len(profile.skills or []),
        "roles_count": len(profile.preferred_roles or []),
    }


# ─── Saved Searches ─────────────────────────────────────────────────────────


class SavedSearchCreate(BaseModel):
    name: str
    search_params: dict
    role_categories: list[str] = []
    skills_filter: list[str] = []
    notify_on_match: bool = True
    min_score_threshold: int = 70


class SavedSearchOut(BaseModel):
    id: UUID
    name: str
    search_params: dict
    role_categories: list[str] = []
    skills_filter: list[str] = []
    is_active: bool = True
    notify_on_match: bool = True
    min_score_threshold: int = 70
    match_count: int = 0

    class Config:
        from_attributes = True


@router.get("/saved-searches", response_model=list[SavedSearchOut])
async def list_saved_searches(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all saved searches for the current user."""
    result = await db.execute(
        select(SavedSearch)
        .where(SavedSearch.user_id == current_user["user_id"])
        .order_by(desc(SavedSearch.created_at))
    )
    return result.scalars().all()


@router.post("/saved-searches", response_model=SavedSearchOut, status_code=201)
async def create_saved_search(
    body: SavedSearchCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new saved search."""
    # Limit saved searches per user
    count = (await db.execute(
        select(func.count(SavedSearch.id))
        .where(SavedSearch.user_id == current_user["user_id"])
    )).scalar() or 0

    if count >= 20:
        raise HTTPException(400, "Maximum 20 saved searches allowed")

    search = SavedSearch(
        user_id=current_user["user_id"],
        name=body.name,
        search_params=body.search_params,
        role_categories=body.role_categories,
        skills_filter=body.skills_filter,
        notify_on_match=body.notify_on_match,
        min_score_threshold=body.min_score_threshold,
    )
    db.add(search)
    await db.commit()
    await db.refresh(search)
    return search


@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(
    search_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a saved search."""
    result = await db.execute(
        select(SavedSearch).where(
            SavedSearch.id == search_id,
            SavedSearch.user_id == current_user["user_id"],
        )
    )
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(404, "Saved search not found")

    await db.delete(search)
    await db.commit()
    return {"status": "deleted"}


@router.patch("/saved-searches/{search_id}/toggle")
async def toggle_saved_search(
    search_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a saved search active/inactive."""
    result = await db.execute(
        select(SavedSearch).where(
            SavedSearch.id == search_id,
            SavedSearch.user_id == current_user["user_id"],
        )
    )
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(404, "Saved search not found")

    search.is_active = not search.is_active
    await db.commit()
    return {"id": str(search.id), "is_active": search.is_active}
