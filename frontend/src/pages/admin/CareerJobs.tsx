/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Chip, Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

const STATUSES = ["all", "Draft", "Open", "Analyzing", "Ready for Application", "Applied", "Closed"];
const SETTABLE = ["Draft", "Open", "Analyzing", "Ready for Application", "Applied", "Closed"];
const BLANK: any = { company_id: "", title: "", job_url: "", description: "", location: "", employment_type: "", required_skills: "", preferred_skills: "", experience: "", technologies: "", keywords: "", deadline: "", status: "Draft" };

export default function CareerJobs() {
  const [list, setList] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [companyId, setCompanyId] = useState("");
  const [form, setForm] = useState<any>({ ...BLANK });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    const p = new URLSearchParams();
    if (q.trim()) p.set("q", q.trim());
    if (status !== "all") p.set("status", status);
    if (companyId) p.set("company_id", companyId);
    api.get<any>(`/api/admin/career/jobs?${p}`).then((r) => setList(r.items || [])).catch(() => {});
  };
  useEffect(() => {
    api.get<any>("/api/admin/career/companies?active=true").then((r) => setCompanies(r.items || [])).catch(() => {});
    load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const t = setTimeout(load, 400); return () => clearTimeout(t); }, [q, status, companyId]); // eslint-disable-line react-hooks/exhaustive-deps

  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const csv = (v: any) => Array.isArray(v) ? v.join(", ") : (v || "");
  const uncsv = (s: string) => String(s || "").split(",").map((x) => x.trim()).filter(Boolean);
  const save = async () => {
    if (form.title.trim().length < 2) { toast("Validation", "Job title is required."); return; }
    if ((form.description || "").trim().length < 20) { toast("Validation", "Full job description is required (min 20 characters)."); return; }
    setBusy(true);
    try {
      const body = {
        ...form, company_id: form.company_id || null,
        required_skills: uncsv(form.required_skills), preferred_skills: uncsv(form.preferred_skills),
        technologies: uncsv(form.technologies), keywords: uncsv(form.keywords),
      };
      if (editingId) await api.put(`/api/admin/career/jobs/${editingId}`, body);
      else await api.post("/api/admin/career/jobs", body);
      setForm({ ...BLANK }); setEditingId(null); load();
      toast("Saved", "Job opening saved.");
    } catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 160)); } finally { setBusy(false); }
  };
  const edit = (j: any) => {
    setForm({
      ...BLANK, ...j,
      required_skills: csv(j.required_skills), preferred_skills: csv(j.preferred_skills),
      technologies: csv(j.technologies), keywords: csv(j.keywords),
    });
    setEditingId(j.id);
    window.scrollTo({ top: 0 });
  };
  const del = async (id: string) => {
    if (!confirm("Delete this job opening? Blocked while applications exist.")) return;
    try { await api.del(`/api/admin/career/jobs/${id}`); load(); }
    catch (e: any) { toast("Delete failed", String(e.message || e).slice(0, 160)); }
  };

  return (
    <div>
      <PageHead title="Career — Job Openings" desc="Roles to pursue. Analyze with the Career Agent, then generate from the workspace."
        actions={<input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search title, description, tech…"
          className="rla-search-input" aria-label="Search jobs" />} />
      <div className="rla-chip-row">
        {STATUSES.map((s) => <Chip key={s} active={status === s} onClick={() => setStatus(s)}>{s}</Chip>)}
        <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} className="rla-select" style={{ fontSize: ".78rem", padding: "6px 10px" }} aria-label="Company filter">
          <option value="">all companies</option>
          {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <Chip onClick={load}>↻ Refresh</Chip>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rla-stack">
          {list.map((j) => (
            <div key={j.id} className="rla-list-card text-sm">
              <div className="flex flex-wrap justify-between gap-2">
                <span className="font-medium">{j.title} <span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{j.company_name || ""} · {j.location || ""}</span></span>
                <span className="rla-inline-actions"><StatusPill status={j.status} />
                  <span className="rla-code">{j.application_count ?? 0} applications</span></span>
              </div>
              <div className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>{(j.technologies || []).slice(0, 6).join(", ")}</div>
              <div className="rla-inline-actions" style={{ marginTop: 8 }}>
                <a href={`/admin/career/workspace?job=${j.id}`} className="rla-btn rla-btn-primary rla-btn-sm">Open Workspace →</a>
                <button onClick={() => edit(j)} className="rla-btn rla-btn-ghost rla-btn-sm">Edit</button>
                <button onClick={() => del(j.id)} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>
              </div>
            </div>
          ))}
          {list.length === 0 && <Empty>No job openings yet — add the first role below.</Empty>}
        </div>
        <div>
          <Panel title={editingId ? "Edit job opening" : "Add job opening"} sub="Drafts stay out of the pipeline until opened">
            <div className="rla-form-grid">
              <Field label="Company"><select value={form.company_id} onChange={(e) => set("company_id", e.target.value)} className="rla-select">
                <option value="">— none —</option>
                {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select></Field>
              <Field label="Status"><select value={form.status} onChange={(e) => set("status", e.target.value)} className="rla-select">
                {SETTABLE.map((s) => <option key={s} value={s}>{s}</option>)}
              </select></Field>
              <Field label="Job title" span><input value={form.title} onChange={(e) => set("title", e.target.value)} className="rla-input" /></Field>
              <Field label="Job URL" span><input value={form.job_url} onChange={(e) => set("job_url", e.target.value)} placeholder="https://…" className="rla-input" /></Field>
              <Field label="Full job description" span><textarea value={form.description} onChange={(e) => set("description", e.target.value)} rows={8} className="rla-textarea" /></Field>
              <Field label="Location"><input value={form.location} onChange={(e) => set("location", e.target.value)} className="rla-input" /></Field>
              <Field label="Employment type"><input value={form.employment_type} onChange={(e) => set("employment_type", e.target.value)} placeholder="Full-time, Contract…" className="rla-input" /></Field>
              <Field label="Required skills (comma separated)" span><input value={form.required_skills} onChange={(e) => set("required_skills", e.target.value)} className="rla-input" /></Field>
              <Field label="Preferred skills (comma separated)" span><input value={form.preferred_skills} onChange={(e) => set("preferred_skills", e.target.value)} className="rla-input" /></Field>
              <Field label="Technologies (comma separated)" span><input value={form.technologies} onChange={(e) => set("technologies", e.target.value)} className="rla-input" /></Field>
              <Field label="Keywords (comma separated)" span><input value={form.keywords} onChange={(e) => set("keywords", e.target.value)} className="rla-input" /></Field>
              <Field label="Experience requirements" span><input value={form.experience} onChange={(e) => set("experience", e.target.value)} className="rla-input" /></Field>
              <Field label="Application deadline"><input value={form.deadline} onChange={(e) => set("deadline", e.target.value)} placeholder="2026-…, or Strategist note" className="rla-input" /></Field>
            </div>
            <div className="rla-inline-actions" style={{ marginTop: 10 }}>
              <button onClick={save} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">{busy ? "Saving…" : editingId ? "Save" : "Add Job"}</button>
              {editingId && <button onClick={() => { setEditingId(null); setForm({ ...BLANK }); }} className="rla-btn rla-btn-ghost rla-btn-sm">Cancel</button>}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
