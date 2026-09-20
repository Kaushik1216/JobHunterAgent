-- Add portal provenance for multi-board search results
ALTER TABLE jobs ADD COLUMN source_portal TEXT NOT NULL DEFAULT 'unknown';
CREATE INDEX IF NOT EXISTS idx_jobs_source_portal ON jobs(source_portal);
