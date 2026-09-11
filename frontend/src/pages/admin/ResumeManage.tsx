/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useRef } from "react";
import { api } from "../../services/api";
import { Empty, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { useAsyncActions } from "../../components/admin/async";
import { InlineLoader, StepProgress } from "../../components/admin/ui";

const STEPS = [
  "Uploading Resume...",
  "Processing Resume...",
  "Extracting Information...",
  "Updating Knowledge...",
  "Completed",
];

export default function ResumeManage() {
  const [list, setList] = useState<any[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const { run, isLoading } = useAsyncActions();
  const [uploadStep, setUploadStep] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<"processing" | "done" | "error">("processing");
  const timerRef = useRef<number | null>(null);
  const uploading = isLoading("upload");

  const load = () => api.get<any[]>("/api/admin/resumes").then((l) => setList(Array.isArray(l) ? l : [])).catch(() => {});

  useEffect(() => {
    load();
  }, []);

  // Advance simulated steps while upload is in progress.
  // Step reset happens in upload() before the request starts; this effect
  // only owns the timer (interval callbacks may call setState).
  useEffect(() => {
    if (!uploading) {
      if (timerRef.current) window.clearInterval(timerRef.current);
      return;
    }
    let step = 0;
    timerRef.current = window.setInterval(() => {
      step = Math.min(step + 1, STEPS.length - 2); // hold at "Updating Knowledge..." until request finishes
      setUploadStep(step);
    }, 800);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [uploading]);

  const upload = async () => {
    if (!file) return;
    if (isLoading("upload")) return;
    const fd = new FormData();
    fd.append("file", file);
    setUploadStep(0);
    setUploadStatus("processing");
    try {
      await run(
        "upload",
        async () => {
          await api.upload("/api/admin/resumes/upload", fd);
        },
        {
          successTitle: "Resume uploaded and profile knowledge updated successfully.",
          successMsg: "",
          errorTitle: "Resume upload failed. Please try again.",
        }
      );
      // Only reached on success because run re-throws on error
      if (timerRef.current) window.clearInterval(timerRef.current);
      setUploadStep(STEPS.length - 1);
      setUploadStatus("done");
      setFile(null);
      // Reset file input
      const el = document.querySelector<HTMLInputElement>('input[type="file"][accept=".pdf,.docx"]');
      if (el) el.value = "";
      await load();
      // Briefly show completed then reset
      setTimeout(() => {
        setUploadStep(0);
        setUploadStatus("processing");
      }, 2500);
    } catch {
      if (timerRef.current) window.clearInterval(timerRef.current);
      setUploadStatus("error");
      // keep file for retry, reset step after delay
      setTimeout(() => {
        setUploadStep(0);
        setUploadStatus("processing");
      }, 2000);
    }
  };

  const handlePublish = (id: string) =>
    run(
      `publish-${id}`,
      async () => {
        await api.patch(`/api/admin/resumes/${id}`, {});
        await load();
      },
      { successTitle: "Resume published", successMsg: "Selected version is now live.", errorTitle: "Publish failed" }
    );

  const handleExtract = (id: string) =>
    run(
      `extract-${id}`,
      async () => {
        await api.post(`/api/admin/resumes/${id}/extract`);
        await load();
      },
      { successTitle: "Extraction queued", successMsg: "Review it before publishing.", errorTitle: "Extraction failed" }
    );

  const handleDelete = (id: string) =>
    run(
      `delete-${id}`,
      async () => {
        if (!confirm("Delete this version? This cannot be undone.")) throw new Error("Cancelled");
        await api.del(`/api/admin/resumes/${id}`);
        await load();
      },
      { successTitle: "Resume deleted", successMsg: "", errorTitle: "Delete failed" }
    );

  return (
    <div>
      <PageHead title="Resume" desc={<>PDF/DOCX, 10MB max, versioned. Current published is served at <span className="rla-code">/api/resume/current</span>.</>} />

      <Panel title="Upload new version" sub="Replaces the live resume immediately">
        <div className="rla-form-grid">
          <div style={{ gridColumn: "1 / -1" }}>
            <div className="rla-inline-actions" style={{ alignItems: "center" }}>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="rla-input"
                style={{ maxWidth: 320 }}
                disabled={uploading}
              />
              <button
                onClick={upload}
                disabled={!file || uploading}
                className="rla-btn rla-btn-primary rla-btn-sm"
                style={{ opacity: !file || uploading ? 0.6 : 1 }}
                aria-busy={uploading}
              >
                {uploading ? <><i className="fas fa-spinner fa-spin" /> Processing...</> : <><i className="fas fa-upload" /> Upload & Publish</>}
              </button>
              {uploading && <InlineLoader text={STEPS[uploadStep] || "Processing..."} />}
            </div>

            {uploading && (
              <div style={{ marginTop: 16, padding: 16, background: "var(--rla-bg)", border: "1px solid var(--rla-border)", borderRadius: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                  <span className="text-sm" style={{ fontWeight: 600 }}>Resume processing</span>
                  <span className="text-xs rla-code" style={{ color: uploadStatus === "error" ? "var(--rla-red)" : "var(--rla-text-faint)" }}>
                    {uploadStatus === "error" ? "Error" : uploadStatus === "done" ? "Completed" : `Step ${Math.min(uploadStep + 1, STEPS.length)} of ${STEPS.length}`}
                  </span>
                </div>
                <StepProgress steps={STEPS} current={uploadStep} status={uploadStatus} />
                <div className="text-xs" style={{ color: "var(--rla-text-faint)", marginTop: 10, display: "flex", alignItems: "center", gap: 6 }}>
                  <i className="fas fa-circle-info" /> {uploadStatus === "done" ? "Resume uploaded and knowledge updated." : uploadStatus === "error" ? "Processing encountered an issue." : "Please keep this tab open — do not close or retry."}
                </div>
              </div>
            )}
            {!uploading && uploadStatus === "done" && (
              <div className="text-sm" style={{ color: "var(--rla-green)", marginTop: 10, display: "flex", alignItems: "center", gap: 6 }}>
                <i className="fas fa-check-circle" /> Resume uploaded and profile knowledge updated successfully.
              </div>
            )}
          </div>
        </div>
      </Panel>

      <div style={{ height: 16 }} />
      <Panel title="Versions" sub={`${list.length} stored`}>
        <div className="rla-stack">
          {list.map((r) => {
            const publishing = isLoading(`publish-${r.id}`);
            const extracting = isLoading(`extract-${r.id}`);
            const deleting = isLoading(`delete-${r.id}`);
            const rowBusy = publishing || extracting || deleting;
            return (
              <div key={r.id} className="rla-list-card" style={{ opacity: rowBusy ? 0.7 : 1 }}>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="rla-doc-cell">
                    <span className="rla-doc-ic" style={{ background: "var(--rla-violet-soft)", color: "var(--rla-violet)" }}>
                      <i className="fas fa-file-pdf" />
                    </span>
                    <div>
                      <b>{r.fileName}</b>
                      <span>
                        v{r.version} · {new Date(r.uploadedAt).toLocaleString()} · {(r.sizeBytes / 1024).toFixed(1)} KB · {r.contentType}
                      </span>
                    </div>
                  </div>
                  <div className="rla-inline-actions">
                    <StatusPill status={r.status} />
                    <a
                      href={`/api/admin/resumes/${r.id}/download`}
                      target="_blank"
                      rel="noreferrer"
                      className="rla-mini-btn"
                      title="Download"
                      aria-label="Download resume"
                    >
                      <i className="fas fa-download" />
                    </a>
                    {r.status !== "published" && (
                      <button
                        onClick={() => handlePublish(r.id)}
                        disabled={rowBusy}
                        className="rla-btn rla-btn-primary rla-btn-sm"
                        aria-busy={publishing}
                      >
                        {publishing ? <InlineLoader text="Publishing..." /> : "Publish"}
                      </button>
                    )}
                    <button
                      onClick={() => handleExtract(r.id)}
                      disabled={rowBusy}
                      className="rla-btn rla-btn-ghost rla-btn-sm"
                      aria-busy={extracting}
                    >
                      {extracting ? <InlineLoader text="Extracting..." /> : "Extract → Review"}
                    </button>
                    <button
                      onClick={() => handleDelete(r.id)}
                      disabled={rowBusy}
                      className="rla-mini-btn danger"
                      title="Delete"
                      aria-label="Delete resume"
                    >
                      {deleting ? <i className="fas fa-spinner fa-spin" /> : <i className="fas fa-trash" />}
                    </button>
                  </div>
                </div>
                {rowBusy && (
                  <div className="text-xs" style={{ color: "var(--rla-text-faint)", marginTop: 8, display: "flex", gap: 6, alignItems: "center" }}>
                    <i className="fas fa-spinner fa-spin" style={{ color: "var(--rla-violet)" }} />
                    {publishing ? "Publishing version..." : extracting ? "Extracting information..." : "Deleting..."}
                  </div>
                )}
              </div>
            );
          })}
          {list.length === 0 && <Empty>No resumes yet. Upload one.</Empty>}
        </div>
      </Panel>
    </div>
  );
}
