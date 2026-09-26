import { useState, useEffect, useRef } from "react";
import {
  FileText,
  Upload,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Trash2,
  RefreshCw,
  Star,
  Briefcase,
  FolderGit2,
  GraduationCap,
  Award,
  Globe,
  Mail,
  Phone,
  MapPin,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Cpu,
  Layers,
  ArrowLeft,
  Sparkles,
  Code2,
} from "lucide-react";
import { api } from "../api";
import type { ResumeRecord } from "../types";

interface ResumePageProps {
  onNavigateHome: () => void;
}

export function ResumePage({ onNavigateHome }: ResumePageProps) {
  const [resumes, setResumes] = useState<ResumeRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [reparsing, setReparsing] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [showRawText, setShowRawText] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const loadResumes = async () => {
    try {
      setLoading(true);
      const list = await api.listResumes();
      setResumes(list);
      if (list.length > 0) {
        const active = list.find((r) => r.is_active);
        setSelectedId((curr) => {
          if (curr && list.some((r) => r.id === curr)) return curr;
          return active ? active.id : list[0].id;
        });
      } else {
        setSelectedId(null);
      }
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to load resumes", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResumes();
  }, []);

  const selectedResume = resumes.find((r) => r.id === selectedId) || null;
  const profile = selectedResume?.parsed_profile || null;

  const handleFileUpload = async (file: File) => {
    if (!file) return;
    const validExtensions = [".pdf", ".docx", ".doc", ".txt", ".md"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!validExtensions.includes(ext)) {
      setMessage({
        text: `Unsupported file format. Please upload PDF, DOCX, TXT, or Markdown.`,
        type: "error",
      });
      return;
    }

    try {
      setUploading(true);
      setMessage(null);
      const saved = await api.uploadResume(file);
      await loadResumes();
      setSelectedId(saved.id);
      setMessage({
        text: `Resume "${file.name}" uploaded and structured profile extracted via AI!`,
        type: "success",
      });
    } catch (err: any) {
      setMessage({ text: err.message || "Resume upload failed", type: "error" });
    } finally {
      setUploading(false);
    }
  };

  const handleSetActive = async (id: string) => {
    try {
      await api.setActiveResume(id);
      await loadResumes();
      setMessage({ text: "Active resume profile updated successfully!", type: "success" });
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to set active resume", type: "error" });
    }
  };

  const handleReparse = async (id: string) => {
    try {
      setReparsing(true);
      setMessage(null);
      const updated = await api.reparseResume(id);
      await loadResumes();
      setSelectedId(updated.id);
      setMessage({ text: "Resume re-analyzed with latest AI model!", type: "success" });
    } catch (err: any) {
      setMessage({ text: err.message || "AI extraction failed", type: "error" });
    } finally {
      setReparsing(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this resume?")) return;
    try {
      await api.deleteResume(id);
      await loadResumes();
      setMessage({ text: "Resume deleted.", type: "success" });
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to delete resume", type: "error" });
    }
  };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "24px 20px" }}>
      {/* Top Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onNavigateHome}
            style={{ display: "flex", alignItems: "center", gap: 6, padding: "8px 12px" }}
          >
            <ArrowLeft size={16} /> Back to Jobs
          </button>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
              <FileText size={26} color="var(--primary)" /> Resume Profile
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: 13, margin: "2px 0 0" }}>
              Upload your resume once. AI extracts skills, experience, and projects to match jobs accurately.
            </p>
          </div>
        </div>

        <div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            style={{ display: "flex", alignItems: "center", gap: 8 }}
          >
            {uploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
            {uploading ? "Analyzing with AI..." : "Upload New Resume"}
          </button>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: "none" }}
            accept=".pdf,.docx,.doc,.txt,.md"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileUpload(e.target.files[0]);
                e.target.value = "";
              }
            }}
          />
        </div>
      </div>

      {/* Status Alert Banner */}
      {message && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: 8,
            marginBottom: 20,
            display: "flex",
            alignItems: "center",
            gap: 10,
            backgroundColor: message.type === "success" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
            border: `1px solid ${message.type === "success" ? "rgba(16, 185, 129, 0.4)" : "rgba(239, 68, 68, 0.4)"}`,
            color: message.type === "success" ? "#34d399" : "#f87171",
            fontSize: 14,
          }}
        >
          {message.type === "success" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Uploading progress notification */}
      {uploading && (
        <div
          style={{
            padding: "16px 20px",
            background: "linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(56, 189, 248, 0.1))",
            border: "1px solid var(--primary)",
            borderRadius: 10,
            marginBottom: 24,
            display: "flex",
            alignItems: "center",
            gap: 14,
          }}
        >
          <Loader2 size={24} color="var(--primary)" className="animate-spin" />
          <div>
            <div style={{ fontWeight: 600, fontSize: 14, color: "var(--text)" }}>
              Extracting candidate profile with AI...
            </div>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
              Parsing work history, projects, tech stack, and skills (one-time job).
            </div>
          </div>
        </div>
      )}

      {/* Empty State / Dropzone if no resumes */}
      {!loading && resumes.length === 0 && !uploading && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
              handleFileUpload(e.dataTransfer.files[0]);
            }
          }}
          style={{
            border: `2px dashed ${dragActive ? "var(--primary)" : "var(--border)"}`,
            borderRadius: 12,
            padding: "54px 24px",
            textAlign: "center",
            backgroundColor: dragActive ? "rgba(99, 102, 241, 0.05)" : "var(--card)",
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: "rgba(99, 102, 241, 0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
            }}
          >
            <Upload size={28} color="var(--primary)" />
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Upload Your Resume</h3>
          <p style={{ color: "var(--text-muted)", fontSize: 14, maxWidth: 480, margin: "0 auto 16px" }}>
            Drag and drop your resume file here or click to browse. Supports <strong>PDF, DOCX, TXT, or Markdown</strong>.
          </p>
          <span className="btn btn-outline" style={{ fontSize: 13 }}>
            Choose File from Computer
          </span>
          <div style={{ marginTop: 20, fontSize: 12, color: "var(--text-muted)" }}>
            Stored locally in project <code style={{ color: "var(--primary)" }}>resumes/</code> (git-ignored) &bull; One-time extraction
          </div>
        </div>
      )}

      {/* Resumes Tab & Selection Bar */}
      {resumes.length > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 10,
            alignItems: "center",
            justifyContent: "space-between",
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 10,
            padding: "10px 16px",
            marginBottom: 20,
          }}
        >
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
              Resumes:
            </span>
            {resumes.map((r) => {
              const isSelected = r.id === selectedId;
              return (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => setSelectedId(r.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "6px 12px",
                    borderRadius: 6,
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: "pointer",
                    border: isSelected ? "1px solid var(--primary)" : "1px solid var(--border)",
                    backgroundColor: isSelected ? "rgba(99, 102, 241, 0.15)" : "var(--bg)",
                    color: isSelected ? "var(--primary)" : "var(--text)",
                    transition: "all 0.15s ease",
                  }}
                >
                  <FileText size={14} />
                  <span style={{ maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {r.filename}
                  </span>
                  {r.is_active && (
                    <span
                      style={{
                        background: "rgba(16, 185, 129, 0.2)",
                        color: "#34d399",
                        fontSize: 10,
                        fontWeight: 700,
                        padding: "1px 5px",
                        borderRadius: 4,
                        textTransform: "uppercase",
                      }}
                    >
                      Active
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Action buttons for selected resume */}
          {selectedResume && (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {!selectedResume.is_active && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => handleSetActive(selectedResume.id)}
                  style={{ fontSize: 12, padding: "5px 10px", display: "flex", alignItems: "center", gap: 5 }}
                >
                  <Star size={13} color="#f59e0b" /> Set as Active
                </button>
              )}
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => handleReparse(selectedResume.id)}
                disabled={reparsing}
                style={{ fontSize: 12, padding: "5px 10px", display: "flex", alignItems: "center", gap: 5 }}
                title="Re-run AI extraction with current model"
              >
                {reparsing ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                {reparsing ? "Extracting..." : "Re-Analyze with AI"}
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={() => handleDelete(selectedResume.id)}
                style={{ fontSize: 12, padding: "5px 10px", display: "flex", alignItems: "center", gap: 5 }}
              >
                <Trash2 size={13} /> Delete
              </button>
            </div>
          )}
        </div>
      )}

      {/* Main Profile View */}
      {selectedResume && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Candidate Hero Card */}
          <div
            style={{
              background: "var(--card)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: "24px 28px",
              position: "relative",
              overflow: "hidden",
            }}
          >
            <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 16 }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0, color: "var(--text)" }}>
                    {profile?.name || selectedResume.candidate_name || selectedResume.filename}
                  </h2>
                  {selectedResume.is_active && (
                    <span
                      style={{
                        background: "rgba(16, 185, 129, 0.2)",
                        color: "#34d399",
                        border: "1px solid rgba(16, 185, 129, 0.4)",
                        fontSize: 11,
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: 12,
                        textTransform: "uppercase",
                      }}
                    >
                      Active Profile for Matching
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 15, color: "var(--primary)", fontWeight: 500, marginTop: 4 }}>
                  {profile?.headline || selectedResume.headline || "Candidate Profile"}
                </div>

                {/* Contact info row */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginTop: 12, fontSize: 13, color: "var(--text-muted)" }}>
                  {(profile?.email || selectedResume.email) && (
                    <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                      <Mail size={14} color="var(--primary)" />
                      <span>{profile?.email || selectedResume.email}</span>
                    </div>
                  )}
                  {profile?.phone && (
                    <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                      <Phone size={14} color="var(--primary)" />
                      <span>{profile.phone}</span>
                    </div>
                  )}
                  {profile?.location && (
                    <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                      <MapPin size={14} color="var(--primary)" />
                      <span>{profile.location}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Right side stats pill */}
              <div style={{ display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-end" }}>
                <div
                  style={{
                    background: "rgba(99, 102, 241, 0.12)",
                    border: "1px solid rgba(99, 102, 241, 0.3)",
                    padding: "8px 14px",
                    borderRadius: 8,
                    textAlign: "right",
                  }}
                >
                  <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                    Experience
                  </div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: "var(--primary)" }}>
                    {profile?.total_experience_years !== undefined && profile?.total_experience_years !== null
                      ? `${profile.total_experience_years} Years`
                      : selectedResume.total_yoe
                      ? `${selectedResume.total_yoe} Years`
                      : "Not specified"}
                  </div>
                </div>

                {/* Social links */}
                <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                  {profile?.linkedin_url && (
                    <a
                      href={profile.linkedin_url.startsWith("http") ? profile.linkedin_url : `https://${profile.linkedin_url}`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-secondary"
                      style={{ fontSize: 11, padding: "3px 8px", display: "flex", alignItems: "center", gap: 4 }}
                    >
                      <Globe size={12} /> LinkedIn <ExternalLink size={10} />
                    </a>
                  )}
                  {profile?.github_url && (
                    <a
                      href={profile.github_url.startsWith("http") ? profile.github_url : `https://${profile.github_url}`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-secondary"
                      style={{ fontSize: 11, padding: "3px 8px", display: "flex", alignItems: "center", gap: 4 }}
                    >
                      <FolderGit2 size={12} /> GitHub <ExternalLink size={10} />
                    </a>
                  )}
                </div>
              </div>
            </div>

            {/* Inferred Target Roles */}
            {profile?.target_roles && profile.target_roles.length > 0 && (
              <div style={{ marginTop: 18, paddingTop: 14, borderTop: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)" }}>Target Roles:</span>
                {profile.target_roles.map((r, i) => (
                  <span
                    key={i}
                    style={{
                      background: "rgba(56, 189, 248, 0.15)",
                      color: "#38bdf8",
                      fontSize: 11,
                      fontWeight: 600,
                      padding: "2px 8px",
                      borderRadius: 4,
                    }}
                  >
                    {r}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Professional Summary */}
          {profile?.summary && (
            <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 24px" }}>
              <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
                <Sparkles size={16} color="var(--primary)" /> Professional Summary
              </h3>
              <p style={{ color: "var(--text)", fontSize: 14, lineHeight: 1.6, margin: 0 }}>
                {profile.summary}
              </p>
            </div>
          )}

          {/* Categorized Skills Section */}
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 24px" }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <Code2 size={16} color="var(--primary)" /> Extracted Skills & Technologies
            </h3>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
              {/* Languages */}
              {profile?.skills?.languages && profile.skills.languages.length > 0 && (
                <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase" }}>
                    Programming Languages
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {profile.skills.languages.map((skill, i) => (
                      <span key={i} style={{ background: "rgba(99, 102, 241, 0.15)", color: "var(--primary)", fontSize: 12, padding: "2px 8px", borderRadius: 4, fontWeight: 500 }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Frameworks */}
              {profile?.skills?.frameworks_and_libraries && profile.skills.frameworks_and_libraries.length > 0 && (
                <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase" }}>
                    Frameworks & Libraries
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {profile.skills.frameworks_and_libraries.map((skill, i) => (
                      <span key={i} style={{ background: "rgba(168, 85, 247, 0.15)", color: "#c084fc", fontSize: 12, padding: "2px 8px", borderRadius: 4, fontWeight: 500 }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Databases */}
              {profile?.skills?.databases && profile.skills.databases.length > 0 && (
                <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase" }}>
                    Databases & Storage
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {profile.skills.databases.map((skill, i) => (
                      <span key={i} style={{ background: "rgba(16, 185, 129, 0.15)", color: "#34d399", fontSize: 12, padding: "2px 8px", borderRadius: 4, fontWeight: 500 }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Cloud & DevOps */}
              {profile?.skills?.cloud_and_devops && profile.skills.cloud_and_devops.length > 0 && (
                <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase" }}>
                    Cloud & DevOps
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {profile.skills.cloud_and_devops.map((skill, i) => (
                      <span key={i} style={{ background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", fontSize: 12, padding: "2px 8px", borderRadius: 4, fontWeight: 500 }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Tools & Platforms */}
              {profile?.skills?.tools_and_platforms && profile.skills.tools_and_platforms.length > 0 && (
                <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase" }}>
                    Tools & Platforms
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {profile.skills.tools_and_platforms.map((skill, i) => (
                      <span key={i} style={{ background: "rgba(245, 158, 11, 0.15)", color: "#fbbf24", fontSize: 12, padding: "2px 8px", borderRadius: 4, fontWeight: 500 }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Core Competencies */}
              {profile?.skills?.core_competencies && profile.skills.core_competencies.length > 0 && (
                <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase" }}>
                    Core Competencies
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {profile.skills.core_competencies.map((skill, i) => (
                      <span key={i} style={{ background: "rgba(244, 63, 94, 0.15)", color: "#fb7185", fontSize: 12, padding: "2px 8px", borderRadius: 4, fontWeight: 500 }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Fallback flat skills if categorized is empty */}
            {(!profile?.skills?.languages || profile.skills.languages.length === 0) &&
              profile?.skills?.all_skills &&
              profile.skills.all_skills.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {profile.skills.all_skills.map((skill, i) => (
                    <span key={i} style={{ background: "rgba(99, 102, 241, 0.15)", color: "var(--primary)", fontSize: 12, padding: "3px 9px", borderRadius: 4, fontWeight: 500 }}>
                      {skill}
                    </span>
                  ))}
                </div>
              )}
          </div>

          {/* Work Experience */}
          {profile?.work_experience && profile.work_experience.length > 0 && (
            <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 24px" }}>
              <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <Briefcase size={16} color="var(--primary)" /> Work Experience
              </h3>

              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {profile.work_experience.map((exp, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "var(--bg)",
                      border: "1px solid var(--border)",
                      borderRadius: 10,
                      padding: 16,
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8 }}>
                      <div>
                        <div style={{ fontSize: 16, fontWeight: 600, color: "var(--text)" }}>{exp.role}</div>
                        <div style={{ fontSize: 14, color: "var(--primary)", fontWeight: 500 }}>{exp.company}</div>
                      </div>
                      <div style={{ textAlign: "right", fontSize: 12, color: "var(--text-muted)" }}>
                        {exp.start_date || ""} {exp.end_date ? `– ${exp.end_date}` : ""}
                        {exp.is_current && (
                          <span style={{ marginLeft: 6, background: "rgba(16, 185, 129, 0.2)", color: "#34d399", padding: "1px 5px", borderRadius: 3, fontWeight: 600, fontSize: 10 }}>
                            Current
                          </span>
                        )}
                        {exp.location && <div>{exp.location}</div>}
                      </div>
                    </div>

                    {exp.description && (
                      <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8, marginBottom: 8, lineHeight: 1.5 }}>
                        {exp.description}
                      </p>
                    )}

                    {/* Achievements */}
                    {exp.achievements && exp.achievements.length > 0 && (
                      <ul style={{ margin: "8px 0 0 16px", padding: 0, fontSize: 13, color: "var(--text)" }}>
                        {exp.achievements.map((ach, aIdx) => (
                          <li key={aIdx} style={{ marginBottom: 4 }}>
                            {ach}
                          </li>
                        ))}
                      </ul>
                    )}

                    {/* Tech used in this job */}
                    {exp.technologies && exp.technologies.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginTop: 12, paddingTop: 10, borderTop: "1px solid var(--border)" }}>
                        <span style={{ fontSize: 11, color: "var(--text-muted)", alignSelf: "center", marginRight: 4 }}>Technologies:</span>
                        {exp.technologies.map((t, tIdx) => (
                          <span key={tIdx} style={{ background: "rgba(255, 255, 255, 0.05)", border: "1px solid var(--border)", fontSize: 11, padding: "1px 6px", borderRadius: 3, color: "var(--text-muted)" }}>
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Projects Portfolio */}
          {profile?.projects && profile.projects.length > 0 && (
            <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 24px" }}>
              <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <FolderGit2 size={16} color="var(--primary)" /> Projects Portfolio
              </h3>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
                {profile.projects.map((proj, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "var(--bg)",
                      border: "1px solid var(--border)",
                      borderRadius: 10,
                      padding: 16,
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                        <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>{proj.title}</div>
                        {proj.link && (
                          <a
                            href={proj.link.startsWith("http") ? proj.link : `https://${proj.link}`}
                            target="_blank"
                            rel="noreferrer"
                            style={{ color: "var(--primary)", display: "flex", alignItems: "center", gap: 3, fontSize: 12 }}
                          >
                            Demo <ExternalLink size={12} />
                          </a>
                        )}
                      </div>

                      {proj.role && (
                        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>
                          Role: {proj.role}
                        </div>
                      )}

                      {proj.description && (
                        <p style={{ fontSize: 13, color: "var(--text-muted)", margin: "6px 0", lineHeight: 1.5 }}>
                          {proj.description}
                        </p>
                      )}

                      {proj.highlights && proj.highlights.length > 0 && (
                        <ul style={{ margin: "6px 0 8px 16px", padding: 0, fontSize: 12, color: "var(--text)" }}>
                          {proj.highlights.map((h, hIdx) => (
                            <li key={hIdx} style={{ marginBottom: 3 }}>
                              {h}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {proj.technologies && proj.technologies.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 10, paddingTop: 8, borderTop: "1px solid var(--border)" }}>
                        {proj.technologies.map((t, tIdx) => (
                          <span key={tIdx} style={{ background: "rgba(99, 102, 241, 0.1)", color: "var(--primary)", fontSize: 11, padding: "1px 6px", borderRadius: 3 }}>
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Education & Certifications Row */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
            {/* Education */}
            {profile?.education && profile.education.length > 0 && (
              <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 24px" }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
                  <GraduationCap size={16} color="var(--primary)" /> Education
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {profile.education.map((edu, idx) => (
                    <div key={idx} style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: 12 }}>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{edu.degree}</div>
                      <div style={{ color: "var(--primary)", fontSize: 13 }}>{edu.institution}</div>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                        <span>{edu.field_of_study || ""}</span>
                        <span>{edu.graduation_year || ""}</span>
                      </div>
                      {edu.grade && <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>Grade: {edu.grade}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Certifications */}
            {profile?.certifications && profile.certifications.length > 0 && (
              <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 24px" }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
                  <Award size={16} color="var(--primary)" /> Certifications & Honors
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {profile.certifications.map((cert, idx) => (
                    <div key={idx} style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 6, padding: "8px 12px", fontSize: 13, display: "flex", alignItems: "center", gap: 8 }}>
                      <CheckCircle2 size={14} color="#34d399" />
                      <span>{cert}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Raw Text Drawer / Toggle */}
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "14px 20px" }}>
            <button
              type="button"
              onClick={() => setShowRawText(!showRawText)}
              style={{
                width: "100%",
                background: "none",
                border: "none",
                color: "var(--text-muted)",
                cursor: "pointer",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                fontSize: 13,
                padding: 0,
              }}
            >
              <span>View Extracted Raw Text ({selectedResume.raw_text.length} chars)</span>
              {showRawText ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>

            {showRawText && (
              <pre
                style={{
                  marginTop: 14,
                  padding: 14,
                  background: "var(--bg)",
                  borderRadius: 8,
                  fontSize: 12,
                  fontFamily: "monospace",
                  color: "var(--text-muted)",
                  whiteSpace: "pre-wrap",
                  maxHeight: 300,
                  overflowY: "auto",
                  border: "1px solid var(--border)",
                }}
              >
                {selectedResume.raw_text}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
