"""MCP-style (Model Context Protocol) tool handler registry.

Provides a tool registry where each tool is a callable with a schema definition.
The agent orchestrator can invoke tools by name, passing structured arguments.
Tools wrap calls to downstream microservices.
"""

import logging
from typing import Any, Callable, Awaitable
from pydantic import BaseModel

import httpx

from .config import settings

logger = logging.getLogger(__name__)

# ─── Tool Definition ─────────────────────────────────────────────────────────


class ToolParameter(BaseModel):
    name: str
    type: str = "string"
    description: str = ""
    required: bool = False


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: list[ToolParameter] = []
    category: str = "general"


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None


# ─── Registry ────────────────────────────────────────────────────────────────

_tools: dict[str, tuple[ToolDefinition, Callable[..., Awaitable[ToolResult]]]] = {}


def register_tool(definition: ToolDefinition):
    """Decorator to register an async tool handler."""

    def decorator(fn: Callable[..., Awaitable[ToolResult]]):
        _tools[definition.name] = (definition, fn)
        return fn

    return decorator


def list_tools() -> list[ToolDefinition]:
    return [defn for defn, _ in _tools.values()]


async def invoke_tool(name: str, arguments: dict[str, Any]) -> ToolResult:
    """Look up and execute a registered tool."""
    entry = _tools.get(name)
    if not entry:
        return ToolResult(tool_name=name, success=False, error=f"Unknown tool: {name}")
    definition, handler = entry
    try:
        return await handler(**arguments)
    except Exception as e:
        logger.exception("Tool %s failed", name)
        return ToolResult(tool_name=name, success=False, error=str(e))


# ─── Built-in Tools ─────────────────────────────────────────────────────────

_http = httpx.AsyncClient(timeout=30.0)


@register_tool(ToolDefinition(
    name="search_jobs",
    description="Search for job listings with filters",
    category="job_discovery",
    parameters=[
        ToolParameter(name="query", description="Search text", required=False),
        ToolParameter(name="source", description="Job source filter"),
        ToolParameter(name="remote_only", type="boolean", description="Only remote jobs"),
        ToolParameter(name="min_score", type="integer", description="Minimum match score"),
        ToolParameter(name="page", type="integer", description="Page number"),
    ],
))
async def search_jobs(
    query: str = "",
    source: str = "",
    remote_only: bool = False,
    min_score: int | None = None,
    page: int = 1,
) -> ToolResult:
    params: dict[str, Any] = {"page": page, "page_size": 20}
    if query:
        params["search"] = query
    if source:
        params["source"] = source
    if remote_only:
        params["remote_only"] = True
    if min_score is not None:
        params["min_score"] = min_score
    resp = await _http.get(f"{settings.job_discovery_url}/api/jobs", params=params)
    resp.raise_for_status()
    return ToolResult(tool_name="search_jobs", success=True, data=resp.json())


@register_tool(ToolDefinition(
    name="analyze_job",
    description="Analyze a job posting and get a match score",
    category="intelligence",
    parameters=[
        ToolParameter(name="job_id", description="Job UUID", required=True),
        ToolParameter(name="job_title", description="Job title", required=True),
        ToolParameter(name="company_name", description="Company name"),
        ToolParameter(name="job_description", description="Full job description"),
        ToolParameter(name="job_link", description="Job URL", required=True),
    ],
))
async def analyze_job_tool(
    job_id: str = "",
    job_title: str = "",
    company_name: str = "",
    job_description: str = "",
    job_link: str = "",
) -> ToolResult:
    payload = {
        "job_id": job_id,
        "job_title": job_title,
        "company_name": company_name,
        "job_description": job_description,
        "job_link": job_link,
    }
    resp = await _http.post(f"{settings.job_intelligence_url}/api/analyze", json=payload)
    resp.raise_for_status()
    return ToolResult(tool_name="analyze_job", success=True, data=resp.json())


@register_tool(ToolDefinition(
    name="generate_resume",
    description="Generate a tailored resume for a specific job",
    category="resume",
    parameters=[
        ToolParameter(name="user_id", description="User UUID", required=True),
        ToolParameter(name="job_id", description="Job UUID", required=True),
    ],
))
async def generate_resume_tool(user_id: str = "", job_id: str = "") -> ToolResult:
    resp = await _http.post(
        f"{settings.resume_generator_url}/api/generate-resume",
        json={"user_id": user_id, "job_id": job_id},
    )
    resp.raise_for_status()
    return ToolResult(tool_name="generate_resume", success=True, data=resp.json())


@register_tool(ToolDefinition(
    name="apply_to_job",
    description="Submit an application for a job",
    category="application",
    parameters=[
        ToolParameter(name="user_id", description="User UUID", required=True),
        ToolParameter(name="job_id", description="Job UUID", required=True),
    ],
))
async def apply_to_job_tool(user_id: str = "", job_id: str = "") -> ToolResult:
    resp = await _http.post(
        f"{settings.application_automation_url}/api/applications",
        json={"user_id": user_id, "job_id": job_id},
    )
    resp.raise_for_status()
    return ToolResult(tool_name="apply_to_job", success=True, data=resp.json())


@register_tool(ToolDefinition(
    name="semantic_job_search",
    description="Find jobs semantically similar to a user profile or query",
    category="intelligence",
    parameters=[
        ToolParameter(name="query", description="Natural language search query"),
        ToolParameter(name="skills", type="array", description="User skills list"),
        ToolParameter(name="limit", type="integer", description="Max results"),
    ],
))
async def semantic_job_search_tool(
    query: str = "",
    skills: list[str] | None = None,
    limit: int = 20,
) -> ToolResult:
    payload: dict[str, Any] = {"limit": limit}
    if query:
        payload["query"] = query
    if skills:
        payload["skills"] = skills
    resp = await _http.post(
        f"{settings.job_intelligence_url}/api/semantic-search",
        json=payload,
    )
    resp.raise_for_status()
    return ToolResult(tool_name="semantic_job_search", success=True, data=resp.json())


@register_tool(ToolDefinition(
    name="send_notification",
    description="Send a notification to a user via their configured channels",
    category="notification",
    parameters=[
        ToolParameter(name="user_id", description="User UUID", required=True),
        ToolParameter(name="subject", description="Notification subject", required=True),
        ToolParameter(name="body", description="Notification body", required=True),
    ],
))
async def send_notification_tool(
    user_id: str = "",
    subject: str = "",
    body: str = "",
) -> ToolResult:
    resp = await _http.post(
        f"http://localhost:5005/api/notifications/send",
        json={"user_id": user_id, "subject": subject, "body": body},
    )
    resp.raise_for_status()
    return ToolResult(tool_name="send_notification", success=True, data=resp.json())


@register_tool(ToolDefinition(
    name="get_application_stats",
    description="Get application statistics for a user",
    category="application",
    parameters=[],
))
async def get_application_stats_tool() -> ToolResult:
    resp = await _http.get(f"{settings.application_automation_url}/api/applications/stats/summary")
    resp.raise_for_status()
    return ToolResult(tool_name="get_application_stats", success=True, data=resp.json())


@register_tool(ToolDefinition(
    name="trigger_crawl",
    description="Trigger a job crawl cycle to discover new listings",
    category="crawl",
    parameters=[],
))
async def trigger_crawl_tool() -> ToolResult:
    resp = await _http.post(f"{settings.job_discovery_url}/api/crawl/trigger")
    resp.raise_for_status()
    return ToolResult(tool_name="trigger_crawl", success=True, data=resp.json())


@register_tool(ToolDefinition(
    name="interview_prep",
    description="Generate interview preparation materials",
    category="interview",
    parameters=[
        ToolParameter(name="job_title", description="Role title", required=True),
        ToolParameter(name="company_name", description="Company name"),
        ToolParameter(name="job_description", description="Job description"),
    ],
))
async def interview_prep_tool(
    job_title: str = "",
    company_name: str = "",
    job_description: str = "",
) -> ToolResult:
    resp = await _http.post(
        f"{settings.interview_ai_url}/api/interview/prep",
        json={
            "job_title": job_title,
            "company_name": company_name,
            "job_description": job_description,
        },
    )
    resp.raise_for_status()
    return ToolResult(tool_name="interview_prep", success=True, data=resp.json())


@register_tool(ToolDefinition(
    name="negotiate_offer",
    description="Analyze and create a negotiation strategy for a job offer",
    category="negotiation",
    parameters=[
        ToolParameter(name="job_title", description="Role title", required=True),
        ToolParameter(name="offered_rate", description="Offered rate/salary"),
        ToolParameter(name="experience_years", type="integer", description="Years of experience"),
    ],
))
async def negotiate_offer_tool(
    job_title: str = "",
    offered_rate: str = "",
    experience_years: int = 0,
) -> ToolResult:
    resp = await _http.post(
        f"{settings.negotiation_ai_url}/api/negotiation/analyze",
        json={
            "job_title": job_title,
            "offered_rate": offered_rate,
            "experience_years": experience_years,
        },
    )
    resp.raise_for_status()
    return ToolResult(tool_name="negotiate_offer", success=True, data=resp.json())
