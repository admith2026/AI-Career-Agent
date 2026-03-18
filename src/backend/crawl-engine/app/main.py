"""Crawl Engine — Distributed crawling microservice."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.routes import router
from app.orchestrator import CrawlOrchestrator
from app.seeds import seed_default_sources
from shared.database import async_session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

orchestrator = CrawlOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed default sources
    async with async_session_factory() as db:
        await seed_default_sources(db)

    # Start crawler orchestrator in background
    task = asyncio.create_task(orchestrator.start())
    logger.info("Crawl Engine started — worker_id=%s", settings.worker_id)
    yield
    await orchestrator.stop()
    task.cancel()


app = FastAPI(
    title="Crawl Engine",
    description="Distributed internet-scale crawling service",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "crawl-engine", "worker_id": settings.worker_id}
