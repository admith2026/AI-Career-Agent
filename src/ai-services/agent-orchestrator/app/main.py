"""Agent Orchestrator — coordinates multi-agent workflows with autonomous execution."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import router
from .executor import process_queued_tasks
from shared.database import engine
from shared.models import Base

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass  # Tables may already exist from another service

    # Start background task processor
    task_processor = asyncio.create_task(process_queued_tasks())
    logger.info("Agent Orchestrator started on port %d (autonomous mode)", settings.service_port)
    yield
    task_processor.cancel()
    logger.info("Agent Orchestrator shut down")


app = FastAPI(title="Agent Orchestrator", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"service": "agent-orchestrator", "status": "healthy"}
