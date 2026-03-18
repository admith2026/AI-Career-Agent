"""WhatsApp Cloud API notification channel."""

import logging

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


async def send_whatsapp(phone_number: str, message: str) -> bool:
    """Send a text message via WhatsApp Cloud API."""
    if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
        logger.warning("WhatsApp credentials not configured")
        return False

    url = f"{settings.whatsapp_api_url}/{settings.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message},
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("WhatsApp message sent to %s", phone_number)
            return True
        except Exception:
            logger.exception("Failed to send WhatsApp message to %s", phone_number)
            return False
