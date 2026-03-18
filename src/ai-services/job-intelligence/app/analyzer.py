import json
import logging
from openai import AsyncOpenAI
from app.config import settings
from app.models import JobAnalysisRequest, JobAnalysisResponse, ScoreBreakdown
from app.scoring import calculate_match_score
from shared.vectors import VectorStore, generate_embedding, build_job_text

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

# Qdrant vector store
try:
    vector_store = VectorStore(host=settings.qdrant_host, port=settings.qdrant_port)
except Exception:
    logger.warning("Qdrant not available — vector matching disabled")
    vector_store = None

ANALYSIS_PROMPT = """You are an AI job analyst. Analyze this job posting and extract structured information.
You support ALL technical roles — not limited to any specific technology.

Job Title: {job_title}
Company: {company_name}
Job Description:
{job_description}

Return a JSON object with these fields:
{{
    "technologies": ["list of specific technologies mentioned"],
    "seniority_level": "junior|mid|senior|lead|principal|staff or null",
    "is_contract": true/false,
    "is_remote_confirmed": true/false,
    "has_recruiter": true/false (is this posted by a recruiter/staffing agency?),
    "vendor_detected": "staffing agency name or null",
    "key_requirements": ["top 5 requirements"],
    "summary": "2-3 sentence summary of the role",
    "role_category": "one of: fullstack_dotnet, fullstack_java, python_backend, frontend_react, ai_ml_engineer, data_engineer, devops_cloud, mobile_developer, security_engineer, golang_developer, other",
    "visa_sponsorship": true/false/null,
    "experience_years_min": integer or null,
    "experience_years_max": integer or null
}}

Return ONLY valid JSON, no markdown formatting."""


async def analyze_job(request: JobAnalysisRequest) -> JobAnalysisResponse:
    """Analyze a job using LLM + rule-based scoring. Supports ALL technical roles."""

    description = request.job_description or ""
    technologies: list[str] = []
    seniority_level = None
    is_contract = False
    is_remote = True
    has_recruiter = False
    vendor_detected = None
    key_requirements: list[str] = []
    ai_summary = ""
    model_used = "rule-based"
    role_category = None
    visa_sponsorship = None
    experience_years_min = None
    experience_years_max = None

    # Try LLM analysis if API key is configured
    if client and description:
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a job posting analyst. Return only valid JSON.",
                    },
                    {
                        "role": "user",
                        "content": ANALYSIS_PROMPT.format(
                            job_title=request.job_title,
                            company_name=request.company_name or "Unknown",
                            job_description=description[:4000],
                        ),
                    },
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            content = response.choices[0].message.content or "{}"
            # Strip markdown code fences if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content)
            technologies = data.get("technologies", [])
            seniority_level = data.get("seniority_level")
            is_contract = data.get("is_contract", False)
            is_remote = data.get("is_remote_confirmed", True)
            has_recruiter = data.get("has_recruiter", False)
            vendor_detected = data.get("vendor_detected")
            key_requirements = data.get("key_requirements", [])
            ai_summary = data.get("summary", "")
            role_category = data.get("role_category")
            visa_sponsorship = data.get("visa_sponsorship")
            experience_years_min = data.get("experience_years_min")
            experience_years_max = data.get("experience_years_max")
            model_used = settings.openai_model
        except Exception as e:
            logger.error(f"LLM analysis failed for job {request.job_id}: {e}")
            # Fall through to rule-based scoring

    # Calculate match score
    score, breakdown = calculate_match_score(
        job_title=request.job_title,
        job_description=description,
        technologies=technologies,
        is_remote=is_remote,
        is_contract=is_contract,
    )

    # Generate and store embedding in Qdrant
    embedding_id = None
    if client and vector_store and description:
        try:
            job_text = build_job_text(request.job_title, request.company_name, description)
            embedding = await generate_embedding(job_text, client)
            embedding_id = vector_store.upsert_embedding(
                job_id=request.job_id,
                embedding=embedding,
                payload={
                    "job_title": request.job_title,
                    "company": request.company_name or "",
                    "technologies": technologies,
                    "match_score": score,
                    "is_remote": is_remote,
                    "is_contract": is_contract,
                    "role_category": role_category,
                    "seniority_level": seniority_level,
                },
            )
        except Exception as e:
            logger.error("Embedding generation/storage failed for job %s: %s", request.job_id, e)

    return JobAnalysisResponse(
        job_id=request.job_id,
        technologies=technologies,
        seniority_level=seniority_level,
        is_contract=is_contract,
        is_remote_confirmed=is_remote,
        has_recruiter=has_recruiter,
        vendor_detected=vendor_detected,
        match_score=score,
        score_breakdown=breakdown,
        key_requirements=key_requirements,
        ai_summary=ai_summary or f"Job: {request.job_title} at {request.company_name or 'Unknown'}",
        embedding_id=embedding_id,
        llm_model=model_used,
        role_category=role_category,
        visa_sponsorship=visa_sponsorship,
        experience_years_min=experience_years_min,
        experience_years_max=experience_years_max,
    )
