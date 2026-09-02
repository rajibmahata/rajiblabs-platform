/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";

export default function ContentManage() {
  const [list, setList] = useState<any[]>([]); const [key, setKey] = useState("home_order"); const [title, setTitle] = useState(""); const [body, setBody] = useState("{}");
  const load = () => api.get<any[]>("/api/admin/content").then(setList).catch(() => {});
  useEffect(() => { load(); }, []);
  const save = async () => { await api.put(`/api/admin/content/${key}`, { title, body: JSON.parse(body) }); load(); };
  return (
    <div>
      <h1 className="text-xl font-bold" style={{ fontFamily: "Fraunces, serif" }}>Website Content</h1>
      <p className="text-sm mb-6" style={{ color: "var(--c-text-secondary)" }}>Key-value CMS for HOME flow, SEO, etc. Public: <code>/api/content/:key</code>.</p>
      <div className="p-4 rounded-xl border grid gap-3" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}>
        <input placeholder="Key (e.g. home_order)" value={key} onChange={e => setKey(e.target.value)} className="px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} className="px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <textarea placeholder='Body JSON e.g. ["hero","about"]' value={body} onChange={e => setBody(e.target.value)} rows={4} className="px-3 py-2 rounded border font-mono text-xs" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <button onClick={save} className="px-4 py-2 rounded-full text-white text-sm w-fit" style={{ background: "#1547be" }}>Save Content</button>
      </div>
      <div className="mt-6 space-y-2">
        {list.map(c => <div key={c.id} className="p-3 rounded border text-sm" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}><div className="font-medium">{c.key} — {c.title}</div><pre className="text-xs mt-1 whitespace-pre-wrap" style={{ color: "var(--c-text-muted)" }}>{c.bodyJson}</pre></div>)}
      </div>
    </div>
  );
}
