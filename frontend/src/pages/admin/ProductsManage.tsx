/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";

export default function ProductsManage() {
  const [list, setList] = useState<any[]>([]); const [form, setForm] = useState<any>({ name: "", slug: "", category: "", description: "", status: "draft", featured: false });
  const load = () => api.get<any[]>("/api/admin/products").then((l) => setList(Array.isArray(l) ? l : [])).catch(() => {});
  useEffect(() => { load(); }, []);
  const create = async () => { await api.post("/api/admin/products", form); setForm({ name: "", slug: "", category: "", description: "", status: "draft", featured: false }); load(); };
  return (
    <div>
      <PageHead title="Products" desc={<>RajibLabs applications. Public: <span className="rla-code">/products/:slug</span>.</>} />
      <Panel title="Add product" sub="Drafts stay hidden until published">
        <div className="rla-form-grid">
          <Field label="Name"><input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="rla-input" /></Field>
          <Field label="Slug"><input placeholder="Slug" value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value })} className="rla-input" /></Field>
          <Field label="Category"><input placeholder="Category" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="rla-input" /></Field>
          <Field label="Status">
            <div className="rla-inline-actions">
              <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="rla-select"><option>draft</option><option>published</option><option>featured</option></select>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.featured} onChange={e => setForm({ ...form, featured: e.target.checked })} /> Featured</label>
            </div>
          </Field>
          <Field label="Description" span><input placeholder="Description" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="rla-input" /></Field>
        </div>
        <div style={{ marginTop: 12 }}><button onClick={create} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-plus" /> Add Product</button></div>
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title="Catalog" sub={`${list.length} products`}>
        <div className="rla-table-wrap">
          <table className="rla-table">
            <thead><tr><th>Item</th><th>Status</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
            <tbody>
              {list.map(p => (
                <tr key={p.id}>
                  <td><div className="rla-doc-cell"><span className="rla-doc-ic" style={{ background: "var(--rla-amber-soft)", color: "var(--rla-amber)" }}><i className="fas fa-cube" /></span><div><b>{p.name}</b><span>{p.slug} · {p.category}{p.featured ? " · ★" : ""}</span></div></div></td>
                  <td><StatusPill status={p.status} /></td>
                  <td><div className="rla-row-actions">
                    <a href={`/products/${p.slug}`} target="_blank" rel="noreferrer" className="rla-mini-btn" title="View"><i className="fas fa-eye" /></a>
                    <button onClick={async () => { if (!confirm("Delete?")) return; await api.del(`/api/admin/products/${p.id}`); load(); }} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>
                  </div></td>
                </tr>
              ))}
            </tbody>
          </table>
          {list.length === 0 && <Empty>No products yet.</Empty>}
        </div>
      </Panel>
    </div>
  );
}
