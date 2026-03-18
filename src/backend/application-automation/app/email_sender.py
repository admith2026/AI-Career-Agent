"""Email sending utility using aiosmtplib."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from .config import settings

logger = logging.getLogger(__name__)


async def send_application_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> bool:
    """Send an application/outreach email via SMTP."""
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP credentials not configured — email not sent")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    if body_text:
        msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info("Application email sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False
