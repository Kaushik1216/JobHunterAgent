import type { FilterOptions, Job, JobQuery, JobStatus, Meta, RunMode, RunState, Stats } from "./types";

function params(query: JobQuery): string {
  const search = new URLSearchParams();
  query.company.forEach((value) => search.append("company", value));
  query.portal.forEach((value) => search.append("portal", value));
  if (query.max_days !== "") search.append("max_days", String(query.max_days));
  query.location.forEach((value) => search.append("location", value));
  search.set("min_fit", String(query.minFit));
  if (query.evaluated) search.set("evaluated", query.evaluated);
  if (query.yoeMatch) search.set("yoe_match", query.yoeMatch);
  if (query.q.trim()) search.set("q", query.q.trim());
  search.set("sort", query.sort);
  return search.toString();
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const api = {
  meta: () => request<Meta>("/api/meta"),
  stats: () => request<Stats>("/api/stats"),
  filters: () => request<FilterOptions>("/api/filters"),
  jobs: (query: JobQuery) => request<Job[]>(`/api/jobs?${params(query)}`),
  updateStatus: (id: string, status: JobStatus) =>
    request<Job>(`/api/jobs/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  runStatus: () => request<RunState>("/api/runs/current"),
  startRun: (mode: RunMode, extras?: { company?: string; title?: string; location?: string }) =>
    request<RunState>("/api/runs", {
      method: "POST",
      body: JSON.stringify({ mode, ...extras }),
    }),
  getSettings: () => request<any>("/api/settings"),
  updateSettings: (settings: any) => request<any>("/api/settings", {
    method: "POST",
    body: JSON.stringify(settings),
  }),
  deleteAllJobs: () => request<{deleted: number}>("/api/jobs", { method: "DELETE" }),
};
