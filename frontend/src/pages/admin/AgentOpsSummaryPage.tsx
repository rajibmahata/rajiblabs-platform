/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";

const get = async <T,>(p: string): Promise<T | null> => {
  try { return await api.get<T>(p); } catch { return null; }
};

export default function AgentOpsSummaryPage() {
  const [data, setData] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      get<any>("/api/admin/ops/summary"),
      get<any>("/api/admin/ops/usage-timeline?days=14"),
    ]).then(([s, t]) => { setData(s); setTimeline(t?.days || []); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-center" style={{ color: "var(--rla-text-dim)" }}>Loading operations data…</div>;
  if (!data) return <div className="p-6 text-center" style={{ color: "var(--rla-red)" }}>Failed to load ops data.</div>;

  const today = data.today || {};
  const week = data.week || {};
  const month = data.month || {};
  const agents: any[] = data.agents || [];
  const conv = data.conversations || {};
  const errors: any[] = data.recent_errors || [];
  const health = data.system_health || {};
  const rt = data.response_types || {};
  const ah = data.agent_health || {};

  const maxCost = Math.max(0.0001, ...timeline.map((d: any) => d.cost_usd));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>
          <i className="fas fa-microchip" style={{ marginRight: 8, color: "var(--rla-violet)" }} />
          Agent & AI Operations
        </h2>
        <div style={{ display: "flex", gap: 8 }}>
          <Link to="/admin/ops/runs" className="rla-btn rla-btn-ghost rla-btn-sm"><i className="fas fa-clock-rotate-left" /> Run History</Link>
          <Link to="/admin/ops/conversations" className="rla-btn rla-btn-ghost rla-btn-sm"><i className="fas fa-comments" /> Conversations</Link>
          <Link to="/admin/ops/token-budget" className="rla-btn rla-btn-ghost rla-btn-sm"><i className="fas fa-coins" /> Token Budget</Link>
        </div>
      </div>

      {/* ── Stat Cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(175px,1fr))", gap: 14 }}>
        {[
          { label: "LLM Calls Today", value: today.calls ?? 0, icon: "fas fa-bolt", color: "var(--rla-violet)" },
          { label: "Tokens Today", value: `${((today.total_tokens ?? 0) / 1000).toFixed(1)}k`, icon: "fas fa-database", color: "var(--rla-cyan)" },
          { label: "Cost Today", value: `$${(today.cost_usd ?? 0).toFixed(4)}`, icon: "fas fa-dollar-sign", color: "var(--rla-green)" },
          { label: "Cost This Week", value: `$${(week.cost_usd ?? 0).toFixed(4)}`, icon: "fas fa-calendar-week", color: "var(--rla-cyan)" },
          { label: "Cost This Month", value: `$${(month.cost_usd ?? 0).toFixed(4)}`, icon: "fas fa-calendar", color: "var(--rla-amber)" },
          { label: "Cache Hit Rate", value: `${today.cache_hit_rate ?? 0}%`, icon: "fas fa-bolt", color: "var(--rla-green)" },
          { label: "LLM Fallbacks", value: today.llm_fallbacks ?? 0, icon: "fas fa-triangle-exclamation", color: "var(--rla-red)" },
          { label: "Active Sessions", value: conv.active_24h ?? 0, icon: "fas fa-comments", color: "var(--rla-cyan)" },
        ].map((s) => (
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

      {/* ── Charts: Cost + Response Types ── */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
        <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--rla-text-dim)", marginBottom: 12 }}>Daily Cost (14 days)</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: 100 }}>
            {timeline.map((d: any, i: number) => (
              <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
                <span style={{ fontSize: 9, color: "var(--rla-text-faint)" }}>${d.cost_usd.toFixed(4)}</span>
                <div style={{ width: "100%", height: Math.max(3, (d.cost_usd / maxCost) * 80), background: "var(--rla-violet)", borderRadius: 3, opacity: 0.8 }} />
                <span style={{ fontSize: 8, color: "var(--rla-text-faint)" }}>{d.date.slice(5)}</span>
              </div>
            ))}
          </div>
        </div>
        <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--rla-text-dim)", marginBottom: 12 }}>Response Types (Today)</div>
          {Object.keys(rt).length === 0 && <div style={{ color: "var(--rla-text-faint)", fontSize: 13 }}>No data yet</div>}
          {Object.entries(rt).map(([type, count]) => (
            <div key={type} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", borderBottom: "1px solid var(--rla-border)" }}>
              <span style={{ fontSize: 12, fontFamily: "monospace" }}>{type}</span>
              <span style={{ fontSize: 12, fontWeight: 600 }}>{String(count)}</span>
            </div>
          ))}
          <div style={{ marginTop: 8, fontSize: 11, color: "var(--rla-text-dim)" }}>
            RAG-only: {today.rag_only ?? 0} · LLM: {today.llm_calls ?? 0}
          </div>
        </div>
      </div>

      {/* ── Agent Health Grid ── */}
      <div>
        <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
          <i className="fas fa-robot" style={{ color: "var(--rla-violet)" }} /> Agents
          <span style={{ fontSize: 12, fontWeight: 400, color: "var(--rla-text-dim)" }}>
            ({ah.enabled ?? 0} enabled · {ah.running ?? 0} running · {ah.with_errors ?? 0} errors)
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(280px,1fr))", gap: 12 }}>
          {agents.map((a: any) => (
            <Link key={a.slug} to={`/admin/ops/agents/${a.slug}`} style={{
              background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 10, padding: 14,
              textDecoration: "none", color: "inherit", display: "flex", flexDirection: "column", gap: 6,
              transition: "border-color 0.15s, box-shadow 0.15s",
            }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--rla-violet)"; e.currentTarget.style.boxShadow = "var(--rla-shadow-md)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--rla-border)"; e.currentTarget.style.boxShadow = "none"; }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{a.name}</span>
                <div style={{ display: "flex", gap: 4 }}>
                  {a.has_running_job && <span style={{ fontSize: 9, fontWeight: 600, padding: "2px 6px", borderRadius: 6, background: "var(--rla-amber-soft)", color: "var(--rla-amber)" }}>RUNNING</span>}
                  <span style={{ fontSize: 9, fontWeight: 600, padding: "2px 6px", borderRadius: 6, background: a.enabled ? "var(--rla-green-soft)" : "var(--rla-red-soft)", color: a.enabled ? "var(--rla-green)" : "var(--rla-red)" }}>
                    {a.enabled ? "ON" : "OFF"}
                  </span>
                </div>
              </div>
              <div style={{ fontSize: 11, color: "var(--rla-text-dim)" }}>{a.agent_type}</div>
              <div style={{ display: "flex", gap: 12, fontSize: 11, color: "var(--rla-text-dim)" }}>
                <span><b>{a.turns}</b> turns</span>
                <span><b>{a.tool_calls}</b> tools</span>
                <span><b>{a.leads}</b> leads</span>
                {a.errors > 0 && <span style={{ color: "var(--rla-red)" }}><b>{a.errors}</b> err</span>}
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* ── Recent Errors ── */}
      {errors.length > 0 && (
        <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, display: "flex", alignItems: "center", gap: 6 }}>
            <i className="fas fa-triangle-exclamation" style={{ color: "var(--rla-red)" }} /> Recent Errors (24h)
            <Link to="/admin/logs" style={{ marginLeft: "auto", fontSize: 12, color: "var(--rla-violet)" }}>All logs →</Link>
          </div>
          {errors.slice(0, 5).map((e: any) => (
            <div key={e.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 0", borderBottom: "1px solid var(--rla-border)", fontSize: 13 }}>
              <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 6, background: "var(--rla-red-soft)", color: "var(--rla-red)", fontWeight: 600, whiteSpace: "nowrap" }}>{e.source}</span>
              <span style={{ flex: 1, color: "var(--rla-text-dim)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.message}</span>
              <span style={{ fontSize: 11, color: "var(--rla-text-faint)", whiteSpace: "nowrap" }}>{e.created_at ? new Date(e.created_at).toLocaleString() : ""}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── System Health ── */}
      <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>
          <i className="fas fa-heartbeat" style={{ marginRight: 6, color: "var(--rla-green)" }} /> System Health (1h)
        </div>
        <div style={{ display: "flex", gap: 24, fontSize: 13 }}>
          <div><span style={{ color: "var(--rla-text-dim)" }}>Calls:</span> <b>{health.calls_1h ?? 0}</b></div>
          <div><span style={{ color: "var(--rla-text-dim)" }}>Avg Latency:</span> <b>{health.avg_latency_ms ?? 0}ms</b></div>
          <div><span style={{ color: "var(--rla-text-dim)" }}>Error Rate:</span> <b style={{ color: (health.error_rate_1h ?? 0) > 5 ? "var(--rla-red)" : "var(--rla-green)" }}>{health.error_rate_1h ?? 0}%</b></div>
          <div><span style={{ color: "var(--rla-text-dim)" }}>Embedding Cache:</span> <b>{health.embedding_cache ?? 0}</b></div>
          <div><span style={{ color: "var(--rla-text-dim)" }}>Response Cache:</span> <b>{health.response_cache ?? 0}</b></div>
        </div>
      </div>
    </div>
  );
}
