"""Standalone notification helpers for the job-hunt pipeline.

Provides direct Telegram, Email (SMTP/Gmail), and Twilio WhatsApp delivery
without requiring a database user record.  These are lightweight wrappers
used by the scheduled job-hunt Celery task.
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
import aiosmtplib

from shared.config import BaseServiceSettings

logger = logging.getLogger(__name__)


# ── Telegram ─────────────────────────────────────────────────────────────────

async def send_telegram_alert(chat_id: str, message: str) -> bool:
    """Send a Markdown message via Telegram Bot API."""
    settings = BaseServiceSettings()
    token = settings.telegram_bot_token

    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — skipping Telegram")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
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
            logger.info("Telegram alert sent to chat %s", chat_id)
            return True
        except Exception:
            logger.exception("Telegram send failed for chat %s", chat_id)
            return False


# ── Email (Gmail SMTP) ───────────────────────────────────────────────────────

async def send_email_alert(to_email: str, subject: str, body_html: str) -> bool:
    """Send an HTML email via Gmail SMTP."""
    settings = BaseServiceSettings()
    user = settings.email_user
    password = settings.email_pass

    if not user or not password:
        logger.warning("EMAIL_USER / EMAIL_PASS not configured — skipping email")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"AI Career Agent <{user}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            username=user,
            password=password,
            start_tls=True,
        )
        logger.info("Email alert sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Email send failed to %s", to_email)
        return False


# ── Twilio WhatsApp ──────────────────────────────────────────────────────────

async def send_whatsapp_alert(to_number: str, message: str) -> bool:
    """Send a WhatsApp message via Twilio API.

    ``to_number`` should be in E.164 format, e.g. ``+14155238886``.
    """
    settings = BaseServiceSettings()
    sid = settings.twilio_account_sid
    token = settings.twilio_auth_token

    if not sid or not token:
        logger.warning("TWILIO credentials not configured — skipping WhatsApp")
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    payload = {
        "From": "whatsapp:+14155238886",  # Twilio sandbox number
        "To": f"whatsapp:{to_number}",
        "Body": message,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(url, data=payload, auth=(sid, token))
            resp.raise_for_status()
            logger.info("Twilio WhatsApp message sent to %s", to_number)
            return True
        except Exception:
            logger.exception("Twilio WhatsApp send failed to %s", to_number)
            return False
