-- ============================================================
-- Autonomous Career Intelligence Engine — PostgreSQL Schema
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    full_name       VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(512) NOT NULL,
    phone           VARCHAR(50),
    telegram_chat_id VARCHAR(100),
    whatsapp_number VARCHAR(50),
    notification_preferences JSONB DEFAULT '{"email": true, "telegram": false, "whatsapp": false, "push": true}'::jsonb,
    auto_apply_enabled BOOLEAN DEFAULT FALSE,
    auto_outreach_enabled BOOLEAN DEFAULT FALSE,
    max_daily_applications INTEGER DEFAULT 10,
    min_score_auto_apply INTEGER DEFAULT 75,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- USER PROFILES (skills, preferences)
-- ============================================================
CREATE TABLE user_profiles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    headline        VARCHAR(500),
    summary         TEXT,
    skills          TEXT[] DEFAULT '{}',
    experience_years INTEGER DEFAULT 0,
    preferred_rate_min DECIMAL(10,2),
    preferred_rate_max DECIMAL(10,2),
    preferred_contract_types TEXT[] DEFAULT '{Contract,Freelance}',
    preferred_technologies TEXT[] DEFAULT '{}',
    preferred_roles TEXT[] DEFAULT '{}',
    preferred_locations TEXT[] DEFAULT '{Remote,USA}',
    visa_required   BOOLEAN DEFAULT FALSE,
    min_company_size VARCHAR(50),
    resume_base     TEXT,
    linkedin_url    VARCHAR(500),
    github_url      VARCHAR(500),
    portfolio_url   VARCHAR(500),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- JOBS
-- ============================================================
CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id     VARCHAR(500),
    source          VARCHAR(100) NOT NULL,  -- linkedin, indeed, dice, etc.
    job_title       VARCHAR(500) NOT NULL,
    company_name    VARCHAR(500),
    vendor_name     VARCHAR(500),
    recruiter_name  VARCHAR(500),
    recruiter_email VARCHAR(255),
    phone_number    VARCHAR(50),
    job_description TEXT,
    job_link        VARCHAR(2000) NOT NULL,
    salary_or_rate  VARCHAR(255),
    location        VARCHAR(500),
    is_remote       BOOLEAN DEFAULT TRUE,
    contract_type   VARCHAR(100),  -- contract, full-time, freelance
    date_posted     TIMESTAMPTZ,
    date_discovered TIMESTAMPTZ DEFAULT NOW(),
    raw_data        JSONB,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_jobs_date_discovered ON jobs(date_discovered DESC);
CREATE INDEX idx_jobs_is_remote ON jobs(is_remote);
CREATE INDEX idx_jobs_contract_type ON jobs(contract_type);
CREATE INDEX idx_jobs_title_trgm ON jobs USING gin(job_title gin_trgm_ops);
CREATE UNIQUE INDEX idx_jobs_external_source ON jobs(external_id, source) WHERE external_id IS NOT NULL;

-- ============================================================
-- JOB ANALYSIS (AI-generated)
-- ============================================================
CREATE TABLE job_analyses (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id              UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    technologies        TEXT[] DEFAULT '{}',
    seniority_level     VARCHAR(100),
    is_contract         BOOLEAN,
    is_remote_confirmed BOOLEAN,
    has_recruiter       BOOLEAN,
    vendor_detected     VARCHAR(500),
    match_score         INTEGER CHECK (match_score >= 0 AND match_score <= 100),
    score_breakdown     JSONB,
    key_requirements    TEXT[],
    ai_summary          TEXT,
    role_category       VARCHAR(100),
    embedding_id        VARCHAR(255),  -- reference to vector DB
    analyzed_at         TIMESTAMPTZ DEFAULT NOW(),
    llm_model           VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id)
);

CREATE INDEX idx_job_analyses_score ON job_analyses(match_score DESC);

-- ============================================================
-- RECRUITER CONTACTS
-- ============================================================
CREATE TABLE recruiter_contacts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(500) NOT NULL,
    email           VARCHAR(255),
    phone           VARCHAR(50),
    company         VARCHAR(500),
    linkedin_url    VARCHAR(500),
    source          VARCHAR(100),
    notes           TEXT,
    last_contacted  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_recruiter_email ON recruiter_contacts(email) WHERE email IS NOT NULL;

-- ============================================================
-- GENERATED RESUMES
-- ============================================================
CREATE TABLE generated_resumes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id          UUID REFERENCES jobs(id) ON DELETE SET NULL,
    resume_content  TEXT NOT NULL,
    cover_letter    TEXT,
    outreach_email  TEXT,
    format          VARCHAR(50) DEFAULT 'markdown',  -- markdown, pdf, docx
    file_url        VARCHAR(2000),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_resumes_user ON generated_resumes(user_id);

-- ============================================================
-- JOB APPLICATIONS
-- ============================================================
CREATE TABLE job_applications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    resume_id       UUID REFERENCES generated_resumes(id) ON DELETE SET NULL,
    status          VARCHAR(50) DEFAULT 'pending',  -- pending, applied, rejected, interview, offer
    applied_via     VARCHAR(100),  -- email, form, recruiter_outreach
    applied_at      TIMESTAMPTZ,
    response_received BOOLEAN DEFAULT FALSE,
    response_date   TIMESTAMPTZ,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, job_id)
);

CREATE INDEX idx_applications_user ON job_applications(user_id);
CREATE INDEX idx_applications_status ON job_applications(status);

-- ============================================================
-- NOTIFICATIONS LOG
-- ============================================================
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel         VARCHAR(50) NOT NULL,  -- email, telegram, whatsapp, push
    subject         VARCHAR(500),
    body            TEXT NOT NULL,
    job_ids         UUID[] DEFAULT '{}',
    status          VARCHAR(50) DEFAULT 'pending',  -- pending, sent, failed
    sent_at         TIMESTAMPTZ,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);

-- ============================================================
-- CRAWL LOGS
-- ============================================================
CREATE TABLE crawl_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source          VARCHAR(100) NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ,
    jobs_found      INTEGER DEFAULT 0,
    jobs_new        INTEGER DEFAULT 0,
    status          VARCHAR(50) DEFAULT 'running',  -- running, completed, failed
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SCHEDULED TASKS
-- ============================================================
CREATE TABLE scheduled_tasks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_name       VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(100) NOT NULL,
    last_run        TIMESTAMPTZ,
    next_run        TIMESTAMPTZ,
    is_enabled      BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- COMPANIES (Knowledge Graph — relational mirror)
-- ============================================================
CREATE TABLE companies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(500) NOT NULL,
    domain          VARCHAR(500),
    industry        VARCHAR(255),
    size_range      VARCHAR(100),
    headquarters    VARCHAR(500),
    careers_url     VARCHAR(2000),
    linkedin_url    VARCHAR(2000),
    github_org      VARCHAR(500),
    tech_stack      TEXT[] DEFAULT '{}',
    is_actively_hiring BOOLEAN DEFAULT FALSE,
    hiring_velocity INTEGER DEFAULT 0,
    last_crawled_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_companies_domain ON companies(domain) WHERE domain IS NOT NULL;
CREATE INDEX idx_companies_name_trgm ON companies USING gin(name gin_trgm_ops);

-- ============================================================
-- HIRING SIGNALS (Predictive Intelligence)
-- ============================================================
CREATE TABLE hiring_signals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES companies(id) ON DELETE SET NULL,
    signal_type     VARCHAR(100) NOT NULL,
    -- funding_round, product_launch, team_expansion, blog_post,
    -- job_removal, exec_hire, acquisition, ipo_filing
    title           VARCHAR(1000) NOT NULL,
    description     TEXT,
    source_url      VARCHAR(2000),
    source_name     VARCHAR(255),
    confidence      DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    predicted_roles TEXT[] DEFAULT '{}',
    raw_data        JSONB,
    detected_at     TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_signals_company ON hiring_signals(company_id);
CREATE INDEX idx_signals_type ON hiring_signals(signal_type);
CREATE INDEX idx_signals_detected ON hiring_signals(detected_at DESC);

-- ============================================================
-- CRAWLER SOURCES (Distributed Crawl Config)
-- ============================================================
CREATE TABLE crawler_sources (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL UNIQUE,
    source_type     VARCHAR(100) NOT NULL,
    -- job_board, company_career, github, reddit, news, blog
    url_pattern     VARCHAR(2000) NOT NULL,
    crawl_frequency_minutes INTEGER DEFAULT 60,
    priority        INTEGER DEFAULT 5,
    is_enabled      BOOLEAN DEFAULT TRUE,
    requires_js     BOOLEAN DEFAULT FALSE,
    anti_bot_level  VARCHAR(50) DEFAULT 'low',
    last_crawled_at TIMESTAMPTZ,
    success_rate    DECIMAL(5,2) DEFAULT 100.0,
    config          JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CRAWL QUEUE (Distributed Task Tracking)
-- ============================================================
CREATE TABLE crawl_queue (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id       UUID REFERENCES crawler_sources(id) ON DELETE CASCADE,
    url             VARCHAR(2000) NOT NULL,
    priority        INTEGER DEFAULT 5,
    status          VARCHAR(50) DEFAULT 'pending',
    -- pending, running, completed, failed, retrying
    worker_id       VARCHAR(255),
    attempts        INTEGER DEFAULT 0,
    max_attempts    INTEGER DEFAULT 3,
    scheduled_at    TIMESTAMPTZ DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT,
    result_data     JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_crawl_queue_status ON crawl_queue(status, priority DESC, scheduled_at);
CREATE INDEX idx_crawl_queue_worker ON crawl_queue(worker_id) WHERE worker_id IS NOT NULL;

-- ============================================================
-- OUTREACH CAMPAIGNS (Autonomous Outreach)
-- ============================================================
CREATE TABLE outreach_campaigns (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recruiter_id    UUID REFERENCES recruiter_contacts(id) ON DELETE SET NULL,
    company_id      UUID REFERENCES companies(id) ON DELETE SET NULL,
    job_id          UUID REFERENCES jobs(id) ON DELETE SET NULL,
    campaign_type   VARCHAR(100) NOT NULL,
    -- cold_outreach, follow_up, thank_you, network_intro
    subject         VARCHAR(500),
    body            TEXT NOT NULL,
    channel         VARCHAR(50) NOT NULL,  -- email, linkedin, telegram
    status          VARCHAR(50) DEFAULT 'draft',
    -- draft, scheduled, sent, replied, no_reply, bounced
    scheduled_at    TIMESTAMPTZ,
    sent_at         TIMESTAMPTZ,
    replied_at      TIMESTAMPTZ,
    follow_up_count INTEGER DEFAULT 0,
    max_follow_ups  INTEGER DEFAULT 3,
    next_follow_up  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_outreach_user ON outreach_campaigns(user_id);
CREATE INDEX idx_outreach_status ON outreach_campaigns(status);
CREATE INDEX idx_outreach_scheduled ON outreach_campaigns(scheduled_at) WHERE status = 'scheduled';
CREATE INDEX idx_outreach_followup ON outreach_campaigns(next_follow_up) WHERE status = 'sent' AND follow_up_count < max_follow_ups;

-- ============================================================
-- PIPELINE EVENTS (Streaming Event Log)
-- ============================================================
CREATE TABLE pipeline_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type      VARCHAR(100) NOT NULL,
    source_service  VARCHAR(100) NOT NULL,
    payload         JSONB NOT NULL,
    processed       BOOLEAN DEFAULT FALSE,
    processed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pipeline_events_type ON pipeline_events(event_type);
CREATE INDEX idx_pipeline_events_unprocessed ON pipeline_events(created_at) WHERE processed = FALSE;

-- ============================================================
-- DECISION LOG (Audit Trail)
-- ============================================================
CREATE TABLE decision_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id          UUID REFERENCES jobs(id) ON DELETE SET NULL,
    decision_type   VARCHAR(100) NOT NULL,
    -- auto_apply, skip, outreach, wait, follow_up
    decision        VARCHAR(50) NOT NULL,  -- approved, rejected, deferred
    reason          TEXT,
    score_data      JSONB,
    executed        BOOLEAN DEFAULT FALSE,
    executed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_decision_log_user ON decision_log(user_id);
CREATE INDEX idx_decision_log_job ON decision_log(job_id);

-- ============================================================
-- SAVED SEARCHES (Multi-Role Search Profiles)
-- ============================================================
CREATE TABLE saved_searches (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    search_params       JSONB NOT NULL,
    role_categories     TEXT[] DEFAULT '{}',
    skills_filter       TEXT[] DEFAULT '{}',
    is_active           BOOLEAN DEFAULT TRUE,
    notify_on_match     BOOLEAN DEFAULT TRUE,
    min_score_threshold INTEGER DEFAULT 70,
    last_run_at         TIMESTAMPTZ,
    match_count         INTEGER DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_saved_searches_user ON saved_searches(user_id);
CREATE INDEX idx_saved_searches_active ON saved_searches(is_active) WHERE is_active = TRUE;

-- ============================================================
-- AUDIT LOGS (Security & Compliance)
-- ============================================================
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(100),
    resource_id     VARCHAR(255),
    details         JSONB DEFAULT '{}',
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(500),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
