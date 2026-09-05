/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Chip, Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

const BLANK_COMPANY: any = { name: "", website: "", industry: "", careers_url: "", linkedin_url: "", location: "", description: "", active: true, notes: "" };
const BLANK_CONTACT: any = { name: "", email: "", designation: "", department: "", contact_type: "HR", source: "", verified: false, active: true, notes: "" };
const TYPES = ["HR", "Recruiter", "Talent Acquisition", "General"];

export default function CareerCompanies() {
  const [list, setList] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [activeOnly, setActiveOnly] = useState(false);
  const [form, setForm] = useState<any>({ ...BLANK_COMPANY });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [sel, setSel] = useState<any>(null);
  const [contacts, setContacts] = useState<any[]>([]);
  const [cform, setCform] = useState<any>({ ...BLANK_CONTACT });
  const [cedit, setCedit] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    const p = new URLSearchParams();
    if (q.trim()) p.set("q", q.trim());
    if (activeOnly) p.set("active", "true");
    api.get<any>(`/api/admin/career/companies?${p}`).then((r) => setList(r.items || [])).catch(() => {});
  };
  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const t = setTimeout(load, 400); return () => clearTimeout(t); }, [q, activeOnly]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadContacts = (cid: string) => {
    api.get<any>(`/api/admin/career/contacts?company_id=${cid}`).then((r) => setContacts(r.items || [])).catch(() => {});
  };
  const select = async (id: string) => {
    const d = await api.get<any>(`/api/admin/career/companies/${id}`).catch(() => null);
    if (d) { setSel(d); setEditingId(null); setForm({ ...BLANK_COMPANY }); loadContacts(id); }
  };
  const saveCompany = async () => {
    if (form.name.trim().length < 2) { toast("Validation", "Company name is required."); return; }
    setBusy(true);
    try {
      if (editingId) { await api.put(`/api/admin/career/companies/${editingId}`, form); toast("Saved", "Company updated."); }
      else { const r = await api.post<any>("/api/admin/career/companies", form); toast("Created", "Company added."); select(r.id); }
      setForm({ ...BLANK_COMPANY }); setEditingId(null); load();
    } catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 160)); } finally { setBusy(false); }
  };
  const delCompany = async (id: string) => {
    if (!confirm("Delete this company? Blocked while jobs or contacts exist.")) return;
    try { await api.del(`/api/admin/career/companies/${id}`); if (sel?.id === id) { setSel(null); setContacts([]); } load(); }
    catch (e: any) { toast("Delete failed", String(e.message || e).slice(0, 160)); }
  };
  const saveContact = async () => {
    if (!sel) return;
    if (cform.name.trim().length < 2 || !/.+@.+\..+/.test(cform.email)) { toast("Validation", "Contact name + valid email required."); return; }
    setBusy(true);
    try {
      if (cedit) await api.put(`/api/admin/career/contacts/${cedit}`, { ...cform, company_id: sel.id });
      else await api.post("/api/admin/career/contacts", { ...cform, company_id: sel.id });
      setCform({ ...BLANK_CONTACT }); setCedit(null); loadContacts(sel.id); load();
      toast("Saved", "Contact saved.");
    } catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 160)); } finally { setBusy(false); }
  };
  const delContact = async (id: string) => {
    if (!confirm("Delete this contact? Blocked while used by applications.")) return;
    try { await api.del(`/api/admin/career/contacts/${id}`); if (sel) loadContacts(sel.id); }
    catch (e: any) { toast("Delete failed", String(e.message || e).slice(0, 160)); }
  };
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const cset = (k: string, v: any) => setCform((f: any) => ({ ...f, [k]: v }));

  return (
    <div>
      <PageHead title="Career — Companies" desc="Target employers and their HR/recruiter contacts."
        actions={<input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, industry, location…"
          className="rla-search-input" aria-label="Search companies" />} />
      <div className="rla-chip-row">
        <Chip active={!activeOnly} onClick={() => setActiveOnly(false)}>all</Chip>
        <Chip active={activeOnly} onClick={() => setActiveOnly(true)}>active only</Chip>
        <Chip onClick={load}>↻ Refresh</Chip>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rla-stack">
          {list.map((c) => (
            <button key={c.id} onClick={() => void select(c.id)}
              className={`rla-list-card w-full text-left${sel?.id === c.id ? " selected" : ""}`}>
              <div className="flex flex-wrap justify-between gap-2">
                <span className="font-medium">{c.name} <span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{c.industry || ""} · {c.location || ""}</span></span>
                <span className="rla-inline-actions"><StatusPill status={c.active ? "active" : "inactive"} />
                  <span className="rla-code">{c.contact_count ?? 0} contacts · {c.job_count ?? 0} jobs</span></span>
              </div>
              <div className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>{c.website || "—"}</div>
            </button>
          ))}
          {list.length === 0 && <Empty>No companies yet — add the first target employer below.</Empty>}
          <Panel title={editingId ? "Edit company" : "Add company"} sub="Drafts stay inactive until marked active">
            <div className="rla-form-grid">
              <Field label="Name"><input value={form.name} onChange={(e) => set("name", e.target.value)} className="rla-input" /></Field>
              <Field label="Website"><input value={form.website} onChange={(e) => set("website", e.target.value)} placeholder="https://…" className="rla-input" /></Field>
              <Field label="Industry"><input value={form.industry} onChange={(e) => set("industry", e.target.value)} className="rla-input" /></Field>
              <Field label="Location"><input value={form.location} onChange={(e) => set("location", e.target.value)} className="rla-input" /></Field>
              <Field label="Careers URL"><input value={form.careers_url} onChange={(e) => set("careers_url", e.target.value)} className="rla-input" /></Field>
              <Field label="LinkedIn URL"><input value={form.linkedin_url} onChange={(e) => set("linkedin_url", e.target.value)} className="rla-input" /></Field>
              <Field label="Description" span><textarea value={form.description} onChange={(e) => set("description", e.target.value)} rows={2} className="rla-textarea" /></Field>
              <Field label="Notes" span><textarea value={form.notes} onChange={(e) => set("notes", e.target.value)} rows={2} className="rla-textarea" /></Field>
              <Field label="Active"><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!form.active} onChange={(e) => set("active", e.target.checked)} /> Active</label></Field>
            </div>
            <div className="rla-inline-actions" style={{ marginTop: 10 }}>
              <button onClick={saveCompany} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">{busy ? "Saving…" : editingId ? "Save" : "Add Company"}</button>
              {editingId && <button onClick={() => { setEditingId(null); setForm({ ...BLANK_COMPANY }); }} className="rla-btn rla-btn-ghost rla-btn-sm">Cancel</button>}
            </div>
          </Panel>
        </div>
        <div>
          {!sel && <Panel title="Contacts" sub="Select a company on the left"><Empty>HR/recruiter contacts live here — multiple per company.</Empty></Panel>}
          {sel && (
            <Panel title={`Contacts — ${sel.name}`}
              action={<div className="rla-inline-actions">
                <button onClick={() => { setEditingId(sel.id); setForm({ ...BLANK_COMPANY, ...sel }); window.scrollTo({ top: 0 }); }} className="rla-btn rla-btn-ghost rla-btn-sm">Edit company</button>
                <button onClick={() => delCompany(sel.id)} className="rla-mini-btn danger" title="Delete company"><i className="fas fa-trash" /></button>
              </div>}>
              <div className="rla-stack">
                {contacts.map((c) => (
                  <div key={c.id} className="rla-list-card text-sm">
                    <div className="flex flex-wrap justify-between gap-2">
                      <span className="font-medium">{c.name} <span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{c.designation || ""} · {c.contact_type}{c.verified ? " · ✓ verified" : ""}</span></span>
                      <span className="rla-inline-actions"><StatusPill status={c.active ? "active" : "inactive"} />
                        <button onClick={() => { setCedit(c.id); setCform({ ...BLANK_CONTACT, ...c }); }} className="rla-mini-btn" title="Edit"><i className="fas fa-pen" /></button>
                        <button onClick={() => delContact(c.id)} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button></span>
                    </div>
                    <div className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>{c.email} · {c.department || "—"}{c.source ? ` · via ${c.source}` : ""}</div>
                    {c.notes && <div className="text-xs mt-1">{c.notes}</div>}
                  </div>
                ))}
                {contacts.length === 0 && <Empty>No contacts yet for this company.</Empty>}
              </div>
              <div className="rla-section-title" style={{ marginTop: 12 }}>{cedit ? "Edit contact" : "Add contact"}</div>
              <div className="rla-form-grid">
                <Field label="Name"><input value={cform.name} onChange={(e) => cset("name", e.target.value)} className="rla-input" /></Field>
                <Field label="Email"><input value={cform.email} onChange={(e) => cset("email", e.target.value)} className="rla-input" /></Field>
                <Field label="Designation"><input value={cform.designation} onChange={(e) => cset("designation", e.target.value)} className="rla-input" /></Field>
                <Field label="Department"><input value={cform.department} onChange={(e) => cset("department", e.target.value)} className="rla-input" /></Field>
                <Field label="Type"><select value={cform.contact_type} onChange={(e) => cset("contact_type", e.target.value)} className="rla-select">
                  {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}</select></Field>
                <Field label="Source"><input value={cform.source} onChange={(e) => cset("source", e.target.value)} placeholder="LinkedIn, referral…" className="rla-input" /></Field>
                <Field label="Flags"><div className="rla-inline-actions">
                  <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!cform.verified} onChange={(e) => cset("verified", e.target.checked)} /> Verified</label>
                  <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!cform.active} onChange={(e) => cset("active", e.target.checked)} /> Active</label>
                </div></Field>
                <Field label="Notes" span><input value={cform.notes} onChange={(e) => cset("notes", e.target.value)} className="rla-input" /></Field>
              </div>
              <div className="rla-inline-actions" style={{ marginTop: 10 }}>
                <button onClick={saveContact} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">{busy ? "Saving…" : cedit ? "Save" : "Add Contact"}</button>
                {cedit && <button onClick={() => { setCedit(null); setCform({ ...BLANK_CONTACT }); }} className="rla-btn rla-btn-ghost rla-btn-sm">Cancel</button>}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
