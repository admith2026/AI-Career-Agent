"""Decision Engine — autonomous job evaluation and decision microservice."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.routes import router, set_engine
from app.engine import DecisionEngine
from app.events import start_consumer
from shared.events import EventBus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

event_bus = EventBus(settings.rabbitmq_url)
engine = DecisionEngine(event_bus)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await event_bus.connect()
    set_engine(engine)
    await start_consumer(engine)
    logger.info("Decision Engine started")
    yield
    await event_bus.close()
    logger.info("Decision Engine shutting down")


app = FastAPI(
    title="Decision Engine",
    description="Autonomous job scoring, evaluation, and decision service",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "decision-engine"}
