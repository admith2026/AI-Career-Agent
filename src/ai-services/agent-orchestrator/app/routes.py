"""Agent Orchestrator API routes — manage agents, tasks, and workflows."""

import logging
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import AgentTask, AgentWorkflow, JobApplication, Job

from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])

AGENT_TYPES = ["discovery", "matching", "application", "outreach", "follow_up", "interview", "negotiation"]

AGENT_SERVICE_MAP = {
    "discovery": settings.job_discovery_url,
    "matching": settings.job_intelligence_url,
    "application": settings.application_automation_url,
    "outreach": settings.linkedin_automation_url,
    "follow_up": settings.voice_ai_url,
    "interview": settings.interview_ai_url,
    "negotiation": settings.negotiation_ai_url,
}


# ─── Agent Status ────────────────────────────────────────────────────────────

@router.get("/status")
async def get_agents_status(current_user: dict = Depends(get_current_user)):
    """Get live status of all AI agents by pinging their health endpoints."""
    statuses = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for agent, url in AGENT_SERVICE_MAP.items():
            try:
                resp = await client.get(f"{url}/health")
                statuses[agent] = {"status": "online", "service_url": url}
            except Exception:
                statuses[agent] = {"status": "offline", "service_url": url}
    return {"agents": statuses}


# ─── Task Management ────────────────────────────────────────────────────────

@router.post("/tasks")
async def create_task(
    agent_type: str,
    task_type: str,
    input_data: dict = {},
    priority: int = 5,
    parent_task_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Queue a new task for an AI agent."""
    if agent_type not in AGENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid agent_type. Must be one of: {AGENT_TYPES}")

    task = AgentTask(
        user_id=current_user["user_id"],
        agent_type=agent_type,
        task_type=task_type,
        input_data=input_data,
        priority=priority,
        parent_task_id=parent_task_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return {"id": str(task.id), "status": task.status, "agent_type": agent_type, "task_type": task_type}


@router.get("/tasks")
async def list_tasks(
    status_filter: str | None = None,
    agent_type: str | None = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List agent tasks for the current user."""
    query = select(AgentTask).where(AgentTask.user_id == current_user["user_id"])
    if status_filter:
        query = query.where(AgentTask.status == status_filter)
    if agent_type:
        query = query.where(AgentTask.agent_type == agent_type)
    query = query.order_by(desc(AgentTask.created_at)).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return {"tasks": [
        {
            "id": str(t.id),
            "agent_type": t.agent_type,
            "task_type": t.task_type,
            "status": t.status,
            "priority": t.priority,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "error_message": t.error_message,
        }
        for t in tasks
    ]}


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get task details including input/output data."""
    result = await db.execute(
        select(AgentTask).where(AgentTask.id == task_id, AgentTask.user_id == current_user["user_id"])
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": str(task.id),
        "agent_type": task.agent_type,
        "task_type": task.task_type,
        "status": task.status,
        "priority": task.priority,
        "input_data": task.input_data,
        "output_data": task.output_data,
        "error_message": task.error_message,
        "parent_task_id": str(task.parent_task_id) if task.parent_task_id else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cancel a queued or running task."""
    result = await db.execute(
        select(AgentTask).where(AgentTask.id == task_id, AgentTask.user_id == current_user["user_id"])
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status in ("completed", "failed", "canceled"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel task in {task.status} state")
    task.status = "canceled"
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": str(task.id), "status": "canceled"}


# ─── Workflow Management ─────────────────────────────────────────────────────

@router.post("/workflows")
async def create_workflow(
    name: str,
    steps: list[dict],
    description: str = "",
    trigger: str = "manual",
    schedule_cron: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a multi-agent workflow pipeline."""
    workflow = AgentWorkflow(
        user_id=current_user["user_id"],
        name=name,
        description=description,
        steps=steps,
        trigger=trigger,
        schedule_cron=schedule_cron,
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return {"id": str(workflow.id), "name": workflow.name, "steps_count": len(steps)}


@router.get("/workflows")
async def list_workflows(
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List user's agent workflows."""
    result = await db.execute(
        select(AgentWorkflow)
        .where(AgentWorkflow.user_id == current_user["user_id"])
        .order_by(desc(AgentWorkflow.created_at))
        .limit(limit)
    )
    workflows = result.scalars().all()
    return {"workflows": [
        {
            "id": str(w.id),
            "name": w.name,
            "description": w.description,
            "trigger": w.trigger,
            "steps_count": len(w.steps) if w.steps else 0,
            "is_active": w.is_active,
            "run_count": w.run_count,
            "last_run_at": w.last_run_at.isoformat() if w.last_run_at else None,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in workflows
    ]}


@router.post("/workflows/{workflow_id}/run")
async def run_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Execute a workflow — creates chained agent tasks for each step."""
    result = await db.execute(
        select(AgentWorkflow).where(
            AgentWorkflow.id == workflow_id, AgentWorkflow.user_id == current_user["user_id"]
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    created_tasks = []
    parent_id = None
    for step in (workflow.steps or []):
        task = AgentTask(
            user_id=current_user["user_id"],
            agent_type=step.get("agent_type", "discovery"),
            task_type=step.get("task_type", "execute"),
            input_data=step.get("config", {}),
            priority=step.get("priority", 5),
            parent_task_id=parent_id,
        )
        db.add(task)
        await db.flush()
        parent_id = task.id
        created_tasks.append(str(task.id))

    workflow.run_count = (workflow.run_count or 0) + 1
    workflow.last_run_at = datetime.now(timezone.utc)
    await db.commit()

    return {"workflow_id": str(workflow_id), "tasks_created": len(created_tasks), "task_ids": created_tasks}


@router.patch("/workflows/{workflow_id}")
async def toggle_workflow(
    workflow_id: UUID,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Toggle workflow active state."""
    result = await db.execute(
        select(AgentWorkflow).where(
            AgentWorkflow.id == workflow_id, AgentWorkflow.user_id == current_user["user_id"]
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if is_active is not None:
        workflow.is_active = is_active
    await db.commit()
    return {"id": str(workflow.id), "is_active": workflow.is_active}


# ─── Automation Pipeline ─────────────────────────────────────────────────────

@router.post("/pipeline/run")
async def run_full_pipeline(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Execute the full automation pipeline: Discover → Score → Apply → Outreach → Follow-up."""
    # Verify user exists in the database
    from shared.models import User
    user_check = await db.execute(select(User).where(User.id == current_user["user_id"]))
    if not user_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User account not found. Please log out and re-register.")

    pipeline_steps = [
        {"agent_type": "discovery", "task_type": "scan_jobs"},
        {"agent_type": "matching", "task_type": "score_jobs"},
        {"agent_type": "application", "task_type": "auto_apply"},
        {"agent_type": "outreach", "task_type": "send_outreach"},
        {"agent_type": "follow_up", "task_type": "schedule_follow_ups"},
    ]
    parent_id = None
    task_ids = []
    for step in pipeline_steps:
        task = AgentTask(
            user_id=current_user["user_id"],
            agent_type=step["agent_type"],
            task_type=step["task_type"],
            parent_task_id=parent_id,
            priority=3,
        )
        db.add(task)
        await db.flush()
        parent_id = task.id
        task_ids.append(str(task.id))
    await db.commit()

    # Auto-execute the pipeline tasks in background
    import asyncio
    from .executor import execute_pipeline_tasks
    asyncio.create_task(execute_pipeline_tasks(task_ids))

    return {"pipeline": "full_automation", "tasks_created": len(task_ids), "task_ids": task_ids}


# ─── AI Planner ──────────────────────────────────────────────────────────────

from .planner import create_plan  # noqa: E402


class PlanRequest(BaseModel):
    goal: str


@router.post("/plan")
async def ai_plan(
    req: PlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Use AI to create and execute an autonomous career plan from a goal."""
    plan = await create_plan(req.goal)

    task_ids = []
    parent_id = None
    for step in plan.get("steps", []):
        task = AgentTask(
            user_id=current_user["user_id"],
            agent_type=step["agent_type"],
            task_type=step["task_type"],
            input_data=step.get("config", {}),
            priority=step.get("priority", 5),
            parent_task_id=parent_id,
        )
        db.add(task)
        await db.flush()
        parent_id = task.id
        task_ids.append(str(task.id))
    await db.commit()

    # Auto-execute
    import asyncio
    from .executor import execute_pipeline_tasks
    asyncio.create_task(execute_pipeline_tasks(task_ids))

    return {
        "plan": plan.get("plan_name"),
        "reasoning": plan.get("reasoning"),
        "steps": len(plan.get("steps", [])),
        "task_ids": task_ids,
        "status": "executing",
    }


@router.post("/tasks/{task_id}/execute")
async def execute_single_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Manually trigger execution of a queued task."""
    result = await db.execute(
        select(AgentTask).where(AgentTask.id == task_id, AgentTask.user_id == current_user["user_id"])
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "queued":
        raise HTTPException(status_code=400, detail=f"Task is {task.status}, not queued")

    from .executor import execute_task
    output = await execute_task(task_id)
    return {"task_id": str(task_id), "result": output}


# ─── Stats ───────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get agent orchestrator stats for user."""
    user_id = current_user["user_id"]
    total_q = await db.execute(select(func.count(AgentTask.id)).where(AgentTask.user_id == user_id))
    total = total_q.scalar() or 0

    running_q = await db.execute(
        select(func.count(AgentTask.id)).where(AgentTask.user_id == user_id, AgentTask.status == "running")
    )
    running = running_q.scalar() or 0

    completed_q = await db.execute(
        select(func.count(AgentTask.id)).where(AgentTask.user_id == user_id, AgentTask.status == "completed")
    )
    completed = completed_q.scalar() or 0

    failed_q = await db.execute(
        select(func.count(AgentTask.id)).where(AgentTask.user_id == user_id, AgentTask.status == "failed")
    )
    failed = failed_q.scalar() or 0

    workflows_q = await db.execute(
        select(func.count(AgentWorkflow.id)).where(AgentWorkflow.user_id == user_id)
    )
    workflows = workflows_q.scalar() or 0

    return {
        "total_tasks": total,
        "running": running,
        "completed": completed,
        "failed": failed,
        "workflows": workflows,
        "agents_available": len(AGENT_TYPES),
    }


# ─── MCP Tool Endpoints ─────────────────────────────────────────────────────

from .mcp_tools import list_tools, invoke_tool  # noqa: E402


class MCPInvokeRequest(BaseModel):
    tool_name: str
    arguments: dict = {}


@router.get("/mcp/tools")
async def mcp_list_tools(current_user: dict = Depends(get_current_user)):
    """List all available MCP tool definitions."""
    tools = list_tools()
    return {"tools": [t.model_dump() for t in tools]}


@router.post("/mcp/invoke")
async def mcp_invoke_tool(
    req: MCPInvokeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Invoke an MCP tool by name with arguments."""
    result = await invoke_tool(req.tool_name, req.arguments)
    return result.model_dump()


@router.get("/mcp/categories")
async def mcp_tool_categories(current_user: dict = Depends(get_current_user)):
    """List tool categories."""
    tools = list_tools()
    categories: dict[str, list[str]] = {}
    for t in tools:
        categories.setdefault(t.category, []).append(t.name)
    return {"categories": categories}


# ─── Real-Time Activity Feed ─────────────────────────────────────────────────

@router.get("/activity")
async def get_activity_feed(
    limit: int = Query(30, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a unified real-time activity feed combining tasks, applications, and agent events."""
    user_id = current_user["user_id"]

    # Recent tasks
    task_result = await db.execute(
        select(AgentTask)
        .where(AgentTask.user_id == user_id)
        .order_by(desc(AgentTask.created_at))
        .limit(limit)
    )
    tasks = task_result.scalars().all()

    # Recent applications
    app_result = await db.execute(
        select(JobApplication)
        .where(JobApplication.user_id == user_id)
        .order_by(desc(JobApplication.applied_at))
        .limit(limit)
    )
    apps = app_result.scalars().all()

    # Merge into unified feed
    feed = []
    for t in tasks:
        feed.append({
            "type": "agent_task",
            "icon": "🤖",
            "title": f"{t.agent_type} → {t.task_type}",
            "status": t.status,
            "timestamp": (t.completed_at or t.started_at or t.created_at).isoformat() if (t.completed_at or t.started_at or t.created_at) else None,
            "detail": t.error_message if t.status == "failed" else None,
        })
    for a in apps:
        feed.append({
            "type": "application",
            "icon": "📝",
            "title": f"Applied via {a.applied_via or 'manual'}",
            "status": a.status,
            "timestamp": a.applied_at.isoformat() if a.applied_at else None,
            "detail": str(a.job_id),
        })

    # Sort by timestamp descending
    feed.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return {"feed": feed[:limit]}
