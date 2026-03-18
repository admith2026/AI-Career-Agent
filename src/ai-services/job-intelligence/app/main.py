import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from app.config import settings
from app.models import JobAnalysisRequest, JobAnalysisResponse
from app.analyzer import analyze_job, vector_store, client
from app.events import start_event_consumer
from shared.vectors import generate_embedding, build_profile_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start event consumer on startup."""
    task = asyncio.create_task(start_event_consumer())
    logger.info("Job Intelligence AI Service started")
    yield
    task.cancel()


app = FastAPI(
    title="Job Intelligence AI Service",
    description="Analyzes job descriptions using AI, extracts technologies, and scores relevance",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.service_name}


@app.post("/api/analyze", response_model=JobAnalysisResponse)
async def analyze_job_endpoint(request: JobAnalysisRequest):
    """Analyze a single job posting via REST API."""
    try:
        result = await analyze_job(request)
        return result
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/batch", response_model=list[JobAnalysisResponse])
async def analyze_batch(requests: list[JobAnalysisRequest]):
    """Analyze multiple job postings."""
    results = []
    for req in requests:
        try:
            result = await analyze_job(req)
            results.append(result)
        except Exception as e:
            logger.error(f"Batch analysis error for {req.job_id}: {e}")
    return results


# ─── Semantic Search Endpoints ───────────────────────────────────────────────


class SemanticSearchRequest(BaseModel):
    query: str | None = None
    skills: list[str] = []
    preferred_technologies: list[str] = []
    headline: str | None = None
    summary: str | None = None
    limit: int = 20
    score_threshold: float = 0.5


@app.post("/api/semantic-search")
async def semantic_search(req: SemanticSearchRequest):
    """Find jobs similar to a user profile or free-text query using vector similarity."""
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not available")
    if not client:
        raise HTTPException(status_code=503, detail="OpenAI not configured")

    text = req.query or build_profile_text(
        headline=req.headline,
        summary=req.summary,
        skills=req.skills,
        preferred_technologies=req.preferred_technologies,
    )
    if not text.strip():
        raise HTTPException(status_code=400, detail="Provide query text or profile fields")

    embedding = await generate_embedding(text, client)
    results = vector_store.search_similar(
        query_vector=embedding,
        limit=req.limit,
        score_threshold=req.score_threshold,
    )
    return {"results": results, "total": len(results)}


@app.get("/api/vector-stats")
async def vector_stats():
    """Return Qdrant collection stats."""
    if not vector_store:
        return {"status": "unavailable"}
    return {"collection": "job_embeddings", "count": vector_store.count()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
