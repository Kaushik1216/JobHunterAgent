import { Filter, RotateCcw, Search } from "lucide-react";
import type { FilterOptions, JobQuery, JobStatus } from "../types";

interface Props {
  query: JobQuery;
  setQuery: (q: JobQuery) => void;
  options: FilterOptions | null;
  defaultQuery: JobQuery;
}

export function FilterSidebar({ query, setQuery, options, defaultQuery }: Props) {
  return (
    <aside className="sidebar">
      <div className="filter-group">
        <h3>Global Search</h3>
        <div style={{ position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', top: 10, left: 10, color: 'var(--text-muted)' }} />
          <input 
            className="filter-input" 
            style={{ paddingLeft: 34 }}
            placeholder="Role, skills, company..." 
            value={query.q}
            onChange={e => setQuery({...query, q: e.target.value})}
          />
        </div>
      </div>

      <FilterGroup label="Company" opts={options?.companies ?? []} selected={query.company} onChange={v => setQuery({...query, company: v})} />
      <FilterGroup label="Location" opts={options?.locations ?? []} selected={query.location} onChange={v => setQuery({...query, location: v})} />
      <FilterGroup label="Portal" opts={options?.portals ?? []} selected={query.portal} onChange={v => setQuery({...query, portal: v})} />

      <div className="filter-group">
        <label className="filter-label">Max Job Age (Days)</label>
        <input 
          type="number" 
          className="filter-input" 
          placeholder="e.g. 7" 
          value={query.max_days}
          onChange={e => setQuery({...query, max_days: e.target.value === "" ? "" : Number(e.target.value)})}
        />
      </div>

      <div className="filter-group">
        <label className="filter-label">Minimum Fit Score: {(query.minFit * 100).toFixed(0)}%</label>
        <input 
          type="range" style={{ width: '100%' }}
          min={0} max={1} step={0.05} 
          value={query.minFit}
          onChange={e => setQuery({...query, minFit: Number(e.target.value)})}
        />
      </div>

      <button className="btn btn-secondary" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }} onClick={() => setQuery(defaultQuery)}>
        <RotateCcw size={16} /> Reset Filters
      </button>
    </aside>
  );
}

function FilterGroup({ label, opts, selected, onChange }: { label: string, opts: string[], selected: string[], onChange: (v: string[]) => void }) {
  if (!opts || opts.length === 0) return null;
  return (
    <div className="filter-group">
      <h3>{label}</h3>
      <div className="chips-wrap">
        {opts.map(opt => (
          <button 
            key={opt} 
            className={`chip-toggle ${selected.includes(opt) ? 'active' : ''}`}
            onClick={() => {
              if (selected.includes(opt)) onChange(selected.filter(x => x !== opt));
              else onChange([...selected, opt]);
            }}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}
