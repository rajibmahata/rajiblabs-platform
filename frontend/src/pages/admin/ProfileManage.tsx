/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";

export default function ProfileManage() {
  const [form, setForm] = useState<any>({}); const [msg, setMsg] = useState("");
  useEffect(() => { api.get<any>("/api/admin/profile").then(p => setForm(p)).catch(() => {}); }, []);
  const save = async () => { try { await api.put("/api/admin/profile", form); setMsg("Saved"); setTimeout(() => setMsg(""), 2000); } catch (e: any) { setMsg(String(e.message || e)); } };
  const fields: [string, string][] = [["fullName", "Full Name"], ["title", "Title"], ["headline", "Headline"], ["email", "Email"], ["phone", "Phone"], ["whatsApp", "WhatsApp"], ["location", "Location"], ["linkedIn", "LinkedIn"], ["gitHub", "GitHub"], ["website", "Website"], ["profileImageUrl", "Profile Image URL"]];
  return (
    <div>
      <h1 className="text-xl font-bold" style={{ fontFamily: "Fraunces, serif" }}>Professional Profile</h1>
      <p className="text-sm mb-6" style={{ color: "var(--c-text-secondary)" }}>Centralized contact — used for CALL / WHATSAPP / EMAIL everywhere. Do not hard-code elsewhere.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-4 rounded-xl border" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}>
        {fields.map(([k, label]) => (
          <label key={k} className="block"><span className="text-xs" style={{ color: "var(--c-text-muted)", fontFamily: "JetBrains Mono, monospace" }}>{label.toUpperCase()}</span><input value={form[k] || ""} onChange={e => setForm({ ...form, [k]: e.target.value })} className="w-full mt-1 px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} /></label>
        ))}
        <label className="block md:col-span-2"><span className="text-xs" style={{ color: "var(--c-text-muted)", fontFamily: "JetBrains Mono, monospace" }}>BIO</span><textarea value={form.bio || ""} onChange={e => setForm({ ...form, bio: e.target.value })} rows={4} className="w-full mt-1 px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} /></label>
      </div>
      <button onClick={save} className="mt-4 px-6 py-2 rounded-full text-white" style={{ background: "#1547be" }}>Save Profile</button>
      {msg && <span className="ml-3 text-sm" style={{ color: "var(--c-accent-teal)" }}>{msg}</span>}
    </div>
  );
}
