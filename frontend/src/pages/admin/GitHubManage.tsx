/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Chip, Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

export default function GitHubManage() {
  const [repos, setRepos] = useState<any[]>([]); const [log, setLog] = useState<any>(null); const [syncing, setSyncing] = useState(false); const [filter, setFilter] = useState("all");
  const [cfg, setCfg] = useState<any>(null); const [token, setToken] = useState(""); const [acct, setAcct] = useState<any>(null); const [testing, setTesting] = useState(false);
  const [kbRepos, setKbRepos] = useState<any[]>([]); const [kbSyncing, setKbSyncing] = useState<string | null>(null);
  const load = () => { api.get<any[]>("/api/admin/github/repos").then((r) => setRepos(Array.isArray(r) ? r : [])).catch(() => {}); api.get<any>("/api/admin/github/sync-log").then(setLog).catch(() => {}); };
  const loadKb = () => {
    api.get<any>("/api/admin/github/config").then(setCfg).catch(() => {});
    api.get<any[]>("/api/admin/github/repositories").then((r) => setKbRepos(Array.isArray(r) ? r : [])).catch(() => {});
  };
  useEffect(() => { load(); loadKb(); }, []);
  const sync = async () => { setSyncing(true); try { const r = await api.post<any>("/api/admin/github/sync"); load(); toast("Sync complete", `${r.found ?? r.added ?? 0} repositories found.`); } catch (e: any) { toast("Sync failed", String(e.message || e).slice(0, 120)); } finally { setSyncing(false); } };
  const patch = async (id: string, body: any) => { await api.patch(`/api/admin/github/repos/${id}`, body); load(); };
  const saveToken = async () => {
    if (!token.trim()) { toast("Token required", "Paste a GitHub personal access token first."); return; }
    try { await api.post("/api/admin/github/config", { token: token.trim() }); setToken(""); setAcct(null); loadKb(); toast("Token saved", "Stored server-side only — never displayed again."); }
    catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 160)); }
  };
  const testToken = async () => {
    setTesting(true);
    try { const r = await api.post<any>("/api/admin/github/test", token.trim() ? { token: token.trim() } : {}); setAcct(r); toast("Connected", `${r.login} · ${r.public_repos} public repos`); }
    catch (e: any) { setAcct(null); toast("Connection failed", String(e.message || e).slice(0, 160)); } finally { setTesting(false); }
  };
  const revokeToken = async () => {
    if (!confirm("Remove the stored token? (Env-configured token, if any, still applies.)")) return;
    try { await api.del("/api/admin/github/config"); setAcct(null); loadKb(); toast("Token removed", ""); }
    catch (e: any) { toast("Revoke failed", String(e.message || e).slice(0, 120)); }
  };
  const kbToggle = async (id: string, enabled: boolean) => {
    try { await api.patch(`/api/admin/github/repositories/${id}`, { rag_enabled: enabled }); loadKb(); }
    catch (e: any) { toast("Update failed", String(e.message || e).slice(0, 120)); }
  };
  const kbSync = async (id: string, name: string) => {
    setKbSyncing(id);
    try { const r = await api.post<any>(`/api/admin/github/repositories/${id}/sync`); loadKb(); toast("Knowledge synced", `${name}: ${r.created ?? 0} new · ${r.updated ?? 0} updated · ${r.stale_removed ?? 0} removed`); }
    catch (e: any) { toast("Sync failed", String(e.message || e).slice(0, 160)); loadKb(); } finally { setKbSyncing(null); }
  };
  const filtered = repos.filter(r => filter === "all" || r.syncStatus === filter || r.classification === filter);
  return (
    <div>
      <PageHead title="GitHub Projects" desc={<>Server-side sync via <span className="rla-code">GITHUB_TOKEN</span> (never exposed). AI summaries are heuristic — review before publish.</>}
        actions={<button onClick={sync} disabled={syncing} className="rla-btn rla-btn-primary rla-btn-sm"><i className={`fas fa-rotate${syncing ? " fa-spin" : ""}`} /> {syncing ? "Syncing…" : "Sync GitHub Now"}</button>} />
      {log && <Panel title="Last sync" sub={`${new Date(log.startedAt).toLocaleString()} · Found ${log.found} · Added ${log.added} · Updated ${log.updated}`}><span /></Panel>}
      <div style={{ height: 16 }} />
      <Panel title="Connection" sub={cfg ? `Token ${cfg.masked || "—"} · source: ${cfg.source} · owner: ${cfg.owner}${cfg.updated_at ? ` · updated ${new Date(cfg.updated_at).toLocaleString()}` : ""}` : "Token status unknown"}>
        <div className="rla-form-grid">
          <Field label="Personal access token (write-only, never displayed)" span>
            <div className="rla-inline-actions">
              <input type="password" value={token} onChange={(e) => setToken(e.target.value)} placeholder={cfg?.configured ? "•••• (saved — paste to replace)" : "ghp_…"} className="rla-input" autoComplete="off" />
              <button onClick={saveToken} className="rla-btn rla-btn-primary rla-btn-sm">Save</button>
              <button onClick={testToken} disabled={testing} className="rla-btn rla-btn-ghost rla-btn-sm">{testing ? "Testing…" : "Test"}</button>
              {cfg?.configured && <button onClick={revokeToken} className="rla-mini-btn danger" title="Remove stored token"><i className="fas fa-trash" /></button>}
            </div>
          </Field>
        </div>
        {acct && <div className="text-sm mt-2">Connected as <b>{acct.login}</b>{acct.name ? ` (${acct.name})` : ""} · {acct.public_repos} public repos · {acct.followers} followers</div>}
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title="Knowledge base sync" sub="Per-repo RAG indexing (shared knowledge layer — no separate GitHub index). Disabled repos are excluded from retrieval.">
        <div className="rla-table-wrap">
          <table className="rla-table">
            <thead><tr><th>Repository</th><th>Sync</th><th>Last sync</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
            <tbody>
              {kbRepos.map(r => (
                <tr key={r.id}>
                  <td><div><b><a href={r.html_url} target="_blank" rel="noreferrer" className="hover:underline">{r.full_name}</a></b></div>
                    <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{r.language || "—"} · ★{r.stars ?? 0} · {r.rag_doc_count ?? 0} docs{r.rag_last_error ? ` · ⚠ ${String(r.rag_last_error).slice(0, 80)}` : ""}</div></td>
                  <td><StatusPill status={r.rag_enabled === false ? "disabled" : "enabled"} /></td>
                  <td className="text-xs">{r.rag_last_synced_at ? new Date(r.rag_last_synced_at).toLocaleString() : "never"}</td>
                  <td><div className="rla-row-actions" style={{ justifyContent: "flex-end" }}>
                    <button onClick={() => kbSync(r.id, r.full_name)} disabled={kbSyncing === r.id || r.rag_enabled === false} className="rla-btn rla-btn-primary rla-btn-sm" title={r.rag_enabled === false ? "Enable first" : "Sync now"}>{kbSyncing === r.id ? "Syncing…" : "Sync Now"}</button>
                    {r.rag_enabled === false
                      ? <button onClick={() => kbToggle(r.id, true)} className="rla-btn rla-btn-ghost rla-btn-sm">Enable</button>
                      : <button onClick={() => kbToggle(r.id, false)} className="rla-btn rla-btn-ghost rla-btn-sm">Disable</button>}
                  </div></td>
                </tr>
              ))}
            </tbody>
          </table>
          {kbRepos.length === 0 && <Empty>No tracked repositories yet — run Sync GitHub Now below (requires a token above or GITHUB_TOKEN on server).</Empty>}
        </div>
      </Panel>
      <div style={{ height: 16 }} />
      <div className="rla-chip-row">
        {["all", "review", "published", "ignored", "ai", "dotnet"].map(f => (
          <Chip key={f} active={filter === f} onClick={() => setFilter(f)}>{f}</Chip>
        ))}
      </div>
      <div className="rla-stack">
        {filtered.map(r => (
          <div key={r.id} className="rla-list-card">
            <div className="flex flex-wrap justify-between gap-2">
              <div className="rla-doc-cell">
                <span className="rla-doc-ic" style={{ background: "var(--rla-green-soft)", color: "var(--rla-green)" }}><i className="fab fa-github" /></span>
                <div><b><a href={r.htmlUrl} target="_blank" rel="noreferrer" className="hover:underline">{r.fullName}</a></b><span>{r.language || "—"} · ★{r.stars} · {r.classification} · {r.aiConfidence}</span></div>
              </div>
              <StatusPill status={r.syncStatus} />
            </div>
            <div className="text-sm mt-1">{r.aiSummary || r.description || "—"}</div>
            <div className="rla-inline-actions" style={{ marginTop: 10 }}>
              <button onClick={() => patch(r.id, { syncStatus: "published" })} className="rla-btn rla-btn-primary rla-btn-sm">Publish</button>
              <button onClick={() => patch(r.id, { syncStatus: "ignored" })} className="rla-btn rla-btn-ghost rla-btn-sm">Ignore</button>
              <button onClick={() => patch(r.id, { syncStatus: "hidden" })} className="rla-btn rla-btn-ghost rla-btn-sm">Hide</button>
              <button onClick={() => { const s = prompt("Edit AI summary", r.aiSummary || ""); if (s !== null) patch(r.id, { aiSummary: s }); }} className="rla-btn rla-btn-ghost rla-btn-sm">Edit</button>
            </div>
          </div>
        ))}
        {filtered.length === 0 && <Empty>No repositories. Click Sync GitHub Now (requires GITHUB_TOKEN on server).</Empty>}
      </div>
    </div>
  );
}
