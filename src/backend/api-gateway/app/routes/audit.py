"""Audit logging routes and middleware."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["Audit"])


async def log_action(
    db: AsyncSession,
    user_id: UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    """Record an audit log entry."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()


@router.get("/logs")
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    action: str | None = None,
    resource_type: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit log entries for the current user."""
    query = select(AuditLog).where(AuditLog.user_id == current_user["user_id"])

    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    query = query.order_by(desc(AuditLog.created_at)).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "details": r.details,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/stats")
async def audit_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit log statistics."""
    total = (await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.user_id == current_user["user_id"])
    )).scalar() or 0

    by_action = (await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .where(AuditLog.user_id == current_user["user_id"])
        .group_by(AuditLog.action)
        .order_by(desc(func.count(AuditLog.id)))
        .limit(20)
    )).all()

    return {
        "total": total,
        "by_action": {row[0]: row[1] for row in by_action},
    }
