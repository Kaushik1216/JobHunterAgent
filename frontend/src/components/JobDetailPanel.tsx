import { useState } from "react";
import { ExternalLink, Target, Briefcase, FileText, CheckCircle2, XCircle, Building2, MapPin, Sparkles, RefreshCw, Maximize2, Loader2, Search } from "lucide-react";
import type { Job, JobStatus } from "../types";
import { getCleanApplyUrl, getDirectSearchUrl } from "../utils";

interface Props {
  job: Job | null;
  statuses: JobStatus[];
  onStatusChange: (s: JobStatus) => void;
  onOpenModal: (job: Job) => void;
  onEvaluateJob: (id: string) => Promise<Job | null>;
}

export function JobDetailPanel({ job, statuses, onStatusChange, onOpenModal, onEvaluateJob }: Props) {
  const [evaluating, setEvaluating] = useState(false);

  if (!job) {
    return (
      <aside className="detail-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <Target size={48} style={{ opacity: 0.5, marginBottom: 16 }} />
          <h3>No Job Selected</h3>
          <p>Select a job from the feed to view details.</p>
        </div>
      </aside>
    );
  }

  const handleEvaluate = async () => {
    setEvaluating(true);
    try {
      await onEvaluateJob(job.id);
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <aside className="detail-panel">
      <div className="dp-scroll">
        <div className="dp-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, marginBottom: 4 }}>
            <h2 className="dp-title" style={{ margin: 0, flex: 1 }}>{job.title}</h2>
            <button
              type="button"
              className="btn-icon"
              onClick={() => onOpenModal(job)}
              title="Open in Full Modal"
              style={{ padding: 4, borderRadius: 4, color: 'var(--text-muted)' }}
            >
              <Maximize2 size={16} />
            </button>
          </div>

          <div className="dp-company" style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
            <Building2 size={16}/> {job.company} • <MapPin size={16}/> {job.location}
          </div>
          
          <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleEvaluate}
              disabled={evaluating}
              style={{
                flex: 1,
                fontSize: 12,
                padding: '8px 12px',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 6,
                background: job.evaluated ? 'var(--primary)' : 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
              }}
            >
              {evaluating ? <Loader2 size={14} className="spin" /> : job.evaluated ? <RefreshCw size={14} /> : <Sparkles size={14} />}
              {evaluating ? "Evaluating..." : job.evaluated ? "Rematch with AI" : "Match with AI"}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => onOpenModal(job)}
              style={{ fontSize: 12, padding: '8px 12px', display: 'inline-flex', alignItems: 'center', gap: 4 }}
            >
              <Maximize2 size={14} /> Modal
            </button>
          </div>

          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <a 
              href={getCleanApplyUrl(job.apply_url)} 
              target="_blank" 
              rel="noreferrer" 
              className="dp-apply-btn" 
              style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, margin: 0 }}
            >
              Apply on {job.source_portal} <ExternalLink size={15} />
            </a>
            <a
              href={getDirectSearchUrl(job.company, job.title, job.location)}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary"
              style={{ padding: '0 12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 13, textDecoration: 'none' }}
              title="Search company careers on Google if direct board link expired"
            >
              <Search size={14} /> Search Role
            </a>
          </div>
          <select 
            className="status-select" 
            value={job.status} 
            onChange={e => onStatusChange(e.target.value as JobStatus)}
          >
            {statuses.map(s => <option key={s} value={s}>Status: {s}</option>)}
          </select>
        </div>

        <div className="dp-grid">
          <div className="dp-stat">
            <label>Fit Score</label>
            <span>{job.evaluated ? `${(job.fit_score * 100).toFixed(0)}%` : "Unevaluated"}</span>
          </div>
          <div className="dp-stat">
            <label>Experience Required</label>
            <span>{job.extracted_min_yoe ?? "?"}-{job.extracted_max_yoe ?? "?"} Years</span>
          </div>
          <div className="dp-stat">
            <label>Target YoE</label>
            <span>{job.target_yoe !== null ? job.target_yoe : "Any"}</span>
          </div>
          <div className="dp-stat">
            <label>Target Skills</label>
            <span>{job.core_skills?.length ? job.core_skills.join(", ") : "Any"}</span>
          </div>
        </div>

        <div className="dp-section">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}><FileText size={16}/> Evaluation Summary</h3>
          <p style={{ fontSize: '14px', lineHeight: '1.5', color: '#172b4d' }}>{job.summary_reason || "No summary available."}</p>
        </div>

        <div className="dp-section">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}><CheckCircle2 size={16} color="var(--good)"/> Matched Skills</h3>
          <div className="chips-wrap">
            {job.matched_skills.map(s => <span key={s} className="skill-tag matched">{s}</span>)}
            {job.matched_skills.length === 0 && <span className="filter-label">None</span>}
          </div>
        </div>

        <div className="dp-section">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}><XCircle size={16} color="var(--low)"/> Missing Skills</h3>
          <div className="chips-wrap">
            {job.missing_skills.map(s => <span key={s} className="skill-tag">{s}</span>)}
            {job.missing_skills.length === 0 && <span className="filter-label">None</span>}
          </div>
        </div>

        <div className="dp-section">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Briefcase size={16}/> Job Description</h3>
          <div className="dp-snippet" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', fontSize: '13px' }}>{job.raw_snippet || "No description available."}</div>
        </div>
      </div>
    </aside>
  );
}
