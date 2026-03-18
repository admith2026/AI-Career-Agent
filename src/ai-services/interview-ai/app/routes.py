"""Interview AI routes — prep, questions, and company research."""

import json
import random
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import get_current_user
from shared.database import get_db
from shared.models import InterviewPrep, Job

router = APIRouter(prefix="/api/interview", tags=["Interview AI"])


class PrepRequest(BaseModel):
    job_id: UUID | None = None
    company_name: str
    role_title: str
    difficulty_level: str = "intermediate"  # beginner / intermediate / senior / staff


@router.post("/prep")
async def generate_prep(
    body: PrepRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a full interview prep package for a company + role."""
    questions = _generate_questions(body.role_title, body.difficulty_level)
    answers = _generate_answers(questions)
    behavioral = _generate_behavioral_stories(body.role_title)
    research = _generate_company_research(body.company_name)
    technical = _get_technical_topics(body.role_title)

    prep = InterviewPrep(
        user_id=user["user_id"],
        job_id=body.job_id,
        company_name=body.company_name,
        role_title=body.role_title,
        questions=questions,
        answers=answers,
        behavioral_stories=behavioral,
        technical_topics=technical,
        company_research=research,
        difficulty_level=body.difficulty_level,
    )
    db.add(prep)
    await db.commit()
    await db.refresh(prep)

    return {
        "id": str(prep.id),
        "company": body.company_name,
        "role": body.role_title,
        "difficulty": body.difficulty_level,
        "questions_count": len(questions),
        "behavioral_count": len(behavioral),
        "technical_topics": technical,
        "company_research_sections": list(research.keys()),
    }


@router.get("/preps")
async def list_preps(
    limit: int = 20,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all interview prep packages."""
    result = await db.execute(
        select(InterviewPrep)
        .where(InterviewPrep.user_id == user["user_id"])
        .order_by(InterviewPrep.created_at.desc())
        .limit(limit)
    )
    preps = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "company": p.company_name,
            "role": p.role_title,
            "difficulty": p.difficulty_level,
            "questions_count": len(p.questions) if p.questions else 0,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in preps
    ]


@router.get("/preps/{prep_id}")
async def get_prep(
    prep_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a full interview prep package."""
    result = await db.execute(
        select(InterviewPrep).where(
            InterviewPrep.id == prep_id, InterviewPrep.user_id == user["user_id"]
        )
    )
    prep = result.scalar_one_or_none()
    if not prep:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Prep not found")

    return {
        "id": str(prep.id),
        "company": prep.company_name,
        "role": prep.role_title,
        "difficulty": prep.difficulty_level,
        "questions": prep.questions,
        "answers": prep.answers,
        "behavioral_stories": prep.behavioral_stories,
        "technical_topics": prep.technical_topics,
        "company_research": prep.company_research,
        "created_at": prep.created_at.isoformat() if prep.created_at else None,
    }


@router.get("/questions/{role_title}")
async def predict_questions(
    role_title: str,
    difficulty: str = "intermediate",
    user: dict = Depends(get_current_user),
):
    """Predict likely interview questions for a role."""
    questions = _generate_questions(role_title, difficulty)
    answers = _generate_answers(questions)
    return {
        "role": role_title,
        "difficulty": difficulty,
        "questions": [
            {"question": q, "suggested_answer": a} for q, a in zip(questions, answers)
        ],
    }


@router.get("/stats")
async def interview_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get interview prep statistics."""
    total = await db.execute(
        select(func.count(InterviewPrep.id)).where(
            InterviewPrep.user_id == user["user_id"]
        )
    )
    by_company = await db.execute(
        select(InterviewPrep.company_name, func.count(InterviewPrep.id))
        .where(InterviewPrep.user_id == user["user_id"])
        .group_by(InterviewPrep.company_name)
        .order_by(func.count(InterviewPrep.id).desc())
        .limit(10)
    )

    return {
        "total_preps": total.scalar() or 0,
        "by_company": {r[0]: r[1] for r in by_company.all()},
    }


# ---------- AI generation helpers ----------


def _generate_questions(role: str, difficulty: str) -> list[dict]:
    """Generate predicted interview questions."""
    role_lower = role.lower()

    base_technical = []
    if any(k in role_lower for k in ["python", "backend", "fastapi", "django"]):
        base_technical = [
            {"type": "technical", "q": "Explain the GIL in Python and how you work around it for CPU-bound tasks."},
            {"type": "technical", "q": "How would you design a rate-limited API with Redis?"},
            {"type": "technical", "q": "Walk me through SQLAlchemy async session management and connection pooling."},
            {"type": "technical", "q": "How do you handle database migrations in a microservices environment?"},
        ]
    elif any(k in role_lower for k in [".net", "c#", "dotnet", "asp.net"]):
        base_technical = [
            {"type": "technical", "q": "Explain dependency injection in ASP.NET Core and its lifetime scopes."},
            {"type": "technical", "q": "How would you implement CQRS with MediatR in a .NET microservice?"},
            {"type": "technical", "q": "Describe your approach to handling distributed transactions across microservices."},
            {"type": "technical", "q": "How does the middleware pipeline work in ASP.NET Core?"},
        ]
    elif any(k in role_lower for k in ["react", "frontend", "full-stack", "fullstack"]):
        base_technical = [
            {"type": "technical", "q": "Explain the React reconciliation algorithm and when useMemo is appropriate."},
            {"type": "technical", "q": "How would you architect state management for a large-scale React application?"},
            {"type": "technical", "q": "Walk me through your approach to performance optimization in a Next.js app."},
            {"type": "technical", "q": "How do you handle authentication and authorization in a React SPA?"},
        ]
    else:
        base_technical = [
            {"type": "technical", "q": "Describe a complex system you've designed and the trade-offs you made."},
            {"type": "technical", "q": "How do you approach debugging a production performance issue?"},
            {"type": "technical", "q": "Explain your strategy for ensuring high availability and fault tolerance."},
            {"type": "technical", "q": "How would you design a real-time notification system at scale?"},
        ]

    system_design = [
        {"type": "system_design", "q": "Design a URL shortener that handles 10M requests/day."},
        {"type": "system_design", "q": "Design a real-time chat system like Slack."},
        {"type": "system_design", "q": "Design a job board platform that can crawl and index 1M jobs daily."},
    ]

    behavioral = [
        {"type": "behavioral", "q": "Tell me about a time you had a disagreement with a team member."},
        {"type": "behavioral", "q": "Describe a project where you had to learn a new technology quickly."},
        {"type": "behavioral", "q": "Tell me about a time you dealt with a production outage."},
        {"type": "behavioral", "q": "How do you handle conflicting priorities from multiple stakeholders?"},
    ]

    questions = base_technical + random.sample(system_design, min(2, len(system_design))) + behavioral

    if difficulty == "senior" or difficulty == "staff":
        questions.append({"type": "leadership", "q": "How do you mentor junior engineers while still delivering your own work?"})
        questions.append({"type": "leadership", "q": "Describe how you've influenced engineering culture or processes."})

    return questions


def _generate_answers(questions: list[dict]) -> list[dict]:
    """Generate suggested answer frameworks."""
    return [
        {
            "question": q["q"],
            "framework": "STAR" if q["type"] == "behavioral" else "structured",
            "key_points": [
                "Start with the high-level approach",
                "Discuss trade-offs and alternatives considered",
                "Mention specific technologies and patterns",
                "Quantify impact where possible",
            ],
            "time_target_minutes": 3 if q["type"] == "behavioral" else 5,
        }
        for q in questions
    ]


def _generate_behavioral_stories(role: str) -> list[dict]:
    """Generate STAR-format behavioral story templates."""
    return [
        {
            "theme": "Technical Leadership",
            "situation": "Led migration of monolith to microservices",
            "task": "Break down system, maintain uptime, coordinate team",
            "action": "Designed strangler fig pattern, created API contracts, set up CI/CD",
            "result": "Zero-downtime migration, 40% performance improvement, team upskilled",
        },
        {
            "theme": "Conflict Resolution",
            "situation": "Disagreement on tech stack choice for new project",
            "task": "Reach consensus while maintaining team morale",
            "action": "Organized spike sessions, created comparison matrix, let data drive decision",
            "result": "Team aligned on choice, shipped 2 weeks early, approach became team standard",
        },
        {
            "theme": "Deadline Pressure",
            "situation": "Critical feature needed for client demo in 3 days",
            "task": "Deliver MVP without sacrificing quality",
            "action": "Scoped minimum viable feature, pair-programmed critical paths, automated testing",
            "result": "Delivered on time, demo secured contract, later iterated to full feature",
        },
    ]


def _generate_company_research(company: str) -> dict:
    """Generate company research framework."""
    return {
        "overview": f"Research {company}'s mission, recent funding, and market position.",
        "tech_stack": f"Investigate {company}'s engineering blog, GitHub repos, and job postings for tech clues.",
        "culture": f"Check {company}'s Glassdoor reviews, LinkedIn posts, and company values page.",
        "recent_news": f"Search for {company}'s recent press releases, product launches, and earnings.",
        "questions_to_ask": [
            f"What's the biggest technical challenge {company} is facing right now?",
            "How does the engineering team handle technical debt?",
            "What does the on-call rotation look like?",
            "How are engineering priorities decided?",
            "What's the team's approach to code reviews and testing?",
        ],
    }


def _get_technical_topics(role: str) -> list[str]:
    """Return technical topics to study based on role."""
    role_lower = role.lower()
    base = ["System Design", "Data Structures", "Algorithms", "API Design"]

    if any(k in role_lower for k in ["python", "backend", "fastapi"]):
        return base + ["Python Concurrency", "SQLAlchemy", "Redis", "Message Queues", "Docker"]
    elif any(k in role_lower for k in [".net", "c#"]):
        return base + ["ASP.NET Core", "Entity Framework", "Azure", "CQRS/MediatR", "gRPC"]
    elif any(k in role_lower for k in ["react", "frontend"]):
        return base + ["React Hooks", "State Management", "Performance", "Accessibility", "CSS-in-JS"]
    return base + ["Microservices", "Cloud Architecture", "CI/CD", "Monitoring"]
