/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import { toast } from "../../components/admin/toast";

const get = async <T,>(p: string): Promise<T | null> => {
  try { return await api.get<T>(p); } catch { return null; }
};
const fmtDT = (v: string | undefined | null) =>
  v ? new Date(v).toLocaleString() : "—";

function Trend({ kind, icon, text }: { kind: "up" | "down" | "neutral"; icon: string; text: string }) {
  return <span className={`rla-trend ${kind}`}><i className={`fas ${icon}`} /> {text}</span>;
}

export default function Dashboard() {
  const [dash, setDash] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [ghStatus, setGhStatus] = useState<any>(null);
  const [notifs, setNotifs] = useState<any[]>([]);
  const [logStats, setLogStats] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [rag, setRag] = useState<any>(null);
  const [proposals, setProposals] = useState<any[]>([]);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const arr = (v: any) => (Array.isArray(v) ? v : []);
    get<any>("/api/admin/dashboard").then((d) => d && setDash(d));
    get<any>("/health").then((h) => h && setHealth(h));
    get<any>("/api/admin/github/status").then((s) => s && setGhStatus(s));
    get<any>("/api/admin/notifications").then((n) => setNotifs(arr(n).slice(0, 6)));
    get<any>("/api/admin/logs/stats").then((s) => s && setLogStats(s));
    get<any>("/api/admin/leads").then((l) => setLeads(arr(l)));
    get<any>("/api/admin/projects").then((p) => setProjects(arr(p)));
    get<any>("/api/admin/products").then((p) => setProducts(arr(p)));
    get<any>("/api/admin/rag/dashboard").then((r) => r && setRag(r));
    get<any>("/api/admin/ai/proposals").then((p) => setProposals(arr(p)));
  }, []);

  const doSync = async () => {
    if (syncing) return;
    setSyncing(true);
    toast("Sync started", "pulling latest GitHub repositories…");
    try {
      const r = await api.post<any>("/api/admin/github/sync");
      const s = await get<any>("/api/admin/github/status");
      if (s) setGhStatus(s);
      toast("Sync complete", `${r.found ?? r.added ?? 0} repositories found.`);
    } catch (e) {
      toast("Sync failed", String(e instanceof Error ? e.message : e).slice(0, 120));
    } finally {
      setSyncing(false);
    }
  };

  const resume = dash?.resume;
  const pub = dash?.portfolio?.published ?? 0;
  const pTotal = dash?.portfolio?.total ?? 0;
  const ghCount = ghStatus?.count ?? dash?.github?.total ?? 0;
  const lastSync = ghStatus?.last_sync?.started_at || ghStatus?.last_sync?.startedAt
    || dash?.lastSync?.startedAt || dash?.lastSync?.started_at;
  const prodTotal = products.length || dash?.products?.total || 0;
  const newLeads = leads.filter((l) => (l.status || "new") === "new").length;
  // /api/admin/logs/stats returns by_level as an OBJECT ({error: n}), not an array.
  const byLevel = logStats?.by_level;
  const errCount = Array.isArray(byLevel)
    ? byLevel.reduce((a: number, r: any) => a + (r._id === "error" ? r.count : 0), 0)
    : (byLevel?.error ?? 0);
  const failedDocs = Object.values((rag?.by_source || {}) as Record<string, any>)
    .reduce((a: number, s: any) => a + (s.failed || 0), 0);
  const drafts = projects.filter((p) => p.status !== "published" && p.published !== true).length
    + products.filter((p) => p.status !== "published" && p.published !== true).length;

  const kpis = [
    { label: "Resume", icon: "fa-file-pdf", color: "violet",
      value: resume ? `v${resume.version ?? 1}` : "—",
      sub: resume?.fileName || "No published resume",
      trend: resume ? <Trend kind="up" icon="fa-check" text="Live" />
                    : <Trend kind="neutral" icon="fa-triangle-exclamation" text="Missing" /> },
    { label: "Portfolio", icon: "fa-briefcase", color: "cyan",
      value: <>{pub}<small>/{pTotal}</small></>,
      sub: "Published / total",
      trend: pTotal === 0 ? <Trend kind="neutral" icon="fa-triangle-exclamation" text="Empty" />
        : pub === pTotal ? <Trend kind="up" icon="fa-check" text="All live" />
        : <Trend kind="neutral" icon="fa-pen" text={`${pTotal - pub} drafts`} /> },
    { label: "GitHub Repos", icon: "fab fa-github", color: "green",
      value: `${ghCount}`,
      sub: lastSync ? `Synced ${fmtDT(lastSync)}` : "Never synced",
      trend: ghCount > 0 && lastSync ? <Trend kind="up" icon="fa-check" text="Synced" />
        : <Trend kind="down" icon="fa-rotate" text="Sync now" /> },
    { label: "Products", icon: "fa-cube", color: "amber",
      value: `${prodTotal}`,
      sub: proposals.length ? `${proposals.length} proposal${proposals.length === 1 ? "" : "s"} saved` : "Catalog",
      trend: prodTotal > 0 ? <Trend kind="up" icon="fa-arrow-trend-up" text="Active" />
        : <Trend kind="neutral" icon="fa-triangle-exclamation" text="Empty" /> },
  ];

  const actions = [
    { to: "/admin/resume", icon: "fa-upload", color: "linear-gradient(135deg,#8b5cf6,#6d28d9)", b: "Upload Resume", s: resume ? `Replace current PDF (v${resume.version ?? 1})` : "Upload your first resume" },
    { to: "/admin/portfolio", icon: "fa-plus", color: "linear-gradient(135deg,#22d3ee,#0e7490)", b: "Add Portfolio Item", s: `${pub} published — manage items` },
    { to: "/admin/ai-workbench", icon: "fa-wand-magic-sparkles", color: "linear-gradient(135deg,#f472b6,#be185d)", b: "AI Proposal Studio", s: "Draft tailored proposals" },
    { to: "/admin/leads", icon: "fa-user-plus", color: "linear-gradient(135deg,#34d399,#059669)", b: "Review Leads", s: newLeads ? `${newLeads} new enquiries` : "No new enquiries" },
    { to: "/admin/content", icon: "fa-pen", color: "linear-gradient(135deg,#fbbf24,#d97706)", b: "Edit Website Content", s: "Hero, about & contact sections" },
    { to: "/admin/knowledge", icon: "fa-brain", color: "linear-gradient(135deg,#60a5fa,#1d4ed8)", b: "Knowledge Base", s: rag ? `${rag.chunks ?? 0} chunks indexed` : "RAG index status" },
  ];

  const feedIcon = (t: string) => {
    const s = `${t}`.toLowerCase();
    if (/resume/.test(s)) return ["violet", "fa-file-pdf"];
    if (/lead|contact|enquiry/.test(s)) return ["green", "fa-user-plus"];
    if (/github|sync|repo/.test(s)) return ["cyan", "fab fa-github"];
    if (/rag|knowledge|proposal|ai/.test(s)) return ["violet", "fa-brain"];
    if (/error|fail|vulnerab|security/.test(s)) return ["red", "fa-shield-halved"];
    return ["amber", "fa-bell"];
  };

  const attention: { icon: string; color: string; b: string; p: string; pill: [string, string]; to: string }[] = [];
  if (newLeads > 0) attention.push({ icon: "fa-user-plus", color: "var(--rla-green-soft)", b: `${newLeads} new leads`, p: "Enquiries awaiting review", pill: ["warn", "REVIEW"], to: "/admin/leads" });
  if (errCount > 0) attention.push({ icon: "fa-triangle-exclamation", color: "var(--rla-red-soft)", b: `${errCount} errors (5d)`, p: "System log entries need a look", pill: ["err", "ACTION"], to: "/admin/logs" });
  if (failedDocs > 0) attention.push({ icon: "fa-brain", color: "var(--rla-amber-soft)", b: `${failedDocs} failed RAG docs`, p: "Knowledge entries failed to index", pill: ["warn", "REVIEW"], to: "/admin/knowledge" });
  if (drafts > 0) attention.push({ icon: "fa-pen", color: "var(--rla-cyan-soft)", b: `${drafts} unpublished drafts`, p: "Projects or products not yet live", pill: ["info", "DRAFTS"], to: "/admin/portfolio" });
  if (!lastSync) attention.push({ icon: "fab fa-github", color: "var(--rla-amber-soft)", b: "GitHub never synced", p: "Connect repositories to the CMS", pill: ["warn", "STALE"], to: "/admin/github" });

  const backendOk = !health || health.status === "ok";
  const statusRows = [
    { icon: "fa-server", bg: backendOk ? "var(--rla-green-soft)" : "var(--rla-red-soft)",
      fg: backendOk ? "var(--rla-green)" : "var(--rla-red)",
      name: "CMS Backend", sub: health ? `${health.status} · db ${health.database || "?"}` : "Checking…",
      pill: health ? (backendOk ? (["ok", "ONLINE"] as const) : (["err", "DOWN"] as const)) : (["muted", "…"] as const) },
    { icon: "fab fa-github", bg: ghStatus?.connected ? "var(--rla-green-soft)" : "var(--rla-amber-soft)",
      fg: ghStatus?.connected ? "var(--rla-green)" : "var(--rla-amber)",
      name: "GitHub Integration",
      sub: ghStatus ? (ghStatus.connected ? `${ghStatus.owner || ""} · ${ghCount} repos` : "Token not configured") : "Checking…",
      pill: ghStatus ? (lastSync ? (["ok", "SYNCED"] as const) : (["warn", "STALE"] as const)) : (["muted", "…"] as const) },
    { icon: "fa-brain", bg: "var(--rla-violet-soft)", fg: "var(--rla-violet)",
      name: "Knowledge Base (RAG)",
      sub: rag ? `${rag.chunks ?? 0} chunks · qdrant ${rag.qdrant?.ok ? "ok" : "down"}` : "Checking…",
      pill: rag ? (rag.qdrant?.ok ? (["ok", "READY"] as const) : (["warn", "DEGRADED"] as const)) : (["muted", "…"] as const) },
    { icon: "fa-robot", bg: "var(--rla-cyan-soft)", fg: "var(--rla-cyan)",
      name: "AI Providers",
      sub: health ? `openai ${health.openai || "?"}${health.github ? ` · github ${health.github}` : ""}` : "Checking…",
      pill: (["info", "INFO"] as const) },
  ];

  const tableRows: { icon: string; bg: string; fg: string; b: string; s: string; type: string; pill: [string, string]; updated: string; to: string }[] = [];
  if (resume) tableRows.push({ icon: "fa-file-pdf", bg: "var(--rla-violet-soft)", fg: "var(--rla-violet)", b: resume.fileName || "Resume", s: `v${resume.version ?? 1}`, type: "resume", pill: ["ok", "PUBLISHED"], updated: fmtDT(resume.uploadedAt), to: "/admin/resume" });
  projects.slice(0, 3).forEach((p) => {
    const live = p.status === "published" || p.published === true;
    tableRows.push({ icon: "fa-briefcase", bg: "var(--rla-cyan-soft)", fg: "var(--rla-cyan)", b: p.name || p.slug || "Project", s: p.category || "project", type: "project", pill: live ? ["ok", "PUBLISHED"] : ["warn", (p.status || "DRAFT").toUpperCase()], updated: fmtDT(p.updated_at || p.updatedAt), to: "/admin/portfolio" });
  });
  products.slice(0, 2).forEach((p) => {
    const live = p.status === "published" || p.published === true;
    tableRows.push({ icon: "fa-cube", bg: "var(--rla-cyan-soft)", fg: "var(--rla-cyan)", b: p.name || p.slug || "Product", s: "product", type: "product", pill: live ? ["ok", "PUBLISHED"] : ["warn", (p.status || "DRAFT").toUpperCase()], updated: fmtDT(p.updated_at || p.updatedAt), to: "/admin/products" });
  });

  return (
    <div>
      <div className="rla-page-head">
        <div>
          <h1>Dashboard</h1>
          <p>Overview of portfolio CMS — last content update <b>{dash?.profileUpdatedAt ? fmtDT(dash.profileUpdatedAt) : "—"}</b></p>
        </div>
        <div className="rla-head-actions">
          <a href="/" target="_blank" rel="noreferrer" className="rla-btn rla-btn-ghost rla-btn-sm"><i className="fas fa-arrow-up-right-from-square" /> View Site</a>
          <Link to="/admin/portfolio" className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-briefcase" /> Manage Portfolio</Link>
        </div>
      </div>

      <div className="rla-kpi-grid">
        {kpis.map((k) => (
          <div className="rla-kpi" key={k.label}>
            <div className="rla-kpi-top">
              <span className="rla-kpi-label">{k.label}</span>
              <span className={`rla-kpi-icon ${k.color}`}><i className={`fas ${k.icon}`} /></span>
            </div>
            <div className="rla-kpi-value">{k.value}</div>
            <div className="rla-kpi-foot">
              <span className="rla-kpi-sub mono">{k.sub}</span>
              {k.trend}
            </div>
          </div>
        ))}
      </div>

      <div className="rla-panel-grid">
        <div className="rla-panel">
          <div className="rla-panel-head">
            <div><h3>Quick Actions</h3><p>Frequent admin operations</p></div>
          </div>
          <div className="rla-panel-body">
            <div className="rla-qa-grid">
              {actions.slice(0, 4).map((a) => (
                <Link key={a.b} to={a.to} className="rla-qa">
                  <span className="rla-qa-icon" style={{ background: a.color }}><i className={`fas ${a.icon}`} /></span>
                  <div><b>{a.b}</b><span>{a.s}</span></div>
                  <i className="fas fa-chevron-right arr" />
                </Link>
              ))}
            </div>
            <div className="rla-qa-grid" style={{ marginTop: 12 }}>
              {actions.slice(4).map((a) => (
                <Link key={a.b} to={a.to} className="rla-qa">
                  <span className="rla-qa-icon" style={{ background: a.color }}><i className={`fas ${a.icon}`} /></span>
                  <div><b>{a.b}</b><span>{a.s}</span></div>
                  <i className="fas fa-chevron-right arr" />
                </Link>
              ))}
            </div>
          </div>
        </div>

        <div className="rla-panel">
          <div className="rla-panel-head">
            <div><h3>System Status</h3><p>Services &amp; integrations</p></div>
            <span className={`rla-pill ${backendOk ? "ok" : "err"}`}>{backendOk ? "HEALTHY" : "CHECK"}</span>
          </div>
          <div className="rla-panel-body">
            {statusRows.map((r) => (
              <div className="rla-status-row" key={r.name}>
                <span className="rla-status-icon" style={{ background: r.bg, color: r.fg }}><i className={`fas ${r.icon}`} /></span>
                <div><div className="rla-st-name">{r.name}</div><div className="rla-st-sub">{r.sub}</div></div>
                <span className={`rla-pill ${r.pill[0]}`}>{r.pill[1]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rla-panel-grid">
        <div className="rla-panel">
          <div className="rla-panel-head">
            <div><h3>Recent Activity</h3><p>Latest notifications</p></div>
            <Link to="/admin/logs" className="rla-panel-link">View all <i className="fas fa-arrow-right" /></Link>
          </div>
          <div className="rla-panel-body">
            <div className="rla-feed">
              {notifs.length === 0 && <p style={{ fontSize: ".85rem", color: "var(--rla-text-faint)" }}>No recent activity.</p>}
              {notifs.map((n, i) => {
                const [color, icon] = feedIcon(n.title || n.message || "");
                return (
                  <div className="rla-feed-item" key={i}>
                    <span className={`rla-feed-dot ${color}`}><i className={`fas ${icon}`} /></span>
                    <div className="rla-feed-body">
                      <b>{n.title || "Notification"}</b>
                      {n.message && <p>{n.message}</p>}
                      <span className="rla-feed-time">{fmtDT(n.created_at)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="rla-panel">
          <div className="rla-panel-head">
            <div><h3>Needs Attention</h3><p>Live counts from your CMS</p></div>
          </div>
          <div className="rla-panel-body">
            {attention.length === 0 && <p style={{ fontSize: ".85rem", color: "var(--rla-text-faint)" }}>All clear — nothing needs review.</p>}
            {attention.map((a) => (
              <div className="rla-status-row" key={a.b}>
                <span className="rla-status-icon" style={{ background: a.color, color: "var(--rla-text)" }}><i className={`fas ${a.icon}`} /></span>
                <div><div className="rla-st-name">{a.b}</div><div className="rla-st-sub">{a.p}</div></div>
                <Link to={a.to} className={`rla-pill ${a.pill[0]}`} style={{ marginLeft: "auto" }}>{a.pill[1]}</Link>
              </div>
            ))}
            <div className="rla-status-row">
              <span className="rla-status-icon" style={{ background: "var(--rla-green-soft)", color: "var(--rla-green)" }}><i className="fab fa-github" /></span>
              <div><div className="rla-st-name">GitHub Sync</div><div className="rla-st-sub">{ghCount} repos · {lastSync ? `last ${fmtDT(lastSync)}` : "never synced"}</div></div>
              <button onClick={() => void doSync()} disabled={syncing} className="rla-pill info" style={{ border: "none", cursor: "pointer" }}>
                {syncing ? "SYNCING…" : "SYNC NOW"}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="rla-panel">
        <div className="rla-panel-head">
          <div><h3>Content Library</h3><p>Managed assets &amp; entries</p></div>
          <Link to="/admin/portfolio" className="rla-panel-link">Manage <i className="fas fa-arrow-right" /></Link>
        </div>
        <div className="rla-table-wrap">
          <table className="rla-table">
            <thead><tr><th>Item</th><th>Type</th><th>Status</th><th>Updated</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
            <tbody>
              {tableRows.length === 0 && <tr><td colSpan={5}><span className="rla-mono-cell">No content yet — add your first portfolio item.</span></td></tr>}
              {tableRows.map((r, i) => (
                <tr key={i}>
                  <td>
                    <div className="rla-doc-cell">
                      <span className="rla-doc-ic" style={{ background: r.bg, color: r.fg }}><i className={`fas ${r.icon}`} /></span>
                      <div><b>{r.b}</b><span>{r.s}</span></div>
                    </div>
                  </td>
                  <td><span className="rla-mono-cell">{r.type}</span></td>
                  <td><span className={`rla-pill ${r.pill[0]}`}>{r.pill[1]}</span></td>
                  <td><span className="rla-mono-cell">{r.updated}</span></td>
                  <td>
                    <div className="rla-row-actions">
                      <Link to={r.to} className="rla-mini-btn" title="Manage"><i className="fas fa-pen" /></Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
