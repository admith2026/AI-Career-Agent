"""LinkedIn Automation routes — outreach, messaging, tracking."""

from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import LinkedInOutreach, RecruiterContact

router = APIRouter(prefix="/api/linkedin", tags=["LinkedIn"])


class ConnectRequest(BaseModel):
    profile_url: str | None = None
    person_name: str | None = None
    recruiter_name: str | None = None
    recruiter_contact_id: str | None = None
    person_title: str | None = None
    title: str | None = None
    company_name: str | None = None
    company: str | None = None
    message: str | None = None


class MessageRequest(BaseModel):
    outreach_id: UUID
    message: str


class BulkConnectRequest(BaseModel):
    targets: list[ConnectRequest]


@router.post("/connect")
async def send_connection(
    body: ConnectRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queue a LinkedIn connection request with personalized message."""
    name = body.person_name or body.recruiter_name or "Unknown"
    title = body.person_title or body.title
    company = body.company_name or body.company
    outreach = LinkedInOutreach(
        user_id=user["user_id"],
        profile_url=body.profile_url or "",
        person_name=name,
        person_title=title,
        company_name=company,
        action_type="connect",
        message_text=body.message or _generate_connect_message(name, title, company),
        status="pending",
    )
    db.add(outreach)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=401, detail="User account not found. Please log out and register again.")
    await db.refresh(outreach)
    return {"id": str(outreach.id), "status": "queued", "message": outreach.message_text}


@router.post("/bulk-connect")
async def bulk_connect(
    body: BulkConnectRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queue multiple connection requests."""
    created = []
    for target in body.targets[:50]:  # Cap at 50
        outreach = LinkedInOutreach(
            user_id=user["user_id"],
            profile_url=target.profile_url,
            person_name=target.person_name,
            person_title=target.person_title,
            company_name=target.company_name,
            action_type="connect",
            message_text=target.message or _generate_connect_message(target.person_name, target.person_title, target.company_name),
            status="pending",
        )
        db.add(outreach)
        created.append(target.person_name)

    await db.commit()
    return {"queued": len(created), "names": created}


@router.post("/message")
async def send_message(
    body: MessageRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a follow-up message to an existing connection."""
    result = await db.execute(
        select(LinkedInOutreach).where(
            LinkedInOutreach.id == body.outreach_id,
            LinkedInOutreach.user_id == user["user_id"],
        )
    )
    outreach = result.scalar_one_or_none()
    if not outreach:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Outreach not found")

    new_msg = LinkedInOutreach(
        user_id=user["user_id"],
        profile_url=outreach.profile_url,
        person_name=outreach.person_name,
        person_title=outreach.person_title,
        company_name=outreach.company_name,
        action_type="message",
        message_text=body.message,
        status="pending",
    )
    db.add(new_msg)

    outreach.follow_up_count = (outreach.follow_up_count or 0) + 1
    outreach.next_follow_up = datetime.now(timezone.utc) + timedelta(days=3)
    await db.commit()
    return {"id": str(new_msg.id), "status": "queued"}


@router.get("/outreach")
async def list_outreach(
    status_filter: str | None = None,
    limit: int = 50,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all outreach activities."""
    query = select(LinkedInOutreach).where(
        LinkedInOutreach.user_id == user["user_id"]
    ).order_by(LinkedInOutreach.created_at.desc()).limit(limit)

    if status_filter:
        query = query.where(LinkedInOutreach.status == status_filter)

    result = await db.execute(query)
    items = result.scalars().all()

    return [
        {
            "id": str(o.id),
            "person_name": o.person_name,
            "person_title": o.person_title,
            "company": o.company_name,
            "action": o.action_type,
            "status": o.status,
            "message": o.message_text[:100] + "..." if o.message_text and len(o.message_text) > 100 else o.message_text,
            "sent_at": o.sent_at.isoformat() if o.sent_at else None,
            "replied_at": o.replied_at.isoformat() if o.replied_at else None,
            "follow_ups": o.follow_up_count,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in items
    ]


@router.get("/stats")
async def outreach_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get LinkedIn outreach statistics."""
    base = select(LinkedInOutreach).where(LinkedInOutreach.user_id == user["user_id"])

    total = await db.execute(select(func.count()).select_from(base.subquery()))
    by_status = await db.execute(
        select(LinkedInOutreach.status, func.count(LinkedInOutreach.id))
        .where(LinkedInOutreach.user_id == user["user_id"])
        .group_by(LinkedInOutreach.status)
    )

    status_map = {row[0]: row[1] for row in by_status.all()}
    total_count = total.scalar() or 0
    replied = status_map.get("replied", 0)

    return {
        "total_outreach": total_count,
        "by_status": status_map,
        "response_rate": round(replied / total_count * 100, 1) if total_count else 0,
        "connections_pending": status_map.get("pending", 0),
        "connections_accepted": status_map.get("accepted", 0),
    }


@router.post("/{outreach_id}/mark-replied")
async def mark_replied(
    outreach_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an outreach as replied."""
    result = await db.execute(
        select(LinkedInOutreach).where(
            LinkedInOutreach.id == outreach_id,
            LinkedInOutreach.user_id == user["user_id"],
        )
    )
    outreach = result.scalar_one_or_none()
    if not outreach:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Outreach not found")

    outreach.status = "replied"
    outreach.replied_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "replied"}


def _generate_connect_message(name: str, title: str | None, company: str | None) -> str:
    """Generate a personalized connection request message."""
    greeting = f"Hi {name.split()[0] if name else 'there'}"
    if title and company:
        return f"{greeting}, I noticed your role as {title} at {company}. I'm a Senior .NET/Python developer specializing in contract work. I'd love to connect and learn about any opportunities your team may have."
    elif company:
        return f"{greeting}, I see you work at {company}. I'm a Senior Software Engineer with expertise in .NET, Python, and cloud platforms. Would love to connect!"
    return f"{greeting}, I'm a Senior Software Engineer looking for new contract opportunities. Would love to connect and share insights!"
