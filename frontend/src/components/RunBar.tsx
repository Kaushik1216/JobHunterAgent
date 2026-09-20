import { Activity, CheckCircle, Search, Cpu, AlertTriangle, XCircle } from "lucide-react";
import type { RunState } from "../types";

export function RunBar({ run }: { run: RunState }) {
  if (!run || run.status === "idle") return null;

  const isRunning = run.status === "running";
  const isFailed = run.status === "failed";
  const hasErrors = !isRunning && run.error;

  return (
    <div className={`run-bar ${isRunning ? 'active' : isFailed ? 'failed' : 'completed'}`}>
      <div className="run-bar-status">
        {isRunning ? (
          <Activity size={18} className="animate-pulse" style={{ color: 'var(--accent)' }} />
        ) : isFailed ? (
          <XCircle size={18} style={{ color: '#dc2626' }} />
        ) : (
          <CheckCircle size={18} style={{ color: '#22c55e' }} />
        )}
        <strong>
          {isRunning
            ? run.message || "Agent is working..."
            : isFailed
            ? run.message || "Search failed"
            : "Agent finished work."}
        </strong>
      </div>

      {/* Search error details */}
      {hasErrors && (
        <div className="run-error-block">
          <AlertTriangle size={14} style={{ color: '#f59e0b', flexShrink: 0 }} />
          <span style={{ fontSize: 12 }}>{run.error}</span>
        </div>
      )}

      {run.summary && (
        <div className="run-stats">
          <div className="run-stat-item">
            <Search size={16} className="text-muted-light" />
            Discovered: <span className="run-stat-val">{run.summary.jobs_discovered || run.summary.jobs_found}</span>
          </div>
          <div className="run-stat-item">
            <Cpu size={16} className="text-muted-light" />
            Qualified: <span className="run-stat-val">{run.summary.jobs_qualified}</span>
          </div>
          {run.summary.jobs_errored > 0 && (
            <div className="run-stat-item" style={{ color: '#f59e0b' }}>
              <AlertTriangle size={16} />
              Errors: <span className="run-stat-val">{run.summary.jobs_errored}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
