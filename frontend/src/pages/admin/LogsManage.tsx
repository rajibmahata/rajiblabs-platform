/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";

type LogEntry = { id: string; level: string; source: string; message: string; details?: string; created_at: string };
type Stats = { retention_days: number; total_in_window: number; by_level: Record<string, number>; by_source: Record<string, string | number> };

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

export default function LogsManage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [level, setLevel] = useState("all");
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<string | null>(null);

  const load = () => {
    const q = level === "all" ? "" : `?level=${level}`;
    api.get<LogEntry[]>(`${BASE}/api/admin/logs${q}`).then(setLogs).catch((e) => setErr(String(e)));
    api.get<Stats>(`${BASE}/api/admin/logs/stats`).then(setStats).catch(() => {});
  };
  useEffect(() => { load(); }, [level]);

  const purge = async () => {
    if (!confirm("Delete all system logs now? (Automatic 5-day expiry otherwise.)")) return;
    try { await api.del(`${BASE}/api/admin/logs`); load(); } catch (e: any) { alert(String(e.message || e)); }
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h1 className="text-xl font-bold" style={{ fontFamily: "Fraunces, serif" }}>System Logs</h1>
          <p className="text-sm" style={{ color: "var(--c-text-secondary)" }}>
            Failures from agents, sync, AI and chat. Auto-deleted after {stats?.retention_days ?? 5} days.
            {stats && <> · {stats.total_in_window} in window · {stats.by_level.error ?? 0} errors · {stats.by_level.warning ?? 0} warnings</>}
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <select value={level} onChange={e => setLevel(e.target.value)} className="px-3 py-1.5 rounded-full text-xs border" style={{ background: "var(--c-bg-tertiary)", borderColor: "var(--c-border)" }}>
            <option value="all">all levels</option>
            <option value="error">errors</option>
            <option value="warning">warnings</option>
          </select>
          <button onClick={purge} className="px-3 py-1.5 rounded-full text-xs border" style={{ borderColor: "rgba(239,68,68,0.3)", color: "#f87171" }}>Purge now</button>
        </div>
      </div>
      {err && <div className="p-3 rounded border text-sm mb-4" style={{ background: "rgba(239,68,68,0.12)", color: "#f87171", borderColor: "rgba(239,68,68,0.3)" }}>{err} — is the FastAPI backend reachable?</div>}
      <div className="space-y-2">
        {logs.map(l => (
          <div key={l.id} className="p-3 rounded-xl border text-sm" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}>
            <button onClick={() => setOpen(open === l.id ? null : l.id)} className="w-full text-left flex flex-wrap items-center gap-2">
              <span className="text-xs px-1.5 py-0.5 rounded" style={{ background: l.level === "error" ? "rgba(239,68,68,0.15)" : "rgba(238,192,78,0.15)", color: l.level === "error" ? "#f87171" : "#eec04e" }}>{l.level.toUpperCase()}</span>
              <span className="text-xs px-1.5 py-0.5 rounded" style={{ background: "rgba(255,255,255,0.06)", color: "var(--c-text-muted)", fontFamily: "JetBrains Mono, monospace" }}>{l.source}</span>
              <span className="flex-1" style={{ color: "var(--c-text-primary)" }}>{l.message}</span>
              <span className="text-xs" style={{ color: "var(--c-text-muted)" }}>{new Date(l.created_at).toLocaleString()}</span>
            </button>
            {open === l.id && l.details && <pre className="text-xs mt-2 whitespace-pre-wrap p-2 rounded" style={{ background: "var(--c-bg-tertiary)", color: "var(--c-text-muted)" }}>{l.details}</pre>}
          </div>
        ))}
        {!logs.length && !err && <div className="text-sm p-6 text-center" style={{ color: "var(--c-text-muted)" }}>No failures logged — systems healthy.</div>}
      </div>
    </div>
  );
}
