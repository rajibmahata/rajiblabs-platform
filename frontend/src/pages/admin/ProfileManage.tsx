/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

const toCSV = (v: any): string => Array.isArray(v) ? v.join(", ") : (v || "");
const fromCSV = (s: string): string[] =>
  String(s || "").split(",").map((x) => x.trim()).filter(Boolean);
const toLines = (v: any): string => Array.isArray(v) ? v.join("\n") : (v || "");
const fromLines = (s: string): string[] =>
  String(s || "").split("\n").map((x) => x.trim()).filter(Boolean);

const EMPTY_CAREER: any = { company: "", role: "", period: "", client: "", description: "", achievements: "", tech_stack: "" };

export default function ProfileManage() {
  const [form, setForm] = useState<any>({});
  const [skillsText, setSkillsText] = useState("");
  const [career, setCareer] = useState<any[]>([]);
  const [editing, setEditing] = useState<number | null>(null);
  const [draft, setDraft] = useState<any>({ ...EMPTY_CAREER });
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false)
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));

  useEffect(() => {
    api.get<any>("/api/admin/profile").then((p) => {
      setForm(p);
      setSkillsText(toCSV(p.skills));
      setCareer(Array.isArray(p.career) ? p.career.map((c: any) => ({
        ...c,
        achievements: toLines(c.achievements),
        tech_stack: toCSV(c.tech_stack || c.technologies),
      })) : []);
    }).catch(() => {});
  }, []);

  const save = async () => {
    setBusy(true);
    try {
      const body = {
        ...form,
        skills: fromCSV(skillsText),
        socialLinks: {
          ...(form.socialLinks || {}),
          github: (form.socialLinks?.github || "").trim() || undefined,
          linkedin: (form.socialLinks?.linkedin || "").trim() || undefined,
        },
        career: career.map((c: any) => ({
          company: (c.company || "").trim(),
          role: (c.role || "").trim(),
          period: (c.period || "").trim(),
          client: (c.client || "").trim(),
          description: (c.description || "").trim(),
          achievements: fromLines(c.achievements),
          tech_stack: fromCSV(c.tech_stack),
        })).filter((c: any) => c.company || c.role),
      };
      const updated = await api.put<any>("/api/admin/profile", body);
      setForm(updated);
      setSkillsText(toCSV(updated.skills));
      setMsg("Saved"); toast("Profile saved", "Public profile updated.");
      setTimeout(() => setMsg(""), 2000);
    } catch (e: any) { setMsg(String(e.message || e)); } finally { setBusy(false); }
  };

  const openAdd = () => { setDraft({ ...EMPTY_CAREER }); setEditing(career.length); setCareer([...career, { ...EMPTY_CAREER }]); };
  const openEdit = (i: number) => { setDraft({ ...career[i] }); setEditing(i); };
  const applyDraft = () => {
    if (!draft.company.trim() && !draft.role.trim()) { toast("Validation", "Company or role required."); return; }
    setCareer(career.map((c, i) => (i === editing ? { ...draft } : c)));
    setEditing(null);
  };
  const removeEntry = (i: number) => {
    if (!confirm("Remove this career entry?")) return;
    setCareer(career.filter((_, j) => j !== i));
    if (editing === i) setEditing(null);
  };

  const fields: [string, string][] = [["fullName", "Full Name"], ["title", "Title"], ["headline", "Headline"], ["email", "Email"], ["phone", "Phone"], ["whatsApp", "WhatsApp"], ["location", "Location"], ["website", "Website"], ["profileImageUrl", "Profile Image URL"]];
  return (
    <div>
      <PageHead title="Professional Profile" desc="Centralized contact — used for CALL / WHATSAPP / EMAIL everywhere. Do not hard-code elsewhere."
        actions={<><button onClick={save} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-check" /> {busy ? "Saving…" : "Save Profile"}</button>{msg && <span className="text-sm">{msg}</span>}</>} />
      <Panel title="Contact & identity" sub="Shown across the public site">
        <div className="rla-form-grid">
          {fields.map(([k, label]) => (
            <Field key={k} label={label}><input value={form[k] || ""} onChange={e => set(k, e.target.value)} className="rla-input" /></Field>
          ))}
          <Field label="Bio" span><textarea value={form.bio || ""} onChange={e => set("bio", e.target.value)} rows={4} className="rla-textarea" /></Field>
        </div>
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title="Social links" sub="Public buttons — empty hides the button">
        <div className="rla-form-grid">
          <Field label="GitHub URL"><input value={form.socialLinks?.github || ""} onChange={e => set("socialLinks", { ...(form.socialLinks || {}), github: e.target.value })} className="rla-input" placeholder="https://github.com/…" /></Field>
          <Field label="LinkedIn URL"><input value={form.socialLinks?.linkedin || ""} onChange={e => set("socialLinks", { ...(form.socialLinks || {}), linkedin: e.target.value })} className="rla-input" placeholder="https://linkedin.com/in/…" /></Field>
        </div>
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title="Skills" sub="Comma separated — shown grouped on the public site, indexed by RAG">
        <Field label="Skills (comma separated)" span>
          <textarea value={skillsText} onChange={e => setSkillsText(e.target.value)} rows={3} className="rla-textarea" placeholder="C#, .NET, React, Azure, …" />
        </Field>
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title="Career history" sub={`${career.length} entries — newest first on the public timeline`}
        action={<button onClick={openAdd} className="rla-btn rla-btn-ghost rla-btn-sm"><i className="fas fa-plus" /> Add entry</button>}>
        <div className="rla-stack">
          {career.map((c: any, i: number) => (
            <div key={i} className="rla-list-card">
              {editing === i ? (
                <div>
                  <div className="rla-form-grid">
                    <Field label="Company"><input value={draft.company} onChange={e => setDraft({ ...draft, company: e.target.value })} className="rla-input" /></Field>
                    <Field label="Role"><input value={draft.role} onChange={e => setDraft({ ...draft, role: e.target.value })} className="rla-input" /></Field>
                    <Field label="Period"><input value={draft.period} onChange={e => setDraft({ ...draft, period: e.target.value })} placeholder="Aug 2019 – Present" className="rla-input" /></Field>
                    <Field label="Client"><input value={draft.client} onChange={e => setDraft({ ...draft, client: e.target.value })} className="rla-input" /></Field>
                    <Field label="Description" span><textarea value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value })} rows={2} className="rla-textarea" /></Field>
                    <Field label="Achievements (one per line)" span><textarea value={draft.achievements} onChange={e => setDraft({ ...draft, achievements: e.target.value })} rows={3} className="rla-textarea rla-mono" /></Field>
                    <Field label="Tech stack (comma separated)" span><input value={draft.tech_stack} onChange={e => setDraft({ ...draft, tech_stack: e.target.value })} className="rla-input" /></Field>
                  </div>
                  <div className="rla-inline-actions" style={{ marginTop: 10 }}>
                    <button onClick={applyDraft} className="rla-btn rla-btn-primary rla-btn-sm">Done</button>
                    <button onClick={() => { if (!career[i].company && !career[i].role) setCareer(career.filter((_, j) => j !== i)); setEditing(null); }} className="rla-btn rla-btn-ghost rla-btn-sm">Cancel</button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div><b>{c.role || "(no role)"}</b> <span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{c.company} · {c.period}</span></div>
                  <div className="rla-inline-actions">
                    <button onClick={() => openEdit(i)} className="rla-mini-btn" title="Edit"><i className="fas fa-pen" /></button>
                    <button onClick={() => removeEntry(i)} className="rla-mini-btn danger" title="Remove"><i className="fas fa-trash" /></button>
                  </div>
                </div>
              )}
            </div>
          ))}
          {career.length === 0 && <Empty>No career entries. Add the first one.</Empty>}
        </div>
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title="Publish state" sub="Backend record status">
        <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>
          Skills: {fromCSV(skillsText).length} · Career entries: {career.length} · Last save: {msg || "—"}
          {" "}<StatusPill status={form.fullName ? "ok" : "missing"} />
        </div>
      </Panel>
    </div>
  );
}
