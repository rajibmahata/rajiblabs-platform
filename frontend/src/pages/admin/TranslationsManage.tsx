/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Chip, Empty, PageHead, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

const STATUSES = ["all", "approved", "generated", "needs_review", "needs_update"];

export default function TranslationsManage() {
  const [langs, setLangs] = useState<any[]>([]);
  const [target, setTarget] = useState("bn");
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");
  const [rows, setRows] = useState<any[]>([]);
  const [coverage, setCoverage] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [editText, setEditText] = useState("");
  const [compare, setCompare] = useState<any>(null);

  const loadLangs = () => {
    api.get<any[]>("/api/admin/languages").then((l) => {
      const list = (Array.isArray(l) ? l : []).filter((x) => !x.is_default);
      setLangs(list);
      if (list.length && !list.some((x) => x.code === target)) setTarget(list[0].code);
    }).catch(() => {});
  };
  const loadRows = () => {
    const q = new URLSearchParams();
    if (target) q.set("target", target);
    if (status !== "all") q.set("status", status);
    if (search.trim()) q.set("search", search.trim());
    api.get<any[]>(`/api/admin/translations?${q}`).then((r) => setRows(Array.isArray(r) ? r : [])).catch(() => {});
  };
  const loadCoverage = () => {
    api.get<any[]>("/api/admin/translations/coverage").then((c) => setCoverage(Array.isArray(c) ? c : [])).catch(() => {});
  };
  useEffect(() => { loadLangs(); loadCoverage(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { loadRows(); }, [target, status]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const t = setTimeout(loadRows, 400); return () => clearTimeout(t); }, [search]); // eslint-disable-line react-hooks/exhaustive-deps

  const generate = async () => {
    if (!confirm(`Generate missing translations for ${target}? Each missing key bills one LLM call.`)) return;
    setBusy(true);
    try {
      const r = await api.post<any>("/api/admin/translations/generate", { target_language: target, limit: 100 });
      toast("Generation done", `${r.done?.length ?? 0} ready · ${r.billed ?? 0} LLM calls · ${r.skipped ?? 0} skipped`);
      loadRows(); loadCoverage();
    } catch (e: any) { toast("Generation failed", String(e.message || e).slice(0, 140)); } finally { setBusy(false); }
  };

  const act = async (id: string, action: "approve" | "regenerate" | "delete") => {
    try {
      if (action === "delete") {
        if (!confirm("Delete this translation?")) return;
        await api.del(`/api/admin/translations/${id}`);
      } else {
        await api.post(`/api/admin/translations/${id}/${action}`);
      }
      loadRows(); loadCoverage();
    } catch (e: any) { toast("Action failed", String(e.message || e).slice(0, 140)); }
  };

  const saveEdit = async () => {
    if (!editText.trim()) return;
    try {
      await api.put(`/api/admin/translations/${editing.id}`, { translated_text: editText });
      setEditing(null); setEditText(""); loadRows(); loadCoverage();
      toast("Saved", "Translation approved with your edit.");
    } catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 140)); }
  };

  return (
    <div>
      <PageHead title="Translations" desc="Cache-first pipeline: approved → cached → generated. LLM is billed only for missing keys."
        actions={<button onClick={generate} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">
          <i className="fas fa-wand-magic-sparkles" /> {busy ? "Working…" : `Generate missing (${target})`}
        </button>} />

      <div className="rla-kpi-grid" style={{ gridTemplateColumns: "repeat(auto-fill,minmax(220px,1fr))" }}>
        {coverage.map((c) => (
          <div className="rla-panel" key={c.target}>
            <div className="rla-panel-head"><div><h3>{c.target}</h3><p>{c.total_keys} keys</p></div>
              <button onClick={() => setTarget(c.target)} className="rla-btn rla-btn-ghost rla-btn-sm">Inspect</button>
            </div>
            <div className="rla-panel-body text-xs">
              {Object.entries(c.by_status || {}).map(([s, n]: any) => (
                <div key={s} className="flex justify-between py-0.5"><span>{s}</span><b>{n}</b></div>
              ))}
              <div className="flex justify-between py-0.5"><span>missing</span><b>{c.missing_count}</b></div>
              {c.stale_count > 0 && <div className="flex justify-between py-0.5"><span>stale</span><b>{c.stale_count}</b></div>}
            </div>
          </div>
        ))}
      </div>

      <div className="rla-chip-row">
        <select value={target} onChange={(e) => setTarget(e.target.value)} className="rla-select" style={{ fontSize: ".8rem", padding: "6px 12px", borderRadius: 100 }} aria-label="Target language">
          {langs.map((l) => <option key={l.code} value={l.code}>{l.native_name} ({l.code})</option>)}
        </select>
        {STATUSES.map((s) => <Chip key={s} active={status === s} onClick={() => setStatus(s)}>{s}</Chip>)}
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search key or text…" className="rla-search-input" style={{ minWidth: 160 }} aria-label="Search translations" />
      </div>

      <div className="rla-stack">
        {rows.map((r) => (
          <div key={r.id} className="rla-list-card text-sm">
            <div className="flex flex-wrap justify-between gap-2">
              <div><span className="rla-code">{r.key}</span> <span className="text-xs" style={{ color: "var(--rla-text-faint)" }}>v{r.version ?? 1} · {r.provider || "?"} {r.model || ""}</span></div>
              <div className="rla-inline-actions">
                <StatusPill status={r.status} />
                <button onClick={() => setCompare(r)} className="rla-btn rla-btn-ghost rla-btn-sm">Compare</button>
                <button onClick={() => { setEditing(r); setEditText(r.translated_text || ""); }} className="rla-btn rla-btn-ghost rla-btn-sm">Edit</button>
                {r.status !== "approved" && <button onClick={() => act(r.id, "approve")} className="rla-btn rla-btn-ghost rla-btn-sm">Approve</button>}
                <button onClick={() => act(r.id, "regenerate")} className="rla-btn rla-btn-ghost rla-btn-sm">Regenerate</button>
                <button onClick={() => act(r.id, "delete")} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>
              </div>
            </div>
            <div className="text-xs mt-1">{r.translated_text}</div>
          </div>
        ))}
        {rows.length === 0 && <Empty>No translations match. Generate missing ones for this language.</Empty>}
      </div>

      {editing && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(15,17,30,.45)", zIndex: 300, display: "grid", placeItems: "center", padding: 16 }} onClick={() => setEditing(null)}>
          <div className="rla-panel" style={{ maxWidth: 640, width: "100%" }} onClick={(e) => e.stopPropagation()}>
            <div className="rla-panel-head"><div><h3>Edit translation</h3><p>{editing.key} → {editing.target_language}</p></div></div>
            <div className="rla-panel-body">
              <div className="rla-section-title">Source (English)</div>
              <p className="text-sm" style={{ marginBottom: 10 }}>{editing.source_text}</p>
              <div className="rla-section-title">Translation (manual edit approves it)</div>
              <textarea value={editText} onChange={(e) => setEditText(e.target.value)} rows={5} className="rla-textarea" />
              <div className="rla-inline-actions" style={{ marginTop: 10 }}>
                <button onClick={saveEdit} className="rla-btn rla-btn-primary rla-btn-sm">Save & Approve</button>
                <button onClick={() => setEditing(null)} className="rla-btn rla-btn-ghost rla-btn-sm">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {compare && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(15,17,30,.45)", zIndex: 300, display: "grid", placeItems: "center", padding: 16 }} onClick={() => setCompare(null)}>
          <div className="rla-panel" style={{ maxWidth: 720, width: "100%" }} onClick={(e) => e.stopPropagation()}>
            <div className="rla-panel-head"><div><h3>Compare</h3><p>{compare.key}</p></div></div>
            <div className="rla-panel-body" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div><div className="rla-section-title">English source</div><p className="text-sm">{compare.source_text}</p></div>
              <div><div className="rla-section-title">{compare.target_language} · {compare.status}</div><p className="text-sm">{compare.translated_text}</p></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
