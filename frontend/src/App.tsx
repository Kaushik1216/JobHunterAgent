import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { FilterOptions, Job, JobQuery, JobStatus, Meta, RunState, Stats } from "./types";

import { Navbar } from "./components/Navbar";
import { RunBar } from "./components/RunBar";
import { FilterSidebar } from "./components/FilterSidebar";
import { JobCard } from "./components/JobCard";
import { JobDetailPanel } from "./components/JobDetailPanel";
import { JobModal } from "./components/JobModal";
import { SettingsPage } from "./pages/SettingsPage";
import { ResumePage } from "./pages/ResumePage";

const STATUSES: JobStatus[] = ["DISCOVERED", "NEW", "APPLIED", "SKIPPED", "ARCHIVED"];

const defaultQuery: JobQuery = {
  company: [], portal: [], status: [], max_days: "", location: [], minFit: 0,
  evaluated: "", yoeMatch: "", q: "", sort: "fit_score",
};

export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [query, setQuery] = useState<JobQuery>(defaultQuery);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [modalJob, setModalJob] = useState<Job | null>(null);
  const [run, setRun] = useState<RunState | null>(null);
  const [busy, setBusy] = useState(false);

  // Sync with browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = (path: string) => {
    window.history.pushState({}, "", path);
    setCurrentPath(path);
  };

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

  async function handleEvaluateJob(jobId: string): Promise<Job | null> {
    const updated = await api.evaluateJob(jobId);
    setJobs((current) => current.map((j) => (j.id === updated.id ? updated : j)));
    if (modalJob && modalJob.id === updated.id) {
      setModalJob(updated);
    }
    api.stats().then(setStats).catch(() => {});
    return updated;
  }

  async function onStatus(status: JobStatus, targetJobId?: string) {
    const id = targetJobId || selected?.id;
    if (!id) return;
    const updated = await api.updateStatus(id, status);
    setJobs((current) => current.map((job) => (job.id === updated.id ? updated : job)));
    if (modalJob && modalJob.id === updated.id) {
      setModalJob(updated);
    }
    await refresh();
  }

  const running = run?.status === "running" || busy;
  const unmatchedCount = stats?.unevaluated ?? 0;
  const isSettings = currentPath === "/settings";
  const isResume = currentPath === "/resume";

  return (
    <>
      <Navbar 
        currentPath={currentPath} 
        onNavigate={navigate} 
        running={running} 
      />
      
      {run && <RunBar run={run} />}

      {isSettings ? (
        <SettingsPage 
          onNavigateHome={() => navigate("/")}
          onStartRun={start}
          running={running}
          unmatchedCount={unmatchedCount}
        />
      ) : isResume ? (
        <ResumePage 
          onNavigateHome={() => navigate("/")}
        />
      ) : (
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
                  <option value="days_ago">Recently Posted</option>
                  <option value="experience">Experience (Low to High)</option>
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
                  onOpenModal={(j) => setModalJob(j)}
                />
              ))}
              {jobs.length === 0 && (
                <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)' }}>
                  <h3>No jobs match current filters</h3>
                  <p style={{ marginTop: 8 }}>Go to <strong>Settings</strong> to run job discovery or adjust search criteria.</p>
                  <button 
                    type="button" 
                    className="btn btn-primary" 
                    style={{ marginTop: 16 }}
                    onClick={() => navigate("/settings")}
                  >
                    Open Settings & Discovery
                  </button>
                </div>
              )}
            </div>
          </main>

          <JobDetailPanel 
            job={selected} 
            statuses={STATUSES} 
            onStatusChange={onStatus} 
            onOpenModal={(j) => setModalJob(j)}
            onEvaluateJob={handleEvaluateJob}
          />
        </div>
      )}

      {modalJob && (
        <JobModal
          job={modalJob}
          onClose={() => setModalJob(null)}
          onStatusChange={async (id, s) => {
            await onStatus(s, id);
          }}
          onEvaluateJob={handleEvaluateJob}
          statuses={STATUSES}
        />
      )}
    </>
  );
}
