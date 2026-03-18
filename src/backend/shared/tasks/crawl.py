"""Celery tasks for crawling."""

import logging

from shared.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.crawl.run_scheduled_crawl", queue="crawl")
def run_scheduled_crawl():
    """Periodic task: trigger a crawl cycle via HTTP to the crawl-engine service."""
    import httpx

    try:
        resp = httpx.post("http://crawl-engine:5006/api/crawl/trigger", timeout=120)
        resp.raise_for_status()
        logger.info("Scheduled crawl completed: %s", resp.json())
        return resp.json()
    except Exception:
        logger.exception("Scheduled crawl failed")
        raise
