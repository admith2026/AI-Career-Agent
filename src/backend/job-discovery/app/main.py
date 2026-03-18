"""Job Discovery Service — FastAPI entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.events import EventBus

from .config import settings
from .routes import router, crawl_router, set_event_bus
from .scheduler import crawl_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    event_bus = EventBus(settings.rabbitmq_url)
    await event_bus.connect()
    set_event_bus(event_bus)
    logger.info("Job Discovery Service started on port %d", settings.service_port)

    # Launch the background crawl scheduler
    scheduler_task = asyncio.create_task(crawl_scheduler(event_bus))

    yield

    # Shutdown
    scheduler_task.cancel()
    await event_bus.close()
    logger.info("Job Discovery Service shut down")


app = FastAPI(
    title="Job Discovery Service",
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
app.include_router(crawl_router)


@app.get("/health")
async def health():
    return {"service": "job-discovery", "status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.service_port, reload=True)
