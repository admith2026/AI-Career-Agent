from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class JobAnalysisRequest(BaseModel):
    job_id: UUID
    job_title: str
    company_name: str | None = None
    job_description: str | None = None
    job_link: str


class ScoreBreakdown(BaseModel):
    remote: int = 0
    contract: int = 0
    skill_match: int = 0
    seniority_match: int = 0
    tech_stack: int = 0
    bonus: int = 0
    # Legacy fields (kept for backward compat)
    dotnet_core: int = 0
    azure: int = 0
    frontend: int = 0
    csharp: int = 0
    microservices: int = 0


class JobAnalysisResponse(BaseModel):
    job_id: UUID
    technologies: list[str]
    seniority_level: str | None = None
    is_contract: bool
    is_remote_confirmed: bool
    has_recruiter: bool
    vendor_detected: str | None = None
    match_score: int
    score_breakdown: ScoreBreakdown
    key_requirements: list[str]
    ai_summary: str
    embedding_id: str | None = None
    llm_model: str
    # Multi-role fields
    role_category: str | None = None
    visa_sponsorship: bool | None = None
    experience_years_min: int | None = None
    experience_years_max: int | None = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []


class JobDiscoveredEvent(BaseModel):
    JobId: UUID
    Source: str
    JobTitle: str
    CompanyName: str | None = None
    JobLink: str
    DiscoveredAt: datetime


class JobAnalyzedEvent(BaseModel):
    JobId: UUID
    MatchScore: int
    Technologies: list[str]
    IsContract: bool
    IsRemote: bool
    AiSummary: str | None = None
    RoleCategory: str | None = None
