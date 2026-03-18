"""n8n / Automation Webhook endpoints.

Provides inbound webhook URLs that n8n (or any automation platform) can call
to trigger actions in the Career Agent platform.  Each webhook validates a
shared secret token for security.
"""

import hmac
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

# Shared secret — set via WEBHOOK_SECRET env var
WEBHOOK_SECRET = getattr(settings, "webhook_secret", "")


def _verify_secret(token: str | None) -> None:
    """Validate the inbound webhook token."""
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not configured — rejecting all webhook requests")
        raise HTTPException(status_code=403, detail="Webhook secret not configured")
    if not token or not hmac.compare_digest(token, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid webhook token")


# ─── Webhook Payloads ────────────────────────────────────────────────────────


class JobWebhookPayload(BaseModel):
    source: str = "n8n"
    job_title: str
    company_name: str | None = None
    job_link: str
    job_description: str | None = None
    location: str | None = None
    salary_or_rate: str | None = None
    is_remote: bool = True
    contract_type: str | None = None


class NotificationWebhookPayload(BaseModel):
    user_email: str
    subject: str
    body: str
    channels: list[str] = ["email"]


class CrawlWebhookPayload(BaseModel):
    sources: list[str] = []  # empty = all


class ApplicationWebhookPayload(BaseModel):
    user_email: str
    job_id: str
    auto_generate_resume: bool = True


# ─── Webhook Handlers ────────────────────────────────────────────────────────


@router.post("/job-discovered")
async def webhook_job_discovered(
    payload: JobWebhookPayload,
    x_webhook_token: str | None = Header(None),
):
    """n8n hook: push a new job into the system (bypasses crawlers)."""
    _verify_secret(x_webhook_token)

    import httpx
    async with httpx.AsyncClient(timeout=20) as client:
        # Forward to job-discovery to persist and publish event
        resp = await client.post(
            f"{settings.job_discovery_url}/api/jobs/ingest",
            json=payload.model_dump(),
        )
    status = resp.status_code
    return {"status": "accepted" if status < 400 else "error", "upstream_status": status}


@router.post("/trigger-crawl")
async def webhook_trigger_crawl(
    payload: CrawlWebhookPayload | None = None,
    x_webhook_token: str | None = Header(None),
):
    """n8n hook: trigger a crawl cycle."""
    _verify_secret(x_webhook_token)

    import httpx
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{settings.job_discovery_url}/api/crawl/trigger")
    return {"status": "triggered", "result": resp.json()}


@router.post("/send-notification")
async def webhook_send_notification(
    payload: NotificationWebhookPayload,
    x_webhook_token: str | None = Header(None),
):
    """n8n hook: send a notification to a user."""
    _verify_secret(x_webhook_token)

    import httpx
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{settings.notifications_url}/api/notifications/send",
            json={"email": payload.user_email, "subject": payload.subject, "body": payload.body},
        )
    return {"status": "sent" if resp.status_code < 400 else "error"}


@router.post("/auto-apply")
async def webhook_auto_apply(
    payload: ApplicationWebhookPayload,
    x_webhook_token: str | None = Header(None),
):
    """n8n hook: apply to a job for a user."""
    _verify_secret(x_webhook_token)

    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.application_automation_url}/api/applications",
            json={"job_id": payload.job_id, "user_id": payload.user_email},
        )
    return {"status": "applied" if resp.status_code < 400 else "error", "detail": resp.json()}


@router.post("/pipeline-run")
async def webhook_run_pipeline(
    x_webhook_token: str | None = Header(None),
):
    """n8n hook: trigger the full automation pipeline."""
    _verify_secret(x_webhook_token)

    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.agent_orchestrator_url}/api/agents/pipeline/run",
        )
    return {"status": "started", "result": resp.json()}


@router.get("/status")
async def webhook_status():
    """Check webhook subsystem health and list available endpoints."""
    return {
        "status": "active",
        "endpoints": [
            "/api/webhooks/job-discovered",
            "/api/webhooks/trigger-crawl",
            "/api/webhooks/send-notification",
            "/api/webhooks/auto-apply",
            "/api/webhooks/pipeline-run",
        ],
    }
