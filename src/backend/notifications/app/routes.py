"""API routes for Notification service."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import Notification, User
from shared.schemas import NotificationOut

from .dispatcher import dispatch_notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List notifications for the current user."""
    query = (
        select(Notification)
        .where(Notification.user_id == current_user["user_id"])
        .order_by(desc(Notification.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    rows = result.scalars().all()
    return [NotificationOut.model_validate(r) for r in rows]


@router.post("/send")
async def send_notification(
    subject: str,
    body: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Manually trigger a notification to the current user (for testing)."""
    user = await db.get(User, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    channels = await dispatch_notification(
        user=user,
        subject=subject,
        body=body,
        db=db,
    )
    return {"status": "sent", "channels": channels}


@router.get("/{notification_id}", response_model=NotificationOut)
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single notification."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user["user_id"],
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationOut.model_validate(notif)


# ─── Channel Preferences & Multi-channel ─────────────────────────────────────


class ChannelPreferences(BaseModel):
    email: bool = True
    telegram: bool = False
    whatsapp: bool = False
    push: bool = True


@router.put("/preferences")
async def update_notification_preferences(
    prefs: ChannelPreferences,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update notification channel preferences."""
    user = await db.get(User, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.notification_preferences = prefs.model_dump()
    await db.commit()
    return {"status": "updated", "preferences": prefs.model_dump()}


@router.get("/preferences")
async def get_notification_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get current notification channel preferences."""
    user = await db.get(User, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.notification_preferences or {"email": True, "telegram": False, "whatsapp": False, "push": True}


class TelegramSetup(BaseModel):
    chat_id: str


@router.post("/setup/telegram")
async def setup_telegram(
    body: TelegramSetup,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Configure Telegram chat ID for notifications."""
    user = await db.get(User, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.telegram_chat_id = body.chat_id
    prefs = user.notification_preferences or {}
    prefs["telegram"] = True
    user.notification_preferences = prefs
    await db.commit()

    # Send test message
    from .channels.telegram import send_telegram
    sent = await send_telegram(body.chat_id, "AI Career Agent connected! You'll receive job alerts here.")
    return {"status": "configured", "test_sent": sent}


class WhatsAppSetup(BaseModel):
    phone_number: str


@router.post("/setup/whatsapp")
async def setup_whatsapp(
    body: WhatsAppSetup,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Configure WhatsApp number for notifications."""
    user = await db.get(User, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.whatsapp_number = body.phone_number
    prefs = user.notification_preferences or {}
    prefs["whatsapp"] = True
    user.notification_preferences = prefs
    await db.commit()

    from .channels.whatsapp import send_whatsapp
    sent = await send_whatsapp(body.phone_number, "AI Career Agent connected! You'll receive job alerts here.")
    return {"status": "configured", "test_sent": sent}


@router.post("/test/{channel}")
async def test_channel(
    channel: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Send a test notification on a specific channel."""
    user = await db.get(User, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    subject = "Test Notification"
    body = "This is a test notification from AI Career Agent."
    sent = False

    if channel == "telegram":
        from .channels.telegram import send_telegram
        if user.telegram_chat_id:
            sent = await send_telegram(user.telegram_chat_id, f"*{subject}*\n\n{body}")
    elif channel == "whatsapp":
        from .channels.whatsapp import send_whatsapp
        if user.whatsapp_number:
            sent = await send_whatsapp(user.whatsapp_number, f"{subject}\n\n{body}")
    elif channel == "email":
        from .channels.email_channel import send_email_notification
        sent = await send_email_notification(user.email, subject, f"<h2>{subject}</h2><p>{body}</p>")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown channel: {channel}")

    return {"channel": channel, "sent": sent}


@router.get("/stats")
async def notification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get notification statistics."""
    user_id = current_user["user_id"]
    total = (await db.execute(
        select(func.count(Notification.id)).where(Notification.user_id == user_id)
    )).scalar() or 0

    by_channel = (await db.execute(
        select(Notification.channel, func.count(Notification.id))
        .where(Notification.user_id == user_id)
        .group_by(Notification.channel)
    )).all()

    by_status = (await db.execute(
        select(Notification.status, func.count(Notification.id))
        .where(Notification.user_id == user_id)
        .group_by(Notification.status)
    )).all()

    return {
        "total": total,
        "by_channel": {row[0]: row[1] for row in by_channel},
        "by_status": {row[0]: row[1] for row in by_status},
    }
