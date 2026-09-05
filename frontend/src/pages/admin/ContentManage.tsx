/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

export default function ContentManage() {
  const [list, setList] = useState<any[]>([]); const [key, setKey] = useState("home_order"); const [title, setTitle] = useState(""); const [body, setBody] = useState("{}");
  const load = () => api.get<any[]>("/api/admin/content").then((l) => setList(Array.isArray(l) ? l : [])).catch(() => {});
  useEffect(() => { load(); }, []);
  const save = async () => {
    try { await api.put(`/api/admin/content/${key}`, { title, body: JSON.parse(body) }); load(); toast("Content saved", `Key "${key}" updated.`); }
    catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 140)); }
  };
  return (
    <div>
      <PageHead title="Website Content" desc={<>Key-value CMS for HOME flow, SEO, etc. Public: <span className="rla-code">/api/content/:key</span>.</>}
        actions={<button onClick={save} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-check" /> Save Content</button>} />
      <Panel title="Editor" sub="Body must be valid JSON">
        <div className="rla-form-grid">
          <Field label="Key"><input placeholder="Key (e.g. home_order)" value={key} onChange={e => setKey(e.target.value)} className="rla-input mono" /></Field>
          <Field label="Title"><input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} className="rla-input" /></Field>
          <Field label="Body JSON" span><textarea placeholder='Body JSON e.g. ["hero","about"]' value={body} onChange={e => setBody(e.target.value)} rows={4} className="rla-textarea mono" /></Field>
        </div>
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title="Entries" sub={`${list.length} keys`}>
        <div className="rla-stack">
          {list.map(c => (
            <div key={c.id} className="rla-list-card">
              <div><b>{c.key}</b> <span style={{ fontSize: ".78rem", color: "var(--rla-text-faint)" }}>— {c.title}</span></div>
              <pre className="rla-mono-cell mt-1 whitespace-pre-wrap">{c.bodyJson}</pre>
            </div>
          ))}
          {list.length === 0 && <Empty>No content entries yet.</Empty>}
        </div>
      </Panel>
    </div>
  );
}
