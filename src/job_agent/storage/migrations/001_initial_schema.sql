-- Initial schema for jobs_vault.db
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,                  -- SHA-256 of normalized URL
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT NOT NULL,
    apply_url TEXT NOT NULL UNIQUE,
    extracted_min_yoe INTEGER,
    extracted_max_yoe INTEGER,
    yoe_match BOOLEAN NOT NULL,
    fit_score REAL NOT NULL,
    matched_skills TEXT NOT NULL,         -- JSON array
    missing_skills TEXT NOT NULL,         -- JSON array
    summary_reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'NEW',
    source_query TEXT DEFAULT '',
    raw_snippet TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_fit_score ON jobs(fit_score DESC);

-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
