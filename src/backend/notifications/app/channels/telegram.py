"""Telegram Bot API notification channel."""

import logging

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org/bot{token}"


async def send_telegram(chat_id: str, message: str) -> bool:
    """Send a message via Telegram Bot API."""
    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not configured")
        return False

    url = f"{_API_BASE.format(token=settings.telegram_bot_token)}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info("Telegram message sent to chat %s", chat_id)
            return True
        except Exception:
            logger.exception("Failed to send Telegram message to %s", chat_id)
            return False
