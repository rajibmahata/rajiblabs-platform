/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

export default function SkillsManage() {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState("display_order");
  const [selected, setSelected] = useState<any>(null);
  const [evidence, setEvidence] = useState<any>(null);
  const [modal, setModal] = useState<"closed" | "create" | "edit" | "view">("closed");
  const [form, setForm] = useState<any>({ name: "", category: "Backend", status: "published", display_order: 999 });
  const pageSize = 20;

  const load = async (p = page) => {
    const params = new URLSearchParams({ page: String(p), page_size: String(pageSize) });
    if (q.trim()) params.set("q", q.trim());
    if (category) params.set("category", category);
    if (status) params.set("status", status);
    if (sort) params.set("sort", sort);
    try {
      const r = await api.get<any>(`/api/admin/skills?${params}`);
      setItems(r.items || []);
      setTotal(r.total || 0);
    } catch (e: any) {
      toast("Load failed", String(e.message || e).slice(0, 120));
    }
  };

  useEffect(() => { load(1); setPage(1); }, [q, category, status, sort]); // eslint-disable-line react-hooks/exhaustive-deps, react-hooks/set-state-in-effect
  useEffect(() => { load(page); }, [page]); // eslint-disable-line react-hooks/exhaustive-deps, react-hooks/set-state-in-effect

  const openView = async (id: string) => {
    try {
      const d = await api.get<any>(`/api/admin/skills/${id}`);
      setSelected(d);
      const ev = await api.get<any>(`/api/admin/skills/${id}/evidence`);
      setEvidence(ev);
      setModal("view");
    } catch (e: any) {
      toast("Load failed", String(e.message || e).slice(0, 120));
    }
  };

  const openEdit = async (id: string) => {
    const d = await api.get<any>(`/api/admin/skills/${id}`);
    setForm({ name: d.name, category: d.category, status: d.status, display_order: d.display_order, featured: d.featured });
    (setSelected as any)({ id });
    setModal("edit");
  };

  const openCreate = () => {
    setForm({ name: "", category: "Backend", status: "published", display_order: 999 });
    setModal("create");
  };

  const save = async () => {
    if (!form.name.trim() || !form.category.trim()) {
      toast("Validation", "Name and category required");
      return;
    }
    try {
      if (modal === "edit" && selected?.id) {
        await api.put(`/api/admin/skills/${selected.id}`, form);
        toast("Saved", "Skill updated");
      } else {
        await api.post("/api/admin/skills", form);
        toast("Created", "Skill created");
      }
      setModal("closed");
      load(page);
    } catch (e: any) {
      toast("Save failed", String(e.message || e).slice(0, 200));
    }
  };

  const toggleStatus = async (item: any) => {
    const next = item.status === "published" ? "archived" : "published";
    try {
      await api.put(`/api/admin/skills/${item.id}`, { status: next });
      load(page);
    } catch (e: any) {
      toast("Update failed", String(e.message || e).slice(0, 120));
    }
  };

  const remove = async (item: any) => {
    if (!confirm(`Delete skill "${item.name}"?`)) return;
    try {
      await api.del(`/api/admin/skills/${item.id}`);
      toast("Deleted", "");
      load(page);
    } catch (e: any) {
      toast("Delete failed", String(e.message || e).slice(0, 120));
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div>
      <PageHead
        title="Skills"
        desc="Evidence-backed skills — auto-discovered by Profile Agent, grouped for public display. Manual edits are overrides."
        actions={<button onClick={openCreate} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-plus" /> Add Skill</button>}
      />
      <Panel title="Skills" sub={`${total} total`}>
        <div className="rla-filter-grid">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, category, skill…" className="rla-input" aria-label="Search" />
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="rla-select" aria-label="Category">
            <option value="">all categories</option>
            {["Programming Languages","Frameworks","Frontend","Backend","Databases","Cloud","DevOps","AI / ML","Agentic AI","Architecture","APIs","Testing / QA","Tools","Business/Domain Skills","Other"].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="rla-select" aria-label="Status">
            <option value="">all statuses</option>
            <option value="published">published</option>
            <option value="archived">archived</option>
            <option value="draft">draft</option>
          </select>
          <select value={sort} onChange={(e) => setSort(e.target.value)} className="rla-select" aria-label="Sort">
            <option value="display_order">display order</option>
            <option value="name">name A–Z</option>
            <option value="category">category</option>
            <option value="confidence">confidence</option>
          </select>
        </div>
        <div style={{ height: 12 }} />
        <div className="rla-table-wrap">
          <table className="rla-table">
            <thead>
              <tr>
                <th>Skill</th>
                <th>Category</th>
                <th>Status</th>
                <th>Confidence</th>
                <th>Evidence</th>
                <th>Updated</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((s) => (
                <tr key={s.id}>
                  <td><b>{s.name}</b><div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{s.slug}</div></td>
                  <td className="text-xs">{s.category}</td>
                  <td><StatusPill status={s.status} /></td>
                  <td className="text-xs">{s.confidence != null ? `${(s.confidence * 100).toFixed(0)}%` : "—"}</td>
                  <td className="text-xs">{s.evidence_count ?? s.evidence?.sources?.length ?? "—"}</td>
                  <td className="text-xs">{s.updated_at ? new Date(s.updated_at).toLocaleDateString() : "—"}</td>
                  <td>
                    <div className="rla-row-actions" style={{ justifyContent: "flex-end" }}>
                      <button onClick={() => openView(s.id)} className="rla-mini-btn" title="View"><i className="fas fa-eye" /></button>
                      <button onClick={() => openEdit(s.id)} className="rla-mini-btn" title="Edit"><i className="fas fa-pen" /></button>
                      <button onClick={() => toggleStatus(s)} className="rla-mini-btn" title={s.status === "published" ? "Archive" : "Publish"}>
                        <i className={`fas ${s.status === "published" ? "fa-eye-slash" : "fa-eye"}`} />
                      </button>
                      <button onClick={() => remove(s)} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {items.length === 0 && <Empty>No skills match. Adjust filters or add one.</Empty>}
        </div>
        <div className="rla-pager">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="rla-btn rla-btn-ghost rla-btn-sm">← Prev</button>
          <span>Page {page} of {totalPages} · {total} records</span>
          <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="rla-btn rla-btn-ghost rla-btn-sm">Next →</button>
        </div>
      </Panel>

      {modal !== "closed" && (
        <div className="rla-modal-overlay" onClick={() => setModal("closed")}>
          <div className="rla-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Skill editor">
            <div className="rla-modal-head">
              <h3>{modal === "create" ? "Add Skill" : modal === "edit" ? `Edit ${form.name}` : selected?.name}</h3>
              <button onClick={() => setModal("closed")} className="rla-mini-btn">✕</button>
            </div>
            {modal === "view" && selected ? (
              <div>
                <h4 className="rla-h4">{selected.name}</h4>
                <p className="text-sm" style={{ color: "var(--rla-text-faint)" }}>{selected.category} · <StatusPill status={selected.status} /> · {selected.confidence != null ? `${(selected.confidence * 100).toFixed(0)}% confidence` : ""}</p>
                {evidence && (
                  <div style={{ marginTop: 12 }}>
                    <h4 className="rla-h4">Evidence</h4>
                    <p className="text-xs" style={{ color: "var(--rla-text-faint)" }}>Sources: {evidence.evidence?.sources?.length || 0} · Evidence count: {selected.evidence_count}</p>
                    <div className="rla-stack" style={{ marginTop: 8 }}>
                      {(evidence.evidence?.sources || []).slice(0, 6).map((src: any, i: number) => (
                        <div key={i} className="rla-list-card text-xs">
                          <b>{src.type}</b> — {src.name || src.id}
                        </div>
                      ))}
                    </div>
                    {evidence.projects?.length > 0 && (
                      <div style={{ marginTop: 12 }}>
                        <h4 className="rla-h4">Related Projects</h4>
                        <div className="rla-chip-row">
                          {evidence.projects.map((p: any) => (
                            <span key={p.slug} className="rla-chip">{p.name} ({p.slug})</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {evidence.github_repositories?.length > 0 && (
                      <div style={{ marginTop: 12 }}>
                        <h4 className="rla-h4">GitHub Repositories</h4>
                        <div className="rla-chip-row">
                          {evidence.github_repositories.map((r: any) => (
                            <a key={r.full_name} href={`https://github.com/${r.full_name}`} target="_blank" rel="noreferrer" className="rla-chip" style={{ textDecoration: "none" }}>
                              {r.full_name} {r.language ? `· ${r.language}` : ""} {r.stars ? `★${r.stars}` : ""}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                    {evidence.resume_versions?.length > 0 && (
                      <div style={{ marginTop: 12 }}>
                        <h4 className="rla-h4">Resume Versions</h4>
                        <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{evidence.resume_versions.join(", ")}</div>
                      </div>
                    )}
                  </div>
                )}
                <div className="rla-inline-actions" style={{ marginTop: 16 }}>
                  <button onClick={() => { setModal("edit"); setForm({ name: selected.name, category: selected.category, status: selected.status, display_order: selected.display_order }); }} className="rla-btn rla-btn-primary rla-btn-sm">Edit</button>
                  <button onClick={() => setModal("closed")} className="rla-btn rla-btn-ghost rla-btn-sm">Close</button>
                </div>
              </div>
            ) : (
              <div>
                <div className="rla-form-grid">
                  <Field label="Skill name"><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="rla-input" placeholder="e.g. C#, React, Azure" /></Field>
                  <Field label="Category">
                    <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="rla-select">
                      {["Programming Languages","Frameworks","Frontend","Backend","Databases","Cloud","DevOps","AI / ML","Agentic AI","Architecture","APIs","Testing / QA","Tools","Business/Domain Skills","Other"].map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Status">
                    <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="rla-select">
                      <option value="published">published</option>
                      <option value="archived">archived</option>
                      <option value="draft">draft</option>
                    </select>
                  </Field>
                  <Field label="Display order"><input type="number" value={form.display_order} onChange={(e) => setForm({ ...form, display_order: e.target.value })} className="rla-input" /></Field>
                </div>
                <div className="rla-inline-actions" style={{ marginTop: 16 }}>
                  <button onClick={save} className="rla-btn rla-btn-primary rla-btn-sm">Save</button>
                  <button onClick={() => setModal("closed")} className="rla-btn rla-btn-ghost rla-btn-sm">Cancel</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
