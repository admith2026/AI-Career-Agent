"""Subscription & Billing API routes."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import Subscription, UsageRecord, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])

PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "monthly_applications": 10,
        "features": {"ai_chat": True, "job_feed": True, "analytics": False, "agents": False, "voice_ai": False, "marketplace": False},
    },
    "starter": {
        "name": "Starter",
        "price": 29,
        "monthly_applications": 100,
        "features": {"ai_chat": True, "job_feed": True, "analytics": True, "agents": True, "voice_ai": False, "marketplace": False},
    },
    "pro": {
        "name": "Pro",
        "price": 79,
        "monthly_applications": 500,
        "features": {"ai_chat": True, "job_feed": True, "analytics": True, "agents": True, "voice_ai": True, "marketplace": True},
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 199,
        "monthly_applications": -1,  # unlimited
        "features": {"ai_chat": True, "job_feed": True, "analytics": True, "agents": True, "voice_ai": True, "marketplace": True, "api_access": True, "priority_support": True},
    },
}


@router.get("/plans")
async def list_plans():
    """List all available subscription plans."""
    return {"plans": [{"id": k, **v} for k, v in PLANS.items()]}


@router.get("/subscription")
async def get_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get the current user's subscription."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user["user_id"])
    )
    sub = result.scalar_one_or_none()
    if not sub:
        # Auto-create free subscription
        sub = Subscription(
            user_id=current_user["user_id"],
            plan="free",
            status="active",
            monthly_applications_limit=PLANS["free"]["monthly_applications"],
            features=PLANS["free"]["features"],
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.add(sub)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=401, detail="User account not found. Please log out and register again.")
        await db.refresh(sub)

    return {
        "id": str(sub.id),
        "plan": sub.plan,
        "plan_details": PLANS.get(sub.plan, {}),
        "status": sub.status,
        "monthly_applications_limit": sub.monthly_applications_limit,
        "monthly_applications_used": sub.monthly_applications_used,
        "features": sub.features,
        "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "cancel_at_period_end": sub.cancel_at_period_end,
    }


@router.post("/subscribe")
async def subscribe(
    plan: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Subscribe to or change plan."""
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {list(PLANS.keys())}")

    plan_details = PLANS[plan]
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user["user_id"])
    )
    sub = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if sub:
        sub.plan = plan
        sub.status = "active"
        sub.monthly_applications_limit = plan_details["monthly_applications"]
        sub.features = plan_details["features"]
        sub.current_period_start = now
        sub.current_period_end = now + timedelta(days=30)
        sub.cancel_at_period_end = False
    else:
        sub = Subscription(
            user_id=current_user["user_id"],
            plan=plan,
            status="active",
            monthly_applications_limit=plan_details["monthly_applications"],
            features=plan_details["features"],
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        db.add(sub)

    await db.commit()
    await db.refresh(sub)
    return {"id": str(sub.id), "plan": sub.plan, "status": "active", "message": f"Subscribed to {plan_details['name']} plan"}


@router.post("/cancel")
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cancel current subscription at period end."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user["user_id"])
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")
    sub.cancel_at_period_end = True
    await db.commit()
    return {"status": "canceled", "effective_at": sub.current_period_end.isoformat() if sub.current_period_end else None}


@router.get("/usage")
async def get_usage(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get usage records for the current user."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(UsageRecord)
        .where(UsageRecord.user_id == current_user["user_id"], UsageRecord.created_at >= since)
        .order_by(UsageRecord.created_at.desc())
        .limit(200)
    )
    records = result.scalars().all()

    # Aggregate by type
    by_type: dict[str, int] = {}
    for r in records:
        by_type[r.action_type] = by_type.get(r.action_type, 0) + r.credits_used

    return {
        "records_count": len(records),
        "total_credits": sum(r.credits_used for r in records),
        "by_type": by_type,
        "records": [
            {
                "id": str(r.id),
                "action_type": r.action_type,
                "credits_used": r.credits_used,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records[:50]
        ],
    }


@router.post("/usage/record")
async def record_usage(
    action_type: str,
    credits: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record a usage event (internal use by other services)."""
    record = UsageRecord(
        user_id=current_user["user_id"],
        action_type=action_type,
        credits_used=credits,
    )
    db.add(record)

    # Increment application counter if applicable
    if action_type == "application":
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == current_user["user_id"])
        )
        sub = result.scalar_one_or_none()
        if sub:
            if sub.monthly_applications_limit != -1 and sub.monthly_applications_used >= sub.monthly_applications_limit:
                raise HTTPException(status_code=429, detail="Monthly application limit reached. Upgrade your plan.")
            sub.monthly_applications_used = (sub.monthly_applications_used or 0) + 1

    await db.commit()
    return {"status": "recorded", "action_type": action_type, "credits": credits}


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get billing stats."""
    user_id = current_user["user_id"]

    sub_q = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    sub = sub_q.scalar_one_or_none()

    total_usage_q = await db.execute(
        select(func.sum(UsageRecord.credits_used)).where(UsageRecord.user_id == user_id)
    )
    total_usage = total_usage_q.scalar() or 0

    return {
        "plan": sub.plan if sub else "free",
        "status": sub.status if sub else "none",
        "applications_used": sub.monthly_applications_used if sub else 0,
        "applications_limit": sub.monthly_applications_limit if sub else 10,
        "total_credits_used": total_usage,
    }
