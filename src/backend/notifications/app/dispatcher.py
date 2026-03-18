"""Notification dispatcher — intelligent omni-channel routing."""

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Notification, User

from .channels.telegram import send_telegram
from .channels.whatsapp import send_whatsapp
from .channels.email_channel import send_email_notification

logger = logging.getLogger(__name__)

# Priority keywords that trigger urgent routing (instant push to all channels)
URGENT_KEYWORDS = {"interview", "offer", "deadline", "expiring", "urgent", "accepted"}
# Keywords for digest-worthy (can batch into daily summary)
DIGEST_KEYWORDS = {"discovered", "crawl", "weekly", "summary", "digest"}


def _classify_priority(subject: str, body: str) -> str:
    """Classify notification priority based on content analysis."""
    text = f"{subject} {body}".lower()
    if any(kw in text for kw in URGENT_KEYWORDS):
        return "urgent"
    if any(kw in text for kw in DIGEST_KEYWORDS):
        return "low"
    return "normal"


async def dispatch_notification(
    user: User,
    subject: str,
    body: str,
    db: AsyncSession,
    job_ids: list[UUID] | None = None,
    priority: str | None = None,
) -> list[str]:
    """Send notification through intelligently selected channels.

    Routing logic:
    - urgent: All enabled channels simultaneously
    - normal: Preferred channel (telegram > whatsapp > email)
    - low: Email only (or preferred channel if email not configured)
    """

    prefs = user.notification_preferences or {}
    channels_sent: list[str] = []

    # Auto-detect priority if not explicitly provided
    if not priority:
        priority = _classify_priority(subject, body)

    if priority == "urgent":
        # Send to ALL enabled channels
        if prefs.get("telegram") and user.telegram_chat_id:
            text = f"🚨 *{subject}*\n\n{body}"
            if await send_telegram(user.telegram_chat_id, text):
                channels_sent.append("telegram")
        if prefs.get("whatsapp") and user.whatsapp_number:
            text = f"🚨 {subject}\n\n{body}"
            if await send_whatsapp(user.whatsapp_number, text):
                channels_sent.append("whatsapp")
        if prefs.get("email") and user.email:
            html = f"<h2>🚨 {subject}</h2><p>{body}</p>"
            if await send_email_notification(user.email, f"[URGENT] {subject}", html):
                channels_sent.append("email")

    elif priority == "low":
        # Email only for low-priority (digest-type) notifications
        if prefs.get("email") and user.email:
            html = f"<h2>{subject}</h2><p>{body}</p>"
            if await send_email_notification(user.email, subject, html):
                channels_sent.append("email")
        elif prefs.get("telegram") and user.telegram_chat_id:
            if await send_telegram(user.telegram_chat_id, f"*{subject}*\n\n{body}"):
                channels_sent.append("telegram")

    else:
        # Normal: use preferred channel cascade (telegram > whatsapp > email)
        sent = False
        if prefs.get("telegram") and user.telegram_chat_id:
            text = f"*{subject}*\n\n{body}"
            if await send_telegram(user.telegram_chat_id, text):
                channels_sent.append("telegram")
                sent = True
        if not sent and prefs.get("whatsapp") and user.whatsapp_number:
            text = f"{subject}\n\n{body}"
            if await send_whatsapp(user.whatsapp_number, text):
                channels_sent.append("whatsapp")
                sent = True
        if not sent and prefs.get("email") and user.email:
            html = f"<h2>{subject}</h2><p>{body}</p>"
            if await send_email_notification(user.email, subject, html):
                channels_sent.append("email")

    # Persist a notification record per channel
    for ch in channels_sent:
        notification = Notification(
            id=uuid4(),
            user_id=user.id,
            channel=ch,
            subject=subject,
            body=body,
            job_ids=job_ids or [],
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
        db.add(notification)

    # If nothing was sent, still record it as pending
    if not channels_sent:
        notification = Notification(
            id=uuid4(),
            user_id=user.id,
            channel="none",
            subject=subject,
            body=body,
            job_ids=job_ids or [],
            status="pending",
        )
        db.add(notification)

    await db.commit()
    return channels_sent
