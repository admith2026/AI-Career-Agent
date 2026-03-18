"""Demand Generation routes — AI content creation, scheduling, engagement."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import ContentPost

router = APIRouter(prefix="/api/content", tags=["Demand Generation"])


class ContentRequest(BaseModel):
    platform: str  # linkedin / twitter / dev.to / medium
    post_type: str = "article"  # article / post / thread / showcase
    topic: str
    tone: str = "professional"  # professional / casual / thought_leader / technical


class ScheduleRequest(BaseModel):
    post_id: UUID
    scheduled_for: str  # ISO datetime


@router.post("/generate")
async def generate_content(
    body: ContentRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI-written content for a specific platform."""
    content = _generate_content(body)
    hashtags = _generate_hashtags(body.topic, body.platform)

    post = ContentPost(
        user_id=user["user_id"],
        platform=body.platform,
        post_type=body.post_type,
        title=content["title"],
        content=content["body"],
        hashtags=hashtags,
        topic=body.topic,
        status="draft",
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return {
        "id": str(post.id),
        "platform": body.platform,
        "title": content["title"],
        "content": content["body"],
        "hashtags": hashtags,
        "status": "draft",
    }


@router.get("/posts")
async def list_posts(
    platform: str | None = None,
    status_filter: str | None = None,
    limit: int = 30,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all content posts with optional filters."""
    q = select(ContentPost).where(ContentPost.user_id == user["user_id"])
    if platform:
        q = q.where(ContentPost.platform == platform)
    if status_filter:
        q = q.where(ContentPost.status == status_filter)
    q = q.order_by(ContentPost.created_at.desc()).limit(limit)

    result = await db.execute(q)
    posts = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "platform": p.platform,
            "type": p.post_type,
            "title": p.title,
            "topic": p.topic,
            "status": p.status,
            "hashtags": p.hashtags,
            "engagement": p.engagement_metrics,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in posts
    ]


@router.get("/posts/{post_id}")
async def get_post(
    post_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full content post details."""
    result = await db.execute(
        select(ContentPost).where(ContentPost.id == post_id, ContentPost.user_id == user["user_id"])
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    return {
        "id": str(post.id),
        "platform": post.platform,
        "type": post.post_type,
        "title": post.title,
        "content": post.content,
        "hashtags": post.hashtags,
        "topic": post.topic,
        "status": post.status,
        "engagement": post.engagement_metrics,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }


@router.patch("/posts/{post_id}")
async def update_post_status(
    post_id: UUID,
    new_status: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update post status (draft → scheduled → published → archived)."""
    result = await db.execute(
        select(ContentPost).where(ContentPost.id == post_id, ContentPost.user_id == user["user_id"])
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    post.status = new_status
    await db.commit()
    return {"id": str(post.id), "status": new_status}


@router.post("/posts/{post_id}/engagement")
async def update_engagement(
    post_id: UUID,
    likes: int = 0,
    comments: int = 0,
    shares: int = 0,
    views: int = 0,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update engagement metrics for a published post."""
    result = await db.execute(
        select(ContentPost).where(ContentPost.id == post_id, ContentPost.user_id == user["user_id"])
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    post.engagement_metrics = {
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "views": views,
        "engagement_rate": round((likes + comments + shares) / max(views, 1) * 100, 2),
    }
    await db.commit()
    return {"id": str(post.id), "engagement": post.engagement_metrics}


@router.get("/calendar")
async def content_calendar(
    days: int = 7,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a content calendar suggestion."""
    return {
        "schedule": _generate_calendar(days),
        "tips": [
            "Post on LinkedIn Tuesday-Thursday mornings for max reach",
            "Twitter threads perform best on weekdays 9-11 AM EST",
            "Dev.to articles get most traction published Monday/Tuesday",
            "Aim for 3-5 posts per week across platforms",
        ],
    }


@router.get("/stats")
async def content_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get content performance statistics."""
    total = await db.execute(
        select(func.count(ContentPost.id)).where(ContentPost.user_id == user["user_id"])
    )
    by_platform = await db.execute(
        select(ContentPost.platform, func.count(ContentPost.id))
        .where(ContentPost.user_id == user["user_id"])
        .group_by(ContentPost.platform)
    )
    by_status = await db.execute(
        select(ContentPost.status, func.count(ContentPost.id))
        .where(ContentPost.user_id == user["user_id"])
        .group_by(ContentPost.status)
    )
    published = await db.execute(
        select(ContentPost)
        .where(ContentPost.user_id == user["user_id"], ContentPost.status == "published")
    )
    published_posts = published.scalars().all()
    total_engagement = sum(
        (p.engagement_metrics or {}).get("likes", 0) + (p.engagement_metrics or {}).get("comments", 0)
        for p in published_posts
    )

    return {
        "total_posts": total.scalar() or 0,
        "by_platform": {r[0]: r[1] for r in by_platform.all()},
        "by_status": {r[0]: r[1] for r in by_status.all()},
        "total_engagement": total_engagement,
        "published_count": len(published_posts),
    }


# ---------- helpers ----------


def _generate_content(body: ContentRequest) -> dict:
    """Generate platform-specific content."""
    topic = body.topic
    templates = {
        "linkedin": {
            "article": {
                "title": f"How {topic} Is Transforming the Tech Industry in 2024",
                "body": f"""🚀 The landscape of {topic} is evolving rapidly, and here's what I've learned from the front lines.

After working with {topic} across multiple enterprise projects, I've identified 3 key patterns that separate successful implementations from failed ones:

**1. Start with the Problem, Not the Technology**
Too many teams adopt {topic} because it's trending. The best results come from clear problem definition first.

**2. Iterate, Don't Over-Architect**
Build a working MVP, measure results, and iterate. I've seen teams spend months on perfect architectures that never ship.

**3. Invest in Your Team**
Technology is only as good as the people wielding it. Continuous learning and knowledge sharing multiply impact.

What's your experience with {topic}? I'd love to hear different perspectives in the comments.

#TechLeadership #SoftwareEngineering #{topic.replace(' ', '')}""",
            },
            "post": {
                "title": f"Quick thoughts on {topic}",
                "body": f"""I've been working with {topic} a lot lately and wanted to share a quick insight:

The biggest mistake I see? Over-complicating things.

Keep it simple. Ship it. Learn from real users. Iterate.

What's your take? 👇""",
            },
        },
        "twitter": {
            "thread": {
                "title": f"Thread: {topic}",
                "body": f"""🧵 Thread: Everything I've learned about {topic} in 8 years of software engineering.

1/ {topic} isn't about the tools — it's about solving real problems efficiently.

2/ The best engineers I've worked with master fundamentals first, then specialize.

3/ Code is a means to an end. The real skill is understanding what to build and why.

4/ Hot take: 80% of {topic} debates don't matter in practice. Ship it and measure.

5/ If you're getting started with {topic}, focus on:
- Understanding the core concepts
- Building something real
- Getting feedback early

6/ The tech industry moves fast, but principles are timeless. Invest in fundamentals.

Follow for more engineering insights. 🚀""",
            },
        },
        "dev.to": {
            "article": {
                "title": f"A Practical Guide to {topic}: Lessons from Production",
                "body": f"""# A Practical Guide to {topic}

## Introduction

After implementing {topic} in several production systems, I've compiled the most important lessons learned. This isn't theory — it's battle-tested advice from real-world projects.

## The Challenge

Every team faces similar challenges when adopting {topic}:
- Understanding when it's the right choice
- Avoiding common pitfalls
- Scaling from prototype to production

## Key Lessons

### 1. Start Small
Don't try to implement everything at once. Pick one use case, nail it, then expand.

### 2. Measure Everything
You can't improve what you don't measure. Set up metrics from day one.

### 3. Automate the Boring Stuff
Invest in CI/CD, testing, and monitoring early. It pays dividends.

## Conclusion

{topic} is a powerful tool when applied correctly. Focus on fundamentals, iterate quickly, and always measure your results.

---
*What's your experience with {topic}? Drop a comment below!*""",
            },
        },
    }

    platform_templates = templates.get(body.platform, templates["linkedin"])
    type_template = platform_templates.get(body.post_type, list(platform_templates.values())[0])
    return type_template


def _generate_hashtags(topic: str, platform: str) -> list[str]:
    """Generate relevant hashtags for the content."""
    base = [f"#{topic.replace(' ', '')}", "#SoftwareEngineering", "#TechCareers"]
    platform_tags = {
        "linkedin": ["#OpenToWork", "#Hiring", "#Engineering", "#Innovation"],
        "twitter": ["#DevCommunity", "#100DaysOfCode", "#Programming"],
        "dev.to": ["#webdev", "#programming", "#tutorial", "#beginners"],
        "medium": ["#Technology", "#Software", "#Career", "#Coding"],
    }
    return base + platform_tags.get(platform, [])[:3]


def _generate_calendar(days: int) -> list[dict]:
    """Generate a content calendar."""
    from datetime import datetime, timedelta

    today = datetime.now()
    schedule = []
    platforms = ["linkedin", "twitter", "dev.to", "linkedin", "twitter"]

    for i in range(min(days, 14)):
        day = today + timedelta(days=i)
        if day.weekday() < 5:  # Weekdays only
            platform = platforms[day.weekday()]
            schedule.append({
                "date": day.strftime("%Y-%m-%d"),
                "day": day.strftime("%A"),
                "platform": platform,
                "suggested_type": "article" if platform in ("dev.to", "medium") else "post",
                "best_time": "9:00 AM EST" if platform == "linkedin" else "10:00 AM EST",
            })

    return schedule
