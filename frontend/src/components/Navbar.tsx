import { Briefcase, Settings, LayoutGrid, FileText } from "lucide-react";

interface NavbarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  running: boolean;
}

export function Navbar({ currentPath, onNavigate, running }: NavbarProps) {
  const isSettings = currentPath === "/settings";
  const isResume = currentPath === "/resume";
  const isHome = currentPath === "/" || (!isSettings && !isResume);

  return (
    <nav className="navbar">
      <div className="brand" onClick={() => onNavigate("/")} style={{ cursor: "pointer" }}>
        <Briefcase className="brand-icon" size={28} color="var(--primary)" />
        <div>
          <h1>JobHunter</h1>
          <span>Autonomous AI Agent</span>
        </div>
      </div>
      <div className="nav-actions" style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {running && (
          <span style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6, color: "var(--primary)", fontWeight: 600, marginRight: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--primary)" }} />
            Agent Running...
          </span>
        )}
        <button 
          type="button"
          className={`btn ${isHome ? "btn-primary" : "btn-secondary"}`}
          onClick={() => onNavigate("/")}
          style={{ display: "flex", alignItems: "center", gap: 6 }}
        >
          <LayoutGrid size={16} /> Jobs Feed
        </button>
        <button 
          type="button"
          className={`btn ${isResume ? "btn-primary" : "btn-secondary"}`}
          onClick={() => onNavigate("/resume")}
          style={{ display: "flex", alignItems: "center", gap: 6 }}
        >
          <FileText size={16} /> Resume
        </button>
        <button 
          type="button"
          className={`btn ${isSettings ? "btn-primary" : "btn-secondary"}`}
          onClick={() => onNavigate("/settings")}
          style={{ display: "flex", alignItems: "center", gap: 6 }}
        >
          <Settings size={16} /> Settings
        </button>
      </div>
    </nav>
  );
}
