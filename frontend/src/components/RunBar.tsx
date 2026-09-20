import { Activity, CheckCircle, Search, Cpu } from "lucide-react";
import type { RunState } from "../types";

export function RunBar({ run }: { run: RunState }) {
  if (!run || run.status === "idle") return null;

  const isRunning = run.status === "running";

  return (
    <div className={`run-bar ${isRunning ? 'active' : 'completed'}`}>
      <div className="run-bar-status">
        {isRunning ? (
          <Activity size={18} className="animate-pulse text-green" />
        ) : (
          <CheckCircle size={18} className="text-blue" />
        )}
        <strong>{isRunning ? run.message || "Agent is working..." : "Agent finished work."}</strong>
      </div>
      
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
        </div>
      )}
    </div>
  );
}
