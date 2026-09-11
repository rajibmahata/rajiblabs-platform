/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { InlineLoader } from "../../components/admin/ui";
import { useAsyncActions } from "../../components/admin/async";
import { toast } from "../../components/admin/toast";

const EMPTY_FORM: any = { name: "", subject: "", preheader: "", html: "", text: "", category: "general", status: "draft" };
const VARS = ["first_name", "full_name", "company_name", "project_name", "project_url", "unsubscribe_url"];

export default function TemplatesManage() {
  const [items, setItems] = useState<any[]>([]);
  const [modal, setModal] = useState<"closed" | "edit" | "preview">("closed");
  const [form, setForm] = useState<any>({ ...EMPTY_FORM });
  const [editId, setEditId] = useState<string | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const { run, isLoading } = useAsyncActions();
  const busy = isLoading("action");
  const setBusy = (_: boolean) => {}; // compat for legacy code, now driven by useAsyncActions

  const load = () => { api.get<any>("/api/admin/marketing/templates").then((r) => setItems(r.items || [])).catch(() => {}); };
  useEffect(() => { load(); }, []);

  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const openCreate = () => { setForm({ ...EMPTY_FORM }); setEditId(null); setModal("edit"); };
  const openEdit = (t: any) => { setForm({ ...EMPTY_FORM, ...t }); setEditId(t.id); setModal("edit"); };
  const openPreview = async (t: any) => {
    const p = await api.post<any>(`/api/admin/marketing/templates/${t.id}/preview`, {}).catch(() => null);
    if (p) { setPreview(p); setForm({ ...EMPTY_FORM, ...t }); setModal("preview"); }
  };
  const save = async () => {
    if (!form.name.trim() || !form.subject.trim()) { toast("Validation", "Name + subject required."); return; }
    setBusy(true);
    try {
      if (editId) await api.put(`/api/admin/marketing/templates/${editId}`, form);
      else await api.post("/api/admin/marketing/templates", form);
      toast("Saved", "Template saved."); setModal("closed"); load();
    } catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 200)); } finally { setBusy(false); }
  };
  const remove = async (t: any) => {
    if (!confirm(`Delete template "${t.name}"?`)) return;
    try { await api.del(`/api/admin/marketing/templates/${t.id}`); toast("Deleted", ""); load(); }
    catch (e: any) { toast("Delete failed", String(e.message || e).slice(0, 200)); }
  };

  return (
    <div>
      <PageHead title="Email Templates" desc="Reusable, sanitized templates with {{variables}}. Only these variables render — unknown ones become empty."
        actions={<button onClick={openCreate} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-plus" /> New template</button>} />
      <p className="text-xs mb-2" style={{ color: "var(--rla-text-faint)" }}>Variables: {VARS.map((v) => `{{${v}}}`).join(" · ")}</p>
      <Panel title="Templates" sub={`${items.length} total`}>
        <div className="rla-table-wrap"><table className="rla-table">
          <thead><tr><th>Name</th><th>Subject</th><th>Category</th><th>Status</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
          <tbody>{items.map((t) => (
            <tr key={t.id}>
              <td><b>{t.name}</b></td>
              <td className="text-xs">{t.subject}</td>
              <td className="text-xs">{t.category}</td>
              <td><StatusPill status={t.status} /></td>
              <td><div className="rla-row-actions" style={{ justifyContent: "flex-end" }}>
                <button onClick={() => void openPreview(t)} className="rla-mini-btn" title="Preview"><i className="fas fa-eye" /></button>
                <button onClick={() => openEdit(t)} className="rla-mini-btn" title="Edit"><i className="fas fa-pen" /></button>
                <button onClick={() => void remove(t)} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>
              </div></td>
            </tr>))}
          </tbody>
        </table>
        {items.length === 0 && <Empty>No templates yet.</Empty>}</div>
      </Panel>
      {modal !== "closed" && (
        <div className="rla-modal-overlay" onClick={() => !busy && setModal("closed")}>
          <div className="rla-modal rla-modal-wide" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Template editor">
            <div className="rla-modal-head">
              <h3>{modal === "preview" ? `Preview: ${form.name}` : editId ? `Edit ${form.name}` : "New template"}</h3>
              <button onClick={() => setModal("closed")} className="rla-mini-btn">✕</button>
            </div>
            {modal === "preview" && preview ? (
              <div>
                <p className="text-sm"><b>Subject:</b> {preview.subject}</p>
                <div className="mt-2 p-3 rounded" style={{ border: "1px solid var(--rla-border)", background: "#fff" }} dangerouslySetInnerHTML={{ __html: preview.html }} />
                {preview.text && <pre className="mt-2 text-xs whitespace-pre-wrap">{preview.text}</pre>}
                <div className="rla-inline-actions" style={{ marginTop: 12 }}>
                  <button onClick={() => setModal("edit")} className="rla-btn rla-btn-ghost rla-btn-sm">Back to edit</button>
                </div>
              </div>
            ) : (
              <div>
                <div className="rla-form-grid">
                  <Field label="Name"><input value={form.name} onChange={(e) => set("name", e.target.value)} className="rla-input" /></Field>
                  <Field label="Category"><input value={form.category} onChange={(e) => set("category", e.target.value)} className="rla-input" /></Field>
                  <Field label="Subject" span><input value={form.subject} onChange={(e) => set("subject", e.target.value)} className="rla-input" placeholder="Use {{first_name}} for personalization" /></Field>
                  <Field label="Preheader" span><input value={form.preheader} onChange={(e) => set("preheader", e.target.value)} className="rla-input" /></Field>
                  <Field label="HTML body (sanitized on save)" span><textarea value={form.html} onChange={(e) => set("html", e.target.value)} rows={10} className="rla-textarea rla-mono" placeholder="<p>Hi {{first_name}},</p>..." /></Field>
                  <Field label="Text version (auto-derived if empty)" span><textarea value={form.text} onChange={(e) => set("text", e.target.value)} rows={4} className="rla-textarea" /></Field>
                  <Field label="Status"><select value={form.status} onChange={(e) => set("status", e.target.value)} className="rla-select">
                    <option value="draft">draft</option><option value="active">active</option><option value="archived">archived</option>
                  </select></Field>
                </div>
                <div className="rla-inline-actions" style={{ marginTop: 14 }}>
                  <button onClick={() => void save()} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">{busy ? "Saving…" : "Save"}</button>
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
