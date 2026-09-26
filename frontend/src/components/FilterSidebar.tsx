import { useState, useMemo } from "react";
import { 
  Filter, 
  RotateCcw, 
  Search, 
  X, 
  Sparkles, 
  CheckCircle2, 
  Clock, 
  Building2, 
  MapPin, 
  Globe2, 
  SlidersHorizontal 
} from "lucide-react";
import type { FilterOptions, JobQuery } from "../types";

interface Props {
  query: JobQuery;
  setQuery: (q: JobQuery) => void;
  options: FilterOptions | null;
  defaultQuery: JobQuery;
}

export function FilterSidebar({ query, setQuery, options, defaultQuery }: Props) {
  const [companySearch, setCompanySearch] = useState("");
  const [showAllCompanies, setShowAllCompanies] = useState(false);

  // Calculate number of active filters
  const activeCount = useMemo(() => {
    let count = 0;
    if (query.q.trim()) count++;
    if (query.company.length > 0) count++;
    if (query.portal.length > 0) count++;
    if (query.status && query.status.length > 0) count++;
    if (query.location.length > 0) count++;
    if (query.max_days !== "") count++;
    if (query.minFit > 0) count++;
    if (query.evaluated) count++;
    if (query.yoeMatch) count++;
    return count;
  }, [query]);

  // Filter companies by search
  const displayedCompanies = useMemo(() => {
    const all = options?.companies ?? [];
    if (!companySearch.trim()) {
      if (showAllCompanies) return all;
      // Show selected companies first, then first 10
      const selected = all.filter(c => query.company.includes(c));
      const unselected = all.filter(c => !query.company.includes(c)).slice(0, 10);
      return Array.from(new Set([...selected, ...unselected]));
    }
    return all.filter(c => c.toLowerCase().includes(companySearch.toLowerCase().trim()));
  }, [options?.companies, query.company, companySearch, showAllCompanies]);

  const allStatuses = ["NEW", "APPLIED", "SKIPPED", "ARCHIVED", "DISCOVERED"];

  return (
    <aside className="sidebar" style={{ maxHeight: "calc(100vh - 100px)", overflowY: "auto" }}>
      {/* Header with Active Filters Count & Reset */}
      <div 
        style={{ 
          display: "flex", 
          justifyContent: "space-between", 
          alignItems: "center", 
          marginBottom: 18, 
          paddingBottom: 12, 
          borderBottom: "1px solid var(--border)" 
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <SlidersHorizontal size={18} color="var(--primary)" />
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: "var(--text-main)", textTransform: "none" }}>
            Filters
          </h3>
          {activeCount > 0 && (
            <span 
              style={{ 
                fontSize: 11, 
                fontWeight: 700, 
                padding: "2px 7px", 
                borderRadius: 10, 
                background: "var(--primary-light, #e0e7ff)", 
                color: "var(--primary, #4338ca)" 
              }}
            >
              {activeCount}
            </span>
          )}
        </div>
        {activeCount > 0 && (
          <button 
            type="button" 
            onClick={() => setQuery(defaultQuery)}
            style={{ 
              background: "none", 
              border: "none", 
              color: "var(--primary)", 
              fontSize: 12, 
              cursor: "pointer", 
              fontWeight: 600,
              padding: 0 
            }}
          >
            Clear all
          </button>
        )}
      </div>

      {/* 1. Global Keyword Search */}
      <div className="filter-group">
        <label className="filter-label" style={{ fontWeight: 600, color: "var(--text-main)" }}>
          Keyword Search
        </label>
        <div style={{ position: "relative" }}>
          <Search size={15} style={{ position: "absolute", top: 10, left: 10, color: "var(--text-muted)" }} />
          <input 
            className="filter-input" 
            style={{ paddingLeft: 32, paddingRight: query.q ? 28 : 12 }}
            placeholder="Role, skills, company, description..." 
            value={query.q}
            onChange={e => setQuery({ ...query, q: e.target.value })}
          />
          {query.q && (
            <button
              type="button"
              onClick={() => setQuery({ ...query, q: "" })}
              style={{
                position: "absolute",
                right: 8,
                top: "50%",
                transform: "translateY(-50%)",
                background: "none",
                border: "none",
                color: "var(--text-muted)",
                cursor: "pointer",
                padding: 2,
              }}
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* 2. AI Evaluation Match Status */}
      <div className="filter-group">
        <label className="filter-label" style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 600, color: "var(--text-main)" }}>
          <Sparkles size={14} color="var(--primary)" /> AI Match Status
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6, marginTop: 4 }}>
          <button
            type="button"
            className={`chip-toggle ${query.evaluated === "" ? "active" : ""}`}
            style={{ textAlign: "center", padding: "6px 4px", fontSize: 12 }}
            onClick={() => setQuery({ ...query, evaluated: "" })}
          >
            All
          </button>
          <button
            type="button"
            className={`chip-toggle ${query.evaluated === "true" ? "active" : ""}`}
            style={{ textAlign: "center", padding: "6px 4px", fontSize: 12 }}
            onClick={() => setQuery({ ...query, evaluated: "true" })}
          >
            Matched
          </button>
          <button
            type="button"
            className={`chip-toggle ${query.evaluated === "false" ? "active" : ""}`}
            style={{ textAlign: "center", padding: "6px 4px", fontSize: 12 }}
            onClick={() => setQuery({ ...query, evaluated: "false" })}
          >
            New
          </button>
        </div>
      </div>

      {/* 3. Job Status Filter */}
      <div className="filter-group">
        <label className="filter-label" style={{ fontWeight: 600, color: "var(--text-main)" }}>
          Application Status
        </label>
        <div className="chips-wrap">
          {allStatuses.map(status => {
            const isSelected = (query.status || []).includes(status);
            return (
              <button
                key={status}
                type="button"
                className={`chip-toggle ${isSelected ? "active" : ""}`}
                onClick={() => {
                  const current = query.status || [];
                  const next = isSelected 
                    ? current.filter(s => s !== status) 
                    : [...current, status];
                  setQuery({ ...query, status: next });
                }}
              >
                {status}
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Minimum Fit Score Slider & Presets */}
      <div className="filter-group">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
          <label className="filter-label" style={{ margin: 0, fontWeight: 600, color: "var(--text-main)" }}>
            Minimum Fit Score
          </label>
          <span style={{ fontSize: 13, fontWeight: 700, color: "var(--primary)" }}>
            {(query.minFit * 100).toFixed(0)}%
          </span>
        </div>
        <input 
          type="range" 
          style={{ width: "100%", accentColor: "var(--primary)" }}
          min={0} 
          max={1} 
          step={0.05} 
          value={query.minFit}
          onChange={e => setQuery({ ...query, minFit: Number(e.target.value) })}
        />
        <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
          {[
            { label: "Any", val: 0 },
            { label: "60%+", val: 0.6 },
            { label: "75%+", val: 0.75 },
            { label: "85%+", val: 0.85 },
          ].map(p => (
            <button
              key={p.label}
              type="button"
              className={`chip-toggle ${query.minFit === p.val ? "active" : ""}`}
              style={{ fontSize: 11, padding: "3px 8px" }}
              onClick={() => setQuery({ ...query, minFit: p.val })}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* 5. Experience (YOE) Match Toggle */}
      <div className="filter-group">
        <label 
          style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: 8, 
            fontSize: 13, 
            cursor: "pointer", 
            color: "var(--text-main)",
            userSelect: "none"
          }}
        >
          <input
            type="checkbox"
            checked={query.yoeMatch === "true"}
            onChange={e => setQuery({ ...query, yoeMatch: e.target.checked ? "true" : "" })}
            style={{ accentColor: "var(--primary)", width: 16, height: 16 }}
          />
          <span style={{ fontWeight: 500 }}>Matches My Experience Target Only</span>
        </label>
      </div>

      {/* 6. Company Multi-Select with Search */}
      <div className="filter-group">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
          <label className="filter-label" style={{ margin: 0, display: "flex", alignItems: "center", gap: 6, fontWeight: 600, color: "var(--text-main)" }}>
            <Building2 size={14} /> Companies ({query.company.length ? `${query.company.length} selected` : "All"})
          </label>
          {query.company.length > 0 && (
            <button
              type="button"
              onClick={() => setQuery({ ...query, company: [] })}
              style={{ background: "none", border: "none", color: "var(--primary)", fontSize: 11, cursor: "pointer", padding: 0 }}
            >
              Clear
            </button>
          )}
        </div>

        {/* Mini Search for companies */}
        {(options?.companies?.length ?? 0) > 6 && (
          <input
            type="text"
            className="filter-input"
            style={{ fontSize: 12, padding: "5px 10px", marginBottom: 8 }}
            placeholder="Search company..."
            value={companySearch}
            onChange={e => setCompanySearch(e.target.value)}
          />
        )}

        <div className="chips-wrap" style={{ maxHeight: showAllCompanies ? 260 : 130, overflowY: "auto", padding: 2 }}>
          {displayedCompanies.map(c => {
            const isSelected = query.company.includes(c);
            return (
              <button
                key={c}
                type="button"
                className={`chip-toggle ${isSelected ? "active" : ""}`}
                onClick={() => {
                  const next = isSelected
                    ? query.company.filter(x => x !== c)
                    : [...query.company, c];
                  setQuery({ ...query, company: next });
                }}
              >
                {c}
              </button>
            );
          })}
        </div>

        {!companySearch && (options?.companies?.length ?? 0) > 10 && (
          <button
            type="button"
            onClick={() => setShowAllCompanies(!showAllCompanies)}
            style={{
              background: "none",
              border: "none",
              color: "var(--primary)",
              fontSize: 11,
              fontWeight: 600,
              cursor: "pointer",
              marginTop: 6,
              padding: 0,
            }}
          >
            {showAllCompanies ? "Show Less" : `+ Show All (${options?.companies.length})`}
          </button>
        )}
      </div>

      {/* 7. Portal Filter */}
      {options?.portals && options.portals.length > 0 && (
        <div className="filter-group">
          <label className="filter-label" style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 600, color: "var(--text-main)" }}>
            <Globe2 size={14} /> Portal Source
          </label>
          <div className="chips-wrap">
            {options.portals.map(p => {
              const isSelected = query.portal.includes(p);
              return (
                <button
                  key={p}
                  type="button"
                  className={`chip-toggle ${isSelected ? "active" : ""}`}
                  onClick={() => {
                    const next = isSelected
                      ? query.portal.filter(x => x !== p)
                      : [...query.portal, p];
                    setQuery({ ...query, portal: next });
                  }}
                >
                  {p}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* 8. Location Filter */}
      {options?.locations && options.locations.length > 0 && (
        <div className="filter-group">
          <label className="filter-label" style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 600, color: "var(--text-main)" }}>
            <MapPin size={14} /> Location
          </label>
          <div className="chips-wrap" style={{ maxHeight: 120, overflowY: "auto" }}>
            {options.locations.map(loc => {
              const isSelected = query.location.includes(loc);
              return (
                <button
                  key={loc}
                  type="button"
                  className={`chip-toggle ${isSelected ? "active" : ""}`}
                  onClick={() => {
                    const next = isSelected
                      ? query.location.filter(x => x !== loc)
                      : [...query.location, loc];
                    setQuery({ ...query, location: next });
                  }}
                >
                  {loc}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* 9. Max Job Age */}
      <div className="filter-group">
        <label className="filter-label" style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 600, color: "var(--text-main)" }}>
          <Clock size={14} /> Posting Recency
        </label>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 6 }}>
          {[
            { label: "Any", val: "" },
            { label: "24h", val: 1 },
            { label: "3d", val: 3 },
            { label: "7d", val: 7 },
            { label: "30d", val: 30 },
          ].map(item => (
            <button
              key={item.label}
              type="button"
              className={`chip-toggle ${query.max_days === item.val ? "active" : ""}`}
              style={{ fontSize: 11, padding: "3px 8px" }}
              onClick={() => setQuery({ ...query, max_days: item.val as number | "" })}
            >
              {item.label}
            </button>
          ))}
        </div>
        <input 
          type="number" 
          className="filter-input" 
          placeholder="Custom days ago (e.g. 14)" 
          value={query.max_days}
          onChange={e => setQuery({ ...query, max_days: e.target.value === "" ? "" : Number(e.target.value) })}
        />
      </div>

      {/* Reset Filters Full Button */}
      <button 
        type="button"
        className="btn btn-secondary" 
        style={{ 
          width: "100%", 
          display: "flex", 
          alignItems: "center", 
          justifyContent: "center", 
          gap: 8, 
          marginTop: 8 
        }} 
        onClick={() => setQuery(defaultQuery)}
      >
        <RotateCcw size={15} /> Reset All Filters
      </button>
    </aside>
  );
}
