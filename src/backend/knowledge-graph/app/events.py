"""Knowledge Graph event consumer — syncs data from pipeline into Neo4j."""

import logging

from shared.events import EventBus, Exchanges
from app.graph import GraphManager

logger = logging.getLogger(__name__)


async def start_consumer(event_bus: EventBus, graph: GraphManager):
    """Subscribe to events and sync into the knowledge graph."""

    async def on_job_analyzed(data: dict):
        company = data.get("company_name", "")
        title = data.get("job_title", "")
        technologies = data.get("technologies", [])

        if company and title:
            await graph.upsert_company(company)
            await graph.add_job_role(title, company, technologies)

        recruiter_email = data.get("recruiter_email", "")
        recruiter_name = data.get("recruiter_name", "")
        if recruiter_email and recruiter_name:
            await graph.upsert_recruiter(recruiter_email, recruiter_name, company)

    try:
        await event_bus.subscribe(
            Exchanges.JOB_ANALYZED,
            "knowledge-graph-jobs-queue",
            on_job_analyzed,
        )
    except Exception:
        logger.info("JOB_ANALYZED exchange not ready yet")

    async def on_signal(data: dict):
        company = data.get("company_name", "")
        if company:
            await graph.add_signal(
                company,
                data.get("signal_type", "unknown"),
                data.get("title", ""),
                data.get("confidence", 0.5),
            )

    try:
        await event_bus.subscribe(
            "signal.detected",
            "knowledge-graph-signals-queue",
            on_signal,
        )
    except Exception:
        logger.info("signal.detected exchange not ready yet")

    logger.info("Knowledge graph event consumer started")
