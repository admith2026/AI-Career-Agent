"""User profile routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import User, UserProfile
from shared.schemas import ProfileOut, ProfileUpdate, NotificationPreferences

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("", response_model=ProfileOut)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user["user_id"])
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile


@router.put("", response_model=ProfileOut)
async def update_profile(
    body: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user["user_id"])
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=current_user["user_id"])
        db.add(profile)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.put("/notifications")
async def update_notification_prefs(
    prefs: NotificationPreferences,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    user.notification_preferences = prefs.model_dump()
    await db.commit()
    return prefs
