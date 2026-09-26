-- Track search-only listings and the criteria used for later matching
ALTER TABLE jobs ADD COLUMN evaluated INTEGER NOT NULL DEFAULT 1;
ALTER TABLE jobs ADD COLUMN search_title TEXT NOT NULL DEFAULT '';
ALTER TABLE jobs ADD COLUMN target_yoe INTEGER;
ALTER TABLE jobs ADD COLUMN core_skills TEXT NOT NULL DEFAULT '[]';
CREATE INDEX IF NOT EXISTS idx_jobs_evaluated ON jobs(evaluated);
