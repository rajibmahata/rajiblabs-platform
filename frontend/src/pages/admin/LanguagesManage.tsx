/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Chip, Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

interface Lang {
  code: string; name: string; native_name: string; enabled: boolean;
  is_default?: boolean; direction: string; sort_order: number;
}

const EMPTY_FORM = { code: "", name: "", native_name: "", direction: "ltr", sort_order: 100 };

export default function LanguagesManage() {
  const [langs, setLangs] = useState<Lang[]>([]);
  const [form, setForm] = useState<any>({ ...EMPTY_FORM });
  const [editing, setEditing] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    api.get<Lang[]>("/api/admin/languages").then((l) => setLangs(Array.isArray(l) ? l : [])).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.code.trim() || !form.name.trim()) { toast("Validation", "Code and name are required."); return; }
    setBusy(true);
    try {
      if (editing) {
        await api.put(`/api/admin/languages/${editing}`, {
          name: form.name, native_name: form.native_name || form.name,
          direction: form.direction, sort_order: Number(form.sort_order) || 100,
        });
        toast("Language updated", editing);
      } else {
        await api.post("/api/admin/languages", {
          code: form.code.trim(), name: form.name.trim(),
          native_name: (form.native_name || form.name).trim(),
          direction: form.direction, sort_order: Number(form.sort_order) || 100,
        });
        toast("Language added", form.code.trim());
      }
      setForm({ ...EMPTY_FORM }); setEditing(null); load();
    } catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 140)); } finally { setBusy(false); }
  };

  const toggle = async (l: Lang) => {
    try {
      await api.patch(`/api/admin/languages/${l.code}/status`, { enabled: !l.enabled });
      load();
    } catch (e: any) { toast("Cannot change status", String(e.message || e).slice(0, 140)); }
  };

  const remove = async (l: Lang) => {
    if (!confirm(`Delete language ${l.code}? Only unused languages can be deleted.`)) return;
    try { await api.del(`/api/admin/languages/${l.code}`); load(); }
    catch (e: any) { toast("Cannot delete", String(e.message || e).slice(0, 140)); }
  };

  const startEdit = (l: Lang) => {
    setEditing(l.code);
    setForm({ code: l.code, name: l.name, native_name: l.native_name, direction: l.direction, sort_order: l.sort_order });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div>
      <PageHead title="Languages" desc="Master list. Only enabled languages appear in the public selector. The default language cannot be disabled or deleted." />
      <Panel title={editing ? `Edit ${editing}` : "Add language"} sub="Code follows BCP-47 style (en, bn, zh-CN)">
        <div className="rla-form-grid">
          <Field label="Code"><input value={form.code} disabled={!!editing} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="e.g. nl" className="rla-input mono" /></Field>
          <Field label="Name"><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Dutch" className="rla-input" /></Field>
          <Field label="Native name"><input value={form.native_name} onChange={(e) => setForm({ ...form, native_name: e.target.value })} placeholder="Nederlands" className="rla-input" /></Field>
          <Field label="Direction & order">
            <div className="rla-inline-actions">
              <select value={form.direction} onChange={(e) => setForm({ ...form, direction: e.target.value })} className="rla-select">
                <option value="ltr">LTR</option><option value="rtl">RTL</option>
              </select>
              <input type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: e.target.value })} className="rla-input" style={{ maxWidth: 110 }} aria-label="Display order" />
            </div>
          </Field>
        </div>
        <div className="rla-inline-actions" style={{ marginTop: 12 }}>
          <button onClick={save} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">
            <i className="fas fa-check" /> {editing ? "Save changes" : "Add language"}
          </button>
          {editing && <button onClick={() => { setEditing(null); setForm({ ...EMPTY_FORM }); }} className="rla-btn rla-btn-ghost rla-btn-sm">Cancel</button>}
        </div>
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title="All languages" sub={`${langs.length} total · ${langs.filter((l) => l.enabled).length} enabled`}>
        <div className="rla-table-wrap">
          <table className="rla-table">
            <thead><tr><th>Language</th><th>Code</th><th>Direction</th><th>Order</th><th>Status</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
            <tbody>
              {langs.map((l) => (
                <tr key={l.code}>
                  <td><div className="rla-doc-cell">
                    <span className="rla-doc-ic" style={{ background: "var(--rla-cyan-soft)", color: "var(--rla-cyan)" }}><i className="fas fa-language" /></span>
                    <div><b>{l.native_name}</b><span>{l.name}{l.is_default ? " · default" : ""}</span></div>
                  </div></td>
                  <td><span className="rla-code">{l.code}</span></td>
                  <td><span className="rla-mono-cell">{l.direction.toUpperCase()}</span></td>
                  <td><span className="rla-mono-cell">{l.sort_order}</span></td>
                  <td><StatusPill status={l.is_default ? "live" : l.enabled ? "active" : "archived"} /></td>
                  <td><div className="rla-row-actions">
                    <Chip active={l.enabled} onClick={() => toggle(l)}>{l.enabled ? "Enabled" : "Disabled"}</Chip>
                    <button onClick={() => startEdit(l)} className="rla-mini-btn" title="Edit"><i className="fas fa-pen" /></button>
                    {!l.is_default && <button onClick={() => remove(l)} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>}
                  </div></td>
                </tr>
              ))}
            </tbody>
          </table>
          {langs.length === 0 && <Empty>No languages found.</Empty>}
        </div>
      </Panel>
    </div>
  );
}
