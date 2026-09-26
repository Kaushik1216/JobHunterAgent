import { Building2, MapPin, Globe, CheckCircle2, XCircle, Sparkles, RefreshCw, Maximize2 } from "lucide-react";
import type { Job } from "../types";
import { getScoreClass } from "../utils";

interface Props {
  job: Job;
  isActive: boolean;
  onClick: () => void;
  onOpenModal: (job: Job) => void;
}

export function JobCard({ job, isActive, onClick, onOpenModal }: Props) {
  return (
    <div 
      className={`job-card ${isActive ? 'active' : ''}`} 
      onClick={onClick}
      style={{ position: 'relative' }}
    >
      <div className="jc-head">
        <div style={{ flex: 1, paddingRight: 8 }}>
          <h3 className="jc-title">{job.title}</h3>
          <div className="jc-company" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Building2 size={14} /> {job.company}
          </div>
        </div>
        <div className={`score-badge ${getScoreClass(job.fit_score, job.evaluated)}`} title={job.evaluated ? "Fit Score" : "Unevaluated"}>
          {job.evaluated ? `${(job.fit_score * 100).toFixed(0)}%` : "New"}
        </div>
      </div>
      
      <div className="jc-meta">
        <div className="jc-meta-item" title="Required Experience">
          💼 {job.extracted_min_yoe ?? "?"}-{job.extracted_max_yoe ?? "?"} YOE
        </div>
        <div className="jc-meta-item">
          <MapPin size={14} /> {job.location}
        </div>
        <div className="jc-meta-item">
          <Globe size={14} /> {job.source_portal}
        </div>
        <div className="jc-meta-item text-muted">
          🗓️ {job.posted_days_ago !== null ? `${job.posted_days_ago}d ago` : 'Recent'}
        </div>
      </div>
      
      <div className="skills-preview" style={{ marginBottom: 12 }}>
        {job.matched_skills.slice(0, 4).map(s => (
          <span key={s} className="skill-tag matched" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <CheckCircle2 size={12} /> {s}
          </span>
        ))}
        {job.missing_skills.slice(0, 2).map(s => (
          <span key={s} className="skill-tag" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <XCircle size={12} /> {s}
          </span>
        ))}
        {job.matched_skills.length + job.missing_skills.length > 6 && (
          <span className="skill-tag">+{job.matched_skills.length + job.missing_skills.length - 6} more</span>
        )}
      </div>

      {/* Card Action Footer */}
      <div 
        style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          paddingTop: 10, 
          borderTop: '1px solid var(--border)',
          marginTop: 6 
        }}
      >
        <span 
          style={{ 
            fontSize: 11, 
            fontWeight: 600, 
            padding: '2px 8px', 
            borderRadius: 4, 
            background: job.status === 'DISCOVERED' ? '#f1f5f9' : 'var(--bg)',
            color: 'var(--text-muted)'
          }}
        >
          {job.status}
        </span>

        <div style={{ display: 'flex', gap: 8 }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={(e) => {
              e.stopPropagation();
              onOpenModal(job);
            }}
            style={{ 
              fontSize: 12, 
              padding: '4px 10px', 
              display: 'inline-flex', 
              alignItems: 'center', 
              gap: 4 
            }}
            title="Open Detailed Modal"
          >
            <Maximize2 size={12} /> Details
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={(e) => {
              e.stopPropagation();
              onOpenModal(job);
            }}
            style={{ 
              fontSize: 12, 
              padding: '4px 10px', 
              display: 'inline-flex', 
              alignItems: 'center', 
              gap: 4,
              background: job.evaluated ? 'var(--primary)' : 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
            }}
          >
            {job.evaluated ? <RefreshCw size={12} /> : <Sparkles size={12} />}
            {job.evaluated ? "Rematch" : "Match with AI"}
          </button>
        </div>
      </div>
    </div>
  );
}
