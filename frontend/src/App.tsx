import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { FilterOptions, Job, JobQuery, JobStatus, Meta, RunState, Stats } from "./types";

import { Navbar } from "./components/Navbar";
import { RunBar } from "./components/RunBar";
import { FilterSidebar } from "./components/FilterSidebar";
import { JobCard } from "./components/JobCard";
import { JobDetailPanel } from "./components/JobDetailPanel";
import { SettingsModal } from "./components/SettingsModal";

const STATUSES: JobStatus[] = ["DISCOVERED", "NEW", "APPLIED", "SKIPPED", "ARCHIVED"];

const defaultQuery: JobQuery = {
  company: [], portal: [], max_days: "", location: [], minFit: 0,
  evaluated: "", yoeMatch: "", q: "", sort: "fit_score",
};

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [query, setQuery] = useState<JobQuery>(defaultQuery);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [run, setRun] = useState<RunState | null>(null);
  const [busy, setBusy] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const selected = useMemo(
    () => jobs.find((job) => job.id === selectedId) ?? jobs[0] ?? null,
    [jobs, selectedId],
  );

  const refresh = useCallback(async () => {
    const [nextStats, nextOptions, nextJobs, nextRun] = await Promise.all([
      api.stats(), api.filters(), api.jobs(query), api.runStatus(),
    ]);
    setStats(nextStats); setOptions(nextOptions); setJobs(nextJobs); setRun(nextRun);
    setSelectedId((current) => {
      if (current && nextJobs.some((job) => job.id === current)) return current;
      return nextJobs[0]?.id ?? null;
    });
  }, [query]);

  useEffect(() => { api.meta().then(setMeta); }, []);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (run?.status !== "running") return;
    const timer = window.setInterval(refresh, 2000);
    return () => window.clearInterval(timer);
  }, [run?.status, refresh]);

  async function start(mode: "search" | "search_and_match" | "match") {
    setBusy(true);
    try {
      const next = await api.startRun(mode);
      setRun(next);
    } finally {
      setBusy(false);
    }
  }

  async function onStatus(status: JobStatus) {
    if (!selected) return;
    const updated = await api.updateStatus(selected.id, status);
    setJobs((current) => current.map((job) => (job.id === updated.id ? updated : job)));
    await refresh();
  }

  const running = run?.status === "running" || busy;
  const unmatchedCount = stats?.unevaluated ?? 0;

  return (
    <>
      <Navbar running={running} unmatchedCount={unmatchedCount} onStart={start} onOpenSettings={() => setShowSettings(true)} />
      
      {run && <RunBar run={run} />}

      <div className="container">
        <FilterSidebar 
          query={query} 
          setQuery={setQuery} 
          options={options} 
          defaultQuery={defaultQuery} 
        />

        <main className="feed">
          <div className="feed-header">
            <h2>{jobs.length} Jobs Found</h2>
            <div className="sort-wrap">
              <select value={query.sort} onChange={e => setQuery({...query, sort: e.target.value})}>
                <option value="fit_score">Sort by Fit Score</option>
                <option value="created_at">Newest First</option>
                <option value="company">Company (A-Z)</option>
              </select>
            </div>
          </div>

          <div className="job-list">
            {jobs.map(job => (
              <JobCard 
                key={job.id} 
                job={job} 
                isActive={selected?.id === job.id} 
                onClick={() => setSelectedId(job.id)} 
              />
            ))}
          </div>
        </main>

        <JobDetailPanel 
          job={selected} 
          statuses={STATUSES} 
          onStatusChange={onStatus} 
        />
      </div>

      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </>
  );
}
