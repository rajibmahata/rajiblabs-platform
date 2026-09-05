/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";

type P = { id: string; title: string; slug: string; shortDescription: string; status: string; featured: boolean; displayOrder: number; techStack: string[] };

export default function PortfolioManage() {
  const [list, setList] = useState<P[]>([]); const [form, setForm] = useState<any>({ title: "", slug: "", shortDescription: "", status: "draft", featured: false, displayOrder: 0, techStack: "" });
  const load = () => api.get<P[]>("/api/admin/portfolio").then((l) => setList(Array.isArray(l) ? l : [])).catch(() => {});
  useEffect(() => { load(); }, []);
  const create = async () => {
    const body: any = { ...form, techStack: form.techStack ? form.techStack.split(",").map((s: string) => s.trim()).filter(Boolean) : [] };
    await api.post("/api/admin/portfolio", body); setForm({ title: "", slug: "", shortDescription: "", status: "draft", featured: false, displayOrder: 0, techStack: "" }); load();
  };
  return (
    <div>
      <PageHead title="Portfolio" desc={<>Rich portfolio with problem/solution, AI/cloud caps. Public: <span className="rla-code">/portfolio/:slug</span>.</>} />
      <Panel title="Add project" sub="Drafts stay hidden until published">
        <div className="rla-form-grid">
          <Field label="Title"><input placeholder="Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="rla-input" /></Field>
          <Field label="Slug (auto)"><input placeholder="Slug (auto)" value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value })} className="rla-input" /></Field>
          <Field label="Short description" span><input placeholder="Short description" value={form.shortDescription} onChange={e => setForm({ ...form, shortDescription: e.target.value })} className="rla-input" /></Field>
          <Field label="Tech stack"><input placeholder="Tech stack, comma separated" value={form.techStack} onChange={e => setForm({ ...form, techStack: e.target.value })} className="rla-input" /></Field>
          <Field label="Status">
            <div className="rla-inline-actions">
              <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="rla-select"><option>draft</option><option>review</option><option>published</option><option>hidden</option></select>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.featured} onChange={e => setForm({ ...form, featured: e.target.checked })} /> Featured</label>
            </div>
          </Field>
        </div>
        <div style={{ marginTop: 12 }}><button onClick={create} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-plus" /> Add Project</button></div>
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title="Projects" sub={`${list.length} total`}>
        <div className="rla-table-wrap">
          <table className="rla-table">
            <thead><tr><th>Item</th><th>Status</th><th>Featured</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
            <tbody>
              {list.map(p => (
                <tr key={p.id}>
                  <td><div className="rla-doc-cell"><span className="rla-doc-ic" style={{ background: "var(--rla-cyan-soft)", color: "var(--rla-cyan)" }}><i className="fas fa-briefcase" /></span><div><b>{p.title}</b><span>{p.slug}</span></div></div></td>
                  <td><StatusPill status={p.status} /></td>
                  <td>{p.featured ? "★" : "—"}</td>
                  <td><div className="rla-row-actions">
                    <a href={`/portfolio/${p.slug}`} target="_blank" rel="noreferrer" className="rla-mini-btn" title="Preview"><i className="fas fa-eye" /></a>
                    <button onClick={async () => { if (!confirm("Delete?")) return; await api.del(`/api/admin/portfolio/${p.id}`); load(); }} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>
                  </div></td>
                </tr>
              ))}
            </tbody>
          </table>
          {list.length === 0 && <Empty>No portfolio projects yet.</Empty>}
        </div>
      </Panel>
    </div>
  );
}
