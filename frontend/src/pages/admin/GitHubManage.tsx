/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";

export default function GitHubManage() {
  const [repos, setRepos] = useState<any[]>([]); const [log, setLog] = useState<any>(null); const [syncing, setSyncing] = useState(false); const [filter, setFilter] = useState("all");
  const load = () => { api.get<any[]>("/api/admin/github/repos").then(setRepos).catch(() => {}); api.get<any>("/api/admin/github/sync-log").then(setLog).catch(() => {}); };
  useEffect(() => { load(); }, []);
  const sync = async () => { setSyncing(true); try { await api.post("/api/admin/github/sync"); load(); } catch (e: any) { alert(String(e.message || e)); } finally { setSyncing(false); } };
  const patch = async (id: string, body: any) => { await api.patch(`/api/admin/github/repos/${id}`, body); load(); };
  const filtered = repos.filter(r => filter === "all" || r.syncStatus === filter || r.classification === filter);
  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-xl font-bold" style={{ fontFamily: "Fraunces, serif" }}>GitHub Projects</h1>
        <button onClick={sync} disabled={syncing} className="px-4 py-2 rounded-full text-white text-sm disabled:opacity-50" style={{ background: "#1547be" }}>{syncing ? "Syncing…" : "Sync GitHub Now"}</button>
      </div>
      <p className="text-sm mb-3" style={{ color: "var(--c-text-secondary)" }}>Server-side sync via <code>GITHUB_TOKEN</code> (never exposed). AI summaries are heuristic — review before publish. Manual edits are preserved.</p>
      {log && <div className="text-xs mb-3 p-2 rounded border" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)", color: "var(--c-text-muted)", fontFamily: "JetBrains Mono, monospace" }}>Last sync {new Date(log.startedAt).toLocaleString()} · Found {log.found} · Added {log.added} · Updated {log.updated}</div>}
      <div className="flex gap-2 mb-3 flex-wrap">
        {["all", "review", "published", "ignored", "ai", "dotnet"].map(f => (
          <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1 rounded-full text-xs border ${filter === f ? "bg-white text-black" : ""}`} style={{ borderColor: "var(--c-border)" }}>{f}</button>
        ))}
      </div>
      <div className="space-y-3">
        {filtered.map(r => (
          <div key={r.id} className="p-4 rounded-xl border" style={{ background: "var(--c-bg-secondary)", borderColor: r.syncStatus === "published" ? "#25D366" : "var(--c-border)" }}>
            <div className="flex flex-wrap justify-between gap-2">
              <div><a href={r.htmlUrl} target="_blank" className="font-medium hover:underline">{r.fullName}</a> <span className="text-xs px-1.5 py-0.5 rounded ml-2" style={{ background: "rgba(255,255,255,0.06)", color: "var(--c-text-muted)" }}>{r.language || "—"} · ★{r.stars}</span> <span className="text-xs px-1.5 py-0.5 rounded ml-1" style={{ background: r.syncStatus === "published" ? "rgba(37,211,102,0.15)" : "rgba(238,192,78,0.12)", color: r.syncStatus === "published" ? "#25D366" : "#eec04e" }}>{r.syncStatus}</span></div>
              <div className="text-xs" style={{ color: "var(--c-text-muted)" }}>{r.classification} · {r.aiConfidence}</div>
            </div>
            <div className="text-sm mt-1" style={{ color: "var(--c-text-secondary)" }}>{r.aiSummary || r.description || "—"}</div>
            <div className="flex gap-2 mt-3 flex-wrap">
              <button onClick={() => patch(r.id, { syncStatus: "published" })} className="px-3 py-1 rounded-full text-xs text-white" style={{ background: "#25D366" }}>Publish</button>
              <button onClick={() => patch(r.id, { syncStatus: "ignored" })} className="px-3 py-1 rounded-full border text-xs" style={{ borderColor: "var(--c-border)" }}>Ignore</button>
              <button onClick={() => patch(r.id, { syncStatus: "hidden" })} className="px-3 py-1 rounded-full border text-xs" style={{ borderColor: "var(--c-border)" }}>Hide</button>
              <button onClick={() => { const s = prompt("Edit AI summary", r.aiSummary || ""); if (s !== null) patch(r.id, { aiSummary: s }); }} className="px-3 py-1 rounded-full border text-xs" style={{ borderColor: "var(--c-border)" }}>Edit</button>
            </div>
          </div>
        ))}
        {filtered.length === 0 && <div className="text-sm" style={{ color: "var(--c-text-muted)" }}>No repositories. Click Sync GitHub Now (requires GITHUB_TOKEN on server).</div>}
      </div>
    </div>
  );
}
