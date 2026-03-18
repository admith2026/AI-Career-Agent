"""Voice AI routes — Twilio call management and AI scripts."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import VoiceCall, RecruiterContact

router = APIRouter(prefix="/api/voice", tags=["Voice AI"])


class CallRequest(BaseModel):
    phone_number: str
    recruiter_id: UUID | None = None
    script_topic: str | None = None  # e.g. "dotnet_contract", "python_remote"


class CallbackPayload(BaseModel):
    call_sid: str
    status: str
    duration: int | None = None


@router.post("/call")
async def initiate_call(
    body: CallRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queue an AI-powered recruiter call via Twilio."""
    script = _generate_script(body.script_topic or "general", user.get("name", ""))

    call = VoiceCall(
        user_id=user["user_id"],
        recruiter_id=body.recruiter_id,
        phone_number=body.phone_number,
        ai_script=script,
        status="queued",
    )
    db.add(call)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=401, detail="User account not found. Please log out and register again.")
    await db.refresh(call)

    return {
        "id": str(call.id),
        "status": "queued",
        "phone": body.phone_number,
        "script_preview": script[:200] + "...",
        "message": "Call queued. Configure TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to enable live calls.",
    }


@router.get("/calls")
async def list_calls(
    limit: int = 30,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all voice calls."""
    result = await db.execute(
        select(VoiceCall)
        .where(VoiceCall.user_id == user["user_id"])
        .order_by(VoiceCall.created_at.desc())
        .limit(limit)
    )
    calls = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "phone": c.phone_number,
            "status": c.status,
            "duration": c.duration_seconds,
            "outcome": c.outcome,
            "resume_sent": c.resume_sent,
            "transcript": c.transcript[:200] + "..." if c.transcript and len(c.transcript) > 200 else c.transcript,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in calls
    ]


@router.get("/calls/{call_id}")
async def get_call(
    call_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full call details including transcript and script."""
    result = await db.execute(
        select(VoiceCall).where(VoiceCall.id == call_id, VoiceCall.user_id == user["user_id"])
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Call not found")

    return {
        "id": str(call.id),
        "phone": call.phone_number,
        "status": call.status,
        "duration": call.duration_seconds,
        "outcome": call.outcome,
        "transcript": call.transcript,
        "ai_script": call.ai_script,
        "resume_sent": call.resume_sent,
        "created_at": call.created_at.isoformat() if call.created_at else None,
    }


@router.post("/callback")
async def twilio_callback(body: CallbackPayload, db: AsyncSession = Depends(get_db)):
    """Twilio status callback endpoint."""
    result = await db.execute(
        select(VoiceCall).where(VoiceCall.call_sid == body.call_sid)
    )
    call = result.scalar_one_or_none()
    if call:
        call.status = body.status
        if body.duration:
            call.duration_seconds = body.duration
        await db.commit()
    return {"received": True}


@router.get("/stats")
async def voice_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get voice call statistics."""
    total = await db.execute(
        select(func.count(VoiceCall.id)).where(VoiceCall.user_id == user["user_id"])
    )
    by_outcome = await db.execute(
        select(VoiceCall.outcome, func.count(VoiceCall.id))
        .where(VoiceCall.user_id == user["user_id"], VoiceCall.outcome.isnot(None))
        .group_by(VoiceCall.outcome)
    )
    by_status = await db.execute(
        select(VoiceCall.status, func.count(VoiceCall.id))
        .where(VoiceCall.user_id == user["user_id"])
        .group_by(VoiceCall.status)
    )

    return {
        "total_calls": total.scalar() or 0,
        "by_outcome": {r[0]: r[1] for r in by_outcome.all()},
        "by_status": {r[0]: r[1] for r in by_status.all()},
    }


def _generate_script(topic: str, user_name: str) -> str:
    """Generate an AI call script."""
    name = user_name or "a Senior Software Engineer"
    scripts = {
        "dotnet_contract": f"""Hello, my name is calling on behalf of {name}, a Senior .NET Developer with 8+ years of experience in C#, ASP.NET Core, Azure, and microservices architecture.

{name} is currently available for contract opportunities — both C2C and W2. Their rate is competitive for the market.

Would you have any .NET or cloud engineering positions that might be a good fit? I can send over their resume right away.

If this isn't a good time, when would be a better time to reconnect?""",

        "python_remote": f"""Hello, I'm reaching out on behalf of {name}, a Senior Python Developer specializing in FastAPI, Django, PostgreSQL, and cloud-native applications.

{name} is actively looking for remote Python opportunities, particularly in the areas of backend engineering, data platforms, and API development.

Do you have any relevant positions open? I'd be happy to forward their resume for review.

Thank you for your time.""",

        "general": f"""Hello, I'm calling on behalf of {name}, a Senior Full-Stack Engineer with strong experience in .NET, Python, React, and cloud platforms.

{name} is currently exploring new contract and full-time opportunities across the US, with a focus on remote positions.

I'd love to learn about any relevant openings you might have. Would it be possible to send over their resume?

I appreciate your time — please let me know a good time to follow up.""",
    }
    return scripts.get(topic, scripts["general"])
