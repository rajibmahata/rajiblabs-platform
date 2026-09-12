import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";

interface DayPoint { date: string; calls: number; tokens: number; cost_usd: number; cache_hits: number }
interface AgentRow { slug: string; name: string; agent_type: string; enabled: boolean; public_enabled: boolean; turns: number; tool_calls: number; leads: number; errors: number; runs: number }

export default function AgentOpsSummaryPage() {
  const [data, setData] = useState<any>(null);
  const [timeline, setTimeline] = useState<DayPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<any>("/api/admin/ops/summary"),
      api.get<{ days: DayPoint[] }>("/api/admin/ops/usage-timeline?days=14"),
    ]).then(([s, t]) => { setData(s); setTimeline(t.days || []); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-center text-[var(--rla-text-dim)]">Loading operations data…</div>;
  if (!data) return <div className="p-6 text-center text-[var(--rla-red)]">Failed to load ops data.</div>;

  const today = data.today || {};
  const week = data.week || {};
  const agents: AgentRow[] = data.agents || [];
  const conv = data.conversations || {};
  const providers = data.providers || {};
  const tags = data.tags || {};

  const maxCost = Math.max(1, ...timeline.map((d) => d.cost_usd));
  const maxCalls = Math.max(1, ...timeline.map((d) => d.calls));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>
          <i className="fas fa-microchip" style={{ marginRight: 8, color: "var(--rla-violet)" }} />
          Agent & AI Operations
        </h2>
        <div style={{ fontSize: 13, color: "var(--rla-text-dim)" }}>
          Last 14 days · <Link to="/admin/ops/conversations" style={{ color: "var(--rla-violet)" }}>All Conversations</Link>
        </div>
      </div>

      {/* Top stat cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(180px,1fr))", gap: 16 }}>
        {[
          { label: "LLM Calls Today", value: today.total_calls ?? 0, icon: "fas fa-bolt", color: "var(--rla-violet)" },
          { label: "Tokens Today", value: (today.total_tokens ?? 0).toLocaleString(), icon: "fas fa-database", color: "var(--rla-cyan)" },
          { label: "Cost Today", value: `$${(today.estimated_cost_usd ?? 0).toFixed(4)}`, icon: "fas fa-dollar-sign", color: "var(--rla-green)" },
          { label: "Cache Hit Rate", value: `${today.cache_hit_rate ?? 0}%`, icon: "fas fa-bolt", color: "var(--rla-amber)" },
          { label: "Week Cost", value: `$${(week.cost_usd ?? 0).toFixed(4)}`, icon: "fas fa-calendar-week", color: "var(--rla-cyan)" },
          { label: "Active Sessions (24h)", value: conv.active_24h ?? 0, icon: "fas fa-comments", color: "var(--rla-green)" },
          { label: "Total Leads", value: data.leads_total ?? 0, icon: "fas fa-user-plus", color: "var(--rla-amber)" },
          { label: "LLM Fallbacks", value: today.llm_fallbacks ?? 0, icon: "fas fa-triangle-exclamation", color: "var(--rla-red)" },
        ].map((s) => (
          <div key={s.label} style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: "16px 18px", display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 40, height: 40, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", background: `${s.color}12`, color: s.color, fontSize: 17 }}>
              <i className={s.icon} />
            </div>
            <div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>{s.value}</div>
              <div style={{ fontSize: 12, color: "var(--rla-text-dim)" }}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Chart row: cost + calls timeline */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {[
          { title: "Daily Cost (USD)", data: timeline, field: "cost_usd" as const, max: maxCost, color: "var(--rla-violet)", fmt: (v: number) => `$${v.toFixed(4)}` },
          { title: "Daily LLM Calls", data: timeline, field: "calls" as const, max: maxCalls, color: "var(--rla-cyan)", fmt: (v: number) => String(v) },
        ].map((chart) => (
          <div key={chart.title} style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--rla-text-dim)", marginBottom: 12 }}>{chart.title}</div>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 120 }}>
              {chart.data.map((d, i) => (
                <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                  <span style={{ fontSize: 10, color: "var(--rla-text-faint)" }}>{chart.fmt(d[chart.field])}</span>
                  <div style={{
                    width: "100%",
                    height: Math.max(4, (d[chart.field] / chart.max) * 100),
                    background: chart.color,
                    borderRadius: 4,
                    opacity: 0.8,
                  }} />
                  <span style={{ fontSize: 9, color: "var(--rla-text-faint)" }}>{d.date.slice(5)}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Provider breakdown + Cache */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--rla-text-dim)", marginBottom: 12 }}>Provider Breakdown (Today)</div>
          {Object.keys(providers).length === 0 && <div style={{ color: "var(--rla-text-faint)" }}>No calls yet today</div>}
          {Object.entries(providers).map(([p, v]: [string, any]) => (
            <div key={p} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--rla-border)" }}>
              <span style={{ fontWeight: 500 }}>{p}</span>
              <span style={{ fontSize: 13, color: "var(--rla-text-dim)" }}>{v.calls} calls · {v.tokens.toLocaleString()} tok · ${v.cost.toFixed(4)}</span>
            </div>
          ))}
        </div>
        <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--rla-text-dim)", marginBottom: 12 }}>Tag Breakdown (Today)</div>
          {Object.keys(tags).length === 0 && <div style={{ color: "var(--rla-text-faint)" }}>No tags yet</div>}
          {Object.entries(tags).sort((a: any, b: any) => b[1].calls - a[1].calls).slice(0, 10).map(([t, v]: [string, any]) => (
            <div key={t} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--rla-border)" }}>
              <span style={{ fontWeight: 500, fontFamily: "monospace", fontSize: 12 }}>{t}</span>
              <span style={{ fontSize: 13, color: "var(--rla-text-dim)" }}>{v.calls} calls · {v.tokens.toLocaleString()} tok</span>
            </div>
          ))}
        </div>
      </div>

      {/* Agent cards */}
      <div>
        <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
          <i className="fas fa-robot" style={{ color: "var(--rla-violet)" }} /> Registered Agents
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(260px,1fr))", gap: 14 }}>
          {agents.map((a) => (
            <Link key={a.slug} to={`/admin/ops/agents/${a.slug}`} style={{
              background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 16,
              textDecoration: "none", color: "inherit", display: "flex", flexDirection: "column", gap: 8,
              transition: "box-shadow 0.15s, border-color 0.15s",
            }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--rla-violet)"; e.currentTarget.style.boxShadow = "var(--rla-shadow-md)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--rla-border)"; e.currentTarget.style.boxShadow = "none"; }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: 600, fontSize: 14 }}>{a.name || a.slug}</span>
                <span style={{
                  fontSize: 10, fontWeight: 600, padding: "2px 8px", borderRadius: 99,
                  background: a.enabled ? "var(--rla-green-soft)" : "var(--rla-red-soft)",
                  color: a.enabled ? "var(--rla-green)" : "var(--rla-red)",
                }}>{a.enabled ? "ON" : "OFF"}</span>
              </div>
              <div style={{ fontSize: 12, color: "var(--rla-text-dim)" }}>{a.agent_type}</div>
              <div style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--rla-text-dim)", marginTop: 4 }}>
                <span><b>{a.turns}</b> turns</span>
                <span><b>{a.tool_calls}</b> tools</span>
                <span><b>{a.leads}</b> leads</span>
                {a.errors > 0 && <span style={{ color: "var(--rla-red)" }}><b>{a.errors}</b> errors</span>}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
