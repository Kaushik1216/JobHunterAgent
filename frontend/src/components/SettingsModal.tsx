import { useState, useEffect } from "react";
import { X, Save, Trash2, Database } from "lucide-react";
import { api } from "../api";
import type { Settings } from "../types";

export function SettingsModal({ onClose }: { onClose: () => void }) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const allPortals = ["linkedin", "indeed", "naukri", "greenhouse", "lever", "ashby", "glassdoor", "wellfound"];

  useEffect(() => {
    api.getSettings().then(setSettings).catch(e => setMessage(e.message));
  }, []);

  if (!settings) {
    return (
      <div className="modal-overlay">
        <div className="modal-content" style={{ padding: 40, textAlign: 'center' }}>Loading Settings...</div>
      </div>
    );
  }

  const togglePortal = (p: string) => {
    setSettings(s => {
      if (!s) return s;
      const current = s.search_portals;
      if (current.includes(p)) return { ...s, search_portals: current.filter(x => x !== p) };
      return { ...s, search_portals: [...current, p] };
    });
  };

  const save = async () => {
    setSaving(true);
    setMessage("");
    try {
      const res = await api.updateSettings(settings);
      setMessage(`Settings saved! ${res.deleted_jobs > 0 ? `Deleted ${res.deleted_jobs} old jobs.` : ''}`);
      setTimeout(onClose, 2000);
    } catch (e: any) {
      setMessage(e.message || "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2><Database size={20} /> Application Settings</h2>
          <button className="btn-icon" onClick={onClose}><X size={20}/></button>
        </div>

        <div className="modal-body">
          <div className="settings-section">
            <label className="settings-label">Portals to Search</label>
            <p className="settings-hint">Select the platforms you want the agent to search across.</p>
            <div className="chips-wrap" style={{ marginTop: 8 }}>
              {allPortals.map(p => (
                <button 
                  key={p} 
                  className={`chip-toggle ${settings.search_portals.includes(p) ? 'active' : ''}`}
                  onClick={() => togglePortal(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="settings-section">
            <label className="settings-label">Job Posting Age (Search Filter)</label>
            <p className="settings-hint">Define in days how far back the agent should search for jobs.</p>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 8 }}>
              <input 
                type="number" 
                className="filter-input" 
                style={{ width: 100 }}
                value={settings.search_max_days || 7}
                onChange={e => setSettings({...settings, search_max_days: parseInt(e.target.value) || 7})}
                placeholder="Days"
              />
              <span className="text-muted" style={{ fontSize: 13 }}>e.g. 7 for past week, 30 for past month.</span>
            </div>
          </div>

          <div className="settings-section">
            <label className="settings-label">Target Companies</label>
            <p className="settings-hint">Enter target companies (comma-separated).</p>
            <textarea 
              className="filter-input" 
              rows={3}
              value={settings.companies.join(", ")}
              onChange={e => setSettings({...settings, companies: e.target.value.split(",").map(s => s.trim()).filter(Boolean)})}
              placeholder="Google, Microsoft, Amazon..."
            />
          </div>

          <div className="settings-section">
            <label className="settings-label">Database TTL (Data Retention)</label>
            <p className="settings-hint">Delete jobs older than X days completely from the database.</p>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 8 }}>
              <input 
                type="number" 
                className="filter-input" 
                style={{ width: 100 }}
                value={settings.ttl_days || ""}
                onChange={e => setSettings({...settings, ttl_days: parseInt(e.target.value) || null})}
                placeholder="Days"
              />
              <span className="text-muted" style={{ fontSize: 13 }}>Leave blank to never delete.</span>
            </div>
          </div>

          <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
            <label className="settings-label" style={{ color: 'var(--danger, #dc2626)' }}>Danger Zone</label>
            <p className="settings-hint" style={{ marginBottom: 12 }}>Permanently delete all fetched and evaluated jobs from your database.</p>
            <button 
              className="btn btn-secondary" 
              style={{ color: 'var(--danger, #dc2626)', borderColor: 'var(--danger, #dc2626)', display: 'flex', alignItems: 'center', gap: 6 }}
              onClick={async () => {
                if (confirm("Are you sure you want to delete ALL jobs? This cannot be undone.")) {
                  setSaving(true);
                  try {
                    const res = await api.deleteAllJobs();
                    setMessage(`Successfully deleted ${res.deleted} jobs.`);
                    setTimeout(() => window.location.reload(), 1500);
                  } catch (e: any) {
                    setMessage(e.message || "Failed to delete jobs");
                  } finally {
                    setSaving(false);
                  }
                }
              }}
              disabled={saving}
            >
              <Trash2 size={16} /> Delete All Jobs
            </button>
          </div>

          {message && (
            <div className={`banner ${message.includes('saved') ? 'success' : 'err'}`}>
              {message}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={save} disabled={saving} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Save size={16} /> Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
