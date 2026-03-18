"""API Gateway — entry point for all client requests."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, profile, proxy, webhooks, recruiters, feedback, job_hunt, skills, audit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API Gateway starting on port %s", settings.service_port)
    yield
    logger.info("API Gateway shutting down")


app = FastAPI(
    title="AI Career Agent — API Gateway",
    description="Central gateway that routes requests to microservices",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Direct routes (handled by gateway itself)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(webhooks.router)
app.include_router(recruiters.router)
app.include_router(feedback.router)
app.include_router(job_hunt.router)
app.include_router(skills.router)
app.include_router(audit.router)

# Catch-all proxy to downstream services
app.include_router(proxy.router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.service_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
