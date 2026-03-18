"""Event consumer — listens for notification.send events and dispatches them."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import async_session_factory
from shared.events import EventBus, Exchanges
from shared.models import User

from .dispatcher import dispatch_notification

logger = logging.getLogger(__name__)


async def _handle_send_notification(data: dict) -> None:
    """Handle a send-notification event from other services."""
    user_id_str = data.get("user_id")
    subject = data.get("subject", "Career Agent Notification")
    body = data.get("body", "")
    job_ids_raw = data.get("job_ids", [])

    if not user_id_str or not body:
        return

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return

    job_ids = []
    for jid in job_ids_raw:
        try:
            job_ids.append(UUID(str(jid)))
        except ValueError:
            pass

    async with async_session_factory() as db:
        user = await db.get(User, user_id)
        if not user:
            logger.warning("User %s not found for notification", user_id)
            return

        channels = await dispatch_notification(user, subject, body, db, job_ids)
        logger.info("Notification dispatched to user %s via %s", user_id, channels)


async def start_consumer(event_bus: EventBus) -> None:
    """Subscribe to notification events."""
    await event_bus.subscribe(
        Exchanges.SEND_NOTIFICATION,
        "notifications.send",
        _handle_send_notification,
    )
    logger.info("Notification event consumer started")
