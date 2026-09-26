import { useState, useEffect, useMemo } from "react";
import { 
  ArrowLeft, 
  Save, 
  Trash2, 
  Search, 
  Plus, 
  ListTodo, 
  Settings as SettingsIcon,
  Sparkles,
  Building2,
  Globe2,
  Clock,
  Database,
  Cpu,
  Cloud,
  Server,
  Key,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Eye,
  EyeOff,
  Zap
} from "lucide-react";
import { api } from "../api";
import type { Settings } from "../types";

const DEFAULT_MASTER_COMPANIES = [
  "Google", "D.E. Shaw & Co", "Sarvam AI", "Microsoft", "Tower Research Capital", "Glance",
  "Amazon", "Databricks", "Snowflake", "NVIDIA", "GitHub", "Juspay", "Qualcomm", "Stripe",
  "Zepto", "Apple", "Atlassian", "PhonePe", "AMD", "Uber", "Swiggy", "Rubrik", "LinkedIn",
  "Zomato", "Salesforce", "Coinbase", "Navi", "Adobe", "Netflix", "MakeMyTrip", "Intuit",
  "Confluent", "ServiceNow", "Airbnb", "Flipkart", "Nutanix", "Meesho", "Cohesity", "Oracle",
  "MongoDB", "Cisco", "Wells Fargo", "Walmart", "Arcesium", "Goldman Sachs", "BNY Mellon",
  "JPMorgan Chase", "PayPal", "Morgan Stanley", "Visa", "Mastercard", "Cadence", "MediaTek",
  "Palo Alto Networks", "OpenAI", "Meta", "Quadeye", "Texas Instruments"
];

interface SettingsPageProps {
  onNavigateHome: () => void;
  onStartRun: (mode: "search" | "match") => void;
  running: boolean;
  unmatchedCount: number;
}

export function SettingsPage({ onNavigateHome, onStartRun, running, unmatchedCount }: SettingsPageProps) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [companySearch, setCompanySearch] = useState("");
  const [customCompany, setCustomCompany] = useState("");
  const [showSelectedOnly, setShowSelectedOnly] = useState(false);
  const [testingModel, setTestingModel] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; latency_ms?: number; model?: string; error?: string } | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);

  const allPortals = ["linkedin", "indeed", "naukri", "greenhouse", "lever", "ashby", "glassdoor", "wellfound"];

  useEffect(() => {
    api.getSettings().then(setSettings).catch(e => setMessage(e.message));
  }, []);

  // Compute full company catalog
  const allAvailableCompanies = useMemo(() => {
    const map = new Map<string, { name: string; job_count: number }>();
    for (const c of DEFAULT_MASTER_COMPANIES) {
      map.set(c.toLowerCase(), { name: c, job_count: 0 });
    }
    if (settings?.available_companies) {
      for (const ac of settings.available_companies) {
        map.set(ac.name.toLowerCase(), { name: ac.name, job_count: ac.job_count || 0 });
      }
    }
    if (settings?.companies) {
      for (const sc of settings.companies) {
        if (!map.has(sc.toLowerCase())) {
          map.set(sc.toLowerCase(), { name: sc, job_count: 0 });
        }
      }
    }
    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' }));
  }, [settings?.available_companies, settings?.companies]);

  // Filtered companies based on search and showSelectedOnly
  const displayedCompanies = useMemo(() => {
    if (!settings) return [];
    return allAvailableCompanies.filter(c => {
      const isSelected = settings.companies.some(x => x.toLowerCase() === c.name.toLowerCase());
      if (showSelectedOnly && !isSelected) return false;
      if (companySearch.trim()) {
        return c.name.toLowerCase().includes(companySearch.toLowerCase().trim());
      }
      return true;
    });
  }, [allAvailableCompanies, settings, companySearch, showSelectedOnly]);

  if (!settings) {
    return (
      <div className="container" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading Settings...
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

  const toggleCompany = (companyName: string) => {
    setSettings(s => {
      if (!s) return s;
      const exists = s.companies.some(c => c.toLowerCase() === companyName.toLowerCase());
      if (exists) {
        return { ...s, companies: s.companies.filter(c => c.toLowerCase() !== companyName.toLowerCase()) };
      }
      return { ...s, companies: [...s.companies, companyName] };
    });
  };

  const selectAllFiltered = () => {
    setSettings(s => {
      if (!s) return s;
      const currentSet = new Set(s.companies.map(c => c.toLowerCase()));
      const newComps = [...s.companies];
      for (const dc of displayedCompanies) {
        if (!currentSet.has(dc.name.toLowerCase())) {
          currentSet.add(dc.name.toLowerCase());
          newComps.push(dc.name);
        }
      }
      return { ...s, companies: newComps };
    });
  };

  const clearAll = () => {
    setSettings(s => s ? { ...s, companies: [] } : s);
  };

  const addCustomCompany = () => {
    const trimmed = customCompany.trim();
    if (!trimmed) return;
    setSettings(s => {
      if (!s) return s;
      const exists = s.companies.some(c => c.toLowerCase() === trimmed.toLowerCase());
      if (exists) return s;
      return { ...s, companies: [...s.companies, trimmed] };
    });
    setCustomCompany("");
  };

  const handleTestModel = async () => {
    if (!settings) return;
    setTestingModel(true);
    setTestResult(null);
    try {
      const res = await api.testModel({
        base_url: settings.llm_base_url || (settings.llm_provider === "online" ? "https://api.openai.com/v1" : "http://localhost:1234/v1"),
        model: settings.llm_model || (settings.llm_provider === "online" ? "gpt-4o-mini" : "qwen2.5-7b-instruct"),
        api_key: settings.llm_api_key || "",
        provider: settings.llm_provider || "local",
      });
      setTestResult(res);
    } catch (e: any) {
      setTestResult({
        success: false,
        message: e.message || "Connection failed",
        error: e.message || "Failed to contact LLM backend",
      });
    } finally {
      setTestingModel(false);
    }
  };

  const save = async () => {
    setSaving(true);
    setMessage("");
    try {
      const res = await api.updateSettings(settings);
      setMessage(`Settings saved! ${res.deleted_jobs > 0 ? `Deleted ${res.deleted_jobs} old jobs.` : ''}`);
      setTimeout(() => setMessage(""), 3500);
    } catch (e: any) {
      setMessage(e.message || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container" style={{ display: 'block', maxWidth: 960, margin: '24px auto', padding: '0 20px' }}>
      {/* Top Navigation / Breadcrumb */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <button 
          className="btn btn-secondary" 
          onClick={onNavigateHome}
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <ArrowLeft size={16} /> Back to Jobs Feed
        </button>
        <button 
          className="btn btn-primary" 
          onClick={save} 
          disabled={saving}
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Save size={16} /> {saving ? "Saving..." : "Save Settings"}
        </button>
      </div>

      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid var(--border)', padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        
        {/* Page Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingBottom: 16, borderBottom: '1px solid var(--border)', marginBottom: 24 }}>
          <SettingsIcon size={24} color="var(--primary)" />
          <div>
            <h2 style={{ margin: 0, fontSize: 20, color: 'var(--text-main)' }}>Settings & Discovery Controls</h2>
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Configure LLM inference model, search targets, active portals, and discovery controls.</span>
          </div>
        </div>

        {/* SECTION 1: LLM INFERENCE MODEL CONFIGURATION */}
        <div className="settings-section" style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 10, padding: 20, marginBottom: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12, marginBottom: 12 }}>
            <div>
              <label className="settings-label" style={{ fontSize: 16, display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <Cpu size={18} color="var(--primary)" /> LLM Model Source & Provider
              </label>
              <p className="settings-hint" style={{ margin: 0 }}>
                Select between a Local LLM (LM Studio / Ollama) or an Online API (OpenAI / Groq / OpenRouter).
              </p>
            </div>

            {/* Provider Toggle Pill (Local vs Online) */}
            <div style={{ display: 'inline-flex', padding: 3, background: 'var(--bg-subtle, #f1f5f9)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <button
                type="button"
                onClick={() => {
                  setSettings(s => s ? {
                    ...s,
                    llm_provider: 'local',
                    llm_base_url: s.llm_base_url && s.llm_base_url.includes('http://localhost') ? s.llm_base_url : 'http://localhost:1234/v1',
                    llm_model: s.llm_model && !s.llm_model.startsWith('gpt-') ? s.llm_model : 'qwen2.5-7b-instruct',
                  } : s);
                  setTestResult(null);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 14px',
                  borderRadius: 6,
                  border: 'none',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: (settings.llm_provider || 'local') === 'local' ? '#fff' : 'transparent',
                  color: (settings.llm_provider || 'local') === 'local' ? 'var(--primary, #4338ca)' : 'var(--text-muted)',
                  boxShadow: (settings.llm_provider || 'local') === 'local' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                <Server size={14} /> Local Model
              </button>
              <button
                type="button"
                onClick={() => {
                  setSettings(s => s ? {
                    ...s,
                    llm_provider: 'online',
                    llm_base_url: s.llm_base_url && s.llm_base_url.startsWith('https://') ? s.llm_base_url : 'https://api.openai.com/v1',
                    llm_model: s.llm_model && s.llm_model.startsWith('gpt-') ? s.llm_model : 'gpt-4o-mini',
                  } : s);
                  setTestResult(null);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 14px',
                  borderRadius: 6,
                  border: 'none',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: settings.llm_provider === 'online' ? '#fff' : 'transparent',
                  color: settings.llm_provider === 'online' ? 'var(--primary, #4338ca)' : 'var(--text-muted)',
                  boxShadow: settings.llm_provider === 'online' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                <Cloud size={14} /> Online API
              </button>
            </div>
          </div>

          {/* Quick Presets */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', margin: '14px 0 16px 0', padding: '10px 12px', background: 'var(--bg-subtle, #f8fafc)', borderRadius: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Quick Presets:</span>
            {(settings.llm_provider || 'local') === 'local' ? (
              <>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4 }}
                  onClick={() => setSettings(s => s ? { ...s, llm_base_url: 'http://localhost:1234/v1', llm_model: 'qwen2.5-7b-instruct' } : s)}
                >
                  LM Studio (1234)
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4 }}
                  onClick={() => setSettings(s => s ? { ...s, llm_base_url: 'http://localhost:11434/v1', llm_model: 'qwen2.5:7b' } : s)}
                >
                  Ollama v1 (11434)
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4 }}
                  onClick={() => setSettings(s => s ? { ...s, llm_base_url: 'https://api.openai.com/v1', llm_model: 'gpt-4o-mini' } : s)}
                >
                  OpenAI (gpt-4o-mini)
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4 }}
                  onClick={() => setSettings(s => s ? { ...s, llm_base_url: 'https://api.groq.com/openai/v1', llm_model: 'llama-3.3-70b-versatile' } : s)}
                >
                  Groq (llama-3.3)
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4 }}
                  onClick={() => setSettings(s => s ? { ...s, llm_base_url: 'https://openrouter.ai/api/v1', llm_model: 'meta-llama/llama-3.3-70b-instruct' } : s)}
                >
                  OpenRouter
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4 }}
                  onClick={() => setSettings(s => s ? { ...s, llm_base_url: 'https://api.deepseek.com/v1', llm_model: 'deepseek-chat' } : s)}
                >
                  DeepSeek
                </button>
              </>
            )}
          </div>

          {/* Form Fields: Grid Layout */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
            {/* Model Name */}
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-main)', marginBottom: 6 }}>
                Model Name
              </label>
              <input
                type="text"
                className="filter-input"
                style={{ width: '100%' }}
                placeholder={(settings.llm_provider || 'local') === 'local' ? 'e.g. qwen2.5-7b-instruct' : 'e.g. gpt-4o-mini'}
                value={settings.llm_model || ''}
                onChange={e => setSettings({ ...settings, llm_model: e.target.value })}
              />
              <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginTop: 4 }}>
                {(settings.llm_provider || 'local') === 'local' ? 'Model identifier in local server' : 'Model name for the online API'}
              </span>
            </div>

            {/* Base URL */}
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-main)', marginBottom: 6 }}>
                Base URL Endpoint
              </label>
              <input
                type="text"
                className="filter-input"
                style={{ width: '100%' }}
                placeholder={(settings.llm_provider || 'local') === 'local' ? 'http://localhost:1234/v1' : 'https://api.openai.com/v1'}
                value={settings.llm_base_url || ''}
                onChange={e => setSettings({ ...settings, llm_base_url: e.target.value })}
              />
              <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginTop: 4 }}>
                OpenAI-compatible `/chat/completions` endpoint
              </span>
            </div>

            {/* API Key */}
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, color: 'var(--text-main)', marginBottom: 6 }}>
                <Key size={14} /> API Key {(settings.llm_provider || 'local') === 'local' ? '(Optional for local)' : '(Required for online API)'}
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showApiKey ? 'text' : 'password'}
                  className="filter-input"
                  style={{ width: '100%', paddingRight: 40 }}
                  placeholder={(settings.llm_provider || 'local') === 'local' ? 'Optional (e.g. lm-studio or leave blank)' : 'sk-... or API key token'}
                  value={settings.llm_api_key || ''}
                  onChange={e => setSettings({ ...settings, llm_api_key: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  style={{
                    position: 'absolute',
                    right: 8,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    padding: 4,
                  }}
                  title={showApiKey ? 'Hide API Key' : 'Show API Key'}
                >
                  {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          </div>

          {/* Test Model Connection Action */}
          <div style={{ marginTop: 18, paddingTop: 14, borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleTestModel}
              disabled={testingModel || !settings.llm_model?.trim() || !settings.llm_base_url?.trim()}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontWeight: 600,
                color: 'var(--primary, #4338ca)',
                borderColor: 'var(--primary, #4338ca)',
                background: testingModel ? '#f1f5f9' : '#fff',
              }}
            >
              {testingModel ? <Loader2 size={16} className="spin" /> : <Zap size={16} />}
              {testingModel ? 'Testing Connection...' : 'Test Model Connection'}
            </button>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {testingModel && (settings.llm_provider === "local" || settings.llm_base_url?.includes("localhost") || settings.llm_base_url?.includes("127.0.0.1"))
                ? "Connecting to local server... Waiting for model weights to load into VRAM/RAM (this may take 30-60s on first load)."
                : "Verifies endpoint connectivity, authentication, and model availability."}
            </span>
          </div>

          {/* Test Result Feedback Banner */}
          {testResult && (
            <div
              style={{
                marginTop: 14,
                padding: '12px 16px',
                borderRadius: 8,
                display: 'flex',
                alignItems: 'flex-start',
                gap: 12,
                background: testResult.success ? '#ecfdf5' : '#fef2f2',
                border: `1px solid ${testResult.success ? '#a7f3d0' : '#fecaca'}`,
                color: testResult.success ? '#065f46' : '#991b1b',
              }}
            >
              {testResult.success ? (
                <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: 2 }} />
              ) : (
                <AlertCircle size={20} color="#dc2626" style={{ flexShrink: 0, marginTop: 2 }} />
              )}
              <div style={{ fontSize: 13, lineHeight: 1.4, flex: 1 }}>
                <div style={{ fontWeight: 600, marginBottom: 2 }}>
                  {testResult.success ? 'Model Connection Verified' : 'Model Connection Failed'}
                  {testResult.latency_ms !== undefined && (
                    <span style={{ marginLeft: 8, fontSize: 11, padding: '1px 6px', borderRadius: 4, background: '#d1fae5', color: '#047857' }}>
                      {testResult.latency_ms} ms
                    </span>
                  )}
                </div>
                <div>{testResult.message}</div>
                {testResult.error && (
                  <div style={{ marginTop: 4, fontFamily: 'monospace', fontSize: 12, color: '#b91c1c' }}>
                    {testResult.error}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* SECTION 2: EXECUTION CONTROLS (SEARCH & MATCH OPTIONS) */}
        <div className="settings-section" style={{ background: 'var(--bg-subtle, #f8fafc)', border: '1px solid var(--border)', borderRadius: 10, padding: 16 }}>
          <label className="settings-label" style={{ fontSize: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Sparkles size={18} color="var(--primary)" /> Job Discovery & AI Matching
          </label>
          <p className="settings-hint">Trigger search or matching runs independently across your configured parameters.</p>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginTop: 12 }}>
            {/* Option 1: Search Only */}
            <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 8, padding: 16, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, color: 'var(--text-main)', marginBottom: 6 }}>
                  <Search size={16} color="var(--primary)" /> Option 1: Search for Jobs
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                  Scan enabled portals for open roles across your selected target companies and store newly found jobs into your database.
                </p>
              </div>
              <button 
                type="button"
                className="btn btn-primary" 
                disabled={running} 
                onClick={() => onStartRun("search")}
                style={{ marginTop: 14, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
              >
                <Search size={16} /> {running ? "Agent Running..." : "Run Search Now"}
              </button>
            </div>

            {/* Option 2: Separate Match Option */}
            <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 8, padding: 16, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, color: 'var(--text-main)' }}>
                    <ListTodo size={16} color="#059669" /> Option 2: Separate Match Option
                  </div>
                  <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, background: unmatchedCount > 0 ? '#ecfdf5' : '#f1f5f9', color: unmatchedCount > 0 ? '#059669' : 'var(--text-muted)', fontWeight: 600 }}>
                    {unmatchedCount} Pending
                  </span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                  Run LLM inference on discovered jobs to extract skills, evaluate experience requirements, and compute accurate fit scores.
                </p>
              </div>
              <button 
                type="button"
                className="btn btn-secondary" 
                disabled={running || unmatchedCount === 0} 
                onClick={() => onStartRun("match")}
                style={{ marginTop: 14, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
              >
                <ListTodo size={16} /> {running ? "Agent Running..." : `Match Backlog (${unmatchedCount})`}
              </button>
            </div>
          </div>
        </div>

        {/* SECTION 2: TARGET COMPANIES */}
        <div className="settings-section" style={{ marginTop: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 4 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <label className="settings-label" style={{ marginBottom: 0, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Building2 size={16} /> Target Companies
              </label>
              <span style={{ fontSize: 12, padding: '2px 8px', borderRadius: 12, background: 'var(--primary-light, #e0e7ff)', color: 'var(--primary, #4338ca)', fontWeight: 600 }}>
                {settings.companies.length} Selected
              </span>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: 12, padding: '3px 8px' }}
                onClick={selectAllFiltered}
              >
                Select All
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: 12, padding: '3px 8px' }}
                onClick={clearAll}
              >
                Clear All
              </button>
              <button
                type="button"
                className={`btn ${showSelectedOnly ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: 12, padding: '3px 8px' }}
                onClick={() => setShowSelectedOnly(!showSelectedOnly)}
              >
                {showSelectedOnly ? "Show All" : `Selected Only (${settings.companies.length})`}
              </button>
            </div>
          </div>
          <p className="settings-hint">Choose which companies the agent will search. All companies are stored in your database.</p>

          {/* Search & Custom Add Bar */}
          <div style={{ display: 'flex', gap: 8, margin: '12px 0', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', flex: '1 1 240px' }}>
              <Search size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                className="filter-input"
                style={{ paddingLeft: 32 }}
                placeholder="Search companies..."
                value={companySearch}
                onChange={e => setCompanySearch(e.target.value)}
              />
              {companySearch && (
                <button
                  type="button"
                  onClick={() => setCompanySearch("")}
                  style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
                >
                  ×
                </button>
              )}
            </div>
            <div style={{ display: 'flex', gap: 6, flex: '1 1 240px' }}>
              <input
                type="text"
                className="filter-input"
                placeholder="Add custom company..."
                value={customCompany}
                onChange={e => setCustomCompany(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addCustomCompany(); } }}
              />
              <button
                type="button"
                className="btn btn-secondary"
                style={{ display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap' }}
                onClick={addCustomCompany}
              >
                <Plus size={14} /> Add
              </button>
            </div>
          </div>

          {/* Clickable Company Chips Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))',
              gap: 6,
              maxHeight: 260,
              overflowY: 'auto',
              padding: '10px',
              background: 'var(--bg-subtle, #f8fafc)',
              borderRadius: 8,
              border: '1px solid var(--border)'
            }}
          >
            {displayedCompanies.map(c => {
              const isSelected = settings.companies.some(x => x.toLowerCase() === c.name.toLowerCase());
              return (
                <button
                  type="button"
                  key={c.name}
                  className={`chip-toggle ${isSelected ? 'active' : ''}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '6px 10px',
                    fontSize: 12,
                    width: '100%',
                    textAlign: 'left',
                    borderRadius: 6,
                  }}
                  onClick={() => toggleCompany(c.name)}
                >
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {isSelected ? "✓ " : ""}{c.name}
                  </span>
                  {c.job_count > 0 && (
                    <span style={{
                      fontSize: 10,
                      padding: '1px 5px',
                      borderRadius: 10,
                      background: isSelected ? 'rgba(255,255,255,0.3)' : 'var(--border)',
                      color: isSelected ? '#fff' : 'var(--text-muted)',
                      fontWeight: 600,
                      marginLeft: 6
                    }}>
                      {c.job_count}
                    </span>
                  )}
                </button>
              );
            })}
            {displayedCompanies.length === 0 && (
              <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>
                No companies match "{companySearch}". Click "Add" above to add it!
              </div>
            )}
          </div>
        </div>

        {/* SECTION 3: PORTALS */}
        <div className="settings-section" style={{ marginTop: 24 }}>
          <label className="settings-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Globe2 size={16} /> Portals to Search
          </label>
          <p className="settings-hint">Select the platforms you want the agent to search across.</p>
          <div className="chips-wrap" style={{ marginTop: 8 }}>
            {allPortals.map(p => (
              <button 
                key={p} 
                type="button"
                className={`chip-toggle ${settings.search_portals.includes(p) ? 'active' : ''}`}
                onClick={() => togglePortal(p)}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* SECTION 4: AGE & RETENTION */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 20, marginTop: 24 }}>
          <div className="settings-section" style={{ margin: 0 }}>
            <label className="settings-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Clock size={16} /> Job Posting Age (Days)
            </label>
            <p className="settings-hint">How far back the agent should search for jobs.</p>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 8 }}>
              <input 
                type="number" 
                className="filter-input" 
                style={{ width: 100 }}
                value={settings.search_max_days || 7}
                onChange={e => setSettings({...settings, search_max_days: parseInt(e.target.value) || 7})}
                placeholder="Days"
              />
              <span className="text-muted" style={{ fontSize: 12 }}>e.g. 7 (week), 30 (month)</span>
            </div>
          </div>

          <div className="settings-section" style={{ margin: 0 }}>
            <label className="settings-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Database size={16} /> Database TTL Retention
            </label>
            <p className="settings-hint">Delete jobs older than X days from database.</p>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 8 }}>
              <input 
                type="number" 
                className="filter-input" 
                style={{ width: 100 }}
                value={settings.ttl_days || ""}
                onChange={e => setSettings({...settings, ttl_days: parseInt(e.target.value) || null})}
                placeholder="Days"
              />
              <span className="text-muted" style={{ fontSize: 12 }}>Leave blank to keep forever</span>
            </div>
          </div>
        </div>

        {/* SECTION 5: DANGER ZONE */}
        <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: 20, marginTop: 28 }}>
          <label className="settings-label" style={{ color: 'var(--danger, #dc2626)' }}>Danger Zone</label>
          <p className="settings-hint" style={{ marginBottom: 12 }}>Permanently delete all fetched and evaluated jobs from your database.</p>
          <button 
            type="button"
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
          <div className={`banner ${message.includes('saved') ? 'success' : 'err'}`} style={{ marginTop: 16 }}>
            {message}
          </div>
        )}

        {/* Footer Save Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
          <button type="button" className="btn btn-secondary" onClick={onNavigateHome}>Back to Jobs</button>
          <button type="button" className="btn btn-primary" onClick={save} disabled={saving} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Save size={16} /> {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      </div>
    </div>
  );
}
