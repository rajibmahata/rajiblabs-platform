/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef, useState } from "react";
import { api } from "../../services/api";
import { Chip, Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

const ANALYZE_STEPS = ["Reading job requirements…", "Matching Rajib's professional experience…", "Searching relevant projects…", "Checking GitHub evidence…", "Preparing application…"];
const GENERATE_STEPS = ["Reading job requirements…", "Matching Rajib's professional experience…", "Searching relevant projects…", "Checking GitHub evidence…", "Preparing application…"];
const TABS = [
  { v: "email", label: "Email" },
  { v: "cover", label: "Cover Letter" },
  { v: "summary", label: "Summary" },
  { v: "evidence", label: "Evidence" },
  { v: "sources", label: "Sources" },
];

type Progress = { steps: string[]; index: number; startedAt: number; elapsed: number } | null;

function useProgress(steps: string[]): [Progress, () => void, () => void] {
  const [prog, setProg] = useState<Progress>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const start = () => {
    const startedAt = Date.now();
    setProg({ steps, index: 0, startedAt, elapsed: 0 });
    if (timer.current) clearInterval(timer.current);
    timer.current = setInterval(() => {
      setProg((p) => {
        if (!p) return p;
        const elapsed = Math.floor((Date.now() - p.startedAt) / 1000);
        const index = Math.min(p.steps.length - 1, Math.floor(elapsed / 4));
        return { ...p, index, elapsed };
      });
    }, 500);
  };
  const stop = () => {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    setProg(null);
  };
  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);
  return [prog, start, stop];
}

function ProgressBar({ prog }: { prog: NonNullable<Progress> }) {
  const pct = Math.round(((prog.index + 1) / prog.steps.length) * 100);
  return (
    <div className="rla-progress" role="status" aria-live="polite">
      <div className="rla-progress-top"><span>{prog.steps[prog.index]}</span><span>{prog.elapsed}s elapsed</span></div>
      <div className="rla-progress-track"><div className="rla-progress-fill" style={{ width: `${pct}%` }} /></div>
      <div className="rla-progress-steps">{prog.steps.map((s, i) => (
        <span key={s} className={i < prog.index ? "done" : i === prog.index ? "active" : ""}>{i < prog.index ? "✓ " : ""}{s.replace(/…$/, "")}</span>
      ))}</div>
    </div>
  );
}

function jobIdFromUrl(): string {
  try { return new URLSearchParams(window.location.search).get("job") || ""; }
  catch { return ""; }
}

export default function CareerWorkspace() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [jobId, setJobId] = useState(jobIdFromUrl());
  const [job, setJob] = useState<any>(null);
  const [contactId, setContactId] = useState("");
  const [instructions, setInstructions] = useState("");
  const [analysis, setAnalysis] = useState<any>(null);
  const [matches, setMatches] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);
  const [selected, setSelected] = useState<any[]>([]);
  const [quality, setQuality] = useState<any>(null);
  const [app, setApp] = useState<any>(null);
  const [outTab, setOutTab] = useState("email");
  const [refineText, setRefineText] = useState("");
  const [refineTarget, setRefineTarget] = useState("email_body");
  const [showSend, setShowSend] = useState(false);
  const [busyAnalyze, setBusyAnalyze] = useState(false);
  const [busyGenerate, setBusyGenerate] = useState(false);
  const [busyRefine, setBusyRefine] = useState(false);
  const [busySend, setBusySend] = useState(false);
  const [analyzeProg, startAnalyzeProg, stopAnalyzeProg] = useProgress(ANALYZE_STEPS);
  const [generateProg, startGenerateProg, stopGenerateProg] = useProgress(GENERATE_STEPS);
  const [err, setErr] = useState<{ where: string; message: string; retry: () => void } | null>(null);

  const loadJobs = () => {
    api.get<any>("/api/admin/career/jobs?status=Open").then((r) => setJobs(r.items || [])).catch(() => {});
  };
  const loadJob = async (id: string) => {
    if (!id) { setJob(null); return; }
    const d = await api.get<any>(`/api/admin/career/jobs/${id}`).catch(() => null);
    if (d) {
      setJob(d);
      setAnalysis(d.analysis?.title ? d : null);
      if (d.contacts?.length && !contactId) setContactId(d.contacts[0].id);
    }
  };
  useEffect(() => { loadJobs(); }, []);
  useEffect(() => { if (jobId) void loadJob(jobId); }, [jobId]); // eslint-disable-line react-hooks/exhaustive-deps, react-hooks/set-state-in-effect -- fetch on selection change

  const fail = (where: string, e: any, retry: () => void) => {
    const message = String(e?.message || e).slice(0, 300);
    setErr({ where, message, retry });
    toast(`${where} failed`, message.slice(0, 120));
  };
  const conflicting = busyAnalyze || busyGenerate || busyRefine || busySend;

  const doAnalyze = async () => {
    if (!job || busyAnalyze || busyGenerate) return;
    setBusyAnalyze(true); startAnalyzeProg(); setErr(null);
    try {
      const r = await api.post<any>(`/api/admin/career/jobs/${job.id}/analyze`, { instructions: instructions || undefined });
      setAnalysis({ ...r, job_id: job.id });
      setMatches(r.matches || []);
      setReport(r.report || null);
      setSelected(r.selected || []);
      setErr(null);
    } catch (e: any) { fail("Analyze", e, doAnalyze); } finally { setBusyAnalyze(false); stopAnalyzeProg(); }
  };
  const doGenerate = async () => {
    if (!job || busyAnalyze || busyGenerate) return;
    setBusyGenerate(true); startGenerateProg(); setErr(null);
    try {
      const g = await api.post<any>(`/api/admin/career/jobs/${job.id}/generate`,
        { contact_id: contactId || undefined, instructions: instructions || undefined });
      setApp(g);
      setMatches(g.relevant_experience || g.matches || matches);
      setReport(g.match || report);
      setSelected((g.sources || []).map((s: any) => ({ doc_title: s.title, source_type: s.type, doc_url: s.url, reason: s.reason })));
      setQuality(g.quality || null);
      setAnalysis(g.analysis || analysis);
      setErr(null);
      toast("Generated", "Application ready for review — nothing sent.");
    } catch (e: any) { fail("Generate", e, doGenerate); } finally { setBusyGenerate(false); stopGenerateProg(); }
  };
  const doRefine = async () => {
    if (!app || !refineText.trim() || busyRefine || conflicting) return;
    setBusyRefine(true);
    try {
      const r = await api.post<any>(`/api/admin/career/applications/${app.application_id}/refine`,
        { instruction: refineText.trim(), target: refineTarget });
      setApp({ ...app, [refineTarget === "cover_letter" ? "cover_letter" : refineTarget === "summary" ? "summary" : "email_body"]: r.text });
      if (r.quality) setQuality(r.quality);
      setRefineText(""); setErr(null);
    } catch (e: any) { fail("Refine", e, doRefine); } finally { setBusyRefine(false); }
  };
  const doApprove = async () => {
    if (!app || conflicting) return;
    if (!confirm("Approve this application for sending?")) return;
    try {
      const r = await api.post<any>(`/api/admin/career/applications/${app.application_id}/approve`, {});
      setApp({ ...app, status: r.status, approved_by: r.approved_by });
      toast("Approved", "Ready to send.");
    } catch (e: any) { fail("Approve", e, doApprove); }
  };
  const doSend = async () => {
    if (!app || busySend || conflicting) return;
    setBusySend(true);
    try {
      const r = await api.post<any>(`/api/admin/career/applications/${app.application_id}/send`, {});
      setApp({ ...app, status: "Sent", sent_at: r.sent_at });
      setShowSend(false);
      toast("Sent", `Application emailed (${r.to_domain}).`);
    } catch (e: any) { fail("Send", e, doSend); } finally { setBusySend(false); }
  };

  const status: string = app?.status || "";
  const canSend = status === "Approved";
  const emailBody: string = app?.email_body || "";
  const cover: string = app?.cover_letter || "";
  const summary: string = app?.summary || "";
  const ghMatches = matches.filter((m: any) => /github|repo/i.test(`${m.project || ""} ${(m.evidence || "").slice(0, 200)}`));

  return (
    <div>
      <PageHead title="Career Workspace" desc="Analyze a job, generate a targeted application, review, approve, then send." />
      {err && (
        <Panel title={`${err.where} failed`} sub="Your input and generated content are preserved">
          <p className="text-sm rla-danger-text">{err.message}</p>
          <div className="rla-inline-actions" style={{ marginTop: 8 }}>
            <button onClick={() => { const r = err.retry; setErr(null); r(); }} className="rla-btn rla-btn-primary rla-btn-sm">Retry</button>
            <button onClick={() => setErr(null)} className="rla-btn rla-btn-ghost rla-btn-sm">Dismiss</button>
          </div>
        </Panel>
      )}
      <div style={{ height: 16 }} />
      <div className="grid xl:grid-cols-3 lg:grid-cols-2 gap-4">
        {/* LEFT: job info */}
        <div className="rla-stack">
          <Panel title="Job information" sub="Pick an open role">
            <Field label="Job opening">
              <select value={jobId} onChange={(e) => { setJobId(e.target.value); setApp(null); setAnalysis(null); setMatches([]); }} className="rla-select">
                <option value="">— select —</option>
                {jobs.map((j) => <option key={j.id} value={j.id}>{j.title} · {j.company_name || ""}</option>)}
              </select>
            </Field>
            {job && (<div className="text-sm space-y-1 mt-2">
              <div><b>{job.title}</b>{job.company_name ? ` · ${job.company_name}` : ""}</div>
              {job.location && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{job.location}{job.employment_type ? ` · ${job.employment_type}` : ""}</div>}
              {job.job_url && <div className="text-xs"><a href={job.job_url} target="_blank" rel="noreferrer" className="underline">Job posting ↗</a></div>}
              <div className="text-xs" style={{ maxHeight: 160, overflowY: "auto", color: "var(--rla-text-secondary)" }}>{(job.description || "").slice(0, 900)}{(job.description || "").length > 900 ? "…" : ""}</div>
            </div>)}
            <Field label="HR / recruiter">
              <select value={contactId} onChange={(e) => setContactId(e.target.value)} className="rla-select">
                <option value="">— none yet —</option>
                {(job?.contacts || []).map((c: any) => <option key={c.id} value={c.id}>{c.name} · {c.email}{c.verified ? " ✓" : ""}</option>)}
              </select>
            </Field>
            <Field label="Additional instructions"><textarea value={instructions} onChange={(e) => setInstructions(e.target.value)} rows={2} placeholder="Optional guidance for the agent…" className="rla-textarea" /></Field>
            <div className="rla-inline-actions" style={{ marginTop: 10 }}>
              <button onClick={doAnalyze} disabled={!job || busyAnalyze || busyGenerate} className="rla-btn rla-btn-ghost rla-btn-sm">
                <i className={`fas fa-magnifying-glass${busyAnalyze ? " fa-spin" : ""}`} /> {busyAnalyze ? "Analyzing…" : "Analyze"}</button>
              <button onClick={doGenerate} disabled={!job || busyAnalyze || busyGenerate} className="rla-btn rla-btn-primary rla-btn-sm">
                <i className={`fas fa-wand-magic-sparkles${busyGenerate ? " fa-spin" : ""}`} /> {busyGenerate ? "Generating…" : "Generate Application"}</button>
            </div>
            {busyAnalyze && analyzeProg && <div style={{ marginTop: 10 }}><ProgressBar prog={analyzeProg} /></div>}
            {busyGenerate && generateProg && <div style={{ marginTop: 10 }}><ProgressBar prog={generateProg} /></div>}
          </Panel>
        </div>

        {/* CENTER: analysis */}
        <div className="rla-stack">
          <Panel title="AI Analysis"
            sub={analysis?.analysis?.title || analysis?.title ? `${analysis?.analysis?.title || analysis?.title || ""}` : "Run Analyze to extract requirements"}
            action={report ? <span className="rla-pill ok">{report.match_score}% MATCH</span> : undefined}>
            {!analysis && <Empty>No analysis yet — select a job and press Analyze.</Empty>}
            {analysis && (() => {
              const a = analysis.analysis || analysis;
              return (<div className="text-sm space-y-2">
                <div><b>Technologies:</b> {(a.technologies || []).join(", ") || "—"}</div>
                <div><b>Required skills:</b> {(a.required_skills || []).join(", ") || "—"}</div>
                {a.years_experience && <div><b>Experience:</b> {a.years_experience}</div>}
                {(a.pain_points || []).length > 0 && <div><b>Pain points:</b> {a.pain_points.join("; ")}</div>}
                <div><b>Keywords:</b> {(a.keywords || []).slice(0, 12).join(", ") || "—"}</div>
                {quality && !quality.passed && <div className="text-xs" style={{ color: "var(--rla-amber)" }}>Quality flags: {(quality.issues || []).join(", ")}</div>}
              </div>);
            })()}
          </Panel>
          <Panel title="Matching Evidence" sub={matches.length ? `${matches.length} matched · strongest first` : "Appears after Analyze"}>
            {matches.length === 0 && <Empty>Generate or analyze to see requirement → evidence matches.</Empty>}
            {matches.map((m: any, i: number) => (
              <div key={i} className="text-sm py-1.5" style={{ borderBottom: "1px solid var(--rla-border)" }}>
                <div><b>{m.requirement}</b></div>
                <div>→ {m.project || "no direct evidence"}</div>
                {m.reason && <div className="text-xs" style={{ color: "var(--rla-text-secondary)" }}>Why: {m.reason}</div>}
                {m.evidence && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{String(m.evidence).slice(0, 160)}</div>}
                {m.url && <a href={m.url} target="_blank" rel="noreferrer" className="text-xs underline">Verified source ↗</a>}
              </div>
            ))}
            {ghMatches.length > 0 && (<>
              <div className="rla-section-title" style={{ marginTop: 10 }}>GitHub evidence</div>
              {ghMatches.map((m: any, i: number) => (
                <div key={i} className="text-xs py-0.5">{m.project} {m.url && <a href={m.url} target="_blank" rel="noreferrer" className="underline">open ↗</a>}</div>
              ))}
            </>)}
          </Panel>
        </div>

        {/* RIGHT: output tabs */}
        <div className="rla-stack">
          <Panel title="Generated Application"
            sub={app ? `Status: ${app.status || ""}` : "Generate to fill the tabs"}
            action={app && <StatusPill status={app.status || "draft"} />}>
            <div className="rla-chip-row">
              {TABS.map((t) => <Chip key={t.v} active={outTab === t.v} onClick={() => setOutTab(t.v)}>{t.label}</Chip>)}
            </div>
            {outTab === "sources" ? (
              <div>
                {((app?.sources) || selected).length === 0 && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>None yet.</div>}
                {((app?.sources) || selected).map((s: any, i: number) => (
                  <div key={i} className="text-xs py-1" style={{ borderBottom: "1px solid var(--rla-border)" }}>
                    <div><b>{s.title}</b> <span style={{ color: "var(--rla-text-faint)" }}>({s.type || s.source_type})</span></div>
                    {s.reason && <div style={{ color: "var(--rla-text-secondary)" }}>{s.reason}</div>}
                    {s.url && <a href={s.url} target="_blank" rel="noreferrer" className="underline">Verified source ↗</a>}
                  </div>
                ))}
              </div>
            ) : (
              <>
                <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>
                  {outTab === "email" && <>Subject: <b style={{ color: "var(--rla-text)" }}>{app?.email_subject || "—"}</b></>}
                </div>
                <textarea
                  value={outTab === "email" ? emailBody : outTab === "cover" ? cover : summary}
                  readOnly rows={outTab === "summary" ? 4 : 12}
                  placeholder={`${TABS.find((t) => t.v === outTab)?.label} appears here after Generate.`}
                  className="rla-textarea" aria-label={outTab} style={{ marginTop: 6 }} />
                <div className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>Editable after Approve via Applications → edit, or Refine below.</div>
              </>
            )}
            <div className="rla-inline-actions" style={{ marginTop: 10 }}>
              <button onClick={() => doRefine()} disabled={!app || busyRefine || conflicting} className="rla-btn rla-btn-ghost rla-btn-sm">{busyRefine ? "Refining…" : "Refine"}</button>
              <button onClick={doApprove} disabled={!app || conflicting || !["Draft", "AI Generated", "Needs Review"].includes(status)} className="rla-btn rla-btn-ghost rla-btn-sm">Approve</button>
              <button onClick={() => setShowSend(true)} disabled={!app || conflicting || !canSend} className="rla-btn rla-btn-primary rla-btn-sm">Send…</button>
            </div>
            <div className="flex gap-2 mt-2">
              <input value={refineText} onChange={(e) => setRefineText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && doRefine()} placeholder='Refine, e.g. "Make this shorter"' className="rla-input flex-1" aria-label="Refine instruction" />
              <select value={refineTarget} onChange={(e) => setRefineTarget(e.target.value)} className="rla-select" aria-label="Refine target">
                <option value="email_body">Email</option><option value="cover_letter">Cover</option><option value="summary">Summary</option>
              </select>
            </div>
            {showSendFallbackNote(app)}
          </Panel>
        </div>
      </div>
      {showSend && app && (
        <div className="rla-modal-overlay" onClick={() => !busySend && setShowSend(false)}>
          <div className="rla-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Confirm send">
            <div className="rla-modal-head"><h3>Confirm send — nothing sent yet</h3>
              <button onClick={() => setShowSend(false)} className="rla-mini-btn" title="Close">✕</button></div>
            <dl className="rla-kv">
              <dt>Recipient</dt><dd>{app.contact_snapshot ? `${app.contact_snapshot.name} <${app.contact_snapshot.email}>` : "(no HR contact — attach one first)"}</dd>
              <dt>Subject</dt><dd>{app.email_subject || "—"}</dd>
              <dt>Company</dt><dd>{app.company_name || "—"}</dd>
              <dt>Job</dt><dd>{app.job_title || "—"}</dd>
              <dt>Attachments</dt><dd>none</dd>
            </dl>
            <h4>Email body</h4>
            <pre className="rla-pre">{emailBody || "(empty)"}</pre>
            <div className="rla-inline-actions" style={{ marginTop: 12 }}>
              <button onClick={doSend} disabled={busySend || !app.contact_snapshot?.email} className="rla-btn rla-btn-primary rla-btn-sm">{busySend ? "Sending…" : "Confirm & Send"}</button>
              <button onClick={() => setShowSend(false)} className="rla-btn rla-btn-ghost rla-btn-sm">Back to review</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  function showSendFallbackNote(a: any) {
    if (!a) return null;
    if (a.status === "Sent") return <div className="text-xs mt-2" style={{ color: "var(--rla-green)" }}>✓ Sent{a.sent_at ? ` ${new Date(a.sent_at).toLocaleString()}` : ""}. Status changes live in Applications.</div>;
    return null;
  }
}
