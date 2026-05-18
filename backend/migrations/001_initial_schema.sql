-- Building10X SEO Portal — initial schema (Section 4 of the build doc).
--
-- Apply directly to Supabase: paste into the Supabase SQL editor, or run
--   psql "$DATABASE_URL" -f backend/migrations/001_initial_schema.sql
-- Alembic carries the same schema as revision 0001 (backend/alembic/versions).
--
-- gen_random_uuid() is built into PostgreSQL 13+ (Supabase runs 15+),
-- so no pgcrypto/uuid-ossp extension is required.

-- 4.1 sites ---------------------------------------------------------------
CREATE TABLE sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL UNIQUE,
    url VARCHAR(500) NOT NULL,
    site_type VARCHAR(50) NOT NULL DEFAULT 'other',
    schedule VARCHAR(50) NOT NULL DEFAULT 'weekly',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    max_pages INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_audit_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

-- 4.2 audits --------------------------------------------------------------
CREATE TABLE audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    triggered_by VARCHAR(50) NOT NULL DEFAULT 'manual',
    score_overall INTEGER,
    score_technical INTEGER,
    score_content INTEGER,
    score_eeeat INTEGER,
    score_performance INTEGER,
    score_structure INTEGER,
    pages_crawled INTEGER DEFAULT 0,
    issues_critical INTEGER DEFAULT 0,
    issues_warning INTEGER DEFAULT 0,
    issues_info INTEGER DEFAULT 0,
    crawl_data JSONB DEFAULT '[]',
    gsc_data JSONB DEFAULT '{}',
    analysis_summary TEXT,
    quick_wins JSONB DEFAULT '[]',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    error_message TEXT
);

-- 4.3 audit_issues --------------------------------------------------------
CREATE TABLE audit_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
    page_url VARCHAR(1000),
    category VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    rule_id VARCHAR(100) NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    fix_suggestion TEXT NOT NULL,
    affected_value TEXT,
    expected_value TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_issues_audit_id ON audit_issues(audit_id);
CREATE INDEX idx_audit_issues_severity ON audit_issues(severity);
CREATE INDEX idx_audit_issues_category ON audit_issues(category);

-- 4.4 api_tokens ----------------------------------------------------------
CREATE TABLE api_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    token_prefix VARCHAR(10) NOT NULL,
    scopes JSONB NOT NULL DEFAULT '["audit:read","audit:write","site:read"]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4.5 webhooks ------------------------------------------------------------
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    events JSONB NOT NULL DEFAULT '["audit.complete","audit.failed"]',
    secret VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
