"""API routes for Job Discovery service — supports ALL technical roles."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared.database import get_db
from shared.models import Job, CrawlLog
from shared.schemas import JobOut, PaginatedJobs, CrawlLogOut
from shared.events import EventBus

from ..orchestrator import run_crawl_cycle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
crawl_router = APIRouter(prefix="/api/crawl", tags=["crawl"])


# Held at module-level; set from main.py lifespan
_event_bus: EventBus | None = None


def set_event_bus(bus: EventBus) -> None:
    global _event_bus
    _event_bus = bus


# ─── Job Endpoints ───────────────────────────────────────────────────────────


@router.get("", response_model=PaginatedJobs)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: str | None = None,
    sources: str | None = Query(None, description="Comma-separated list of sources"),
    remote_only: bool = False,
    min_score: int | None = None,
    max_score: int | None = None,
    search: str | None = None,
    technologies: str | None = Query(None, description="Comma-separated technology filters"),
    contract_types: str | None = Query(None, description="Comma-separated: Contract,Freelance,Full-time"),
    locations: str | None = Query(None, description="Comma-separated location filters"),
    companies: str | None = Query(None, description="Comma-separated company name filters"),
    has_recruiter: bool | None = None,
    seniority: str | None = Query(None, description="Comma-separated: junior,mid,senior,lead"),
    role_categories: str | None = Query(None, description="Comma-separated role categories"),
    skills: str | None = Query(None, description="Comma-separated skill filters (matches job technologies)"),
    visa_sponsorship: bool | None = None,
    experience_min: int | None = None,
    experience_max: int | None = None,
    date_from: str | None = Query(None, description="ISO date — jobs discovered after this"),
    sort_by: str = Query("date_discovered", regex="^(date_discovered|match_score|job_title|company_name)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """List discovered jobs with advanced multi-select filtering and pagination."""
    query = select(Job).options(joinedload(Job.analysis)).where(Job.is_active.is_(True))

    # Single source (backward compatibility)
    if source:
        query = query.where(Job.source == source)

    # Multi-select source filter
    if sources:
        source_list = [s.strip() for s in sources.split(",") if s.strip()]
        if source_list:
            query = query.where(Job.source.in_(source_list))

    if remote_only:
        query = query.where(Job.is_remote.is_(True))

    if search:
        query = query.where(Job.job_title.ilike(f"%{search}%"))

    # Contract type multi-select
    if contract_types:
        ct_list = [c.strip() for c in contract_types.split(",") if c.strip()]
        if ct_list:
            query = query.where(Job.contract_type.in_(ct_list))

    # Location multi-select
    if locations:
        from sqlalchemy import or_
        loc_list = [l.strip() for l in locations.split(",") if l.strip()]
        if loc_list:
            loc_filters = [Job.location.ilike(f"%{loc}%") for loc in loc_list]
            query = query.where(or_(*loc_filters))

    # Company multi-select
    if companies:
        comp_list = [c.strip() for c in companies.split(",") if c.strip()]
        if comp_list:
            query = query.where(Job.company_name.in_(comp_list))

    # Date filter
    if date_from:
        from datetime import datetime as dt
        try:
            date_obj = dt.fromisoformat(date_from)
            query = query.where(Job.date_discovered >= date_obj)
        except ValueError:
            pass

    # Join-based filters (require JobAnalysis)
    from shared.models import JobAnalysis
    needs_analysis_join = any([min_score, max_score, technologies, has_recruiter,
                               seniority, role_categories, skills, visa_sponsorship,
                               experience_min, experience_max])

    if needs_analysis_join:
        query = query.join(JobAnalysis)
        if min_score is not None:
            query = query.where(JobAnalysis.match_score >= min_score)
        if max_score is not None:
            query = query.where(JobAnalysis.match_score <= max_score)
        if technologies:
            tech_list = [t.strip() for t in technologies.split(",") if t.strip()]
            if tech_list:
                from sqlalchemy import or_
                tech_filters = [JobAnalysis.technologies.any(t) for t in tech_list]
                query = query.where(or_(*tech_filters))
        if skills:
            skills_list = [s.strip() for s in skills.split(",") if s.strip()]
            if skills_list:
                from sqlalchemy import or_
                skill_filters = [JobAnalysis.technologies.any(s) for s in skills_list]
                query = query.where(or_(*skill_filters))
        if has_recruiter is not None:
            query = query.where(JobAnalysis.has_recruiter.is_(has_recruiter))
        if seniority:
            sen_list = [s.strip() for s in seniority.split(",") if s.strip()]
            if sen_list:
                query = query.where(JobAnalysis.seniority_level.in_(sen_list))
        if role_categories:
            role_list = [r.strip() for r in role_categories.split(",") if r.strip()]
            if role_list:
                query = query.where(JobAnalysis.role_category.in_(role_list))
        if visa_sponsorship is not None:
            query = query.where(JobAnalysis.visa_sponsorship.is_(visa_sponsorship))
        if experience_min is not None:
            query = query.where(
                (JobAnalysis.experience_years_min.is_(None)) |
                (JobAnalysis.experience_years_min >= experience_min)
            )
        if experience_max is not None:
            query = query.where(
                (JobAnalysis.experience_years_max.is_(None)) |
                (JobAnalysis.experience_years_max <= experience_max)
            )

    # Total count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Sorting
    if sort_by == "match_score":
        if not needs_analysis_join:
            query = query.join(JobAnalysis)
        order_col = JobAnalysis.match_score
    elif sort_by == "job_title":
        order_col = Job.job_title
    elif sort_by == "company_name":
        order_col = Job.company_name
    elif sort_by == "date_posted":
        order_col = Job.date_posted
    else:
        order_col = Job.date_discovered

    query = query.order_by(desc(order_col) if sort_order == "desc" else order_col)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.unique().scalars().all()

    return PaginatedJobs(
        total=total,
        page=page,
        page_size=page_size,
        data=[JobOut.model_validate(r) for r in rows],
    )


@router.get("/stats")
async def job_stats(db: AsyncSession = Depends(get_db)):
    """Return aggregate statistics."""
    total = (await db.execute(select(func.count(Job.id)))).scalar() or 0
    active = (await db.execute(select(func.count(Job.id)).where(Job.is_active.is_(True)))).scalar() or 0

    sources_q = select(Job.source, func.count(Job.id)).group_by(Job.source)
    source_rows = (await db.execute(sources_q)).all()
    by_source = {row[0]: row[1] for row in source_rows}

    return {"total": total, "active": active, "by_source": by_source}


@router.get("/filter-options")
async def filter_options(db: AsyncSession = Depends(get_db)):
    """Get distinct filter values for the advanced filter panel."""
    from shared.models import JobAnalysis
    from shared.services.skill_engine import ROLE_TEMPLATES, SKILL_CATEGORIES

    sources = (await db.execute(
        select(Job.source).distinct().where(Job.is_active.is_(True))
    )).scalars().all()

    contract_types = (await db.execute(
        select(Job.contract_type).distinct().where(
            Job.is_active.is_(True), Job.contract_type.isnot(None)
        )
    )).scalars().all()

    locations = (await db.execute(
        select(Job.location).distinct().where(
            Job.is_active.is_(True), Job.location.isnot(None)
        ).limit(50)
    )).scalars().all()

    companies = (await db.execute(
        select(Job.company_name, func.count(Job.id))
        .where(Job.is_active.is_(True), Job.company_name.isnot(None))
        .group_by(Job.company_name)
        .order_by(desc(func.count(Job.id)))
        .limit(30)
    )).all()

    seniority_levels = (await db.execute(
        select(JobAnalysis.seniority_level).distinct()
        .where(JobAnalysis.seniority_level.isnot(None))
    )).scalars().all()

    # Get technologies from analyzed jobs
    technologies = (await db.execute(
        select(func.unnest(JobAnalysis.technologies), func.count())
        .group_by(func.unnest(JobAnalysis.technologies))
        .order_by(desc(func.count()))
        .limit(50)
    )).all()

    # Get role categories from analyzed jobs
    role_categories = (await db.execute(
        select(JobAnalysis.role_category, func.count(JobAnalysis.id))
        .where(JobAnalysis.role_category.isnot(None))
        .group_by(JobAnalysis.role_category)
        .order_by(desc(func.count(JobAnalysis.id)))
    )).all()

    return {
        "sources": sources,
        "contract_types": [ct for ct in contract_types if ct],
        "locations": [loc for loc in locations if loc],
        "top_companies": [{"name": row[0], "count": row[1]} for row in companies],
        "seniority_levels": [s for s in seniority_levels if s],
        "technologies": [{"name": row[0], "count": row[1]} for row in technologies] if technologies else [],
        "role_categories": [
            {"key": row[0], "label": ROLE_TEMPLATES.get(row[0], {}).get("label", row[0]), "count": row[1]}
            for row in role_categories
        ],
        "skill_categories": {k: v for k, v in SKILL_CATEGORIES.items()},
    }


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single job by ID."""
    result = await db.execute(
        select(Job).options(joinedload(Job.analysis)).where(Job.id == job_id)
    )
    job = result.unique().scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut.model_validate(job)


# ─── Crawl Endpoints ────────────────────────────────────────────────────────


@crawl_router.post("/trigger")
async def trigger_crawl(db: AsyncSession = Depends(get_db)):
    """Manually trigger a crawl cycle."""
    if not _event_bus:
        raise HTTPException(status_code=503, detail="Event bus not initialised")
    summary = await run_crawl_cycle(db, _event_bus)
    return {"status": "completed", **summary}


@crawl_router.get("/logs", response_model=list[CrawlLogOut])
async def get_crawl_logs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Return recent crawl log entries."""
    result = await db.execute(
        select(CrawlLog).order_by(desc(CrawlLog.started_at)).limit(limit)
    )
    rows = result.scalars().all()
    return [CrawlLogOut.model_validate(r) for r in rows]
