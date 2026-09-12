import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../../services/api";

interface AgentDetail { slug: string; name: string; agent_type: string; enabled: boolean; public_enabled: boolean; description: string; stats: Record<string, number>; usage_24h: { calls: number; tokens: number; cost_usd: number; cache_hits: number }; recent_runs: Run[] }
interface Run { id: string; status: string; triggered_by?: string; started_at?: string; finished_at?: string; results?: Record<string, any> }

function relativeTime(iso?: string) {
  if (!iso) return "";
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString();
}

export default function AgentOpsAgentDetailPage() {
  const { slug } = useParams();
  const [data, setData] = useState<AgentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    api.get<AgentDetail>(`/api/admin/ops/agents/${slug}`)
      .then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <div className="p-6 text-center text-[var(--rla-text-dim)]">Loading agent detail…</div>;
  if (!data) return <div className="p-6 text-center text-[var(--rla-red)]">Agent not found.</div>;

  const u24 = data.usage_24h || {};
  const stats = data.stats || {};

  const statCards = [
    { label: "Calls (24h)", value: u24.calls ?? 0, icon: "fas fa-bolt", color: "var(--rla-violet)" },
    { label: "Tokens (24h)", value: (u24.tokens ?? 0).toLocaleString(), icon: "fas fa-database", color: "var(--rla-cyan)" },
    { label: "Cost (24h)", value: `$${(u24.cost_usd ?? 0).toFixed(4)}`, icon: "fas fa-dollar-sign", color: "var(--rla-green)" },
    { label: "Cache Hits (24h)", value: u24.cache_hits ?? 0, icon: "fas fa-bolt", color: "var(--rla-amber)" },
    { label: "Total Turns", value: stats.turns ?? stats.runs ?? 0, icon: "fas fa-repeat", color: "var(--rla-cyan)" },
    { label: "Tool Calls", value: stats.tool_calls ?? 0, icon: "fas fa-wrench", color: "var(--rla-amber)" },
    { label: "Leads Captured", value: stats.leads ?? 0, icon: "fas fa-user-plus", color: "var(--rla-green)" },
    { label: "Errors", value: stats.errors ?? 0, icon: "fas fa-triangle-exclamation", color: "var(--rla-red)" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
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
          <span style={{
            fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 99,
            background: data.enabled ? "var(--rla-green-soft)" : "var(--rla-red-soft)",
            color: data.enabled ? "var(--rla-green)" : "var(--rla-red)",
          }}>{data.enabled ? "Enabled" : "Disabled"}</span>
          {data.public_enabled && (
            <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 99, background: "var(--rla-cyan-soft)", color: "var(--rla-cyan)" }}>Public</span>
          )}
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(170px,1fr))", gap: 14 }}>
        {statCards.map((s) => (
          <div key={s.label} style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: "14px 16px", display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 36, height: 36, borderRadius: 9, display: "flex", alignItems: "center", justifyContent: "center", background: `${s.color}12`, color: s.color, fontSize: 15 }}>
              <i className={s.icon} />
            </div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{s.value}</div>
              <div style={{ fontSize: 11, color: "var(--rla-text-dim)" }}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent runs */}
      <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
          <i className="fas fa-clock-rotate-left" style={{ marginRight: 6, color: "var(--rla-cyan)" }} />
          Recent Runs
        </div>
        {data.recent_runs.length === 0 && <div style={{ color: "var(--rla-text-faint)", fontSize: 13 }}>No runs recorded yet for this agent.</div>}
        {data.recent_runs.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {data.recent_runs.map((r) => (
              <div key={r.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: "1px solid var(--rla-border)" }}>
                <span style={{
                  width: 8, height: 8, borderRadius: 99,
                  background: r.status === "success" ? "var(--rla-green)" : r.status === "running" ? "var(--rla-amber)" : "var(--rla-red)",
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{r.triggered_by || "—"}</div>
                  <div style={{ fontSize: 11, color: "var(--rla-text-faint)" }}>{relativeTime(r.started_at)}</div>
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 6,
                  background: r.status === "success" ? "var(--rla-green-soft)" : r.status === "running" ? "var(--rla-amber-soft)" : "var(--rla-red-soft)",
                  color: r.status === "success" ? "var(--rla-green)" : r.status === "running" ? "var(--rla-amber)" : "var(--rla-red)",
                }}>{r.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Config summary */}
      <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
          <i className="fas fa-gear" style={{ marginRight: 6, color: "var(--rla-amber)" }} />
          Agent Configuration
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, fontSize: 13 }}>
          <div><span style={{ color: "var(--rla-text-dim)" }}>Type:</span> {data.agent_type}</div>
          <div><span style={{ color: "var(--rla-text-dim)" }}>Slug:</span> <code style={{ fontSize: 12 }}>{data.slug}</code></div>
          <div><span style={{ color: "var(--rla-text-dim)" }}>Enabled:</span> {data.enabled ? "✅" : "❌"}</div>
          <div><span style={{ color: "var(--rla-text-dim)" }}>Public:</span> {data.public_enabled ? "✅" : "❌"}</div>
        </div>
      </div>
    </div>
  );
}
