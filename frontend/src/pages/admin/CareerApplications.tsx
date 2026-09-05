/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

const STATUSES = ["all", "Draft", "AI Generated", "Needs Review", "Approved", "Sent", "Follow-up", "Response Received", "Interview", "Rejected", "Offer", "Closed"];
const SETTABLE = ["Draft", "AI Generated", "Needs Review", "Approved", "Sent", "Follow-up", "Response Received", "Interview", "Rejected", "Offer", "Closed"];

export default function CareerApplications() {
  const [list, setList] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [companyId, setCompanyId] = useState("");
  const [companies, setCompanies] = useState<any[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sortNewest, setSortNewest] = useState(true);
  const [sel, setSel] = useState<any>(null);
  const [notes, setNotes] = useState("");
  const [followup, setFollowup] = useState("");
  const pageSize = 20;

  const load = (p = page) => {
    const params = new URLSearchParams({ page: String(p), limit: String(pageSize), sort: sortNewest ? "-created" : "created" });
    if (q.trim()) params.set("q", q.trim());
    if (status !== "all") params.set("status", status);
    if (companyId) params.set("company_id", companyId);
    if (dateFrom) params.set("date_from", new Date(dateFrom).toISOString());
    if (dateTo) params.set("date_to", new Date(dateTo).toISOString());
    api.get<any>(`/api/admin/career/applications?${params}`).then((r) => {
      setList(r.items || []); setTotal(r.total || 0);
    }).catch(() => {});
  };
  useEffect(() => {
    api.get<any>("/api/admin/career/companies").then((r) => setCompanies(r.items || [])).catch(() => {});
    load(1);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const t = setTimeout(() => { setPage(1); load(1); }, 400); return () => clearTimeout(t); },
    [q, status, companyId, dateFrom, dateTo, sortNewest]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { load(page); }, [page]); // eslint-disable-line react-hooks/exhaustive-deps

  const openApp = async (id: string) => {
    const d = await api.get<any>(`/api/admin/career/applications/${id}`).catch(() => null);
    if (d) { setSel(d); setNotes(d.notes || ""); setFollowup(d.followup_date ? String(d.followup_date).slice(0, 16) : ""); }
  };
  const saveMeta = async () => {
    if (!sel) return;
    try {
      const r = await api.put<any>(`/api/admin/career/applications/${sel.id}`,
        { notes, followup_date: followup || null });
      setSel(r); load(page); toast("Saved", "Notes updated.");
    } catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 160)); }
  };
  const setAppStatus = async (s: string) => {
    if (!sel) return;
    try {
      const r = await api.post<any>(`/api/admin/career/applications/${sel.id}/status`, { status: s });
      setSel(r); load(page); toast("Status", `Application → ${s}.`);
    } catch (e: any) { toast("Update failed", String(e.message || e).slice(0, 160)); }
  };
  const approve = async () => {
    if (!sel || !confirm("Approve this application for sending?")) return;
    try {
      const r = await api.post<any>(`/api/admin/career/applications/${sel.id}/approve`, {});
      setSel(r); load(page); toast("Approved", "Ready to send.");
    } catch (e: any) { toast("Approve failed", String(e.message || e).slice(0, 160)); }
  };
  const sendNow = async () => {
    if (!sel) return;
    if (!confirm(`Send to ${sel.contact_snapshot?.email || "(no contact)"}?`)) return;
    try {
      const r = await api.post<any>(`/api/admin/career/applications/${sel.id}/send`, {});
      const d = await api.get<any>(`/api/admin/career/applications/${sel.id}`).catch(() => null);
      if (d) setSel(d);
      load(page);
      toast("Sent", `Emailed (${r.to_domain}).`);
    } catch (e: any) { toast("Send failed", String(e.message || e).slice(0, 200)); }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div>
      <PageHead title="Career — Applications" desc="Every application with full history: match, artifacts, approvals, sends, responses." />
      <div className="rla-filter-grid">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search job, company, subject…" className="rla-input" aria-label="Search applications" />
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="rla-select" aria-label="Status">
          {STATUSES.map((s) => <option key={s} value={s}>{s === "all" ? "all statuses" : s}</option>)}
        </select>
        <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} className="rla-select" aria-label="Company">
          <option value="">all companies</option>
          {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="rla-input" aria-label="From date" />
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="rla-input" aria-label="To date" />
        <button onClick={() => setSortNewest((v) => !v)} className="rla-btn rla-btn-ghost rla-btn-sm">Sort: {sortNewest ? "newest" : "oldest"}</button>
        <button onClick={() => { setQ(""); setStatus("all"); setCompanyId(""); setDateFrom(""); setDateTo(""); }} className="rla-btn rla-btn-ghost rla-btn-sm">Clear</button>
      </div>
      <div style={{ height: 12 }} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rla-stack">
          {list.map((a) => (
            <button key={a.id} onClick={() => void openApp(a.id)}
              className={`rla-list-card w-full text-left${sel?.id === a.id ? " selected" : ""}`}>
              <div className="flex flex-wrap justify-between gap-2">
                <span className="font-medium">{a.job_title || "(untitled)"} <span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{a.company_name || ""}</span></span>
                <span className="rla-inline-actions"><StatusPill status={a.status} /><span className="rla-code">score {a.match_score ?? 0}</span></span>
              </div>
              <div className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>
                {(a.email_subject || "").slice(0, 90)}{a.created_at ? ` · ${new Date(a.created_at).toLocaleDateString()}` : ""}{a.sent_at ? ` · sent ${new Date(a.sent_at).toLocaleDateString()}` : ""}{a.followup_date ? ` · follow-up ${String(a.followup_date).slice(0, 10)}` : ""}
              </div>
            </button>
          ))}
          {list.length === 0 && <Empty>No applications match. Generate one from the workspace.</Empty>}
          <div className="rla-pager">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="rla-btn rla-btn-ghost rla-btn-sm">← Prev</button>
            <span>Page {page} of {totalPages} · {total} total</span>
            <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="rla-btn rla-btn-ghost rla-btn-sm">Next →</button>
          </div>
        </div>
        <div>
          {!sel && <Panel title="Application detail" sub="Select an application on the left"><Empty>Full artifacts, approvals, send history and notes.</Empty></Panel>}
          {sel && (
            <Panel title={sel.job_title || "(untitled)"} sub={`${sel.company_name || ""} · match ${sel.match_score ?? 0}`}
              action={<StatusPill status={sel.status} />}>
              <div className="text-xs space-y-1" style={{ color: "var(--rla-text-faint)" }}>
                <div>Contact: {sel.contact_snapshot ? `${sel.contact_snapshot.name} <${sel.contact_snapshot.email}>` : "—"}</div>
                {sel.sent_at && <div>Sent: {new Date(sel.sent_at).toLocaleString()}</div>}
                {sel.approved_by && <div>Approved by {sel.approved_by}{sel.approved_at ? ` · ${new Date(sel.approved_at).toLocaleString()}` : ""}</div>}
                {sel.response_at && <div>Response: {new Date(sel.response_at).toLocaleString()}</div>}
              </div>
              <div className="rla-section-title" style={{ marginTop: 10 }}>Email</div>
              <div className="text-sm font-medium">{sel.email_subject}</div>
              <pre className="rla-pre">{sel.email_body}</pre>
              <div className="rla-section-title" style={{ marginTop: 10 }}>Cover letter</div>
              <pre className="rla-pre">{sel.cover_letter || "(empty)"}</pre>
              <div className="rla-section-title" style={{ marginTop: 10 }}>Summary</div>
              <div className="text-sm">{sel.summary || "(empty)"}</div>
              {(sel.sources || []).length > 0 && (<>
                <div className="rla-section-title" style={{ marginTop: 10 }}>Sources</div>
                {sel.sources.map((s: any, i: number) => (
                  <div key={i} className="text-xs py-0.5"><b>{s.title}</b> <span style={{ color: "var(--rla-text-faint)" }}>({s.type})</span> — {s.reason || ""} {s.url && <a href={s.url} target="_blank" rel="noreferrer" className="underline">open ↗</a>}</div>
                ))}
              </>)}
              <div className="rla-section-title" style={{ marginTop: 10 }}>Track</div>
              <div className="rla-form-grid">
                <Field label="Status"><select value={sel.status} onChange={(e) => setAppStatus(e.target.value)} className="rla-select">
                  {SETTABLE.map((s) => <option key={s} value={s}>{s}</option>)}
                </select></Field>
                <Field label="Follow-up date"><input type="datetime-local" value={followup} onChange={(e) => setFollowup(e.target.value)} className="rla-input" /></Field>
                <Field label="Notes" span><textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} className="rla-textarea" /></Field>
              </div>
              <div className="rla-inline-actions" style={{ marginTop: 10 }}>
                <button onClick={saveMeta} className="rla-btn rla-btn-ghost rla-btn-sm">Save notes</button>
                {(sel.status === "Draft" || sel.status === "AI Generated" || sel.status === "Needs Review") && (
                  <button onClick={approve} className="rla-btn rla-btn-ghost rla-btn-sm">Approve</button>)}
                {sel.status === "Approved" && <button onClick={sendNow} className="rla-btn rla-btn-primary rla-btn-sm">Send…</button>}
                {sel.status === "Sent" && <button onClick={async () => { if (confirm("Resend this application?")) { try { await api.post(`/api/admin/career/applications/${sel.id}/send`, { resend: true }); toast("Resent", ""); openApp(sel.id); } catch (e: any) { toast("Resend failed", String(e.message || e).slice(0, 160)); } } }} className="rla-btn rla-btn-ghost rla-btn-sm">Resend</button>}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
