"""Freelance Bidding routes — proposals, bid tracking, platform management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import FreelanceBid

router = APIRouter(prefix="/api/freelance", tags=["Freelance Bidding"])


class BidRequest(BaseModel):
    platform: str  # upwork / freelancer / toptal / fiverr
    project_url: str | None = None
    project_title: str
    client_name: str | None = None
    budget_range: str | None = None  # e.g. "$5000-$10000"
    description: str
    required_skills: list[str] = []
    estimated_hours: int | None = None


@router.post("/bid")
async def create_bid(
    body: BidRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a proposal and create a bid for a freelance project."""
    proposal = _generate_proposal(body, user.get("name", ""))
    bid_amount = _calculate_bid(body)

    bid = FreelanceBid(
        user_id=user["user_id"],
        platform=body.platform,
        project_url=body.project_url,
        project_title=body.project_title,
        client_name=body.client_name,
        budget_range=body.budget_range,
        proposal_text=proposal,
        bid_amount=bid_amount,
        estimated_hours=body.estimated_hours,
        status="draft",
    )
    db.add(bid)
    await db.commit()
    await db.refresh(bid)

    return {
        "id": str(bid.id),
        "platform": body.platform,
        "project": body.project_title,
        "bid_amount": bid_amount,
        "estimated_hours": body.estimated_hours,
        "proposal": proposal,
        "status": "draft",
    }


@router.post("/bid/{bid_id}/submit")
async def submit_bid(
    bid_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a bid as submitted."""
    result = await db.execute(
        select(FreelanceBid).where(FreelanceBid.id == bid_id, FreelanceBid.user_id == user["user_id"])
    )
    bid = result.scalar_one_or_none()
    if not bid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bid not found")
    bid.status = "submitted"
    await db.commit()
    return {"id": str(bid.id), "status": "submitted"}


@router.get("/bids")
async def list_bids(
    platform: str | None = None,
    status_filter: str | None = None,
    limit: int = 30,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all freelance bids with optional filters."""
    q = select(FreelanceBid).where(FreelanceBid.user_id == user["user_id"])
    if platform:
        q = q.where(FreelanceBid.platform == platform)
    if status_filter:
        q = q.where(FreelanceBid.status == status_filter)
    q = q.order_by(FreelanceBid.created_at.desc()).limit(limit)

    result = await db.execute(q)
    bids = result.scalars().all()

    return [
        {
            "id": str(b.id),
            "platform": b.platform,
            "project": b.project_title,
            "client": b.client_name,
            "bid_amount": float(b.bid_amount) if b.bid_amount else None,
            "status": b.status,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in bids
    ]


@router.get("/bids/{bid_id}")
async def get_bid(
    bid_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full bid details including proposal."""
    result = await db.execute(
        select(FreelanceBid).where(FreelanceBid.id == bid_id, FreelanceBid.user_id == user["user_id"])
    )
    bid = result.scalar_one_or_none()
    if not bid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bid not found")

    return {
        "id": str(bid.id),
        "platform": bid.platform,
        "project_url": bid.project_url,
        "project": bid.project_title,
        "client": bid.client_name,
        "budget_range": bid.budget_range,
        "proposal": bid.proposal_text,
        "bid_amount": float(bid.bid_amount) if bid.bid_amount else None,
        "estimated_hours": bid.estimated_hours,
        "status": bid.status,
        "created_at": bid.created_at.isoformat() if bid.created_at else None,
    }


@router.patch("/bids/{bid_id}")
async def update_bid_status(
    bid_id: UUID,
    new_status: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update bid status (draft → submitted → shortlisted → won → completed / lost)."""
    result = await db.execute(
        select(FreelanceBid).where(FreelanceBid.id == bid_id, FreelanceBid.user_id == user["user_id"])
    )
    bid = result.scalar_one_or_none()
    if not bid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bid not found")
    bid.status = new_status
    await db.commit()
    return {"id": str(bid.id), "status": new_status}


@router.get("/stats")
async def freelance_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get freelance bidding statistics."""
    total = await db.execute(
        select(func.count(FreelanceBid.id)).where(FreelanceBid.user_id == user["user_id"])
    )
    by_platform = await db.execute(
        select(FreelanceBid.platform, func.count(FreelanceBid.id))
        .where(FreelanceBid.user_id == user["user_id"])
        .group_by(FreelanceBid.platform)
    )
    by_status = await db.execute(
        select(FreelanceBid.status, func.count(FreelanceBid.id))
        .where(FreelanceBid.user_id == user["user_id"])
        .group_by(FreelanceBid.status)
    )
    won = await db.execute(
        select(func.sum(FreelanceBid.bid_amount)).where(
            FreelanceBid.user_id == user["user_id"], FreelanceBid.status == "won"
        )
    )

    return {
        "total_bids": total.scalar() or 0,
        "by_platform": {r[0]: r[1] for r in by_platform.all()},
        "by_status": {r[0]: r[1] for r in by_status.all()},
        "total_won_value": float(won.scalar() or 0),
    }


# ---------- helpers ----------


def _generate_proposal(body: BidRequest, user_name: str) -> str:
    """Generate a personalized freelance proposal."""
    name = user_name or "a Senior Full-Stack Engineer"
    skills = ", ".join(body.required_skills[:5]) if body.required_skills else "full-stack development"

    return f"""Hi{(' ' + body.client_name) if body.client_name else ''},

Thank you for posting this project. I've carefully reviewed the requirements for "{body.project_title}" and I'm confident I can deliver exactly what you need.

**Why I'm the right fit:**
- 8+ years of professional experience in {skills}
- Track record of delivering similar projects on time and within budget
- Strong communication — daily updates and transparent progress tracking
- Clean, well-tested code with comprehensive documentation

**My Approach:**
1. **Discovery** — I'll start with a brief call to align on requirements and priorities
2. **Architecture** — Before writing code, I'll create a technical plan for your review
3. **Iterative Delivery** — Regular demos so you can see progress and provide feedback
4. **QA & Handoff** — Thorough testing, documentation, and deployment support

**Timeline:** {body.estimated_hours or 'TBD'} hours estimated
**Availability:** Can start immediately

I'd love to discuss your project in more detail. When would be a good time for a quick call?

Best regards,
{name}"""


def _calculate_bid(body: BidRequest) -> float:
    """Calculate a competitive bid amount based on project details."""
    platform_rates = {
        "upwork": 75,
        "freelancer": 65,
        "toptal": 95,
        "fiverr": 55,
    }
    hourly = platform_rates.get(body.platform, 70)
    hours = body.estimated_hours or 40
    return round(hourly * hours, 2)
