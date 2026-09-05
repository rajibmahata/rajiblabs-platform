/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, PageHead, Panel, StatusPill } from "../../components/admin/ui";

type LogEntry = {
  id: string; level: string; source: string; logger?: string | null;
  path?: string | null; message: string; details?: string;
  stack_trace?: string | null; created_at: string;
};
type LogPage = {
  items: LogEntry[]; total: number; page: number; page_size: number;
  retention_days: number; window_start: string;
};
type Stats = { retention_days: number; total_in_window: number; by_level: Record<string, number> };

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
const PAGE_SIZES = [25, 50, 100];

const fmtTime = (iso: string) => {
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
};
const trunc = (s: string, n = 120) => (s && s.length > n ? s.slice(0, n) + "…" : s || "—");

export default function LogsManage() {
  const [page, setPage] = useState<LogPage | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [q, setQ] = useState("");
  const [level, setLevel] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sort, setSort] = useState<"newest" | "oldest">("newest");
  const [pageNo, setPageNo] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [selected, setSelected] = useState<LogEntry | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const load = (p = pageNo) => {
    setLoading(true); setErr("");
    const params = new URLSearchParams({ page: String(p), page_size: String(pageSize), sort });
    if (q.trim()) params.set("q", q.trim());
    if (level !== "all") params.set("level", level);
    if (dateFrom) params.set("date_from", new Date(dateFrom).toISOString());
    if (dateTo) params.set("date_to", new Date(dateTo).toISOString());
    api.get<LogPage>(`${BASE}/api/admin/logs?${params}`)
      .then((r) => setPage(r && Array.isArray(r.items) ? r : null))
      .catch((e) => setErr(String((e as Error)?.message || e)))
      .finally(() => setLoading(false));
    api.get<Stats>(`${BASE}/api/admin/logs/stats`).then(setStats).catch(() => {});
  };

  // Debounced reload (page resets to 1 in the input handlers below).
  useEffect(() => {
    const t = setTimeout(() => load(pageNo), 400);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, level, dateFrom, dateTo, sort, pageSize, pageNo]);

  // ESC closes the details modal.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setSelected(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const clearFilters = () => {
    setQ(""); setLevel("all"); setDateFrom(""); setDateTo("");
    setSort("newest"); setPageSize(25); setPageNo(1);
  };

  const purge = async () => {
    if (!confirm(`Delete ALL system logs now? (Entries older than ${stats?.retention_days ?? 7} days expire automatically.)`)) return;
    try { await api.del(`${BASE}/api/admin/logs`); load(1); setPageNo(1); } catch (e: any) { alert(String(e.message || e)); }
  };

  const totalPages = page ? Math.max(1, Math.ceil(page.total / page.page_size)) : 1;
  const items = page?.items ?? [];

  return (
    <div>
      <PageHead title="System Logs"
        desc={<>Failures from agents, sync, AI and chat — latest {stats?.retention_days ?? 7} days only.
          {stats && <> · {stats.total_in_window} in window · {stats.by_level.error ?? 0} errors · {stats.by_level.warning ?? 0} warnings · {stats.by_level.info ?? 0} info</>}</>}
        actions={<button onClick={purge} className="rla-btn rla-btn-ghost rla-btn-sm rla-danger-text" style={{ borderColor: "#f0b6b6" }}><i className="fas fa-trash" /> Purge now</button>} />

      <Panel title="Search & filters" sub="Message, source, module, path and error text">
        <div className="rla-filter-grid">
          <input value={q} onChange={e => { setQ(e.target.value); setPageNo(1); }} placeholder="Search message / source / error…" className="rla-input" aria-label="Search logs" />
          <select value={level} onChange={e => { setLevel(e.target.value); setPageNo(1); }} className="rla-select" aria-label="Log level">
            <option value="all">all levels</option>
            <option value="error">error</option>
            <option value="warning">warning</option>
            <option value="info">info</option>
          </select>
          <input type="datetime-local" value={dateFrom} onChange={e => { setDateFrom(e.target.value); setPageNo(1); }} className="rla-input" aria-label="From date" />
          <input type="datetime-local" value={dateTo} onChange={e => { setDateTo(e.target.value); setPageNo(1); }} className="rla-input" aria-label="To date" />
          <select value={sort} onChange={e => { setSort(e.target.value as "newest" | "oldest"); setPageNo(1); }} className="rla-select" aria-label="Sort order">
            <option value="newest">newest first</option>
            <option value="oldest">oldest first</option>
          </select>
          <select value={pageSize} onChange={e => { setPageSize(Number(e.target.value)); setPageNo(1); }} className="rla-select" aria-label="Page size">
            {PAGE_SIZES.map(n => <option key={n} value={n}>{n} / page</option>)}
          </select>
          <button onClick={clearFilters} className="rla-btn rla-btn-ghost rla-btn-sm">Clear</button>
        </div>
      </Panel>
      <div style={{ height: 16 }} />

      {err && <Panel title="Backend unreachable"><span className="text-sm rla-danger-text">{err} — is the FastAPI backend reachable?</span></Panel>}
      {err && <div style={{ height: 16 }} />}

      <Panel title={`Entries${page ? ` — ${page.total} total` : ""}`} sub={loading ? "Loading…" : `Page ${pageNo} of ${totalPages}`}>
        <div className="rla-table-wrap">
          <table className="rla-table">
            <thead><tr>
              <th><button onClick={() => { setSort(s => s === "newest" ? "oldest" : "newest"); setPageNo(1); }} className="rla-th-sort" title="Toggle sort">Time {sort === "newest" ? "↓" : "↑"}</button></th>
              <th>Level</th><th>Source</th><th>Message</th><th style={{ textAlign: "right" }}>Actions</th>
            </tr></thead>
            <tbody>
              {items.map(l => (
                <tr key={l.id}>
                  <td className="rla-nowrap">{fmtTime(l.created_at)}</td>
                  <td><StatusPill status={l.level} /></td>
                  <td><span className="rla-code">{l.source}</span>{l.logger && <div className="rla-sub">{l.logger}</div>}</td>
                  <td title={l.message}>{trunc(l.message)}</td>
                  <td><div className="rla-row-actions" style={{ justifyContent: "flex-end" }}>
                    <button onClick={() => setSelected(l)} className="rla-mini-btn" title="View details"><i className="fas fa-eye" /></button>
                  </div></td>
                </tr>
              ))}
            </tbody>
          </table>
          {items.length === 0 && !loading && <Empty>No logs match — systems healthy or filters too narrow.</Empty>}
        </div>
        <div className="rla-pager">
          <button disabled={pageNo <= 1} onClick={() => setPageNo(p => Math.max(1, p - 1))} className="rla-btn rla-btn-ghost rla-btn-sm">← Prev</button>
          <span>Page {pageNo} of {totalPages} · {page?.total ?? 0} entries</span>
          <button disabled={pageNo >= totalPages} onClick={() => setPageNo(p => p + 1)} className="rla-btn rla-btn-ghost rla-btn-sm">Next →</button>
        </div>
      </Panel>

      {selected && (
        <div className="rla-modal-overlay" onClick={() => setSelected(null)}>
          <div className="rla-modal" onClick={e => e.stopPropagation()} role="dialog" aria-label="Log details">
            <div className="rla-modal-head">
              <h3>Log details</h3>
              <button onClick={() => setSelected(null)} className="rla-mini-btn" title="Close">✕</button>
            </div>
            <dl className="rla-kv">
              <dt>ID</dt><dd className="rla-code">{selected.id}</dd>
              <dt>Time</dt><dd>{fmtTime(selected.created_at)}</dd>
              <dt>Level</dt><dd><StatusPill status={selected.level} /></dd>
              <dt>Source</dt><dd className="rla-code">{selected.source}</dd>
              {selected.logger && <><dt>Module</dt><dd className="rla-code">{selected.logger}</dd></>}
              {selected.path && <><dt>Path</dt><dd className="rla-code">{selected.path}</dd></>}
              <dt>Message</dt><dd>{selected.message}</dd>
            </dl>
            {selected.details ? <><h4>Error details</h4><pre className="rla-pre">{selected.details}</pre></> : null}
            {selected.stack_trace ? <><h4>Stack trace</h4><pre className="rla-pre">{selected.stack_trace}</pre></> : null}
          </div>
        </div>
      )}
    </div>
  );
}
