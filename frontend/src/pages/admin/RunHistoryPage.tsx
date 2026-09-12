/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../../services/api";

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
  error: ["var(--rla-red-soft)", "var(--rla-red)"],
  cancelled: ["var(--rla-text-faint)", "var(--rla-text-dim)"],
  skipped: ["var(--rla-text-faint)", "var(--rla-text-dim)"],
};

const AGENT_NAMES: Record<string, string> = {
  "rajiblabs-profile": "Profile Intelligence",
  "rajiblabs-learning": "Learning Agent",
  "rajiblabs-marketing": "Marketing Agent",
  "rajiblabs-concierge": "Concierge",
  "rajiblabs-career": "Career Agent",
};

export default function RunHistoryPage() {
  const { runId } = useParams();
  const [runs, setRuns] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [agent, setAgent] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<any>(null);
  const limit = 30;

  const load = useCallback(() => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) });
    if (agent) params.set("agent", agent);
    if (status) params.set("status", status);
    let active = true;
    api.get<any>(`/api/admin/ops/runs?${params}`)
      .then((r) => { if (active) { setRuns(r?.runs || []); setTotal(r?.total || 0); } })
      .catch(() => {})
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [page, agent, status]);

  useEffect(() => { return load(); }, [load]);

  useEffect(() => {
    if (!runId) return;
    let active = true;
    api.get<any>(`/api/admin/ops/runs/${runId}`)
      .then((d) => { if (active) setDetail(d); })
      .catch(() => { if (active) setDetail(null); });
    return () => { active = false; };
  }, [runId]);

  // Detail view
  if (runId) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
            <i className="fas fa-clock-rotate-left" style={{ marginRight: 8, color: "var(--rla-cyan)" }} />
            Run Detail
          </h2>
          <Link to="/admin/ops/runs" style={{ fontSize: 13, color: "var(--rla-violet)" }}>
            <i className="fas fa-arrow-left" style={{ marginRight: 4 }} /> Back to Runs
          </Link>
        </div>
        {!detail && <div style={{ padding: 20, color: "var(--rla-text-dim)" }}>Loading…</div>}
        {detail && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* Run header */}
            <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
              <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
                <span style={{ fontWeight: 700, fontSize: 16 }}>{AGENT_NAMES[detail.agent_slug] || detail.agent_slug}</span>
                <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 99, ...(STATUS_COLORS[detail.status || ""] || STATUS_COLORS.success).reduce((a, [k, v]) => ({ ...a, [k === "var(--rla-green-soft)" ? "background" : "color"]: v }), {} as any) }}>
                  {(detail.status || "unknown").toUpperCase()}
                </span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(200px,1fr))", gap: 12, marginTop: 16, fontSize: 13 }}>
                <div><span style={{ color: "var(--rla-text-dim)" }}>Triggered by:</span> <b>{detail.triggered_by || "—"}</b></div>
                <div><span style={{ color: "var(--rla-text-dim)" }}>Started:</span> <b>{detail.started_at ? new Date(detail.started_at).toLocaleString() : "—"}</b></div>
                <div><span style={{ color: "var(--rla-text-dim)" }}>Completed:</span> <b>{detail.finished_at ? new Date(detail.finished_at).toLocaleString() : "—"}</b></div>
                <div><span style={{ color: "var(--rla-text-dim)" }}>Duration:</span> <b>{durMs(detail.started_at, detail.finished_at)}</b></div>
                <div><span style={{ color: "var(--rla-text-dim)" }}>Proposed:</span> <b>{detail.proposed ?? 0}</b></div>
                <div><span style={{ color: "var(--rla-text-dim)" }}>Applied:</span> <b>{detail.applied ?? 0}</b></div>
              </div>
            </div>

            {/* Sources inspected */}
            {detail.sources_inspected?.length > 0 && (
              <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Sources Inspected</div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {detail.sources_inspected.map((s: string) => (
                    <span key={s} style={{ fontSize: 11, padding: "3px 8px", borderRadius: 6, background: "var(--rla-cyan-soft)", color: "var(--rla-cyan)" }}>{s}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Errors */}
            {detail.errors?.length > 0 && (
              <div style={{ background: "var(--rla-red-soft)", border: "1px solid var(--rla-red)", borderRadius: 12, padding: 20 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: "var(--rla-red)", marginBottom: 8 }}>
                  <i className="fas fa-triangle-exclamation" style={{ marginRight: 6 }} /> Errors ({detail.errors.length})
                </div>
                {detail.errors.map((e: string, i: number) => (
                  <div key={i} style={{ fontSize: 13, padding: "4px 0", borderBottom: "1px solid var(--rla-red)30" }}>{e}</div>
                ))}
              </div>
            )}

            {/* Health */}
            {detail.health && (
              <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Health Check</div>
                <pre style={{ fontSize: 12, background: "var(--rla-bg)", padding: 12, borderRadius: 8, overflow: "auto" }}>
                  {JSON.stringify(detail.health, null, 2)}
                </pre>
              </div>
            )}

            {/* Full document */}
            {detail.full_document && (
              <div style={{ background: "var(--rla-surface)", border: "1px solid var(--rla-border)", borderRadius: 12, padding: 20 }}>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Full Document</div>
                <pre style={{ fontSize: 11, background: "var(--rla-bg)", padding: 12, borderRadius: 8, overflow: "auto", maxHeight: 400 }}>
                  {JSON.stringify(detail.full_document, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // List view
  const pages = Math.ceil(total / limit);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
          <i className="fas fa-clock-rotate-left" style={{ marginRight: 8, color: "var(--rla-cyan)" }} />
          Agent Run History
        </h2>
        <span style={{ fontSize: 13, color: "var(--rla-text-dim)" }}>{total} runs total</span>
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <select value={agent} onChange={(e) => { setAgent(e.target.value); setPage(0); }}
          style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid var(--rla-border)", fontSize: 13, background: "var(--rla-surface)" }}>
          <option value="">All agents</option>
          <option value="rajiblabs-profile">Profile Intelligence</option>
          <option value="rajiblabs-learning">Learning Agent</option>
          <option value="rajiblabs-marketing">Marketing Agent</option>
        </select>
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(0); }}
          style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid var(--rla-border)", fontSize: 13, background: "var(--rla-surface)" }}>
          <option value="">All statuses</option>
          <option value="success">Success</option>
          <option value="running">Running</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {loading && <div style={{ padding: 16, color: "var(--rla-text-dim)" }}>Loading…</div>}
      {!loading && runs.length === 0 && <div style={{ padding: 20, color: "var(--rla-text-faint)" }}>No runs found.</div>}

      {!loading && runs.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {runs.map((r: any) => {
            const sc = STATUS_COLORS[r.status || ""] || STATUS_COLORS.success;
            return (
              <Link key={r.id} to={`/admin/ops/runs/${r.id}`} style={{
                display: "grid", gridTemplateColumns: "140px 80px 1fr 100px 80px 80px 80px",
                alignItems: "center", gap: 10, padding: "10px 14px", borderRadius: 8,
                background: "var(--rla-surface)", border: "1px solid var(--rla-border)",
                textDecoration: "none", color: "inherit", fontSize: 13,
                transition: "border-color 0.15s",
              }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--rla-violet)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--rla-border)"; }}
              >
                <span style={{ fontWeight: 500, fontSize: 12 }}>{AGENT_NAMES[r.agent_slug] || r.agent_slug}</span>
                <span style={{ fontSize: 10, fontWeight: 600, padding: "2px 6px", borderRadius: 6, background: sc[0], color: sc[1], textAlign: "center" }}>
                  {(r.status || "?").toUpperCase()}
                </span>
                <span style={{ fontSize: 12, color: "var(--rla-text-dim)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {r.triggered_by || "—"} · {r.detail || "—"}
                </span>
                <span style={{ fontSize: 12, color: "var(--rla-text-dim)" }}>
                  {r.proposed ?? 0} prop / {r.applied ?? 0} applied
                </span>
                <span style={{ fontSize: 11, color: "var(--rla-text-dim)" }}>
                  {durMs(r.started_at, r.finished_at)}
                </span>
                <span style={{ fontSize: 11, color: r.errors?.length ? "var(--rla-red)" : "var(--rla-text-faint)" }}>
                  {r.errors?.length ? `${r.errors.length} err` : "—"}
                </span>
                <span style={{ fontSize: 11, color: "var(--rla-text-faint)" }}>{relTime(r.started_at)}</span>
              </Link>
            );
          })}
        </div>
      )}

      {pages > 1 && (
        <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 8 }}>
          <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}
            style={{ padding: "6px 14px", borderRadius: 8, border: "1px solid var(--rla-border)", background: "var(--rla-surface)", cursor: page === 0 ? "default" : "pointer", opacity: page === 0 ? 0.5 : 1, fontSize: 13 }}>
            ← Prev
          </button>
          <span style={{ padding: "6px 12px", fontSize: 13, color: "var(--rla-text-dim)" }}>{page + 1} / {pages}</span>
          <button onClick={() => setPage((p) => Math.min(pages - 1, p + 1))} disabled={page >= pages - 1}
            style={{ padding: "6px 14px", borderRadius: 8, border: "1px solid var(--rla-border)", background: "var(--rla-surface)", cursor: page >= pages - 1 ? "default" : "pointer", opacity: page >= pages - 1 ? 0.5 : 1, fontSize: 13 }}>
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
