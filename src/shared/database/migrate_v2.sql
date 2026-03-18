-- Migration: Add multi-role support, saved searches, audit logs

-- Add new columns to user_profiles
DO $$ BEGIN
  ALTER TABLE user_profiles ADD COLUMN preferred_roles TEXT[] DEFAULT '{}';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE user_profiles ADD COLUMN preferred_locations TEXT[] DEFAULT '{Remote,USA}';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE user_profiles ADD COLUMN visa_required BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE user_profiles ADD COLUMN min_company_size VARCHAR(50);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

-- Add role_category to job_analyses
DO $$ BEGIN
  ALTER TABLE job_analyses ADD COLUMN role_category VARCHAR(100);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

-- Create saved_searches table
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

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_saved_searches_user ON saved_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);
