"""Autonomous Task Executor — executes agent tasks by calling downstream services.

When tasks are created (queued), the executor picks them up, calls the
appropriate microservice, and stores the result. This transforms the
orchestrator from a passive task recorder into an active autonomous system.
"""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import async_session_factory
from shared.models import AgentTask, Job, JobAnalysis

from .config import settings
from .mcp_tools import invoke_tool

logger = logging.getLogger(__name__)

_http = httpx.AsyncClient(timeout=60.0)

# Maps (agent_type, task_type) → execution handler
TASK_HANDLERS: dict[tuple[str, str], str] = {
    ("discovery", "scan_jobs"): "_exec_scan_jobs",
    ("matching", "score_jobs"): "_exec_score_jobs",
    ("application", "auto_apply"): "_exec_auto_apply",
    ("outreach", "send_outreach"): "_exec_send_outreach",
    ("follow_up", "schedule_follow_ups"): "_exec_follow_ups",
    ("interview", "prep"): "_exec_interview_prep",
    ("negotiation", "analyze"): "_exec_negotiation",
}


async def _exec_scan_jobs(task: AgentTask, db: AsyncSession) -> dict:
    """Trigger a job crawl cycle and fetch latest jobs."""
    try:
        resp = await _http.post(f"{settings.job_discovery_url}/api/crawl/trigger")
        resp.raise_for_status()
        crawl_result = resp.json()
    except Exception:
        crawl_result = {"status": "crawl_skipped"}

    # Also invoke MCP tool for JSearch
    search_result = await invoke_tool("search_jobs", {"query": "", "page": 1})
    job_count = 0
    if search_result.success and search_result.data:
        job_count = search_result.data.get("total", 0) if isinstance(search_result.data, dict) else 0

    return {
        "action": "scan_jobs",
        "crawl": crawl_result,
        "jobs_found": job_count,
        "status": "completed",
    }


async def _exec_score_jobs(task: AgentTask, db: AsyncSession) -> dict:
    """Score unscored jobs through the intelligence service."""
    result = await db.execute(
        select(Job)
        .outerjoin(JobAnalysis)
        .where(JobAnalysis.id.is_(None), Job.is_active.is_(True))
        .limit(10)
    )
    unscored = result.scalars().all()
    scored = 0
    for job in unscored:
        try:
            tool_result = await invoke_tool("analyze_job", {
                "job_id": str(job.id),
                "job_title": job.job_title or "",
                "company_name": job.company_name or "",
                "job_description": job.job_description or "",
                "job_link": job.job_link or "",
            })
            if tool_result.success:
                scored += 1
        except Exception:
            logger.warning("Failed to score job %s", job.id)

    return {"action": "score_jobs", "unscored_found": len(unscored), "scored": scored}


async def _exec_auto_apply(task: AgentTask, db: AsyncSession) -> dict:
    """Auto-apply to high-scoring jobs."""
    result = await db.execute(
        select(Job)
        .join(JobAnalysis)
        .where(Job.is_active.is_(True), JobAnalysis.match_score >= 75)
        .order_by(JobAnalysis.match_score.desc())
        .limit(5)
    )
    top_jobs = result.scalars().all()
    applied = 0
    for job in top_jobs:
        try:
            tool_result = await invoke_tool("apply_to_job", {
                "user_id": str(task.user_id),
                "job_id": str(job.id),
            })
            if tool_result.success:
                applied += 1
        except Exception:
            pass

    return {"action": "auto_apply", "candidates": len(top_jobs), "applied": applied}


async def _exec_send_outreach(task: AgentTask, db: AsyncSession) -> dict:
    """Send outreach messages for recent applications."""
    try:
        resp = await _http.get(
            f"{settings.linkedin_automation_url}/api/linkedin/outreach",
            params={"status": "pending"},
        )
        pending = resp.json().get("outreach", []) if resp.status_code == 200 else []
    except Exception:
        pending = []
    return {"action": "send_outreach", "pending_outreach": len(pending), "status": "queued"}


async def _exec_follow_ups(task: AgentTask, db: AsyncSession) -> dict:
    """Schedule follow-ups for stale applications."""
    try:
        resp = await _http.get(
            f"{settings.application_automation_url}/api/follow-ups",
            params={"days_threshold": 7},
        )
        follow_ups = resp.json() if resp.status_code == 200 else []
    except Exception:
        follow_ups = []
    return {"action": "schedule_follow_ups", "due_follow_ups": len(follow_ups) if isinstance(follow_ups, list) else 0}


async def _exec_interview_prep(task: AgentTask, db: AsyncSession) -> dict:
    """Generate interview prep for a given job."""
    input_data = task.input_data or {}
    result = await invoke_tool("interview_prep", {
        "job_title": input_data.get("job_title", "Software Engineer"),
        "company_name": input_data.get("company_name", ""),
        "job_description": input_data.get("job_description", ""),
    })
    return {"action": "interview_prep", "success": result.success, "data": result.data}


async def _exec_negotiation(task: AgentTask, db: AsyncSession) -> dict:
    """Run negotiation analysis."""
    input_data = task.input_data or {}
    result = await invoke_tool("negotiate_offer", {
        "job_title": input_data.get("job_title", ""),
        "offered_rate": input_data.get("offered_rate", ""),
        "experience_years": input_data.get("experience_years", 0),
    })
    return {"action": "negotiation", "success": result.success, "data": result.data}


_HANDLER_MAP = {
    "_exec_scan_jobs": _exec_scan_jobs,
    "_exec_score_jobs": _exec_score_jobs,
    "_exec_auto_apply": _exec_auto_apply,
    "_exec_send_outreach": _exec_send_outreach,
    "_exec_follow_ups": _exec_follow_ups,
    "_exec_interview_prep": _exec_interview_prep,
    "_exec_negotiation": _exec_negotiation,
}


async def execute_task(task_id: UUID) -> dict:
    """Execute a single queued task and update its status."""
    async with async_session_factory() as db:
        result = await db.execute(select(AgentTask).where(AgentTask.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return {"error": "Task not found"}
        if task.status != "queued":
            return {"error": f"Task is {task.status}, not queued"}

        # Mark running
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        await db.commit()

        handler_key = TASK_HANDLERS.get((task.agent_type, task.task_type))
        handler = _HANDLER_MAP.get(handler_key) if handler_key else None

        try:
            if handler:
                output = await handler(task, db)
            else:
                # Generic fallback — try MCP tool matching
                output = {"action": task.task_type, "note": "No specific handler, task recorded"}

            task.status = "completed"
            task.output_data = output
            task.completed_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info("Task %s completed: %s/%s", task_id, task.agent_type, task.task_type)
            return output

        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)[:500]
            task.completed_at = datetime.now(timezone.utc)
            await db.commit()
            logger.exception("Task %s failed", task_id)
            return {"error": str(e)}


async def execute_pipeline_tasks(task_ids: list[str]) -> list[dict]:
    """Execute a sequence of pipeline tasks in order."""
    results = []
    for tid in task_ids:
        result = await execute_task(UUID(tid))
        results.append(result)
        # If a step fails, stop the pipeline
        if "error" in result and result["error"] != "No specific handler, task recorded":
            break
    return results


async def process_queued_tasks():
    """Background loop: pick up queued tasks and execute them."""
    while True:
        try:
            async with async_session_factory() as db:
                result = await db.execute(
                    select(AgentTask)
                    .where(AgentTask.status == "queued")
                    .order_by(AgentTask.priority.asc(), AgentTask.created_at.asc())
                    .limit(5)
                )
                tasks = result.scalars().all()
                for task in tasks:
                    await execute_task(task.id)
        except Exception:
            logger.exception("Error in task processing loop")
        await asyncio.sleep(10)
