"""Pydantic schemas for API request/response serialization."""

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─── Auth ────────────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    token: str
    user: UserOut


# ─── Profile ────────────────────────────────────────────────────────────────


class NotificationPreferences(BaseModel):
    email: bool = True
    telegram: bool = False
    whatsapp: bool = False
    push: bool = True


class ProfileUpdate(BaseModel):
    headline: str | None = Field(None, max_length=500)
    summary: str | None = Field(None, max_length=5000)
    skills: list[str] | None = None
    experience_years: int | None = None
    preferred_rate_min: float | None = None
    preferred_rate_max: float | None = None
    preferred_contract_types: list[str] | None = None
    preferred_technologies: list[str] | None = None
    preferred_roles: list[str] | None = None
    preferred_locations: list[str] | None = None
    visa_required: bool | None = None
    min_company_size: str | None = Field(None, max_length=50)
    resume_base: str | None = Field(None, max_length=50000)
    linkedin_url: str | None = Field(None, max_length=500)
    github_url: str | None = Field(None, max_length=500)
    portfolio_url: str | None = Field(None, max_length=500)


class ProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    headline: str | None = None
    summary: str | None = None
    skills: list[str] = []
    experience_years: int = 0
    preferred_rate_min: float | None = None
    preferred_rate_max: float | None = None
    preferred_contract_types: list[str] = []
    preferred_technologies: list[str] = []
    preferred_roles: list[str] = []
    preferred_locations: list[str] = []
    visa_required: bool = False
    min_company_size: str | None = None
    resume_base: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None

    class Config:
        from_attributes = True


# ─── Jobs ────────────────────────────────────────────────────────────────────


class JobOut(BaseModel):
    id: UUID
    external_id: str | None = None
    source: str
    job_title: str
    company_name: str | None = None
    vendor_name: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    phone_number: str | None = None
    job_description: str | None = None
    job_link: str
    salary_or_rate: str | None = None
    location: str | None = None
    is_remote: bool = True
    contract_type: str | None = None
    date_posted: datetime | None = None
    date_discovered: datetime | None = None
    is_active: bool = True
    analysis: "JobAnalysisOut | None" = None

    class Config:
        from_attributes = True


class JobAnalysisOut(BaseModel):
    id: UUID
    job_id: UUID
    technologies: list[str] = []
    seniority_level: str | None = None
    is_contract: bool | None = None
    is_remote_confirmed: bool | None = None
    has_recruiter: bool | None = None
    vendor_detected: str | None = None
    match_score: int = 0
    score_breakdown: dict | None = None
    key_requirements: list[str] = []
    ai_summary: str | None = None
    llm_model: str | None = None
    analyzed_at: datetime | None = None
    # Multi-role fields
    role_category: str | None = None
    visa_sponsorship: bool | None = None
    experience_years_min: int | None = None
    experience_years_max: int | None = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    match_reasons: list | None = None

    class Config:
        from_attributes = True


class PaginatedJobs(BaseModel):
    total: int
    page: int
    page_size: int
    data: list[JobOut]


# ─── Applications ───────────────────────────────────────────────────────────


class ApplyRequest(BaseModel):
    job_id: UUID
    user_id: UUID | None = None


class ApplicationStatusUpdate(BaseModel):
    status: str
    notes: str | None = None


class ApplicationOut(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    resume_id: UUID | None = None
    status: str = "pending"
    applied_via: str | None = None
    applied_at: datetime | None = None
    response_received: bool = False
    notes: str | None = None
    created_at: datetime | None = None
    job: JobOut | None = None

    class Config:
        from_attributes = True


# ─── Resume ──────────────────────────────────────────────────────────────────


class ResumeRequest(BaseModel):
    user_id: UUID
    job_id: UUID
    job_title: str
    company_name: str | None = None
    job_description: str | None = None
    technologies: list[str] = []
    user_name: str = ""
    user_summary: str = ""
    user_skills: list[str] = []
    user_experience_years: int = 0
    base_resume: str = ""


class ResumeResponse(BaseModel):
    resume_id: UUID
    user_id: UUID
    job_id: UUID
    resume_content: str
    cover_letter: str
    outreach_email: str
    format: str = "markdown"


class ResumeOut(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID | None = None
    resume_content: str
    cover_letter: str | None = None
    outreach_email: str | None = None
    format: str = "markdown"
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ─── Job Intelligence ────────────────────────────────────────────────────────


class JobAnalysisRequest(BaseModel):
    job_id: UUID
    job_title: str
    company_name: str | None = None
    job_description: str | None = None
    job_link: str


class ScoreBreakdown(BaseModel):
    remote: int = 0
    contract: int = 0
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
    llm_model: str


# ─── Notifications ───────────────────────────────────────────────────────────


class NotificationOut(BaseModel):
    id: UUID
    user_id: UUID
    channel: str
    subject: str | None = None
    body: str
    status: str = "pending"
    sent_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ─── Crawl Logs ──────────────────────────────────────────────────────────────


class CrawlLogOut(BaseModel):
    id: UUID
    source: str
    started_at: datetime
    completed_at: datetime | None = None
    jobs_found: int = 0
    jobs_new: int = 0
    status: str = "running"
    error_message: str | None = None

    class Config:
        from_attributes = True


# ─── Recruiter Contacts ─────────────────────────────────────────────────────


class RecruiterContactOut(BaseModel):
    id: UUID
    name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    linkedin_url: str | None = None
    source: str | None = None
    last_contacted: datetime | None = None

    class Config:
        from_attributes = True


# ─── Companies ───────────────────────────────────────────────────────────────


class CompanyOut(BaseModel):
    id: UUID
    name: str
    domain: str | None = None
    industry: str | None = None
    size_range: str | None = None
    headquarters: str | None = None
    careers_url: str | None = None
    linkedin_url: str | None = None
    github_org: str | None = None
    tech_stack: list[str] = []
    is_actively_hiring: bool = False
    hiring_velocity: int = 0

    class Config:
        from_attributes = True


# ─── Hiring Signals ─────────────────────────────────────────────────────────


class HiringSignalOut(BaseModel):
    id: UUID
    company_id: UUID | None = None
    signal_type: str
    title: str
    description: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    confidence: float | None = None
    predicted_roles: list[str] = []
    detected_at: datetime | None = None

    class Config:
        from_attributes = True


class PaginatedSignals(BaseModel):
    total: int
    page: int
    page_size: int
    data: list[HiringSignalOut]


# ─── Crawler Sources ────────────────────────────────────────────────────────


class CrawlerSourceOut(BaseModel):
    id: UUID
    name: str
    source_type: str
    url_pattern: str
    crawl_frequency_minutes: int = 60
    priority: int = 5
    is_enabled: bool = True
    requires_js: bool = False
    anti_bot_level: str = "low"
    last_crawled_at: datetime | None = None
    success_rate: float = 100.0

    class Config:
        from_attributes = True


class CrawlerSourceCreate(BaseModel):
    name: str
    source_type: str
    url_pattern: str
    crawl_frequency_minutes: int = 60
    priority: int = 5
    requires_js: bool = False
    anti_bot_level: str = "low"
    config: dict = {}


# ─── Outreach Campaigns ─────────────────────────────────────────────────────


class OutreachCampaignOut(BaseModel):
    id: UUID
    user_id: UUID
    recruiter_id: UUID | None = None
    company_id: UUID | None = None
    job_id: UUID | None = None
    campaign_type: str
    subject: str | None = None
    body: str
    channel: str
    status: str = "draft"
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    replied_at: datetime | None = None
    follow_up_count: int = 0
    max_follow_ups: int = 3
    next_follow_up: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class OutreachRequest(BaseModel):
    recruiter_id: UUID | None = None
    company_id: UUID | None = None
    job_id: UUID | None = None
    campaign_type: str = "cold_outreach"
    channel: str = "email"


# ─── Decision Engine ────────────────────────────────────────────────────────


class DecisionLogOut(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID | None = None
    decision_type: str
    decision: str
    reason: str | None = None
    score_data: dict | None = None
    executed: bool = False
    executed_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ─── Pipeline ────────────────────────────────────────────────────────────────


class PipelineEventOut(BaseModel):
    id: UUID
    event_type: str
    source_service: str
    payload: dict
    processed: bool = False
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class PipelineStats(BaseModel):
    total_events: int
    processed: int
    pending: int
    events_by_type: dict = {}


# ─── Dashboard Analytics ────────────────────────────────────────────────────


class DashboardAnalytics(BaseModel):
    total_jobs: int = 0
    new_jobs_today: int = 0
    total_applications: int = 0
    pending_applications: int = 0
    interviews: int = 0
    offers: int = 0
    active_signals: int = 0
    companies_tracked: int = 0
    outreach_sent: int = 0
    outreach_replied: int = 0
    avg_match_score: float = 0.0
    top_sources: list[dict] = []
    recent_decisions: list[DecisionLogOut] = []
