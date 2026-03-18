"""Notification Service — FastAPI entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.events import EventBus

from .config import settings
from .routes import router
from .events import start_consumer
from .scheduler import scheduler_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    event_bus = EventBus(settings.rabbitmq_url)
    await event_bus.connect()

    # Start consuming notification events
    await start_consumer(event_bus)

    # Start the scheduled report loop
    scheduler_task = asyncio.create_task(scheduler_loop())
    logger.info("Notification Service started on port %d", settings.service_port)

    yield

    scheduler_task.cancel()
    await event_bus.close()
    logger.info("Notification Service shut down")


app = FastAPI(
    title="Notification Service",
    version="1.0.0",
    lifespan=lifespan,
)

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
    return {"service": "notifications", "status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.service_port, reload=True)
