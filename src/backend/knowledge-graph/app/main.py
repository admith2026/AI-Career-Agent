"""Knowledge Graph — Neo4j-powered company and hiring intelligence service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.routes import router, graph
from app.events import start_consumer
from shared.events import EventBus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

event_bus = EventBus(settings.rabbitmq_url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await graph.connect()
    await event_bus.connect()
    await start_consumer(event_bus, graph)
    logger.info("Knowledge Graph service started")
    yield
    await event_bus.close()
    await graph.close()
    logger.info("Knowledge Graph service shutting down")


app = FastAPI(
    title="Knowledge Graph",
    description="Neo4j-powered company/recruiter/hiring intelligence graph",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "knowledge-graph"}
