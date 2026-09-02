import { useEffect, useState } from "react";
import { api } from "../../services/api";

export default function ProductsManage() {
  const [list, setList] = useState<any[]>([]); const [form, setForm] = useState<any>({ name: "", slug: "", category: "", description: "", status: "draft", featured: false });
  const load = () => api.get<any[]>("/api/admin/products").then(setList).catch(() => {});
  useEffect(() => { load(); }, []);
  const create = async () => { await api.post("/api/admin/products", form); setForm({ name: "", slug: "", category: "", description: "", status: "draft", featured: false }); load(); };
  return (
    <div>
      <h1 className="text-xl font-bold" style={{ fontFamily: "Fraunces, serif" }}>Products & RajibLabs Applications</h1>
      <p className="text-sm mb-6" style={{ color: "var(--c-text-secondary)" }}>Page Flow is a product — edit it here. Public: <code>/products/:slug</code>.</p>
      <div className="p-4 rounded-xl border mb-6 grid grid-cols-1 md:grid-cols-2 gap-3" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}>
        <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <input placeholder="Slug" value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value })} className="px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <input placeholder="Category" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="px-3 py-2 rounded border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }}><option>draft</option><option>published</option><option>featured</option></select>
        <input placeholder="Description" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="px-3 py-2 rounded border md:col-span-2" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }} />
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.featured} onChange={e => setForm({ ...form, featured: e.target.checked })} /> Featured</label>
        <button onClick={create} className="px-4 py-2 rounded-full text-white text-sm" style={{ background: "#1547be" }}>Add Product</button>
      </div>
      <div className="space-y-2">
        {list.map(p => (
          <div key={p.id} className="p-3 rounded border flex justify-between items-center" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}>
            <div><div className="font-medium">{p.name} <span className="text-xs ml-2" style={{ color: "var(--c-text-muted)" }}>{p.slug}</span></div><div className="text-xs" style={{ color: "var(--c-text-muted)" }}>{p.category} · {p.status} {p.featured ? "· ★" : ""}</div></div>
            <div className="flex gap-2"><a href={`/products/${p.slug}`} target="_blank" className="px-2 py-1 rounded border text-xs" style={{ borderColor: "var(--c-border)" }}>View</a><button onClick={async () => { if (!confirm("Delete?")) return; await api.del(`/api/admin/products/${p.id}`); load(); }} className="px-2 py-1 rounded border text-xs" style={{ borderColor: "rgba(239,68,68,0.3)", color: "#f87171" }}>Delete</button></div>
          </div>
        ))}
      </div>
    </div>
  );
}
