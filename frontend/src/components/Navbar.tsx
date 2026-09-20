import { Briefcase, Search, Play, ListTodo, Settings } from "lucide-react";

interface NavbarProps {
  running: boolean;
  unmatchedCount: number;
  onStart: (mode: "search" | "search_and_match" | "match") => void;
  onOpenSettings: () => void;
}

export function Navbar({ running, unmatchedCount, onStart, onOpenSettings }: NavbarProps) {
  return (
    <nav className="navbar">
      <div className="brand">
        <Briefcase className="brand-icon" size={28} color="var(--primary)" />
        <div>
          <h1>JobHunter</h1>
          <span>Autonomous AI Agent</span>
        </div>
      </div>
      <div className="nav-actions">
        <button className="btn btn-icon" onClick={onOpenSettings} title="Settings" style={{ marginRight: 8 }}>
          <Settings size={20} />
        </button>
        <button className="btn btn-secondary" disabled={running} onClick={() => onStart("search")}>
          <Search size={16} /> Search Only
        </button>
        <button className="btn btn-primary" disabled={running} onClick={() => onStart("search_and_match")}>
          <Play size={16} fill="currentColor" /> Search & Match
        </button>
        <button className="btn btn-secondary" disabled={running || unmatchedCount === 0} onClick={() => onStart("match")}>
          <ListTodo size={16} /> Match Backlog ({unmatchedCount})
        </button>
      </div>
    </nav>
  );
}
