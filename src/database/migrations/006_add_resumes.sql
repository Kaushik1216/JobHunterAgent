-- Migration 006: Add resumes table for AI-extracted candidate profiles
CREATE TABLE IF NOT EXISTS resumes (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    parsed_profile TEXT,
    candidate_name TEXT,
    headline TEXT,
    email TEXT,
    total_yoe REAL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_resumes_is_active ON resumes(is_active);
CREATE INDEX IF NOT EXISTS idx_resumes_created_at ON resumes(created_at);
