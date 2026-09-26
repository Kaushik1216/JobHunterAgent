import { useState, useEffect } from "react";
import {
  X,
  ExternalLink,
  Sparkles,
  RefreshCw,
  Building2,
  MapPin,
  Globe,
  Clock,
  Briefcase,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileText,
  Target,
  Loader2,
  Search,
} from "lucide-react";
import type { Job, JobStatus } from "../types";
import { getScoreClass, getCleanApplyUrl, getDirectSearchUrl } from "../utils";

interface JobModalProps {
  job: Job | null;
  onClose: () => void;
  onStatusChange: (id: string, status: JobStatus) => Promise<void>;
  onEvaluateJob: (id: string) => Promise<Job | null>;
  statuses: JobStatus[];
}

export function JobModal({
  job,
  onClose,
  onStatusChange,
  onEvaluateJob,
  statuses,
}: JobModalProps) {
  const [evaluating, setEvaluating] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<Job | null>(job);

  useEffect(() => {
    setCurrentJob(job);
    setEvalError(null);
  }, [job]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!currentJob) return null;

  const handleEvaluate = async () => {
    setEvaluating(true);
    setEvalError(null);
    try {
      const updated = await onEvaluateJob(currentJob.id);
      if (updated) {
        setCurrentJob(updated);
      }
    } catch (err: any) {
      setEvalError(err?.message || "Failed to evaluate job with AI");
    } finally {
      setEvaluating(false);
    }
  };

  const handleStatusSelect = async (newStatus: JobStatus) => {
    try {
      await onStatusChange(currentJob.id, newStatus);
      setCurrentJob({ ...currentJob, status: newStatus });
    } catch (err: any) {
      setEvalError(err?.message || "Failed to update status");
    }
  };

  const scorePercent = currentJob.evaluated ? Math.round(currentJob.fit_score * 100) : null;

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(9, 30, 66, 0.54)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: 16,
      }}
    >
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#fff",
          borderRadius: 12,
          width: "100%",
          maxWidth: 840,
          maxHeight: "90vh",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 12px 32px rgba(9, 30, 66, 0.25)",
          overflow: "hidden",
          animation: "slideInUp 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: "20px 24px 16px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 16,
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, flexWrap: "wrap" }}>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  padding: "2px 8px",
                  borderRadius: 4,
                  background: "var(--bg)",
                  color: "var(--primary)",
                  border: "1px solid var(--border)",
                }}
              >
                {currentJob.source_portal}
              </span>
              <span
                style={{
                  fontSize: 12,
                  color: "var(--text-muted)",
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                }}
              >
                <Clock size={13} />
                {currentJob.posted_days_ago !== null
                  ? `${currentJob.posted_days_ago} days ago`
                  : "Recent"}
              </span>
            </div>
            <h2
              style={{
                margin: 0,
                fontSize: 22,
                fontWeight: 700,
                color: "var(--text-main)",
                lineHeight: 1.3,
                wordBreak: "break-word",
              }}
            >
              {currentJob.title}
            </h2>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                marginTop: 8,
                color: "var(--text-muted)",
                fontSize: 14,
                flexWrap: "wrap",
              }}
            >
              <span style={{ display: "flex", alignItems: "center", gap: 4, fontWeight: 600, color: "var(--text-main)" }}>
                <Building2 size={16} /> {currentJob.company}
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <MapPin size={16} /> {currentJob.location}
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="btn-icon"
            style={{ padding: 6, borderRadius: 6, color: "var(--text-muted)" }}
            title="Close (Esc)"
          >
            <X size={20} />
          </button>
        </div>

        {/* Action Bar: Apply, Status, and AI Match */}
        <div
          style={{
            padding: "12px 24px",
            background: "var(--bg, #f8fafc)",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <a
              href={getCleanApplyUrl(currentJob.apply_url)}
              target="_blank"
              rel="noreferrer"
              className="btn btn-primary"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                textDecoration: "none",
                fontSize: 13,
                padding: "8px 14px",
              }}
            >
              Apply on {currentJob.source_portal} <ExternalLink size={14} />
            </a>

            <a
              href={getDirectSearchUrl(currentJob.company, currentJob.title, currentJob.location)}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                textDecoration: "none",
                fontSize: 13,
                padding: "8px 14px",
              }}
              title="Search company careers on Google if this job board link expired"
            >
              <Search size={14} /> Search Direct Role
            </a>

            <select
              className="filter-input"
              style={{ width: "auto", fontSize: 13, padding: "7px 12px", cursor: "pointer" }}
              value={currentJob.status}
              onChange={(e) => handleStatusSelect(e.target.value as JobStatus)}
            >
              {statuses.map((s) => (
                <option key={s} value={s}>
                  Status: {s}
                </option>
              ))}
            </select>
          </div>

          {/* AI Match / Rematch Button */}
          <button
            type="button"
            className={currentJob.evaluated ? "btn btn-secondary" : "btn btn-primary"}
            onClick={handleEvaluate}
            disabled={evaluating}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13,
              padding: "8px 16px",
              fontWeight: 600,
              background: currentJob.evaluated ? "#fff" : "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
              color: currentJob.evaluated ? "var(--primary)" : "#fff",
              borderColor: currentJob.evaluated ? "var(--primary)" : "transparent",
            }}
          >
            {evaluating ? (
              <Loader2 size={15} className="spin" />
            ) : currentJob.evaluated ? (
              <RefreshCw size={15} />
            ) : (
              <Sparkles size={15} />
            )}
            {evaluating
              ? "Analyzing with AI..."
              : currentJob.evaluated
              ? "Rematch with AI"
              : "Match with AI"}
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div
          style={{
            padding: "20px 24px",
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: 20,
          }}
        >
          {evalError && (
            <div
              style={{
                padding: "10px 14px",
                borderRadius: 6,
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#991b1b",
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 13,
              }}
            >
              <AlertCircle size={16} />
              <span>{evalError}</span>
            </div>
          )}

          {/* AI Match Overview Card */}
          <div
            style={{
              borderRadius: 8,
              border: "1px solid var(--border)",
              padding: 16,
              background: currentJob.evaluated ? "#fff" : "var(--bg-subtle, #f8fafc)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 12,
                flexWrap: "wrap",
                gap: 8,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Target size={18} color="var(--primary)" />
                <span style={{ fontWeight: 600, fontSize: 15, color: "var(--text-main)" }}>
                  AI Fit Evaluation
                </span>
              </div>

              {currentJob.evaluated ? (
                <div
                  className={`score-badge ${getScoreClass(currentJob.fit_score, true)}`}
                  style={{ fontSize: 14, padding: "4px 12px", borderRadius: 16 }}
                >
                  {scorePercent}% Fit Score
                </div>
              ) : (
                <span
                  style={{
                    fontSize: 12,
                    padding: "3px 10px",
                    borderRadius: 12,
                    background: "#f1f5f9",
                    color: "var(--text-muted)",
                    fontWeight: 600,
                  }}
                >
                  Unevaluated (Click "Match with AI" above)
                </span>
              )}
            </div>

            {/* Evaluation Summary */}
            {currentJob.evaluated ? (
              <p
                style={{
                  fontSize: 13,
                  lineHeight: 1.5,
                  color: "var(--text-main)",
                  margin: "0 0 16px 0",
                  background: "var(--bg, #f8fafc)",
                  padding: 12,
                  borderRadius: 6,
                  border: "1px solid var(--border)",
                }}
              >
                {currentJob.summary_reason || "Evaluated by AI without specific summary."}
              </p>
            ) : (
              <p style={{ fontSize: 13, color: "var(--text-muted)", margin: "0 0 16px 0" }}>
                This job was discovered during search and has not been scored yet. Click{" "}
                <strong>Match with AI</strong> to extract required skills, experience bounds, and compute candidate fit.
              </p>
            )}

            {/* Quick Stats Grid */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: 12,
                marginTop: 8,
              }}
            >
              <div style={{ background: "var(--bg)", padding: 10, borderRadius: 6 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)", display: "block" }}>
                  Required Experience
                </span>
                <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-main)" }}>
                  {currentJob.extracted_min_yoe ?? "?"} - {currentJob.extracted_max_yoe ?? "?"} Years
                </span>
              </div>

              <div style={{ background: "var(--bg)", padding: 10, borderRadius: 6 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)", display: "block" }}>
                  Experience Match
                </span>
                <span
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: currentJob.yoe_match ? "var(--good, #059669)" : "var(--low, #dc2626)",
                  }}
                >
                  {currentJob.evaluated
                    ? currentJob.yoe_match
                      ? "✓ Matches Target"
                      : "✕ Experience Mismatch"
                    : "-"}
                </span>
              </div>

              <div style={{ background: "var(--bg)", padding: 10, borderRadius: 6 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)", display: "block" }}>
                  Target Role Search
                </span>
                <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-main)" }}>
                  {currentJob.search_title || currentJob.title}
                </span>
              </div>
            </div>

            {/* Matched Skills */}
            <div style={{ marginTop: 16 }}>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: "var(--good, #059669)",
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  marginBottom: 6,
                }}
              >
                <CheckCircle2 size={14} /> Matched Skills ({currentJob.matched_skills.length})
              </span>
              <div className="chips-wrap">
                {currentJob.matched_skills.map((skill) => (
                  <span key={skill} className="skill-tag matched">
                    {skill}
                  </span>
                ))}
                {currentJob.matched_skills.length === 0 && (
                  <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    {currentJob.evaluated ? "No matching skills extracted" : "Pending AI matching"}
                  </span>
                )}
              </div>
            </div>

            {/* Missing Skills */}
            <div style={{ marginTop: 12 }}>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: "var(--low, #dc2626)",
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  marginBottom: 6,
                }}
              >
                <XCircle size={14} /> Missing Skills ({currentJob.missing_skills.length})
              </span>
              <div className="chips-wrap">
                {currentJob.missing_skills.map((skill) => (
                  <span key={skill} className="skill-tag">
                    {skill}
                  </span>
                ))}
                {currentJob.missing_skills.length === 0 && (
                  <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    {currentJob.evaluated ? "None identified" : "Pending AI matching"}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Job Description Card */}
          <div
            style={{
              borderRadius: 8,
              border: "1px solid var(--border)",
              padding: 16,
              background: "#fff",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: "1px solid var(--border)",
              }}
            >
              <FileText size={18} color="var(--primary)" />
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: "var(--text-main)" }}>
                Full Job Description
              </h3>
            </div>

            <div
              style={{
                fontSize: 13,
                lineHeight: 1.65,
                color: "#1e293b",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                maxHeight: 380,
                overflowY: "auto",
                padding: "8px 4px",
              }}
            >
              {currentJob.raw_snippet || "No description text available."}
            </div>

            {currentJob.source_query && (
              <div
                style={{
                  marginTop: 12,
                  paddingTop: 8,
                  borderTop: "1px solid var(--border)",
                  fontSize: 11,
                  color: "var(--text-muted)",
                }}
              >
                Discovery Query: <code>{currentJob.source_query}</code>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: "14px 24px",
            borderTop: "1px solid var(--border)",
            background: "var(--bg, #f8fafc)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            ID: <code style={{ fontSize: 11 }}>{currentJob.id}</code>
          </span>
          <div style={{ display: "flex", gap: 10 }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
            <a
              href={getDirectSearchUrl(currentJob.company, currentJob.title, currentJob.location)}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary"
              style={{ textDecoration: "none", display: "inline-flex", alignItems: "center", gap: 6 }}
              title="Search official career site directly on Google"
            >
              <Search size={14} /> Search Role
            </a>
            <a
              href={getCleanApplyUrl(currentJob.apply_url)}
              target="_blank"
              rel="noreferrer"
              className="btn btn-primary"
              style={{ textDecoration: "none", display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              Apply on {currentJob.source_portal} <ExternalLink size={14} />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
