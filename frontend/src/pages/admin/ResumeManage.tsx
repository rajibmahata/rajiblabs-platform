import { useEffect, useState } from "react";
import { api } from "../../services/api";

export default function ResumeManage() {
  const [list, setList] = useState<any[]>([]); const [file, setFile] = useState<File | null>(null); const [msg, setMsg] = useState("");
  const load = () => api.get<any[]>("/api/admin/resumes").then(setList).catch(() => {});
  useEffect(() => { load(); }, []);
  const upload = async () => {
    if (!file) return; const fd = new FormData(); fd.append("file", file);
    try { await api.upload("/api/admin/resumes/upload", fd); setMsg("Uploaded"); setFile(null); load(); } catch (e: any) { setMsg(String(e.message || e)); }
  };
  return (
    <div>
      <h1 className="text-xl font-bold" style={{ fontFamily: "Fraunces, serif" }}>Resume Management</h1>
      <p className="text-sm mb-6" style={{ color: "var(--c-text-secondary)" }}>PDF/DOCX, 10MB max, versioned. Current published is served at <code>/api/resume/current</code>.</p>
      <div className="p-4 rounded-xl border flex flex-wrap gap-3 items-center mb-6" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)" }}>
        <input type="file" accept=".pdf,.docx" onChange={e => setFile(e.target.files?.[0] || null)} />
        <button onClick={upload} disabled={!file} className="px-4 py-2 rounded-full text-white text-sm disabled:opacity-50" style={{ background: "#1547be" }}>Upload & Publish</button>
        {msg && <span className="text-sm" style={{ color: "var(--c-accent-teal)" }}>{msg}</span>}
      </div>
      <div className="space-y-3">
        {list.map(r => (
          <div key={r.id} className="p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-3" style={{ background: "var(--c-bg-secondary)", borderColor: r.status === "published" ? "#eec04e" : "var(--c-border)" }}>
            <div>
              <div className="font-medium">{r.fileName} <span className="text-xs px-1.5 py-0.5 rounded" style={{ background: r.status === "published" ? "rgba(238,192,78,0.15)" : "rgba(255,255,255,0.06)", color: r.status === "published" ? "#eec04e" : "var(--c-text-muted)" }}>{r.status.toUpperCase()} v{r.version}</span></div>
              <div className="text-xs" style={{ color: "var(--c-text-muted)" }}>{new Date(r.uploadedAt).toLocaleString()} · {(r.sizeBytes / 1024).toFixed(1)} KB · {r.contentType}</div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <a href={`/api/admin/resumes/${r.id}/download`} target="_blank" className="px-3 py-1.5 rounded-full border text-xs" style={{ borderColor: "var(--c-border)" }}>Download</a>
              {r.status !== "published" && <button onClick={async () => { await api.patch(`/api/admin/resumes/${r.id}`, {}); load(); }} className="px-3 py-1.5 rounded-full text-xs text-white" style={{ background: "#1547be" }}>Publish</button>}
              <button onClick={async () => { if (!confirm("Delete?")) return; await api.del(`/api/admin/resumes/${r.id}`); load(); }} className="px-3 py-1.5 rounded-full border text-xs" style={{ borderColor: "rgba(239,68,68,0.3)", color: "#f87171" }}>Delete</button>
              <button onClick={async () => { await api.post(`/api/admin/resumes/${r.id}/extract`); alert("Extraction queued for review"); }} className="px-3 py-1.5 rounded-full border text-xs" style={{ borderColor: "var(--c-border)" }}>Extract → Review</button>
            </div>
          </div>
        ))}
        {list.length === 0 && <div className="text-sm" style={{ color: "var(--c-text-muted)" }}>No resumes yet. Upload one.</div>}
      </div>
    </div>
  );
}
