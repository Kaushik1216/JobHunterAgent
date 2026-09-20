import { ExternalLink, Target, Briefcase, FileText, CheckCircle2, XCircle, Building2, MapPin } from "lucide-react";
import type { Job, JobStatus } from "../types";

interface Props {
  job: Job | null;
  statuses: JobStatus[];
  onStatusChange: (s: JobStatus) => void;
}

export function JobDetailPanel({ job, statuses, onStatusChange }: Props) {
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

  return (
    <aside className="detail-panel">
      <div className="dp-scroll">
        <div className="dp-header">
          <h2 className="dp-title">{job.title}</h2>
          <div className="dp-company" style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <Building2 size={16}/> {job.company} • <MapPin size={16}/> {job.location}
          </div>
          
          <a href={job.apply_url} target="_blank" rel="noreferrer" className="dp-apply-btn" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
            Apply on {job.source_portal} <ExternalLink size={16} />
          </a>
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
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Briefcase size={16}/> Original Snippet</h3>
          <div className="dp-snippet">{job.raw_snippet}</div>
        </div>
      </div>
    </aside>
  );
}
