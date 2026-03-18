"""Decision Engine API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.models import DecisionLog
from shared.schemas import DecisionLogOut
from app.engine import DecisionEngine
from shared.events import EventBus

router = APIRouter(prefix="/api/decisions", tags=["Decision Engine"])

# Initialized in main.py lifespan
engine: DecisionEngine | None = None


def set_engine(e: DecisionEngine):
    global engine
    engine = e


@router.get("", response_model=list[DecisionLogOut])
async def list_decisions(
    user_id: UUID = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List recent decision logs (alias for /log)."""
    q = select(DecisionLog).order_by(DecisionLog.created_at.desc()).limit(limit)
    if user_id:
        q = q.where(DecisionLog.user_id == user_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/evaluate/{job_id}")
async def evaluate_job(job_id: UUID, user_id: UUID = Query(...), db: AsyncSession = Depends(get_db)):
    return await engine.evaluate_job(job_id, user_id, db)


@router.post("/batch-evaluate")
async def batch_evaluate(
    user_id: UUID = Query(...),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    results = await engine.batch_evaluate(user_id, db, limit)
    return {"evaluated": len(results), "results": results}


@router.get("/log", response_model=list[DecisionLogOut])
async def get_decision_log(
    user_id: UUID = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(DecisionLog).order_by(DecisionLog.created_at.desc()).limit(limit)
    if user_id:
        q = q.where(DecisionLog.user_id == user_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/stats")
async def decision_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(DecisionLog.id)))).scalar() or 0
    by_decision = (
        await db.execute(
            select(DecisionLog.decision, func.count(DecisionLog.id))
            .group_by(DecisionLog.decision)
        )
    ).all()
    executed = (
        await db.execute(
            select(func.count(DecisionLog.id)).where(DecisionLog.executed.is_(True))
        )
    ).scalar() or 0

    return {
        "total_decisions": total,
        "executed": executed,
        "by_decision": {row[0]: row[1] for row in by_decision},
    }
