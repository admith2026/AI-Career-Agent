"""Voice AI Service — Automated recruiter calls via Twilio."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Voice AI Service started on port 5012")
    yield
    logger.info("Voice AI Service shutting down")


app = FastAPI(title="Voice AI Service", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "voice-ai"}
