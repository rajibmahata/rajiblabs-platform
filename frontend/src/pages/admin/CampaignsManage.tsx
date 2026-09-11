/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { InlineLoader } from "../../components/admin/ui";
import { useAsyncActions } from "../../components/admin/async";
import { toast } from "../../components/admin/toast";

const EMPTY_FORM: any = { name: "", subject: "", html: "", text: "", template_id: "", segment: "all_opted_in", max_per_7_days: 2, min_interval_hours: 48 };
const SEGMENTS = ["all_opted_in", "new_leads", "hot_leads", "warm_leads", "project_interest", "ai_interest", "architecture_interest", "saas_interest", "automation_interest", "previous_customer"];

export default function CampaignsManage() {
  const [items, setItems] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [segments, setSegments] = useState<any[]>([]);
  const [settings, setSettings] = useState<any>(null);
  const [modal, setModal] = useState<"closed" | "create" | "detail">("closed");
  const [form, setForm] = useState<any>({ ...EMPTY_FORM });
  const [detail, setDetail] = useState<any>(null);
  const [eligible, setEligible] = useState<number | null>(null);
  const { run, isLoading } = useAsyncActions();
  const busy = isLoading("action");
  const setBusy = (_: boolean) => {}; // compat for legacy code, now driven by useAsyncActions

  const load = () => {
    api.get<any>("/api/admin/marketing/campaigns").then((r) => setItems(r.items || [])).catch(() => {});
    api.get<any>("/api/admin/marketing/templates").then((r) => setTemplates(r.items || [])).catch(() => {});
    api.get<any>("/api/admin/marketing/segments").then((r) => setSegments(r.segments || [])).catch(() => {});
    api.get<any>("/api/admin/marketing/settings").then(setSettings).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const create = async () => {
    if (!form.name.trim() || !form.subject.trim()) { toast("Validation", "Name + subject required."); return; }
    if (!form.template_id && !form.html.trim() && !form.text.trim()) { toast("Validation", "Pick a template or write content."); return; }
    setBusy(true);
    try {
      await api.post("/api/admin/marketing/campaigns", {
        name: form.name.trim(), subject: form.subject.trim(),
        html: form.html, text: form.text,
        template_id: form.template_id || null,
        audience: { segment: form.segment, tags: [], statuses: [] },
        max_per_7_days: Number(form.max_per_7_days) || 2,
        min_interval_hours: Number(form.min_interval_hours) || 48,
      });
      toast("Draft created", "Review, then Approve & Send."); setModal("closed"); setForm({ ...EMPTY_FORM }); load();
    } catch (e: any) { toast("Create failed", String(e.message || e).slice(0, 200)); } finally { setBusy(false); }
  };
  const openDetail = async (id: string) => {
    const d = await api.get<any>(`/api/admin/marketing/campaigns/${id}`).catch(() => null);
    if (d) { setDetail(d); setEligible(null); setModal("detail"); }
  };
  const previewAudience = async () => {
    if (!detail) return;
    const r = await api.post<any>(`/api/admin/marketing/campaigns/${detail.id}/audience-preview`, {}).catch(() => null);
    if (r) setEligible(r.eligible ?? 0);
  };
  const decide = async (action: string) => {
    if (!detail) return;
    if (action === "send" && !confirm(`Send "${detail.name}" now? Only eligible opted-in recipients, frequency caps apply.`)) return;
    setBusy(true);
    try {
      const r = await api.post<any>(`/api/admin/marketing/campaigns/${detail.id}/decision`, { action });
      toast(action === "send" ? "Send finished" : "Updated", action === "send" ? `Sent ${r.sent ?? 0}, skipped ${r.skipped ?? 0}, failed ${r.failed ?? 0}.` : "");
      openDetail(detail.id); load();
    } catch (e: any) { toast("Failed", String(e.message || e).slice(0, 200)); } finally { setBusy(false); }
  };
  const saveSettings = async (patch: any) => {
    try {
      const r = await api.put<any>("/api/admin/marketing/settings", patch);
      setSettings({ ...(settings || {}), ...(r.settings || patch) });
      toast("Saved", "Agent policy updated.");
    } catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 200)); }
  };
  const runAgent = async () => {
    setBusy(true);
    try {
      const r = await api.post<any>("/api/admin/marketing/agent/run", {});
      toast("Agent ran", `${r.action}${r.campaign_id ? ` · ${r.campaign_id.slice(0, 8)}` : ""}${r.reason ? ` · ${r.reason}` : ""}`);
      load();
    } catch (e: any) { toast("Agent failed", String(e.message || e).slice(0, 200)); } finally { setBusy(false); }
  };

  return (
    <div>
      <PageHead title="Promotional Campaigns" desc="Draft-first by default. Sends go only to eligible opted-in recipients with frequency caps."
        actions={<><button onClick={() => setModal("create")} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-plus" /> New campaign</button>
          <button onClick={() => void runAgent()} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm" title="Run the marketing agent now (all gates apply)"><i className="fas fa-robot" /> Run agent</button></>} />
      <Panel title="Audience segments" sub="Eligible right now (consent + opt-out + valid email enforced)">
        <div className="rla-chip-row">{segments.map((s: any) => <span key={s.segment} className="rla-chip">{s.segment}: <b>{s.eligible}</b></span>)}</div>
      </Panel>
      <div style={{ height: 12 }} />
      <Panel title="Campaigns" sub="History with delivery stats">
        <div className="rla-table-wrap"><table className="rla-table">
          <thead><tr><th>Name</th><th>Status</th><th>Sent</th><th>Failed</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
          <tbody>{items.map((c) => (
            <tr key={c.id}>
              <td><b>{c.name}</b><div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{c.subject}</div></td>
              <td><StatusPill status={c.status} /></td>
              <td>{c.sent ?? 0}</td><td>{c.failed ?? 0}</td>
              <td><div className="rla-row-actions" style={{ justifyContent: "flex-end" }}>
                <button onClick={() => void openDetail(c.id)} className="rla-mini-btn" title="Open"><i className="fas fa-eye" /></button>
              </div></td>
            </tr>))}
          </tbody>
        </table>
        {items.length === 0 && <Empty>No campaigns yet. Create a draft to begin.</Empty>}</div>
      </Panel>
      <div style={{ height: 12 }} />
      {settings && (
        <Panel title="Autonomous agent policy" sub="Daily 09:00 run. Draft-first is the safe default.">
          <div className="rla-form-grid">
            <Field label="Enabled"><input type="checkbox" checked={!!settings.enabled} onChange={(e) => void saveSettings({ enabled: e.target.checked })} /></Field>
            <Field label="Auto-send drafts"><input type="checkbox" checked={!!settings.auto_send} onChange={(e) => void saveSettings({ auto_send: e.target.checked })} /></Field>
            <Field label="Max emails / customer / 7 days"><input type="number" min={1} max={10} value={settings.max_per_7_days ?? 2} onChange={(e) => void saveSettings({ max_per_7_days: Number(e.target.value) || 2 })} className="rla-input" /></Field>
            <Field label="Min hours between emails"><input type="number" min={1} value={settings.min_interval_hours ?? 48} onChange={(e) => void saveSettings({ min_interval_hours: Number(e.target.value) || 48 })} className="rla-input" /></Field>
          </div>
        </Panel>
      )}
      {modal === "create" && (
        <div className="rla-modal-overlay" onClick={() => !busy && setModal("closed")}>
          <div className="rla-modal rla-modal-wide" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="New campaign">
            <div className="rla-modal-head"><h3>New campaign (starts as draft)</h3><button onClick={() => setModal("closed")} className="rla-mini-btn">✕</button></div>
            <div className="rla-form-grid">
              <Field label="Name"><input value={form.name} onChange={(e) => set("name", e.target.value)} className="rla-input" /></Field>
              <Field label="Audience segment"><select value={form.segment} onChange={(e) => set("segment", e.target.value)} className="rla-select">
                {SEGMENTS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select></Field>
              <Field label="Subject" span><input value={form.subject} onChange={(e) => set("subject", e.target.value)} className="rla-input" /></Field>
              <Field label="Template (optional)" span><select value={form.template_id} onChange={(e) => set("template_id", e.target.value)} className="rla-select">
                <option value="">— inline content —</option>
                {templates.filter((t: any) => t.status === "active").map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select></Field>
              <Field label="HTML" span><textarea value={form.html} onChange={(e) => set("html", e.target.value)} rows={6} className="rla-textarea rla-mono" /></Field>
              <Field label="Text" span><textarea value={form.text} onChange={(e) => set("text", e.target.value)} rows={3} className="rla-textarea" /></Field>
            </div>
            <div className="rla-inline-actions" style={{ marginTop: 12 }}>
              <button onClick={() => void create()} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">{busy ? "Saving…" : "Create draft"}</button>
              <button onClick={() => setModal("closed")} className="rla-btn rla-btn-ghost rla-btn-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}
      {modal === "detail" && detail && (
        <div className="rla-modal-overlay" onClick={() => setModal("closed")}>
          <div className="rla-modal rla-modal-wide" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Campaign detail">
            <div className="rla-modal-head"><h3>{detail.name}</h3><button onClick={() => setModal("closed")} className="rla-mini-btn">✕</button></div>
            <p className="text-sm"><StatusPill status={detail.status} /> <span style={{ color: "var(--rla-text-faint)" }}>{detail.subject}</span></p>
            <div className="rla-inline-actions" style={{ margin: "10px 0" }}>
              <button onClick={() => void previewAudience()} className="rla-btn rla-btn-ghost rla-btn-sm">Preview audience{eligible !== null ? `: ${eligible}` : ""}</button>
              {(detail.status === "draft") && <button onClick={() => void decide("approve")} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm">Approve</button>}
              {(["draft", "ready", "scheduled"].includes(detail.status)) && <button onClick={() => void decide("send")} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">Approve & Send</button>}
              {(detail.status === "ready") && <button onClick={() => void decide("pause")} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm">Pause</button>}
              {(["draft", "ready", "paused"].includes(detail.status)) && <button onClick={() => void decide("cancel")} disabled={busy} className="rla-mini-btn danger">Cancel</button>}
            </div>
            <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>
              Stats — sent {detail.stats?.sent ?? 0} · failed {detail.stats?.failed ?? 0} · opened {detail.stats?.opened ?? 0} · clicked {detail.stats?.clicked ?? 0} · unsubscribed {detail.stats?.unsubscribed ?? 0}
            </div>
            <div className="space-y-1 mt-2 max-h-64 overflow-y-auto">
              {(detail.sends || []).map((s: any) => (
                <div key={s.id} className="text-xs"><StatusPill status={s.status} /> {s.email}
                  <span style={{ color: "var(--rla-text-faint)" }}>{s.reason ? ` · ${s.reason}` : ""}{s.opened_at ? " · opened" : ""}{s.clicked_at ? " · clicked" : ""}</span>
                </div>
              ))}
              {!(detail.sends || []).length && <Empty>No sends recorded.</Empty>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
