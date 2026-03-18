"""Data Pipeline — streaming data ingestion microservice."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.routes import router
from app.processor import DataProcessor
from app.events import start_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

processor = DataProcessor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await processor.connect()
    await start_consumer(processor)
    logger.info("Data Pipeline started")
    yield
    logger.info("Data Pipeline shutting down")


app = FastAPI(
    title="Data Pipeline",
    description="Streaming data ingestion and normalization service",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "data-pipeline"}
