"""JSearch API integration — fetch jobs for ANY technical role from RapidAPI.

Supports dynamic queries based on user skills and preferred roles.
No longer hardcoded to .NET — works with all technical stacks.
"""

import logging
from dataclasses import dataclass

import httpx

from shared.config import BaseServiceSettings

logger = logging.getLogger(__name__)

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
DEFAULT_QUERY = "software developer remote contract USA"


@dataclass
class ParsedJob:
    title: str
    company: str
    description: str
    apply_link: str
    location: str
    job_id: str
    date_posted: str = ""


async def fetch_jobs(
    query: str = DEFAULT_QUERY,
    num_pages: int = 1,
) -> list[ParsedJob]:
    """Fetch jobs from JSearch API and return parsed results."""
    settings = BaseServiceSettings()
    api_key = settings.jsearch_api_key

    if not api_key:
        logger.error("JSEARCH_API_KEY is not configured")
        return []

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    params = {
        "query": query,
        "num_pages": str(num_pages),
        "date_posted": "week",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(JSEARCH_URL, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("JSearch API HTTP error %s: %s", exc.response.status_code, exc.response.text[:200])
            return []
        except Exception:
            logger.exception("JSearch API request failed")
            return []

    raw_jobs = data.get("data", [])
    logger.info("JSearch returned %d raw jobs for query: %s", len(raw_jobs), query)

    parsed: list[ParsedJob] = []
    for item in raw_jobs:
        title = item.get("job_title", "").strip()
        company = item.get("employer_name", "").strip()
        description = item.get("job_description", "").strip()
        apply_link = (
            item.get("job_apply_link")
            or item.get("job_google_link")
            or ""
        ).strip()
        location = item.get("job_city", "Remote")
        job_id = item.get("job_id", "")
        date_posted = item.get("job_posted_at_datetime_utc", "") or item.get("job_posted_date", "")

        if not title or not description:
            continue

        parsed.append(ParsedJob(
            title=title,
            company=company,
            description=description[:3000],  # cap for LLM context
            apply_link=apply_link,
            location=location or "Remote",
            job_id=job_id,
            date_posted=date_posted,
        ))

    logger.info("Parsed %d valid jobs from JSearch response", len(parsed))
    return parsed


async def fetch_jobs_multi_query(
    queries: list[str],
    num_pages: int = 1,
) -> list[ParsedJob]:
    """Fetch jobs across multiple search queries, deduplicating by job_id."""
    all_jobs: list[ParsedJob] = []
    seen_ids: set[str] = set()

    for query in queries:
        jobs = await fetch_jobs(query=query, num_pages=num_pages)
        for job in jobs:
            if job.job_id and job.job_id not in seen_ids:
                seen_ids.add(job.job_id)
                all_jobs.append(job)
            elif not job.job_id:
                all_jobs.append(job)

    logger.info("Multi-query fetch: %d unique jobs from %d queries", len(all_jobs), len(queries))
    return all_jobs
