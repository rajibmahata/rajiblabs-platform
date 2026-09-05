/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Field, PageHead, Panel } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

export default function ProfileManage() {
  const [form, setForm] = useState<any>({}); const [msg, setMsg] = useState("");
  useEffect(() => { api.get<any>("/api/admin/profile").then(p => setForm(p)).catch(() => {}); }, []);
  const save = async () => { try { await api.put("/api/admin/profile", form); setMsg("Saved"); toast("Profile saved", "Public contact info updated."); setTimeout(() => setMsg(""), 2000); } catch (e: any) { setMsg(String(e.message || e)); } };
  const fields: [string, string][] = [["fullName", "Full Name"], ["title", "Title"], ["headline", "Headline"], ["email", "Email"], ["phone", "Phone"], ["whatsApp", "WhatsApp"], ["location", "Location"], ["linkedIn", "LinkedIn"], ["gitHub", "GitHub"], ["website", "Website"], ["profileImageUrl", "Profile Image URL"]];
  return (
    <div>
      <PageHead title="Professional Profile" desc="Centralized contact — used for CALL / WHATSAPP / EMAIL everywhere. Do not hard-code elsewhere."
        actions={<><button onClick={save} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-check" /> Save Profile</button>{msg && <span className="text-sm">{msg}</span>}</>} />
      <Panel title="Contact & identity" sub="Shown across the public site">
        <div className="rla-form-grid">
          {fields.map(([k, label]) => (
            <Field key={k} label={label}><input value={form[k] || ""} onChange={e => setForm({ ...form, [k]: e.target.value })} className="rla-input" /></Field>
          ))}
          <Field label="Bio" span><textarea value={form.bio || ""} onChange={e => setForm({ ...form, bio: e.target.value })} rows={4} className="rla-textarea" /></Field>
        </div>
      </Panel>
    </div>
  );
}
