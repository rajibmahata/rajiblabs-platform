/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";

type P = { id: string; title: string; slug: string; shortDescription: string; status: string; featured: boolean; displayOrder: number; techStack: string[] };

export default function PortfolioManage() {
  const [list, setList] = useState<P[]>([]); const [form, setForm] = useState<any>({ title: "", slug: "", shortDescription: "", status: "draft", featured: false, displayOrder: 0, techStack: "" });
  const load = () => api.get<P[]>("/api/admin/portfolio").then(setList).catch(() => {});
  useEffect(() => { load(); }, []);
  const create = async () => {
    const body: any = { ...form, techStack: form.techStack ? form.techStack.split(",").map((s: string) => s.trim()).filter(Boolean) : [] };
    await api.post("/api/admin/portfolio", body); setForm({ title: "", slug: "", shortDescription: "", status: "draft", featured: false, displayOrder: 0, techStack: "" }); load();
  };
  return (
    <div>
      <h1 className="text-xl font-bold" style={{ fontFamily: "Fraunces, serif" }}>Portfolio Management</h1>
      <p className="text-sm mb-6" style={{ color: "var(--c-text-secondary)" }}>Rich portfolio with problem/solution, AI/cloud caps. Public: <code>/portfolio/:slug</code> and <code>/api/portfolio</code>.</p>
      <div className="p-4 rounded-xl border mb-6 grid grid-cols-1 md:grid-cols-2 gap-3" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}>
        <input placeholder="Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <input placeholder="Slug (auto)" value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value })} className="px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <input placeholder="Short description" value={form.shortDescription} onChange={e => setForm({ ...form, shortDescription: e.target.value })} className="px-3 py-2 rounded border md:col-span-2" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <input placeholder="Tech stack comma separated" value={form.techStack} onChange={e => setForm({ ...form, techStack: e.target.value })} className="px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <div className="flex gap-2">
          <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }}><option>draft</option><option>review</option><option>published</option><option>hidden</option></select>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.featured} onChange={e => setForm({ ...form, featured: e.target.checked })} /> Featured</label>
        </div>
        <button onClick={create} className="px-4 py-2 rounded-full text-white text-sm" style={{ background: "#1547be" }}>Add Project</button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="text-left" style={{ color: "var(--c-text-muted)", fontFamily: "JetBrains Mono, monospace", fontSize: 11 }}><th className="py-2">Title</th><th>Slug</th><th>Status</th><th>Featured</th><th>Actions</th></tr></thead>
          <tbody>
            {list.map(p => (
              <tr key={p.id} className="border-t" style={{ borderColor: "var(--c-border)" }}>
                <td className="py-2">{p.title}</td><td style={{ color: "var(--c-text-muted)" }}>{p.slug}</td>
                <td><span className="px-2 py-0.5 rounded text-xs" style={{ background: p.status === "published" ? "rgba(37,211,102,0.12)" : "rgba(255,255,255,0.06)", color: p.status === "published" ? "#25D366" : "var(--c-text-muted)" }}>{p.status}</span></td>
                <td>{p.featured ? "★" : "—"}</td>
                <td className="flex gap-2 py-2">
                  <a href={`/portfolio/${p.slug}`} target="_blank" className="px-2 py-1 rounded border text-xs" style={{ borderColor: "var(--c-border)" }}>Preview</a>
                  <button onClick={async () => { if (!confirm("Delete?")) return; await api.del(`/api/admin/portfolio/${p.id}`); load(); }} className="px-2 py-1 rounded border text-xs" style={{ borderColor: "rgba(239,68,68,0.3)", color: "#f87171" }}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.length === 0 && <div className="text-sm mt-3" style={{ color: "var(--c-text-muted)" }}>No portfolio projects yet.</div>}
      </div>
    </div>
  );
}
