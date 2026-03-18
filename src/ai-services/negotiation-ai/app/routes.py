"""Negotiation AI routes — market rates, strategies, and counter-offer scripts."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import NegotiationStrategy

router = APIRouter(prefix="/api/negotiation", tags=["Negotiation AI"])


class NegotiationRequest(BaseModel):
    job_id: UUID | None = None
    role_title: str
    company_name: str
    offered_rate: float
    rate_type: str = "hourly"  # hourly / annual
    years_experience: int = 5
    location: str = "Remote"


class CounterOfferRequest(BaseModel):
    strategy_id: UUID
    counter_amount: float | None = None


@router.post("/analyze")
async def analyze_offer(
    body: NegotiationRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze an offer and generate a negotiation strategy."""
    market = _get_market_rates(body.role_title, body.years_experience, body.location, body.rate_type)
    strategy = _build_strategy(body, market)
    counter_script = _generate_counter_script(body, market, strategy)
    points = _generate_negotiation_points(body.role_title)

    target = market["mid"] * 1.1 if body.offered_rate < market["mid"] else body.offered_rate * 1.05

    neg = NegotiationStrategy(
        user_id=user["user_id"],
        job_id=body.job_id,
        offered_rate=body.offered_rate,
        target_rate=round(target, 2),
        market_rate_low=market["low"],
        market_rate_mid=market["mid"],
        market_rate_high=market["high"],
        strategy=strategy,
        counter_offer_script=counter_script,
        negotiation_points=points,
        status="draft",
    )
    db.add(neg)
    await db.commit()
    await db.refresh(neg)

    return {
        "id": str(neg.id),
        "market_rates": market,
        "offered": body.offered_rate,
        "target": neg.target_rate,
        "offer_assessment": _assess_offer(body.offered_rate, market),
        "strategy": strategy,
        "counter_script": counter_script,
        "negotiation_points": points,
    }


@router.get("/strategies")
async def list_strategies(
    limit: int = 20,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all negotiation strategies."""
    result = await db.execute(
        select(NegotiationStrategy)
        .where(NegotiationStrategy.user_id == user["user_id"])
        .order_by(NegotiationStrategy.created_at.desc())
        .limit(limit)
    )
    strategies = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "offered": float(s.offered_rate) if s.offered_rate else None,
            "target": float(s.target_rate) if s.target_rate else None,
            "market_mid": float(s.market_rate_mid) if s.market_rate_mid else None,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in strategies
    ]


@router.get("/strategies/{strategy_id}")
async def get_strategy(
    strategy_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full negotiation strategy details."""
    result = await db.execute(
        select(NegotiationStrategy).where(
            NegotiationStrategy.id == strategy_id,
            NegotiationStrategy.user_id == user["user_id"],
        )
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Strategy not found")

    return {
        "id": str(s.id),
        "offered": float(s.offered_rate) if s.offered_rate else None,
        "target": float(s.target_rate) if s.target_rate else None,
        "market_rates": {
            "low": float(s.market_rate_low) if s.market_rate_low else None,
            "mid": float(s.market_rate_mid) if s.market_rate_mid else None,
            "high": float(s.market_rate_high) if s.market_rate_high else None,
        },
        "strategy": s.strategy,
        "counter_offer_script": s.counter_offer_script,
        "negotiation_points": s.negotiation_points,
        "status": s.status,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.patch("/strategies/{strategy_id}")
async def update_strategy_status(
    strategy_id: UUID,
    status_val: str = "accepted",
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update strategy status (draft → sent → accepted / rejected / countered)."""
    result = await db.execute(
        select(NegotiationStrategy).where(
            NegotiationStrategy.id == strategy_id,
            NegotiationStrategy.user_id == user["user_id"],
        )
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Strategy not found")

    s.status = status_val
    await db.commit()
    return {"id": str(s.id), "status": s.status}


@router.get("/market-rates/{role_title}")
async def get_market_rates(
    role_title: str,
    experience: int = 5,
    location: str = "Remote",
    rate_type: str = "hourly",
    user: dict = Depends(get_current_user),
):
    """Get market rate data for a role."""
    rates = _get_market_rates(role_title, experience, location, rate_type)
    return {"role": role_title, "experience": experience, "location": location, "type": rate_type, **rates}


@router.get("/stats")
async def negotiation_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get negotiation statistics."""
    total = await db.execute(
        select(func.count(NegotiationStrategy.id)).where(
            NegotiationStrategy.user_id == user["user_id"]
        )
    )
    by_status = await db.execute(
        select(NegotiationStrategy.status, func.count(NegotiationStrategy.id))
        .where(NegotiationStrategy.user_id == user["user_id"])
        .group_by(NegotiationStrategy.status)
    )
    avg_increase = await db.execute(
        select(
            func.avg(NegotiationStrategy.target_rate - NegotiationStrategy.offered_rate)
        ).where(
            NegotiationStrategy.user_id == user["user_id"],
            NegotiationStrategy.status == "accepted",
        )
    )

    return {
        "total_strategies": total.scalar() or 0,
        "by_status": {r[0]: r[1] for r in by_status.all()},
        "avg_rate_increase": round(float(avg_increase.scalar() or 0), 2),
    }


# ---------- helpers ----------


def _get_market_rates(role: str, experience: int, location: str, rate_type: str) -> dict:
    """Return market rate estimates based on role and experience."""
    role_lower = role.lower()

    # Base hourly rates
    if any(k in role_lower for k in [".net", "c#", "dotnet"]):
        base = {"low": 55, "mid": 75, "high": 95}
    elif any(k in role_lower for k in ["python", "backend"]):
        base = {"low": 55, "mid": 72, "high": 90}
    elif any(k in role_lower for k in ["react", "frontend"]):
        base = {"low": 50, "mid": 68, "high": 88}
    elif any(k in role_lower for k in ["devops", "cloud", "sre"]):
        base = {"low": 60, "mid": 80, "high": 100}
    elif any(k in role_lower for k in ["architect", "principal", "staff"]):
        base = {"low": 80, "mid": 100, "high": 130}
    else:
        base = {"low": 50, "mid": 70, "high": 90}

    # Experience multiplier
    exp_mult = 1.0 + max(0, (experience - 5)) * 0.04

    # Location adjustment
    loc_lower = location.lower()
    if any(c in loc_lower for c in ["nyc", "new york", "sf", "san francisco", "seattle"]):
        loc_mult = 1.15
    elif "remote" in loc_lower:
        loc_mult = 1.0
    else:
        loc_mult = 0.95

    result = {k: round(v * exp_mult * loc_mult, 2) for k, v in base.items()}

    if rate_type == "annual":
        result = {k: round(v * 2080, 0) for k, v in result.items()}

    return result


def _assess_offer(offered: float, market: dict) -> dict:
    """Assess where the offer falls relative to market rates."""
    if offered >= market["high"]:
        return {"rating": "excellent", "percentile": 90, "message": "Above market — strong offer."}
    elif offered >= market["mid"]:
        pct = 50 + (offered - market["mid"]) / (market["high"] - market["mid"]) * 40
        return {"rating": "good", "percentile": round(pct), "message": "At or above market midpoint."}
    elif offered >= market["low"]:
        pct = 10 + (offered - market["low"]) / (market["mid"] - market["low"]) * 40
        return {"rating": "below_market", "percentile": round(pct), "message": "Below market mid — negotiate up."}
    else:
        return {"rating": "low", "percentile": 5, "message": "Significantly below market — strong negotiation needed."}


def _build_strategy(body: NegotiationRequest, market: dict) -> dict:
    """Build a negotiation strategy."""
    assessment = _assess_offer(body.offered_rate, market)
    gap = market["mid"] - body.offered_rate

    return {
        "approach": "collaborative" if assessment["rating"] in ("good", "excellent") else "assertive",
        "leverage_points": [
            f"{body.years_experience}+ years of specialized experience",
            f"Market data supports {market['mid']}-{market['high']} range",
            "Strong technical expertise and immediate availability",
            "Track record of delivering high-impact projects",
        ],
        "risks": [
            "Pushing too hard may lose the opportunity",
            "Company may have firm budget constraints",
        ],
        "timeline": "Respond within 24-48 hours to show interest while leaving room for negotiation",
        "recommended_counter": round(market["mid"] * 1.1, 2),
        "walk_away_threshold": market["low"],
    }


def _generate_counter_script(body: NegotiationRequest, market: dict, strategy: dict) -> str:
    """Generate a professional counter-offer script."""
    counter = strategy["recommended_counter"]
    unit = "/hr" if body.rate_type == "hourly" else "/year"

    return f"""Thank you for the offer at ${body.offered_rate}{unit} for the {body.role_title} position at {body.company_name}. I'm excited about the opportunity and the team.

Based on my {body.years_experience} years of experience and current market rates for this role ({body.location}), I was hoping we could discuss a rate closer to ${counter}{unit}. This aligns with the market range of ${market['low']}-${market['high']}{unit} for comparable positions.

I bring [mention 2-3 specific value-adds relevant to their needs], which I believe positions me to make an immediate impact.

I'm flexible and would love to discuss this further. Would there be room to adjust the rate, or perhaps we could explore other elements of the compensation package?

Looking forward to your thoughts."""


def _generate_negotiation_points(role: str) -> list[str]:
    """Generate key negotiation talking points."""
    return [
        "Express genuine enthusiasm for the role and company first",
        "Lead with market data — never make it personal",
        "Quantify your impact: projects delivered, revenue generated, costs saved",
        "Negotiate the full package: rate, PTO, remote flexibility, signing bonus",
        "Use silence effectively — let them respond to your counter",
        "Have a BATNA (Best Alternative to Negotiated Agreement) ready",
        "Get the final offer in writing before accepting",
        "If rate is firm, negotiate start date, equipment budget, or training allowance",
    ]
