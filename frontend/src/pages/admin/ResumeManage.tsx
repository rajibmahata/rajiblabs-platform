/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

export default function ResumeManage() {
  const [list, setList] = useState<any[]>([]); const [file, setFile] = useState<File | null>(null); const [msg, setMsg] = useState("");
  const load = () => api.get<any[]>("/api/admin/resumes").then((l) => setList(Array.isArray(l) ? l : [])).catch(() => {});
  useEffect(() => { load(); }, []);
  const upload = async () => {
    if (!file) return; const fd = new FormData(); fd.append("file", file);
    try { await api.upload("/api/admin/resumes/upload", fd); setMsg("Uploaded"); setFile(null); load(); toast("Resume uploaded", "New version published."); } catch (e: any) { setMsg(String(e.message || e)); }
  };
  return (
    <div>
      <PageHead title="Resume" desc={<>PDF/DOCX, 10MB max, versioned. Current published is served at <span className="rla-code">/api/resume/current</span>.</>} />
      <Panel title="Upload new version" sub="Replaces the live resume immediately">
        <div className="rla-inline-actions">
          <input type="file" accept=".pdf,.docx" onChange={e => setFile(e.target.files?.[0] || null)} className="rla-input" style={{ maxWidth: 320 }} />
          <button onClick={upload} disabled={!file} className="rla-btn rla-btn-primary rla-btn-sm" style={{ opacity: file ? 1 : .5 }}><i className="fas fa-upload" /> Upload & Publish</button>
          {msg && <span className="text-sm">{msg}</span>}
        </div>
      </Panel>
      <div style={{ height: 16 }} />
      <Panel title="Versions" sub={`${list.length} stored`}>
        <div className="rla-stack">
          {list.map(r => (
            <div key={r.id} className="rla-list-card">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div className="rla-doc-cell">
                  <span className="rla-doc-ic" style={{ background: "var(--rla-violet-soft)", color: "var(--rla-violet)" }}><i className="fas fa-file-pdf" /></span>
                  <div><b>{r.fileName}</b><span>v{r.version} · {new Date(r.uploadedAt).toLocaleString()} · {(r.sizeBytes / 1024).toFixed(1)} KB · {r.contentType}</span></div>
                </div>
                <div className="rla-inline-actions">
                  <StatusPill status={r.status} />
                  <a href={`/api/admin/resumes/${r.id}/download`} target="_blank" rel="noreferrer" className="rla-mini-btn" title="Download"><i className="fas fa-download" /></a>
                  {r.status !== "published" && <button onClick={async () => { await api.patch(`/api/admin/resumes/${r.id}`, {}); load(); }} className="rla-btn rla-btn-primary rla-btn-sm">Publish</button>}
                  <button onClick={async () => { await api.post(`/api/admin/resumes/${r.id}/extract`); toast("Extraction queued", "Review it before publishing."); }} className="rla-btn rla-btn-ghost rla-btn-sm">Extract → Review</button>
                  <button onClick={async () => { if (!confirm("Delete?")) return; await api.del(`/api/admin/resumes/${r.id}`); load(); }} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>
                </div>
              </div>
            </div>
          ))}
          {list.length === 0 && <Empty>No resumes yet. Upload one.</Empty>}
        </div>
      </Panel>
    </div>
  );
}
