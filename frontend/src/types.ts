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
  status: string[];
  max_days: number | "";
  location: string[];
  minFit: number;
  evaluated: "true" | "false" | "";
  yoeMatch: "true" | "false" | "";
  q: string;
  sort: string;
}


export interface AvailableCompany {
  name: string;
  enabled: boolean;
  job_count: number;
}

export interface Settings {
  search_portals: string[];
  companies: string[];
  available_companies?: AvailableCompany[];
  ttl_days: number | null;
  search_max_days: number;
  llm_provider?: string;
  llm_base_url?: string;
  llm_model?: string;
  llm_api_key?: string;
}

export interface TestModelPayload {
  base_url: string;
  model: string;
  api_key?: string;
  provider?: string;
}

export interface TestModelResponse {
  success: boolean;
  message: string;
  latency_ms?: number;
  model?: string;
  error?: string;
}

export interface WorkExperienceItem {
  company: string;
  role: string;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  technologies?: string[];
  achievements?: string[];
  description?: string;
}

export interface ProjectItem {
  title: string;
  role?: string | null;
  technologies?: string[];
  description?: string;
  highlights?: string[];
  link?: string | null;
}

export interface EducationItem {
  institution: string;
  degree: string;
  field_of_study?: string | null;
  graduation_year?: string | null;
  grade?: string | null;
}

export interface CategorizedSkills {
  languages?: string[];
  frameworks_and_libraries?: string[];
  databases?: string[];
  cloud_and_devops?: string[];
  tools_and_platforms?: string[];
  core_competencies?: string[];
  all_skills?: string[];
}

export interface ParsedResumeProfile {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  headline?: string | null;
  summary?: string | null;
  total_experience_years?: number | null;
  skills?: CategorizedSkills;
  work_experience?: WorkExperienceItem[];
  projects?: ProjectItem[];
  education?: EducationItem[];
  certifications?: string[];
  target_roles?: string[];
  domains_and_industries?: string[];
  key_strengths?: string[];
}

export interface ResumeRecord {
  id: string;
  filename: string;
  file_path: string;
  file_type: string;
  raw_text: string;
  parsed_profile?: ParsedResumeProfile | null;
  candidate_name?: string | null;
  headline?: string | null;
  email?: string | null;
  total_yoe?: number | null;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}


