-- ============================================================
-- Migration: Global Multi-Role Platform Upgrade
-- Adds: saved_searches, audit_logs, new user_profile columns
-- ============================================================

-- Add new columns to user_profiles
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS preferred_roles TEXT[] DEFAULT '{}';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS preferred_locations TEXT[] DEFAULT '{Remote,USA}';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS visa_required BOOLEAN DEFAULT FALSE;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS min_company_size VARCHAR(50);

-- Update default for preferred_technologies (remove .NET-only default)
ALTER TABLE user_profiles ALTER COLUMN preferred_technologies SET DEFAULT '{}';

-- ============================================================
-- SAVED SEARCHES
-- ============================================================
CREATE TABLE IF NOT EXISTS saved_searches (
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

CREATE INDEX IF NOT EXISTS idx_saved_searches_user ON saved_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_searches_active ON saved_searches(is_active) WHERE is_active = TRUE;

-- ============================================================
-- AUDIT LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(100),
    resource_id     VARCHAR(255),
    details         JSONB DEFAULT '{}'::jsonb,
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(500),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

-- ============================================================
-- Add role_category to job_analyses for multi-role filtering
-- ============================================================
ALTER TABLE job_analyses ADD COLUMN IF NOT EXISTS role_category VARCHAR(100);
ALTER TABLE job_analyses ADD COLUMN IF NOT EXISTS visa_sponsorship BOOLEAN;
ALTER TABLE job_analyses ADD COLUMN IF NOT EXISTS experience_years_min INTEGER;
ALTER TABLE job_analyses ADD COLUMN IF NOT EXISTS experience_years_max INTEGER;
ALTER TABLE job_analyses ADD COLUMN IF NOT EXISTS matched_skills TEXT[] DEFAULT '{}';
ALTER TABLE job_analyses ADD COLUMN IF NOT EXISTS missing_skills TEXT[] DEFAULT '{}';
ALTER TABLE job_analyses ADD COLUMN IF NOT EXISTS match_reasons JSONB DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_job_analyses_role ON job_analyses(role_category);

-- ============================================================
-- Add intelligence_score fields to recruiter_contacts if missing
-- ============================================================
ALTER TABLE recruiter_contacts ADD COLUMN IF NOT EXISTS intelligence_score INTEGER DEFAULT 0;
ALTER TABLE recruiter_contacts ADD COLUMN IF NOT EXISTS response_rate DECIMAL(5,2) DEFAULT 0;
ALTER TABLE recruiter_contacts ADD COLUMN IF NOT EXISTS avg_response_time_hours DECIMAL(10,2);
ALTER TABLE recruiter_contacts ADD COLUMN IF NOT EXISTS total_interactions INTEGER DEFAULT 0;
ALTER TABLE recruiter_contacts ADD COLUMN IF NOT EXISTS successful_placements INTEGER DEFAULT 0;
ALTER TABLE recruiter_contacts ADD COLUMN IF NOT EXISTS specializations TEXT[] DEFAULT '{}';
ALTER TABLE recruiter_contacts ADD COLUMN IF NOT EXISTS last_response_at TIMESTAMPTZ;
ALTER TABLE recruiter_contacts ADD COLUMN IF NOT EXISTS ranking_data JSONB DEFAULT '{}'::jsonb;
