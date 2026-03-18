"""Proxy routes — forwards requests to downstream microservices."""

import logging

import httpx
from fastapi import APIRouter, Request, Response

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Proxy"])

SERVICE_MAP = {
    "/api/jobs": settings.job_discovery_url,
    "/api/analyze": settings.job_intelligence_url,
    "/api/semantic-search": settings.job_intelligence_url,
    "/api/vector-stats": settings.job_intelligence_url,
    "/api/generate-resume": settings.resume_generator_url,
    "/api/applications": settings.application_automation_url,
    "/api/auto-apply": settings.application_automation_url,
    "/api/follow-ups": settings.application_automation_url,
    "/api/notifications": settings.notifications_url,
    "/api/crawl": settings.crawl_engine_url,
    "/api/pipeline": settings.data_pipeline_url,
    "/api/graph": settings.knowledge_graph_url,
    "/api/decisions": settings.decision_engine_url,
    # Blackhole services
    "/api/predictions": settings.predictive_ai_url,
    "/api/linkedin": settings.linkedin_automation_url,
    "/api/voice": settings.voice_ai_url,
    "/api/interview": settings.interview_ai_url,
    "/api/negotiation": settings.negotiation_ai_url,
    "/api/freelance": settings.freelance_bidding_url,
    "/api/content": settings.demand_generation_url,
    # SaaS services
    "/api/agents": settings.agent_orchestrator_url,
    "/api/billing": settings.subscription_url,
    "/api/marketplace": settings.marketplace_url,
}


def _resolve_upstream(path: str) -> tuple[str, str] | None:
    for prefix, base_url in SERVICE_MAP.items():
        if path.startswith(prefix):
            return base_url, path
    return None


@router.api_route(
    "/api/{service_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def proxy(request: Request, service_path: str):
    """Reverse-proxy unmatched /api/* routes to the correct microservice."""
    full_path = f"/api/{service_path}"
    resolved = _resolve_upstream(full_path)

    if not resolved:
        return Response(content='{"detail":"Service not found"}', status_code=404, media_type="application/json")

    base_url, path = resolved
    target_url = f"{base_url}{path}"

    # Forward query params
    if request.url.query:
        target_url += f"?{request.url.query}"

    # Forward headers (strip host)
    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )
    except (httpx.ConnectError, httpx.ConnectTimeout):
        logger.warning("Upstream service unavailable: %s", target_url)
        return Response(
            content='{"detail":"Service temporarily unavailable"}',
            status_code=503,
            media_type="application/json",
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        media_type=resp.headers.get("content-type"),
    )
