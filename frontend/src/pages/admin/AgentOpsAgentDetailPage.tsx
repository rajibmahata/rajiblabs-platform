/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../../services/api";
import { toast } from "../../components/admin/toast";

const get = async <T,>(p: string): Promise<T | null> => {
  try { return await api.get<T>(p); } catch { return null; }
};

function relTime(iso?: string) {
  if (!iso) return "—";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(iso).toLocaleDateString();
}

function durMs(start?: string, end?: string) {
  if (!start) return "—";
  const ms = (end ? new Date(end).getTime() : Date.now()) - new Date(start).getTime();
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
}

const STATUS_COLORS: Record<string, [string, string]> = {
  success: ["var(--rla-green-soft)", "var(--rla-green)"],
  completed: ["var(--rla-green-soft)", "var(--rla-green)"],
  running: ["var(--rla-amber-soft)", "var(--rla-amber)"],
  failed: ["var(--rla-red-soft)", "var(--rla-red)"],
};

export default function AgentOpsAgentDetailPage() {
  const { slug } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [running, setRunning] = useState(false);

  const load = () => {
    if (!slug) return;
    setLoading(true);
    get<any>(`/api/admin/ops/agents/${slug}`)
      .then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [slug]);

  const doToggle = async () => {
    setToggling(true);
    try {
      const r = await api.put<any>(`/api/admin/ops/agents/${slug}/toggle`);
      toast("Updated", `${data?.name} ${r.enabled ? "enabled" : "disabled"}`);
      load();
    } catch (e) {
      toast("Failed", String(e instanceof Error ? e.message : e).slice(0, 120));
    } finally {
      setToggling(false);
    }
  };

  const doRun = async () => {
    setRunning(true);
    try {
      const r = await api.post<any>(`/api/admin/ops/agents/${slug}/run`);
      toast("Dispatched", `${data?.name} run triggered`);
      setTimeout(load, 2000);
    } catch (e) {
      toast("Failed", String(e instanceof Error ? e.message : e).slice(0, 120));
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <div className="p-6 text-center" style={{ color: "var(--rla-text-dim)" }}>Loading agent…</div>;
  if (!data) return <div className="p-6 text-center" style={{ color: "var(--rla-red)" }}>Agent not found.</div>;

  const u = data.usage_24h || {};
  const stats = data.stats || {};
  const runs: any[] = data.recent_runs || [];
  const byModel = u.by_model || {};

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <Link to="/admin/ops/summary" style={{ fontSize: 12, color: "var(--rla-violet)", textDecoration: "none" }}>
            <i className="fas fa-arrow-left" style={{ marginRight: 4 }} /> Back to Operations
          </Link>
          <h2 style={{ fontSize: 20, fontWeight: 700, margin: "6px 0 0" }}>
            <i className="fas fa-robot" style={{ marginRight: 8, color: "var(--rla-violet)" }} />
            {data.name || data.slug}
          </h2>
          <div style={{ fontSize: 13, color: "var(--rla-text-dim)", marginTop: 4 }}>
            {data.agent_type} · {data.description?.slice(0, 120) || ""}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button onClick={() => void doToggle()} disabled={toggling}
            className="rla-btn rla-btn-sm" style={{
              background: data.enabled ? "var(--rla-red-soft)" : "var(--rla-green-soft)",
              color: data.enabled ? "var(--rla-red)" : "var(--rla-green)",
              border: "none", cursor: "pointer",
            }}>
            {toggling ? "…" : data.enabled ? "Disable" : "Enable"}
          </button>
          <button onClick={() => void doRun()} disabled={running || !data.enabled}
            className="rla-btn rla-btn-primary rla-btn-sm">
            {running ? "Dispatching…" : "Run Now"}
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(160px,1fr))", gap: 12 }}>
        {[
          { label: "Calls (24h)", value: u.calls ?? 0, color: "var(--rla-violet)" },
          { label: "Tokens (24h)", value: `${((u.in_tokens ?? 0) + (u.out_tokens ?? 0)).toLocaleString()}`, color: "var(--rla-cyan)" },
          { label: "Cost (24h)", value: `$${(u.cost ?? 0).toFixed(4)}`, color: "var(--rla-green)" },
          { label: "Cache Hits", value: u.cache_hits ?? 0, color: "var(--rla-amber)" },
          { label: "LLM Calls", value: u.llm_calls ?? 0, color: "var(--rla-amber)" },
          { label: "Total Turns", value: stats.turns ?? stats.runs ?? 0, color: "var(--rla-cyan)" },
          { label: "Tool Calls", value: stats.tool_calls ?? 0, color: "var(--rla-amber)" },
          { label: "Errors", value: stats.errors ?? 0, color: "var(--rla-red)" },
        ].map((s) => (
          <div key={s.label} style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 10, padding: "12px 14px" }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 11, color: "var(--rla-text-dim)" }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Token breakdown by model */}
      {Object.keys(byModel).length > 0 && (
        <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>
            <i className="fas fa-database" style={{ marginRight: 6, color: "var(--rla-cyan)" }} /> Token Usage by Model (24h)
          </div>
          {Object.entries(byModel).map(([model, v]: [string, any]) => (
            <div key={model} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--rla-border)", fontSize: 13 }}>
              <span style={{ fontFamily: "monospace", fontSize: 12 }}>{model}</span>
              <span style={{ color: "var(--rla-text-dim)" }}>{v.calls} calls · {v.tokens.toLocaleString()} tok · ${v.cost.toFixed(4)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Recent runs */}
      <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span><i className="fas fa-clock-rotate-left" style={{ marginRight: 6, color: "var(--rla-cyan)" }} /> Recent Runs</span>
          <Link to={`/admin/ops/runs?agent=${slug}`} style={{ fontSize: 12, color: "var(--rla-violet)" }}>View all →</Link>
        </div>
        {runs.length === 0 && <div style={{ color: "var(--rla-text-faint)", fontSize: 13 }}>No runs yet.</div>}
        {runs.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {runs.map((r: any) => {
              const sc = STATUS_COLORS[r.status || ""] || STATUS_COLORS.success;
              return (
                <Link key={r.id} to={`/admin/ops/runs/${r.id}`} style={{
                  display: "grid", gridTemplateColumns: "80px 1fr 80px 80px 80px 70px",
                  alignItems: "center", gap: 10, padding: "8px 12px", borderRadius: 8,
                  border: "1px solid var(--rla-border)", textDecoration: "none", color: "inherit", fontSize: 12,
                  transition: "border-color 0.15s",
                }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--rla-violet)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--rla-border)"; }}
                >
                  <span style={{ fontSize: 10, fontWeight: 600, padding: "2px 6px", borderRadius: 6, background: sc[0], color: sc[1], textAlign: "center" }}>
                    {(r.status || "?").toUpperCase()}
                  </span>
                  <span style={{ color: "var(--rla-text-dim)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {r.triggered_by || "—"} · {r.detail || ""}
                  </span>
                  <span>{r.proposed ?? 0} prop</span>
                  <span>{r.applied ?? 0} applied</span>
                  <span>{durMs(r.started_at, r.finished_at)}</span>
                  <span style={{ color: "var(--rla-text-faint)" }}>{relTime(r.started_at)}</span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
