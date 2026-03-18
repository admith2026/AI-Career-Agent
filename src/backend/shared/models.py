"""SQLAlchemy ORM models for the Career Agent platform."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ─── Users ───────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(512), nullable=False)
    phone = Column(String(50))
    telegram_chat_id = Column(String(100))
    whatsapp_number = Column(String(50))
    notification_preferences = Column(
        JSONB,
        default={"email": True, "telegram": False, "whatsapp": False, "push": True},
    )
    auto_apply_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    applications = relationship("JobApplication", back_populates="user")
    resumes = relationship("GeneratedResume", back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    headline = Column(String(500))
    summary = Column(Text)
    skills = Column(ARRAY(Text), default=[])
    experience_years = Column(Integer, default=0)
    preferred_rate_min = Column(Numeric(10, 2))
    preferred_rate_max = Column(Numeric(10, 2))
    preferred_contract_types = Column(ARRAY(Text), default=["Contract", "Freelance"])
    preferred_technologies = Column(ARRAY(Text), default=[])
    preferred_roles = Column(ARRAY(Text), default=[])  # role template keys from skill_engine
    preferred_locations = Column(ARRAY(Text), default=["Remote", "USA"])
    visa_required = Column(Boolean, default=False)
    min_company_size = Column(String(50))  # startup, small, medium, large, enterprise
    resume_base = Column(Text)
    linkedin_url = Column(String(500))
    github_url = Column(String(500))
    portfolio_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")


# ─── Jobs ────────────────────────────────────────────────────────────────────


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("external_id", "source", name="uq_jobs_external_source"),
        Index("idx_jobs_source", "source"),
        Index("idx_jobs_date_discovered", "date_discovered"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(500))
    source = Column(String(100), nullable=False)
    job_title = Column(String(500), nullable=False)
    company_name = Column(String(500))
    vendor_name = Column(String(500))
    recruiter_name = Column(String(500))
    recruiter_email = Column(String(255))
    phone_number = Column(String(50))
    job_description = Column(Text)
    job_link = Column(String(2000), nullable=False)
    salary_or_rate = Column(String(255))
    location = Column(String(500))
    is_remote = Column(Boolean, default=True)
    contract_type = Column(String(100))
    date_posted = Column(DateTime(timezone=True))
    date_discovered = Column(DateTime(timezone=True), default=datetime.utcnow)
    raw_data = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    analysis = relationship("JobAnalysis", back_populates="job", uselist=False)
    applications = relationship("JobApplication", back_populates="job")


class JobAnalysis(Base):
    __tablename__ = "job_analyses"
    __table_args__ = (
        Index("idx_job_analyses_match_score", "match_score"),
        Index("idx_job_analyses_job_id", "job_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    technologies = Column(ARRAY(Text), default=[])
    seniority_level = Column(String(100))
    is_contract = Column(Boolean)
    is_remote_confirmed = Column(Boolean)
    has_recruiter = Column(Boolean)
    vendor_detected = Column(String(500))
    match_score = Column(Integer)
    score_breakdown = Column(JSONB)
    key_requirements = Column(ARRAY(Text))
    ai_summary = Column(Text)
    embedding_id = Column(String(255))
    # Multi-role fields
    role_category = Column(String(100))
    visa_sponsorship = Column(Boolean)
    experience_years_min = Column(Integer)
    experience_years_max = Column(Integer)
    matched_skills = Column(ARRAY(Text), default=[])
    missing_skills = Column(ARRAY(Text), default=[])
    match_reasons = Column(JSONB, default=[])
    analyzed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    llm_model = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    job = relationship("Job", back_populates="analysis")


# ─── Recruiter Contacts ─────────────────────────────────────────────────────


class RecruiterContact(Base):
    __tablename__ = "recruiter_contacts"
    __table_args__ = (
        Index("idx_recruiter_company", "company"),
        Index("idx_recruiter_email", "email"),
        Index("idx_recruiter_score", "intelligence_score"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    company = Column(String(500))
    linkedin_url = Column(String(500))
    source = Column(String(100))
    notes = Column(Text)
    last_contacted = Column(DateTime(timezone=True))
    # Recruiter Intelligence fields
    intelligence_score = Column(Integer, default=0)
    response_rate = Column(Numeric(5, 2), default=0)
    avg_response_time_hours = Column(Numeric(10, 2))
    total_interactions = Column(Integer, default=0)
    successful_placements = Column(Integer, default=0)
    specializations = Column(ARRAY(Text), default=[])
    last_response_at = Column(DateTime(timezone=True))
    ranking_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ─── Generated Resumes ──────────────────────────────────────────────────────


class GeneratedResume(Base):
    __tablename__ = "generated_resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"))
    resume_content = Column(Text, nullable=False)
    cover_letter = Column(Text)
    outreach_email = Column(Text)
    format = Column(String(50), default="markdown")
    file_url = Column(String(2000))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
    job = relationship("Job")


# ─── Job Applications ───────────────────────────────────────────────────────


class JobApplication(Base):
    __tablename__ = "job_applications"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_application_user_job"),
        Index("idx_application_status", "status"),
        Index("idx_application_user_status", "user_id", "status"),
        Index("idx_application_applied_at", "applied_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("generated_resumes.id", ondelete="SET NULL"))
    status = Column(String(50), default="pending")
    applied_via = Column(String(100))
    applied_at = Column(DateTime(timezone=True))
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("GeneratedResume")


# ─── Notifications ───────────────────────────────────────────────────────────


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notification_user", "user_id"),
        Index("idx_notification_status", "status"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(50), nullable=False)
    subject = Column(String(500))
    body = Column(Text, nullable=False)
    job_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    status = Column(String(50), default="pending")
    sent_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")


# ─── Crawl Logs ──────────────────────────────────────────────────────────────


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    jobs_found = Column(Integer, default=0)
    jobs_new = Column(Integer, default=0)
    status = Column(String(50), default="running")
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ─── Companies ───────────────────────────────────────────────────────────────


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False)
    domain = Column(String(500))
    industry = Column(String(255))
    size_range = Column(String(100))
    headquarters = Column(String(500))
    careers_url = Column(String(2000))
    linkedin_url = Column(String(2000))
    github_org = Column(String(500))
    tech_stack = Column(ARRAY(Text), default=[])
    is_actively_hiring = Column(Boolean, default=False)
    hiring_velocity = Column(Integer, default=0)
    last_crawled_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    signals = relationship("HiringSignal", back_populates="company")


# ─── Hiring Signals ─────────────────────────────────────────────────────────


class HiringSignal(Base):
    __tablename__ = "hiring_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    signal_type = Column(String(100), nullable=False)
    title = Column(String(1000), nullable=False)
    description = Column(Text)
    source_url = Column(String(2000))
    source_name = Column(String(255))
    confidence = Column(Numeric(3, 2))
    predicted_roles = Column(ARRAY(Text), default=[])
    raw_data = Column(JSONB)
    detected_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    company = relationship("Company", back_populates="signals")


# ─── Crawler Sources ────────────────────────────────────────────────────────


class CrawlerSource(Base):
    __tablename__ = "crawler_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    source_type = Column(String(100), nullable=False)
    url_pattern = Column(String(2000), nullable=False)
    crawl_frequency_minutes = Column(Integer, default=60)
    priority = Column(Integer, default=5)
    is_enabled = Column(Boolean, default=True)
    requires_js = Column(Boolean, default=False)
    anti_bot_level = Column(String(50), default="low")
    last_crawled_at = Column(DateTime(timezone=True))
    success_rate = Column(Numeric(5, 2), default=100.0)
    config = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ─── Crawl Queue ────────────────────────────────────────────────────────────


class CrawlQueueItem(Base):
    __tablename__ = "crawl_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("crawler_sources.id", ondelete="CASCADE"))
    url = Column(String(2000), nullable=False)
    priority = Column(Integer, default=5)
    status = Column(String(50), default="pending")
    worker_id = Column(String(255))
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    scheduled_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    result_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    source = relationship("CrawlerSource")


# ─── Outreach Campaigns ─────────────────────────────────────────────────────


class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("recruiter_contacts.id", ondelete="SET NULL"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"))
    campaign_type = Column(String(100), nullable=False)
    subject = Column(String(500))
    body = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False)
    status = Column(String(50), default="draft")
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    replied_at = Column(DateTime(timezone=True))
    follow_up_count = Column(Integer, default=0)
    max_follow_ups = Column(Integer, default=3)
    next_follow_up = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    recruiter = relationship("RecruiterContact")
    company = relationship("Company")
    job = relationship("Job")


# ─── Pipeline Events ────────────────────────────────────────────────────────


class PipelineEvent(Base):
    __tablename__ = "pipeline_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    source_service = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ─── Decision Log ───────────────────────────────────────────────────────────


class DecisionLog(Base):
    __tablename__ = "decision_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"))
    decision_type = Column(String(100), nullable=False)
    decision = Column(String(50), nullable=False)
    reason = Column(Text)
    score_data = Column(JSONB)
    executed = Column(Boolean, default=False)
    executed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")
    job = relationship("Job")


# ─── Hiring Predictions ─────────────────────────────────────────────────────
class HiringPrediction(Base):
    __tablename__ = "hiring_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    predicted_roles = Column(ARRAY(Text), default=[])
    probability = Column(Numeric(5, 4))
    timeframe_days = Column(Integer)
    signals_used = Column(JSONB, default=[])
    prediction_model = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    company = relationship("Company")


# ─── LinkedIn Outreach ───────────────────────────────────────────────────────
class LinkedInOutreach(Base):
    __tablename__ = "linkedin_outreach"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("recruiter_contacts.id", ondelete="SET NULL"))
    profile_url = Column(String(2000), nullable=False)
    person_name = Column(String(500))
    person_title = Column(String(500))
    company_name = Column(String(500))
    action_type = Column(String(50), nullable=False)  # connect, message, follow_up
    message_text = Column(Text)
    status = Column(String(50), default="pending")  # pending, sent, accepted, replied, failed
    sent_at = Column(DateTime(timezone=True))
    replied_at = Column(DateTime(timezone=True))
    follow_up_count = Column(Integer, default=0)
    next_follow_up = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    recruiter = relationship("RecruiterContact")


# ─── Voice Calls (Twilio) ───────────────────────────────────────────────────
class VoiceCall(Base):
    __tablename__ = "voice_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("recruiter_contacts.id", ondelete="SET NULL"))
    phone_number = Column(String(50), nullable=False)
    call_sid = Column(String(255))
    direction = Column(String(20), default="outbound")
    status = Column(String(50), default="queued")  # queued, ringing, in-progress, completed, failed
    duration_seconds = Column(Integer)
    transcript = Column(Text)
    ai_script = Column(Text)
    outcome = Column(String(100))  # interested, not_interested, voicemail, no_answer
    resume_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    recruiter = relationship("RecruiterContact")


# ─── Interview Prep ──────────────────────────────────────────────────────────
class InterviewPrep(Base):
    __tablename__ = "interview_preps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"))
    company_name = Column(String(500))
    role_title = Column(String(500))
    questions = Column(JSONB, default=[])
    answers = Column(JSONB, default=[])
    behavioral_stories = Column(JSONB, default=[])
    technical_topics = Column(ARRAY(Text), default=[])
    company_research = Column(JSONB, default={})
    difficulty_level = Column(String(50), default="senior")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")
    job = relationship("Job")


# ─── Salary Negotiations ────────────────────────────────────────────────────
class NegotiationStrategy(Base):
    __tablename__ = "negotiation_strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"))
    company_name = Column(String(500))
    role_title = Column(String(500))
    offered_rate = Column(Numeric(10, 2))
    target_rate = Column(Numeric(10, 2))
    market_rate_low = Column(Numeric(10, 2))
    market_rate_mid = Column(Numeric(10, 2))
    market_rate_high = Column(Numeric(10, 2))
    strategy = Column(JSONB, default={})
    counter_offer_script = Column(Text)
    negotiation_points = Column(JSONB, default=[])
    status = Column(String(50), default="draft")  # draft, sent, accepted, rejected, countered
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")
    job = relationship("Job")


# ─── Freelance Bids ─────────────────────────────────────────────────────────
class FreelanceBid(Base):
    __tablename__ = "freelance_bids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(100), nullable=False)  # upwork, freelancer, toptal, fiverr
    project_url = Column(String(2000))
    project_title = Column(String(1000))
    client_name = Column(String(500))
    budget_range = Column(String(255))
    proposal_text = Column(Text)
    bid_amount = Column(Numeric(10, 2))
    estimated_hours = Column(Integer)
    status = Column(String(50), default="pending")  # pending, submitted, viewed, shortlisted, awarded, rejected
    submitted_at = Column(DateTime(timezone=True))
    response_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


# ─── Content Posts (Demand Generation) ───────────────────────────────────────
class ContentPost(Base):
    __tablename__ = "content_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(100), nullable=False)  # linkedin, twitter, dev.to, medium
    post_type = Column(String(50), nullable=False)  # article, short_post, comment, thread
    title = Column(String(1000))
    content = Column(Text, nullable=False)
    hashtags = Column(ARRAY(Text), default=[])
    topic = Column(String(255))
    status = Column(String(50), default="draft")  # draft, scheduled, published, failed
    scheduled_at = Column(DateTime(timezone=True))
    published_at = Column(DateTime(timezone=True))
    external_url = Column(String(2000))
    engagement_metrics = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


# ─── Subscriptions & Billing ─────────────────────────────────────────────────
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan = Column(String(50), nullable=False, default="free")  # free, starter, pro, enterprise
    status = Column(String(50), default="active")  # active, canceled, past_due, trialing
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    cancel_at_period_end = Column(Boolean, default=False)
    monthly_applications_limit = Column(Integer, default=10)
    monthly_applications_used = Column(Integer, default=0)
    features = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(100), nullable=False)
    credits_used = Column(Integer, default=1)
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")


# ─── Agent Orchestrator ──────────────────────────────────────────────────────
class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_type = Column(String(100), nullable=False)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), default="queued")
    priority = Column(Integer, default=5)
    input_data = Column(JSONB, default={})
    output_data = Column(JSONB, default={})
    error_message = Column(Text)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("agent_tasks.id", ondelete="SET NULL"))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")
    parent = relationship("AgentTask", remote_side="AgentTask.id")


class AgentWorkflow(Base):
    __tablename__ = "agent_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    steps = Column(JSONB, default=[])
    trigger = Column(String(100), default="manual")
    schedule_cron = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True))
    run_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


# ─── Job Marketplace ─────────────────────────────────────────────────────────
class RecruiterProfile(Base):
    __tablename__ = "recruiter_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    company_name = Column(String(500), nullable=False)
    company_website = Column(String(2000))
    industry = Column(String(255))
    plan = Column(String(50), default="basic")
    verified = Column(Boolean, default=False)
    jobs_posted = Column(Integer, default=0)
    total_hires = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class MarketplaceJob(Base):
    __tablename__ = "marketplace_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    company_name = Column(String(500))
    location = Column(String(500))
    is_remote = Column(Boolean, default=True)
    contract_type = Column(String(100))
    salary_min = Column(Numeric(10, 2))
    salary_max = Column(Numeric(10, 2))
    required_skills = Column(ARRAY(Text), default=[])
    experience_level = Column(String(100))
    status = Column(String(50), default="active")
    views_count = Column(Integer, default=0)
    applications_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    recruiter = relationship("RecruiterProfile")
    candidates = relationship("CandidateMatch", back_populates="job")


class CandidateMatch(Base):
    __tablename__ = "candidate_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_jobs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_score = Column(Numeric(5, 2))
    match_reasons = Column(JSONB, default=[])
    status = Column(String(50), default="matched")
    recruiter_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("MarketplaceJob", back_populates="candidates")
    user = relationship("User")


# ─── Saved Searches ──────────────────────────────────────────────────────────

class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    search_params = Column(JSONB, nullable=False)  # stores all filter state
    role_categories = Column(ARRAY(Text), default=[])
    skills_filter = Column(ARRAY(Text), default=[])
    is_active = Column(Boolean, default=True)
    notify_on_match = Column(Boolean, default=True)
    min_score_threshold = Column(Integer, default=70)
    last_run_at = Column(DateTime(timezone=True))
    match_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


# ─── Audit Log ───────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    details = Column(JSONB, default={})
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")
