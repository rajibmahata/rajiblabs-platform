/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Chip, Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

const DEFAULT_EVAL = [  { question: "Who is Rajib Mahata?", expected_keywords: ["Rajib", "Mahata"] },
  { question: "What does RajibLabs offer?", expected_keywords: ["RajibLabs", "services"] },
  { question: "Show me projects on GitHub", expected_keywords: ["github"] },
];

/* Schema-driven policy editor (GET /api/admin/rag/guardrail-schema). */
function PolicyFields({ group, schema, values, onChange }: any) {
  const fields = schema?.fields?.[group] ?? {};
  const defaults = schema?.[group === "guardrails" ? "guardrails" : "hallucination_control"] ?? {};
  const get = (k: string) => (values?.[k] ?? defaults[k]);
  const set = (k: string, v: any) => onChange({ ...(values || {}), [k]: v });
  return (<div className="rla-form-grid">
    {Object.entries(fields).map(([k, m]: any) => (
      <Field key={k} label={m.label} span={m.type === "text"}>
        {m.type === "bool" ? (
          <label className="flex items-center gap-2 text-sm" title={m.help}>
            <input type="checkbox" checked={Boolean(get(k))} onChange={(e) => set(k, e.target.checked)} />
            <span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{m.help}</span>
          </label>
        ) : m.type === "select" ? (
          <select value={get(k)} onChange={(e) => set(k, e.target.value)} className="rla-select" title={m.help}>
            {(m.options || []).map((o: string) => <option key={o} value={o}>{o}</option>)}
          </select>
        ) : m.type === "number" ? (
          <input type="number" min={0} max={k === "minimum_confidence" ? 1 : 99} step={k === "minimum_confidence" ? 0.05 : 1}
            value={get(k)} onChange={(e) => set(k, Number(e.target.value))} className="rla-input" title={m.help} />
        ) : m.type === "text" ? (
          <textarea value={get(k) || ""} onChange={(e) => set(k, e.target.value)} rows={2} className="rla-textarea" title={m.help} />
        ) : (
          <input value={Array.isArray(get(k)) ? get(k).join(", ") : (get(k) || "")}
            onChange={(e) => set(k, e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean))}
            placeholder="comma, separated, values" className="rla-input" title={m.help} />
        )}
      </Field>
    ))}
  </div>);
}

export default function KnowledgeManage() {  const [dash, setDash] = useState<any>(null);
  const [docs, setDocs] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [busy, setBusy] = useState(false);
  const [evalRes, setEvalRes] = useState<any>(null);
  const [form, setForm] = useState({ title: "", content: "", url: "" });
  const [editing, setEditing] = useState<any>(null);
  const [ghSources, setGhSources] = useState<any[]>([]);
  const [schema, setSchema] = useState<any>(null);
  const [guards, setGuards] = useState<any>({});
  const [hallu, setHallu] = useState<any>({});

  const load = () => {
    api.get<any>("/api/admin/rag/dashboard").then(setDash).catch(() => {});
    api.get<any>("/api/admin/rag/guardrail-schema").then(setSchema).catch(() => {});
    api.get<any[]>("/api/admin/rag/github-sources").then((d) => setGhSources(Array.isArray(d) ? d : [])).catch(() => {});
    const q = new URLSearchParams();
    if (filter !== "all") q.set("status", filter);
    if (search) q.set("search", search);
    api.get<any[]>(`/api/admin/rag/documents?${q}`).then((d) => setDocs(Array.isArray(d) ? d : [])).catch(() => {});
  };
  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const t = setTimeout(load, 400); return () => clearTimeout(t); }, [search, filter]); // eslint-disable-line react-hooks/exhaustive-deps

  const reindex = async (source: string) => {
    setBusy(true);
    try { const r = await api.post<any>(`/api/admin/rag/reindex?source=${source}`); load(); toast("Re-ingest done", `${r.created} new · ${r.updated} updated · ${r.unchanged} unchanged · ${r.failed} failed`); }
    catch (e: any) { toast("Re-ingest failed", String(e.message || e).slice(0, 120)); } finally { setBusy(false); }
  };
  const resetForm = () => {
    setForm({ title: "", content: "", url: "" }); setEditing(null);
    setGuards({}); setHallu({});
  };
  const save = async () => {
    if (!form.title.trim() || form.content.trim().length < 10) { toast("Validation", "Title + at least 10 characters of content are required."); return; }
    setBusy(true);
    try {
      const payload = { ...form, guardrails: guards, hallucination_control: hallu };
      if (editing) await api.put(`/api/admin/rag/documents/${editing.id}`, { ...editing, ...payload });
      else await api.post("/api/admin/rag/documents", { ...payload, source_type: "admin_knowledge" });
      resetForm(); load();
    } catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 120)); } finally { setBusy(false); }
  };
  const docAction = async (id: string, action: "unpublish" | "reindex" | "delete") => {
    if (action === "delete" && !confirm("Delete this document and its vectors?")) return;
    try {
      if (action === "delete") await api.del(`/api/admin/rag/documents/${id}`);
      else await api.post(`/api/admin/rag/documents/${id}/${action}`);
      load();
    } catch (e: any) { toast("Action failed", String(e.message || e).slice(0, 120)); }
  };
  const ghAction = async (repo: string, action: "sync" | "reindex" | "disable" | "enable" | "delete") => {
    const id = encodeURIComponent(repo);
    try {
      setBusy(true);
      if (action === "sync") {
        const r = await api.post<any>(`/api/admin/github/repositories/${id}/sync`);
        toast("Knowledge synced", `${repo}: ${r.created ?? 0} new · ${r.updated ?? 0} updated · ${r.stale_removed ?? 0} removed`);
      } else if (action === "reindex") {
        await api.post(`/api/admin/github/repositories/${id}/reindex`);
        toast("Re-index queued", `${repo} fully re-indexed.`);
      } else if (action === "enable") {
        await api.patch(`/api/admin/github/repositories/${id}`, { rag_enabled: true });
        toast("Enabled", `${repo} back in RAG retrieval.`);
      } else if (action === "disable") {
        await api.post(`/api/admin/github/repositories/${id}/disable`);
        toast("Disabled", `${repo} removed from RAG retrieval.`);
      } else {
        if (!confirm(`Delete ALL indexed knowledge for ${repo}? (Repo record kept; vectors removed.)`)) return;
        await api.del(`/api/admin/github/repositories/${id}/knowledge`);
        toast("Deleted", `${repo} knowledge removed.`);
      }
      load();
    } catch (e: any) { toast("Action failed", String(e.message || e).slice(0, 160)); } finally { setBusy(false); }
  };
  const ghView = (repo: string) => { setSearch(repo); setFilter("all"); window.scrollTo({ top: document.body.scrollHeight }); };
  const runEval = async () => {
    setBusy(true);
    try { setEvalRes(await api.post<any>("/api/admin/rag/evaluate", { items: DEFAULT_EVAL })); }
    catch (e: any) { toast("Evaluation failed", String(e.message || e).slice(0, 120)); } finally { setBusy(false); }
  };

  const bySource = dash?.by_source ?? {};
  return (
    <div>
      <PageHead title="Knowledge Base" desc="MongoDB is the source of truth; vectors re-index automatically on every edit. Only public content is ever indexed."
        actions={<>
          <button onClick={() => reindex("mongodb")} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-database" /> {busy ? "Working…" : "Re-ingest Site"}</button>
          <button onClick={() => reindex("github")} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fab fa-github" /> Re-ingest GitHub</button>
          <button onClick={runEval} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm"><i className="fas fa-vial" /> Run Evaluation</button>
        </>} />
      {dash && (
        <div className="rla-kpi-grid" style={{ gridTemplateColumns: "repeat(3,1fr)" }}>
          <div className="rla-panel"><div className="rla-panel-head"><div><h3>Coverage by source</h3><p>{dash.chunks ?? 0} chunks indexed</p></div></div>
            <div className="rla-panel-body">
              {Object.keys(bySource).length === 0 && <span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>No documents yet — run Re-ingest Site.</span>}
              {Object.entries(bySource).map(([t, s]: any) => (
                <div key={t} className="flex justify-between text-xs py-0.5"><span>{t}</span><span style={{ color: "var(--rla-text-faint)" }}>{s.active ?? 0} active{s.failed ? ` · ${s.failed} failed` : ""}</span></div>
              ))}
            </div>
          </div>
          <div className="rla-panel"><div className="rla-panel-head"><div><h3>Vector store (Qdrant)</h3><p>{dash.config?.provider} · {dash.config?.embedding_model} · top_k {dash.config?.top_k}</p></div>
            {dash.qdrant?.ok ? <span className="rla-pill ok">READY</span> : <span className="rla-pill warn">DOWN</span>}</div>
            <div className="rla-panel-body text-xs">
              {dash.qdrant?.ok
                ? <>Collection <span className="rla-code">{dash.qdrant.collection}</span> · {dash.qdrant.points_count ?? "?"} points</>
                : <>Unavailable — chat still works via site knowledge. {dash.qdrant?.error ?? ""}</>}
            </div>
          </div>
          <div className="rla-panel"><div className="rla-panel-head"><div><h3>Evaluation</h3><p>Golden-question keyword coverage</p></div></div>
            <div className="rla-panel-body text-xs">
              {evalRes
                ? <>{evalRes.summary.passed}/{evalRes.summary.total} passed ({Math.round(evalRes.summary.pass_rate * 100)}%){evalRes.results.map((r: any, i: number) => (<div key={i} className="mt-1">{r.passed ? "✓" : "✗"} {r.question} <span style={{ color: "var(--rla-text-faint)" }}>({r.retrieved} chunks)</span></div>))}</>
                : <span style={{ color: "var(--rla-text-faint)" }}>Not run yet.</span>}
            </div>
          </div>
        </div>
      )}

      <Panel title="GitHub sources" sub="Synced repositories in the shared knowledge layer (configure token + sync in GitHub Projects)">
        <div className="rla-table-wrap">
          <table className="rla-table">
            <thead><tr><th>Repository</th><th>Index</th><th>Last indexed</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
            <tbody>
              {ghSources.map(g => (
                <tr key={g.repository}>
                  <td><div><b>{g.repository_url
                    ? <a href={g.repository_url} target="_blank" rel="noreferrer" className="hover:underline">{g.repository}</a>
                    : g.repository}</b></div>
                    <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>
                      {g.doc_count} docs · {g.chunk_count} chunks · sync: {g.sync_status || "—"}{g.rag_enabled === false ? " · DISABLED from RAG" : ""}
                    </div></td>
                  <td><StatusPill status={g.rag_enabled === false ? "disabled" : (g.by_status?.failed ? "failed" : "synced")} /></td>
                  <td className="text-xs">{g.last_indexed_at ? new Date(g.last_indexed_at).toLocaleString() : "never"}</td>
                  <td><div className="rla-row-actions" style={{ justifyContent: "flex-end" }}>
                    <button onClick={() => ghView(g.repository)} className="rla-btn rla-btn-ghost rla-btn-sm">View</button>
                    <button onClick={() => ghAction(g.repository, "sync")} disabled={busy || g.rag_enabled === false} className="rla-btn rla-btn-ghost rla-btn-sm">Sync</button>
                    <button onClick={() => ghAction(g.repository, "reindex")} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm">Re-index</button>
                    {g.rag_enabled === false
                      ? <button onClick={() => ghAction(g.repository, "enable")} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm">Enable</button>
                      : <button onClick={() => ghAction(g.repository, "disable")} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm">Disable</button>}
                    <button onClick={() => ghAction(g.repository, "delete")} disabled={busy} className="rla-mini-btn danger" title="Delete indexed knowledge"><i className="fas fa-trash" /></button>
                  </div></td>
                </tr>
              ))}
            </tbody>
          </table>
          {ghSources.length === 0 && <Empty>No GitHub repositories indexed yet — sync one from GitHub Projects.</Empty>}
        </div>
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title={editing ? "Edit knowledge entry" : "Add knowledge entry"} sub="Factual public content only (min 10 chars)">
        <div className="rla-form-grid">
          <Field label="Title" span><input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Title" className="rla-input" /></Field>
          <Field label="Content" span><textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} placeholder="Factual public content…" rows={4} className="rla-textarea" /></Field>
          <Field label="Source URL (optional)" span><input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} placeholder="Source URL (optional)" className="rla-input" /></Field>
          <Field label="Access / Visibility" span>
            <span className="text-sm">Visibility: <span className="rla-code">public</span> · Status: <span className="rla-code">{editing?.status || "active (on save)"}</span></span>
          </Field>
        </div>
        <h4 className="rla-h4">Guardrails — enforced server-side before any answer</h4>
        <PolicyFields group="guardrails" schema={schema} values={guards} onChange={setGuards} />
        <h4 className="rla-h4">Hallucination Control</h4>
        <PolicyFields group="hallucination_control" schema={schema} values={hallu} onChange={setHallu} />
        <h4 className="rla-h4">RAG / Indexing</h4>
        <p className="text-xs" style={{ color: "var(--rla-text-faint)" }}>Saving with unchanged content updates policies only — no re-embedding, no version bump. Content edits re-index automatically.</p>
        <div>
        </div>
        <div className="rla-inline-actions" style={{ marginTop: 12 }}>
          <button onClick={save} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-check" /> {editing ? "Save & Re-index" : "Add & Index"}</button>
          {editing && <button onClick={resetForm} className="rla-btn rla-btn-ghost rla-btn-sm">Cancel</button>}
        </div>
      </Panel>
      <div style={{ height: 16 }} />
      <div className="rla-chip-row">
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search documents…" className="rla-search-input" style={{ minWidth: 180 }} aria-label="Search documents" />
        {["all", "active", "inactive", "failed"].map(f => (
          <Chip key={f} active={filter === f} onClick={() => setFilter(f)}>{f}</Chip>
        ))}
      </div>
      <div className="rla-stack">
        {docs.map(d => (
          <div key={d.id} className="rla-list-card text-sm">
            <div className="flex flex-wrap justify-between gap-2">
              <div><span className="font-medium">{d.title}</span> <span className="rla-code" style={{ marginLeft: 6 }}>{d.source_type} · v{d.version}</span></div>
              <div className="rla-inline-actions">
                <StatusPill status={d.status} />
                <button onClick={async () => { try { const full = await api.get<any>(`/api/admin/rag/documents/${d.id}`); setEditing(full); setForm({ title: full.title, content: full.content || "", url: full.url || "" }); setGuards(full.guardrails || {}); setHallu(full.hallucination_control || {}); window.scrollTo({ top: 0 }); } catch (e: any) { toast("Load failed", String(e.message || e).slice(0, 120)); } }} className="rla-btn rla-btn-ghost rla-btn-sm">Edit</button>
                <button onClick={() => docAction(d.id, "reindex")} className="rla-btn rla-btn-ghost rla-btn-sm">Re-index</button>
                {d.status === "active"
                  ? <button onClick={() => docAction(d.id, "unpublish")} className="rla-btn rla-btn-ghost rla-btn-sm">Unpublish</button>
                  : <button onClick={() => docAction(d.id, "reindex")} className="rla-btn rla-btn-ghost rla-btn-sm">Republish</button>}
                <button onClick={() => docAction(d.id, "delete")} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>
              </div>
            </div>
            <div className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>{d.source_id}{d.repository ? ` · ${d.repository}` : ""}{d.error ? ` · ⚠ ${d.error}` : ""}</div>
          </div>
        ))}
        {docs.length === 0 && <Empty>No documents match. Run Re-ingest Site to populate from published content.</Empty>}
      </div>
    </div>
  );
}
