import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from app.config import settings
from app.models import ResumeRequest, ResumeResponse
from app.generator import generate_resume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Resume Generator AI Service started")
    yield


app = FastAPI(
    title="Resume Generator AI Service",
    description="Generates tailored resumes, cover letters, and outreach emails using AI",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.service_name}


@app.post("/api/generate-resume", response_model=ResumeResponse)
async def generate_resume_endpoint(request: ResumeRequest):
    """Generate a tailored resume, cover letter, and outreach email."""
    try:
        result = await generate_resume(request)
        return result
    except Exception as e:
        logger.error(f"Resume generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
