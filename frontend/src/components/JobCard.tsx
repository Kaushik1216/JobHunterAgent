import { Building2, MapPin, Globe, CheckCircle2, XCircle } from "lucide-react";
import type { Job } from "../types";
import { getScoreClass } from "../utils";

interface Props {
  job: Job;
  isActive: boolean;
  onClick: () => void;
}

export function JobCard({ job, isActive, onClick }: Props) {
  return (
    <div className={`job-card ${isActive ? 'active' : ''}`} onClick={onClick}>
      <div className="jc-head">
        <div>
          <h3 className="jc-title">{job.title}</h3>
          <div className="jc-company" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Building2 size={14} /> {job.company}
          </div>
        </div>
        <div className={`score-badge ${getScoreClass(job.fit_score, job.evaluated)}`} title="Fit Score">
          {job.evaluated ? (job.fit_score * 100).toFixed(0) : "-"}
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
          🗓️ {job.posted_days_ago !== null ? `${job.posted_days_ago}d ago` : 'Unknown'}
        </div>
      </div>
      
      <div className="skills-preview">
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
    </div>
  );
}
