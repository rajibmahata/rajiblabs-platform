/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Chip, Empty, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

const FILTERS = ["all", "new", "hot", "warm", "qualified", "customer", "unsubscribed"];

export default function CustomersManage() {
  const [rows, setRows] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState("all");
  const [consent, setConsent] = useState("");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<any>(null);
  const [detail, setDetail] = useState<any>(null);

  const load = () => {
    const params = new URLSearchParams();
    if (filter === "hot") params.set("q", "");
    if (filter !== "all" && filter !== "hot") params.set("status", filter);
    if (consent) params.set("consent", consent);
    if (query.trim()) params.set("q", query.trim());
    api.get<any>(`/api/admin/marketing/customers?${params.toString()}`)
      .then((r) => {
        let items = Array.isArray(r.items) ? r.items : [];
        if (filter === "hot") items = items.filter((x: any) => (x.lead_score ?? 0) >= 50);
        setRows(items); setTotal(r.total ?? items.length);
      }).catch(() => {});
  };
  useEffect(() => { load(); }, [filter, consent]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const t = setTimeout(load, 400); return () => clearTimeout(t); }, [query]); // eslint-disable-line react-hooks/exhaustive-deps

  const openCustomer = async (id: string) => {
    const d = await api.get<any>(`/api/admin/marketing/customers/${id}`).catch(() => null);
    if (d) { setSelected(d.lead); setDetail(d); }
  };
  const unsubscribe = async (id: string) => {
    if (!confirm("Opt this customer out of ALL promotional email? Transactional follow-ups they request are unaffected.")) return;
    try {
      await api.post(`/api/admin/marketing/customers/${id}/unsubscribe`, {});
      toast("Unsubscribed", "Future promotional sends blocked.");
      openCustomer(id); load();
    } catch (e: any) { toast("Failed", String(e.message || e).slice(0, 160)); }
  };

  const fmtDT = (v: any) => (v ? new Date(v).toLocaleString() : "—");

  return (
    <div>
      <PageHead title="Customers" desc="Unified customer view: leads, consent, conversations, email history and timeline. One person, one record."
        actions={<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search name, email, company, phone…"
          className="rla-search-input" aria-label="Search customers" />} />
      <div className="rla-chip-row">
        {FILTERS.map((f) => <Chip key={f} active={filter === f} onClick={() => setFilter(f)}>{f}</Chip>)}
        <select value={consent} onChange={(e) => setConsent(e.target.value)} className="rla-select" aria-label="Consent filter">
          <option value="">consent: all</option>
          <option value="yes">✓ opted in</option>
          <option value="no">not opted in</option>
        </select>
        <Chip onClick={load}>↻ Refresh</Chip>
      </div>
      <p className="text-xs mt-2" style={{ color: "var(--rla-text-faint)" }}>{total} records · consent and opt-out enforced on every send</p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-2">
        <div className="rla-stack">
          {rows.map((l) => (
            <button key={l.id} onClick={() => void openCustomer(l.id)}
              className={`rla-list-card w-full text-left${selected?.id === l.id ? " selected" : ""}`}>
              <div className="flex flex-wrap justify-between gap-2">
                <span className="font-medium">{l.name || "(no name)"} <span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{l.company_name || ""}</span></span>
                <span className="rla-inline-actions"><StatusPill status={l.status} /><span className="rla-code">score {l.lead_score ?? 0}</span></span>
              </div>
              <div className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>
                {l.email || "—"} · {l.conversations} conversations · {l.emails_sent} emails
                {l.marketing_consent ? " · ✓ opted in" : ""}{l.unsubscribe ? " · ✕ opted out" : ""}
              </div>
            </button>
          ))}
          {rows.length === 0 && <Empty>No customers match. They appear here when visitors chat or subscribe.</Empty>}
        </div>
        <div>
          {!detail && <Panel title="Customer 360" sub="Select a customer on the left"><Empty>Select a customer to see profile, timeline and email history.</Empty></Panel>}
          {detail && (
            <div className="rla-stack">
              <Panel title={detail.lead.name || "(no name)"}
                sub={`${detail.lead.email || "—"} · ${detail.lead.phone || "—"} · score ${detail.lead.lead_score ?? 0}`}
                action={!detail.lead.unsubscribe ? <button onClick={() => void unsubscribe(detail.lead.id)} className="rla-mini-btn danger" title="Opt out of promotional email">Unsubscribe</button> : <StatusPill status="unsubscribed" />}>
                <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>
                  Status: <StatusPill status={detail.lead.status} /> · Source: {detail.lead.source || "—"} ·
                  Consent: {detail.lead.marketing_consent ? `✓ ${fmtDT(detail.lead.consent_timestamp)} (${detail.lead.consent_source || "?"})` : "—"}
                </div>
                {!!(detail.lead.score_reasons || []).length && (
                  <div className="text-xs mt-2"><b>Score reasons:</b> {detail.lead.score_reasons.join(" · ")}</div>
                )}
                {!!(detail.lead.interests || []).length && (
                  <div className="text-xs mt-1">Interests: {detail.lead.interests.join(", ")}</div>
                )}
              </Panel>
              <Panel title={`Timeline (${detail.timeline.length})`} sub="Lead, chat, consent, campaign and status events">
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  {detail.timeline.map((t: any, i: number) => (
                    <div key={i} className="text-xs"><span style={{ color: "var(--rla-text-faint)" }}>{t.at ? new Date(t.at).toLocaleString() : ""}</span> — <b>{t.action}</b> <span style={{ color: "var(--rla-text-faint)" }}>{t.actor || ""}</span></div>
                  ))}
                  {detail.timeline.length === 0 && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>No events yet.</div>}
                </div>
              </Panel>
              <Panel title={`Email history (${detail.email_history.length})`} sub="Sends and tracked engagement">
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {detail.email_history.map((s: any) => (
                    <div key={s.id} className="text-xs">
                      <StatusPill status={s.status} /> {s.subject || s.campaign_id}
                      <span style={{ color: "var(--rla-text-faint)" }}> · {s.created_at ? new Date(s.created_at).toLocaleString() : ""}{s.opened_at ? " · opened" : ""}{s.clicked_at ? " · clicked" : ""}{s.reason ? ` · ${s.reason}` : ""}</span>
                    </div>
                  ))}
                  {detail.email_history.length === 0 && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>No emails sent.</div>}
                </div>
              </Panel>
              <Panel title={`Conversations (${detail.conversations.length})`} sub="Chat sessions and ideas">
                {detail.conversations.map((c: any) => (
                  <div key={c.id || c.session_token} className="text-xs" style={{ color: "var(--rla-text-faint)" }}>
                    {c.session_token?.slice(0, 12)}… · {c.message_count ?? "?"} messages · {c.last_activity_at ? new Date(c.last_activity_at).toLocaleString() : ""}
                  </div>
                ))}
                {detail.conversations.length === 0 && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>No conversations.</div>}
              </Panel>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
