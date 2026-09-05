/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Chip, Empty, PageHead, Panel, StatusPill } from "../../components/admin/ui";

const STATUSES = ["all", "new", "contacted", "qualified", "proposal", "won", "lost", "archived", "spam"];
const SETTABLE = ["new", "contacted", "qualified", "proposal", "won", "lost", "archived", "spam"];

export default function LeadsManage() {
  const [leads, setLeads] = useState<any[]>([]);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<any>(null);
  const [detail, setDetail] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [openSession, setOpenSession] = useState<string | null>(null);

  const load = () => {
    const params = new URLSearchParams();
    if (filter !== "all") params.set("status", filter);
    if (query.trim()) params.set("q", query.trim());
    api.get<any[]>(`/api/admin/leads?${params.toString()}`).then((l) => setLeads(Array.isArray(l) ? l : [])).catch(() => {});
  };
  useEffect(() => { load(); }, [filter]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const t = setTimeout(load, 400); return () => clearTimeout(t); }, [query]); // eslint-disable-line react-hooks/exhaustive-deps

  const openLead = async (id: string) => {
    const d = await api.get<any>(`/api/admin/leads/${id}`).catch(() => null);
    if (d) { setSelected(d.lead); setDetail(d); setMessages([]); setOpenSession(null); }
  };
  const setStatus = async (id: string, status: string) => {
    await api.patch(`/api/admin/leads/${id}`, { status }).catch((e) => alert(String(e.message || e)));
    openLead(id); load();
  };
  const openConversation = async (sid: string) => {
    if (openSession === sid) { setOpenSession(null); return; }
    const d = await api.get<any>(`/api/admin/chat/sessions/${sid}/messages`).catch(() => null);
    if (d) { setMessages(d.messages || []); setOpenSession(sid); }
  };

  return (
    <div>
      <PageHead title="Leads & Conversations" desc="AI chat leads with ideas, full conversations and lead scores. New enquiries appear here instantly."
        actions={<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search name, email, company…"
          className="rla-search-input" aria-label="Search leads" />} />
      <div className="rla-chip-row">
        {STATUSES.map((f) => (
          <Chip key={f} active={filter === f} onClick={() => { setFilter(f); }}>{f}</Chip>
        ))}
        <Chip onClick={load}>↻ Refresh</Chip>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rla-stack">
          {leads.map((l) => (
            <button key={l.id} onClick={() => void openLead(l.id)}
              className={`rla-list-card w-full text-left${selected?.id === l.id ? " selected" : ""}`}>
              <div className="flex flex-wrap justify-between gap-2">
                <span className="font-medium">{l.name || "(no name)"} <span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{l.company_name || ""}</span></span>
                <span className="rla-inline-actions"><StatusPill status={l.status} /><span className="rla-code">score {l.lead_score ?? 0}</span></span>
              </div>
              <div className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>{l.email || "—"} · {l.phone || "—"} · {l.created_at ? new Date(l.created_at).toLocaleString() : ""}</div>
            </button>
          ))}
          {leads.length === 0 && <Empty>No leads yet. They appear here when visitors chat.</Empty>}
        </div>
        <div>
          {!detail && <Panel title="Lead detail" sub="Select a lead on the left"><Empty>Select a lead to see ideas, conversations and activity.</Empty></Panel>}
          {detail && (
            <Panel title={detail.lead.name || "(no name)"}
              sub={`${detail.lead.email || "—"} · ${detail.lead.phone || "—"} · ${detail.lead.company_name || ""}${detail.lead.industry ? ` · ${detail.lead.industry}` : ""} · score ${detail.lead.lead_score ?? 0}${detail.lead.marketing_consent ? " · ✓ marketing consent" : ""}`}
              action={<span className="rla-inline-actions"><span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>Status:</span>
                <select value={detail.lead.status} onChange={(e) => void setStatus(detail.lead.id, e.target.value)} className="rla-select" style={{ fontSize: ".78rem", padding: "6px 10px" }}>
                  {SETTABLE.map((s) => <option key={s} value={s}>{s}</option>)}
                </select></span>}>
              <div>
                <div className="rla-section-title">Ideas ({detail.ideas.length})</div>
                {detail.ideas.map((idea: any) => (
                  <div key={idea.id} className="rla-list-card" style={{ marginBottom: 8 }}>
                    <div className="font-medium text-sm">{idea.title || idea.description?.slice(0, 80) || "(empty idea)"}</div>
                    {idea.problem_statement && <div className="mt-1 text-xs"><b>Problem:</b> {idea.problem_statement}</div>}
                    {idea.desired_outcome && <div className="text-xs"><b>Outcome:</b> {idea.desired_outcome}</div>}
                    <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{idea.status}{idea.preliminary_scope ? " · ✓ scope generated" : ""}</div>
                  </div>
                ))}
                {detail.ideas.length === 0 && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>No ideas captured yet.</div>}
              </div>
              <div style={{ marginTop: 14 }}>
                <div className="rla-section-title">Conversations ({detail.sessions.length})</div>
                {detail.sessions.map((s: any) => (
                  <div key={s.id || s.session_token} style={{ marginBottom: 8 }}>
                    <button onClick={() => void openConversation(s.session_token)} className="rla-list-card w-full text-left text-xs mono">
                      {s.session_token?.slice(0, 12)}… · {s.message_count ?? "?"} messages · {s.last_activity_at ? new Date(s.last_activity_at).toLocaleString() : ""} {openSession === s.session_token ? "▾" : "▸"}
                    </button>
                    {openSession === s.session_token && (
                      <div className="rla-list-card" style={{ marginTop: 6, background: "var(--rla-bg)" }}>
                        <div className="space-y-1 max-h-64 overflow-y-auto">
                          {messages.map((m: any, i: number) => (
                            <div key={i} className={m.sender === "user" ? "text-right" : "text-left"}>
                              <span className="inline-block px-2 py-1 rounded-lg text-xs" style={{ background: m.sender === "user" ? "var(--rla-violet)" : "#fff", color: m.sender === "user" ? "#fff" : "var(--rla-text)", border: m.sender === "user" ? "none" : "1px solid var(--rla-border)" }}>{m.message}</span>
                            </div>
                          ))}
                          {messages.length === 0 && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>No messages.</div>}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {detail.sessions.length === 0 && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>No sessions.</div>}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
