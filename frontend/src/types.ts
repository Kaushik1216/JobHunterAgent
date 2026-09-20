export type JobStatus = "DISCOVERED" | "NEW" | "APPLIED" | "SKIPPED" | "ARCHIVED";
export type RunMode = "search" | "search_and_match" | "match";

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  extracted_min_yoe: number | null;
  extracted_max_yoe: number | null;
  yoe_match: boolean;
  matched_skills: string[];
  missing_skills: string[];
  fit_score: number;
  summary_reason: string;
  apply_url: string;
  source_query: string;
  source_portal: string;
  raw_snippet: string;
  status: JobStatus;
  evaluated: boolean;
  search_title: string;
  target_yoe: number | null;
  core_skills: string[];
  apply_label: string;
  posted_days_ago: number | null;
}

export interface Stats {
  total: number;
  unevaluated: number;
  evaluated: number;
  DISCOVERED?: number;
  NEW?: number;
  APPLIED?: number;
  SKIPPED?: number;
  ARCHIVED?: number;
}

export interface FilterOptions {
  companies: string[];
  portals: string[];
  locations: string[];
  statuses: string[];
}

export interface Meta {
  fit_score_threshold: number;
  search_max_results: number;
  enabled_portals: string[];
  all_portals: { id: string; name: string }[];
}

export interface RunSummary {
  run_id: string;
  jobs_found: number;
  jobs_qualified: number;
  jobs_skipped_dedup: number;
  jobs_skipped_low_score: number;
  jobs_errored: number;
  jobs_discovered: number;
  mode: string;
  duration_seconds?: number;
}

export interface RunState {
  status: "idle" | "running" | "completed" | "failed";
  mode: string | null;
  message: string;
  error: string | null;
  summary: RunSummary | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface JobQuery {
  company: string[];
  portal: string[];
  max_days: number | "";
  location: string[];
  minFit: number;
  evaluated: "true" | "false" | "";
  yoeMatch: "true" | "false" | "";
  q: string;
  sort: string;
}


export interface Settings {
  search_portals: string[];
  companies: string[];
  ttl_days: number | null;
  search_max_days: number;
}
