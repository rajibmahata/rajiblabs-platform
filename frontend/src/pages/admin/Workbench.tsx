/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef, useState } from "react";
import { api } from "../../services/api";
import { Chip, Empty, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

const MODES = [
  { v: "job_application", label: "Job Application" },
  { v: "freelance_proposal", label: "Freelance / Upwork" },
  { v: "project_summary", label: "Project Summary" },
  { v: "project_explanation", label: "Project Explanation" },
  { v: "custom", label: "Custom" },
  { v: "cover_letter", label: "Cover Letter" },
  { v: "client_proposal", label: "Client Proposal" },
];
const STATUSES = ["draft", "ready", "submitted", "won", "lost", "archived"];
const TABS = [
  { v: "proposal", label: "Proposal" },
  { v: "cover", label: "Cover Letter" },
  { v: "summary", label: "Short Summary" },
  { v: "explanation", label: "Project Explanation" },
  { v: "sources", label: "Sources" },
];
const ANALYZE_STEPS = ["Reading project requirements…", "Extracting technologies & skills…", "Structuring analysis…"];
const GENERATE_STEPS = ["Reading project requirements…", "Matching Rajib's experience…", "Searching relevant projects…", "Checking GitHub evidence…", "Preparing recommendation…"];

type Progress = { steps: string[]; index: number; startedAt: number; elapsed: number } | null;

function useProgress(active: boolean, steps: string[]): [Progress, () => void] {
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
  useEffect(() => {
    if (!active) {
      if (timer.current) clearInterval(timer.current);
      setProg(null);
    }
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [active]);
  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);
  return [prog, start];
}

function ProgressBar({ prog, doneLabel }: { prog: NonNullable<Progress>; doneLabel?: string }) {
  const pct = Math.round(((prog.index + 1) / prog.steps.length) * 100);
  return (
    <div className="rla-progress" role="status" aria-live="polite">
      <div className="rla-progress-top"><span>{doneLabel ?? prog.steps[prog.index]}</span><span>{prog.elapsed}s elapsed</span></div>
      <div className="rla-progress-track"><div className="rla-progress-fill" style={{ width: `${pct}%` }} /></div>
      <div className="rla-progress-steps">{prog.steps.map((s, i) => (
        <span key={s} className={i < prog.index ? "done" : i === prog.index ? "active" : ""}>{i < prog.index ? "✓ " : ""}{s.replace(/…$/, "")}</span>
      ))}</div>
    </div>
  );
}

export default function Workbench({ initialView = "workspace" }: { initialView?: "workspace" | "history" }) {
  const [view, setView] = useState(initialView);
  const [mode, setMode] = useState("freelance_proposal");
  const [jd, setJd] = useState("");
  const [company, setCompany] = useState("");
  const [instructions, setInstructions] = useState("");
  const [busyAnalyze, setBusyAnalyze] = useState(false);
  const [busyGenerate, setBusyGenerate] = useState(false);
  const [busyRefine, setBusyRefine] = useState<string | null>(null);
  const [busyChat, setBusyChat] = useState(false);
  const [busySave, setBusySave] = useState(false);
  const [analyzeProg, startAnalyzeProg] = useProgress(busyAnalyze, ANALYZE_STEPS);
  const [generateProg, startGenerateProg] = useProgress(busyGenerate, GENERATE_STEPS);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [match, setMatch] = useState<any>(null);
  const [relevant, setRelevant] = useState<any[]>([]);
  const [sources, setSources] = useState<any[]>([]);
  const [quality, setQuality] = useState<any>(null);
  const [stages, setStages] = useState<any[]>([]);
  const [totalMs, setTotalMs] = useState<number | null>(null);
  const [proposal, setProposal] = useState("");
  const [cover, setCover] = useState("");
  const [summary, setSummary] = useState("");
  const [explanation, setExplanation] = useState("");
  const [outTab, setOutTab] = useState("proposal");
  const [err, setErr] = useState<{ where: string; message: string; retry: () => void } | null>(null);
  const [msgs, setMsgs] = useState<{ role: string; text: string }[]>([
    { role: "assistant", text: "Tell me what opportunity you're applying for — paste the job description, RFP or client email." },
  ]);
  const [chat, setChat] = useState("");
  const [docs, setDocs] = useState<any[]>([]);
  const [docFilter, setDocFilter] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const fail = (where: string, e: any, retry: () => void) => {
    const message = String(e?.message || e).slice(0, 300);
    setErr({ where, message, retry });
    toast(`${where} failed`, message.slice(0, 120));
  };

  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight }); }, [msgs]);
  useEffect(() => { if (view === "history") loadDocs(); }, [view]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadDocs = () => {
    const q = docFilter ? `?search=${encodeURIComponent(docFilter)}` : "";
    api.get<any[]>(`/api/admin/ai/proposals${q}`).then(setDocs).catch(() => {});
  };
  const validJd = () => {
    if (jd.trim().length < 20) { toast("Nothing to analyze", "Paste the opportunity description first (min 20 characters)."); return false; }
    return true;
  };
  const syncGen = (g: any) => {
    setAnalysis(g.analysis); setMatch(g.match); setRelevant(g.relevant_experience || []);
    setSources(g.sources || []); setQuality(g.quality || null);
    setStages(g.stages || []); setTotalMs(g.total_ms ?? null);
    setProposal(g.proposal || ""); setCover(g.cover_letter || ""); setSummary(g.short_summary || "");
    setExplanation(g.explanation || "");
    if (g.session_id) setSessionId(g.session_id);
    setErr(null);
  };

  const doAnalyze = async () => {
    if (!validJd() || busyAnalyze || busyGenerate) return;
    setBusyAnalyze(true); startAnalyzeProg(); setErr(null);
    try {
      const r = await api.post<any>("/api/admin/ai/proposal/analyze",
        { job_description: jd, mode, session_id: sessionId, company: company || undefined, instructions: instructions || undefined });
      setAnalysis(r.analysis); setSessionId(r.session_id); setErr(null);
      setMsgs((m) => [...m, { role: "user", text: jd.slice(0, 400) + (jd.length > 400 ? "…" : "") },
        { role: "assistant", text: `Analyzed: ${r.analysis.title || "opportunity"} (${r.analysis.industry || "industry TBD"}). Tech: ${(r.analysis.technologies || []).slice(0, 6).join(", ") || "—"} in ${((r.elapsed_ms ?? 0) / 1000).toFixed(1)}s. Press Generate Proposal when ready.` }]);
    } catch (e: any) { fail("Analyze", e, doAnalyze); } finally { setBusyAnalyze(false); }
  };
  const doGenerate = async () => {
    if (!validJd() || busyAnalyze || busyGenerate) return;
    setBusyGenerate(true); startGenerateProg(); setErr(null);
    try {
      const g = await api.post<any>("/api/admin/ai/proposal/generate",
        { job_description: jd, mode, analysis, session_id: sessionId, company: company || undefined, instructions: instructions || undefined });
      syncGen(g);
      setMsgs((m) => [...m, { role: "assistant", text: `Generated (${mode}, AI relevance estimate ${g.match?.match_score ?? 0}%) in ${((g.total_ms ?? 0) / 1000).toFixed(1)}s. Review the tabs on the right, then refine or save.` }]);
    } catch (e: any) { fail("Generate", e, doGenerate); } finally { setBusyGenerate(false); }
  };
  const refineTarget = outTab === "cover" ? "cover_letter" : outTab === "summary" ? "summary" : outTab === "explanation" ? "explanation" : "proposal";
  const doRefine = async (instruction: string, target: string = refineTarget) => {
    if (!instruction.trim() || busyRefine || busyGenerate) return;
    setBusyRefine(target + instruction);
    try {
      const r = await api.post<any>("/api/admin/ai/proposal/refine", { session_id: sessionId, instruction, target });
      if (target === "cover_letter") setCover(r.text);
      else if (target === "summary") setSummary(r.text);
      else if (target === "explanation") setExplanation(r.text);
      else setProposal(r.text);
      if (r.session_id) setSessionId(r.session_id);
      setErr(null);
    } catch (e: any) { fail("Refine", e, () => doRefine(instruction, target)); } finally { setBusyRefine(null); }
  };
  const refineProject = async (add: boolean) => {
    const name = prompt(add ? "Which project should be added as evidence?" : "Which project reference should be removed?");
    if (!name?.trim()) return;
    await doRefine(add ? `Add the ${name.trim()} project as evidence.` : `Remove the ${name.trim()} project reference.`, refineTarget);
  };
  const sendChat = async (text: string) => {
    const t = text.trim();
    if (!t || busyChat || busyGenerate) return;
    setChat("");
    setMsgs((m) => [...m, { role: "user", text: t }]);
    setBusyChat(true);
    try {
      const r = await api.post<any>("/api/admin/ai/chat", { session_id: sessionId, message: t, mode });
      setSessionId(r.session_id);
      setMsgs((m) => [...m, { role: "assistant", text: r.reply }]);
      if (r.artifacts && (r.artifacts.proposal || r.artifacts.cover_letter || r.artifacts.short_summary)) {
        setProposal(r.artifacts.proposal || proposal);
        setCover(r.artifacts.cover_letter || cover);
        setSummary(r.artifacts.short_summary || summary);
      }
      if (r.analysis) setAnalysis(r.analysis);
      if (r.sources?.length) setSources(r.sources);
      setErr(null);
    } catch (e: any) {
      setMsgs((m) => [...m, { role: "assistant", text: `Error: ${String((e as Error).message || e)}` }]);
    } finally { setBusyChat(false); }
  };
  const doSave = async () => {
    if (!validJd() || busySave) return;
    const title = prompt("Title for this application:", analysis?.title || "Untitled opportunity");
    if (!title) return;
    setBusySave(true);
    try {
      const r = await api.post<any>("/api/admin/ai/proposal/save", {
        type: mode, title, job_description: jd, analysis: analysis || {},
        match: match || {}, relevant_experience: relevant, proposal, cover_letter: cover,
        summary, explanation, sources, status: "draft", session_id: sessionId,
      });
      toast("Saved", `Application saved (${r.id}). Open History to track it.`);
    } catch (e: any) { fail("Save", e, doSave); } finally { setBusySave(false); }
  };
  const docAction = async (id: string, action: "delete" | "duplicate" | string) => {
    try {
      if (action === "delete") { if (!confirm("Delete this application?")) return; await api.del(`/api/admin/ai/proposal/${id}`); }
      else if (action === "duplicate") await api.post(`/api/admin/ai/proposal/${id}/duplicate`);
      else await api.put(`/api/admin/ai/proposal/${id}`, { ...(docs.find((d) => d.id === id) || {}), status: action });
      loadDocs();
    } catch (e: any) { toast("Action failed", String(e.message || e).slice(0, 120)); }
  };
  const copy = (t: string) => { navigator.clipboard?.writeText(t).catch(() => {}); toast("Copied", "Text copied to clipboard."); };
  const download = () => {
    const tabText = outTab === "cover" ? cover : outTab === "summary" ? summary : outTab === "explanation" ? explanation : proposal;
    const md = `# ${analysis?.title || "Proposal"}\n\n${tabText}\n\n---\n_Generated by RajibLabs AI Proposal Studio (${mode})_\n`;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([md], { type: "text/markdown" }));
    a.download = `${(analysis?.title || "proposal").replace(/[^a-z0-9]+/gi, "-").slice(0, 60)}-${outTab}.md`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const anyBusy = busyAnalyze || busyGenerate || busyChat || busySave || busyRefine !== null;
  const ghRelevant = relevant.filter((r) => /github|repo/i.test(`${r.project} ${r.evidence}`));
  return (
    <div>
      <PageHead title="AI Proposal Studio" desc="Paste an opportunity, generate a tailored proposal from verified RAG evidence."
        actions={<><Chip active={view === "workspace"} onClick={() => setView("workspace")}>Workspace</Chip><Chip active={view === "history"} onClick={() => setView("history")}>History</Chip></>} />

      {view === "history" ? (
        <div>
          <div className="rla-chip-row">
            <input value={docFilter} onChange={(e) => setDocFilter(e.target.value)} onKeyDown={(e) => e.key === "Enter" && loadDocs()} placeholder="Search applications…" className="rla-search-input" style={{ minWidth: 180 }} aria-label="Search applications" />
            <Chip onClick={loadDocs}>Search</Chip>
          </div>
          <div className="rla-stack">
            {docs.map((d) => (
              <div key={d.id} className="rla-list-card text-sm">
                <div className="flex flex-wrap justify-between gap-2">
                  <div><span className="font-medium">{d.title}</span>
                    <span className="rla-code" style={{ marginLeft: 6 }}>{d.type} · {d.match_score}% · {d.client || "no company"} · {d.created_at?.slice(0, 10)}</span></div>
                  <div className="rla-inline-actions">
                    <select value={d.status} onChange={(e) => docAction(d.id, e.target.value)} className="rla-select" style={{ fontSize: ".76rem", padding: "6px 10px", borderRadius: 100 }}>
                      {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <button onClick={() => docAction(d.id, "duplicate")} className="rla-btn rla-btn-ghost rla-btn-sm">Duplicate</button>
                    <button onClick={() => docAction(d.id, "delete")} className="rla-mini-btn danger" title="Delete"><i className="fas fa-trash" /></button>
                  </div>
                </div>
                <div className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>{d.job_title}</div>
              </div>
            ))}
            {docs.length === 0 && <Empty>No saved applications yet.</Empty>}
          </div>
        </div>
      ) : (
        <div className="grid xl:grid-cols-3 lg:grid-cols-2 gap-4">
          {/* LEFT: input */}
          <div className="rla-stack">
            <Panel title="Opportunity" sub="Paste the job, RFP or client email">
              <div className="rla-chip-row">
                {MODES.map((m) => (
                  <Chip key={m.v} active={mode === m.v} onClick={() => setMode(m.v)}>{m.label}</Chip>
                ))}
              </div>
              <textarea value={jd} onChange={(e) => setJd(e.target.value)} rows={7} placeholder="Paste the freelancer job, LinkedIn opportunity, RFP, client email…" className="rla-textarea" aria-label="Job description" />
              <div className="rla-form-grid" style={{ marginTop: 8 }}>
                <div><input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Company / client (optional)" className="rla-input" aria-label="Company" /></div>
                <div><input value={instructions} onChange={(e) => setInstructions(e.target.value)} placeholder="Extra instructions (optional)" className="rla-input" aria-label="Extra instructions" /></div>
              </div>
              <div className="rla-inline-actions" style={{ marginTop: 10 }}>
                <button onClick={doAnalyze} disabled={busyAnalyze || busyGenerate} className="rla-btn rla-btn-ghost rla-btn-sm"><i className={`fas fa-magnifying-glass${busyAnalyze ? " fa-spin" : ""}`} /> {busyAnalyze ? "Analyzing…" : analysis ? "Re-analyze" : "Analyze"}</button>
                <button onClick={doGenerate} disabled={busyAnalyze || busyGenerate} className="rla-btn rla-btn-primary rla-btn-sm"><i className={`fas fa-wand-magic-sparkles${busyGenerate ? " fa-spin" : ""}`} /> {busyGenerate ? "Generating…" : proposal ? "Regenerate" : "Generate Proposal"}</button>
              </div>
              {busyAnalyze && analyzeProg && <div style={{ marginTop: 10 }}><ProgressBar prog={analyzeProg} /></div>}
              {busyGenerate && generateProg && <div style={{ marginTop: 10 }}><ProgressBar prog={generateProg} /></div>}
              {!busyAnalyze && !busyGenerate && stages.length > 0 && (
                <div className="text-xs mt-2" style={{ color: "var(--rla-text-faint)" }}>
                  Completed in {(totalMs ?? 0) / 1000 < 1 ? `${totalMs ?? 0} ms` : `${((totalMs ?? 0) / 1000).toFixed(1)}s`}: {stages.map((s) => `${s.label.replace(/…$/, "")} ${(s.ms / 1000).toFixed(1)}s`).join(" · ")}
                </div>
              )}
            </Panel>

            {err && (
              <Panel title={`${err.where} failed`} sub="Your input and generated content are preserved">
                <p className="text-sm rla-danger-text">{err.message}</p>
                <div className="rla-inline-actions" style={{ marginTop: 8 }}>
                  <button onClick={() => { const r = err.retry; setErr(null); r(); }} className="rla-btn rla-btn-primary rla-btn-sm">Retry</button>
                  <button onClick={() => setErr(null)} className="rla-btn rla-btn-ghost rla-btn-sm">Dismiss</button>
                </div>
              </Panel>
            )}

            <Panel title="Conversation" sub="Refine, ask, or paste a new opportunity">
              <div ref={scrollRef} className="space-y-2 max-h-72 overflow-y-auto mb-2">
                {msgs.map((m, i) => (
                  <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                    <span className="inline-block px-3 py-1.5 rounded-xl text-sm" style={m.role === "user" ? { background: "var(--rla-violet)", color: "#fff" } : { background: "#eef0f6" }}>{m.text}</span>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input value={chat} onChange={(e) => setChat(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendChat(chat)} placeholder="Refine, ask, or paste a new opportunity…" className="rla-input flex-1" aria-label="Workbench chat" />
                <button onClick={() => sendChat(chat)} disabled={busyChat || busyGenerate} className="rla-btn rla-btn-primary rla-btn-sm">{busyChat ? "Sending…" : "Send"}</button>
              </div>
            </Panel>
          </div>

          {/* CENTER: analysis */}
          <div className="rla-stack">
            <Panel title="Analysis" sub={analysis ? `${analysis.title || ""}${analysis.company ? ` · ${analysis.company}` : ""}${analysis.industry ? ` · ${analysis.industry}` : ""}` : "Run Analyze to extract requirements"}
              action={match != null ? <span className="rla-pill ok">{match.match_score}% RELEVANCE</span> : undefined}>
              {!analysis && <Empty>No analysis yet — paste an opportunity and press Analyze.</Empty>}
              {analysis && (<div className="text-sm space-y-2">
                <div><b>Technologies:</b> {(analysis.technologies || []).join(", ") || "—"}</div>
                <div><b>Required skills:</b> {(analysis.required_skills || []).join(", ") || "—"}</div>
                {analysis.years_experience && <div><b>Experience:</b> {analysis.years_experience}</div>}
                {analysis.business_problem && <div><b>Problem:</b> {analysis.business_problem}</div>}
                {(analysis.responsibilities || []).length > 0 && <div><b>Responsibilities:</b> {analysis.responsibilities.join("; ")}</div>}
                {(analysis.deliverables || []).length > 0 && <div><b>Deliverables:</b> {analysis.deliverables.join("; ")}</div>}
                {(analysis.pain_points || []).length > 0 && <div><b>Client pain points:</b> {analysis.pain_points.join("; ")}</div>}
                <div><b>Keywords:</b> {(analysis.keywords || []).slice(0, 12).join(", ") || "—"}</div>
                {quality && !quality.passed && <div className="text-xs" style={{ color: "var(--rla-amber)" }}>Quality flags: {quality.issues.join(", ")}</div>}
              </div>)}
            </Panel>

            <Panel title="Matching Evidence" sub={relevant.length ? `${relevant.length} matched · 2–4 strongest used` : "Appears after Generate"}>
              {relevant.length === 0 && <Empty>Generate to see requirement → evidence matches.</Empty>}
              {relevant.map((r, i) => (
                <div key={i} className="text-sm py-1.5" style={{ borderBottom: "1px solid var(--rla-border)" }}>
                  <div><b>{r.requirement}</b></div>
                  <div>→ {r.project || "no direct evidence"}</div>
                  {r.reason && <div className="text-xs" style={{ color: "var(--rla-text-secondary)" }}>Why: {r.reason}</div>}
                  {r.evidence && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>{String(r.evidence).slice(0, 160)}</div>}
                  {r.url && <a href={r.url} target="_blank" rel="noreferrer" className="text-xs underline">Verified source ↗</a>}
                </div>
              ))}
              {match && (match.gaps || []).length > 0 && (
                <div className="text-xs mt-2" style={{ color: "var(--rla-amber)" }}>Gaps / missing evidence: {match.gaps.join("; ")}</div>
              )}
              {match && (match.strengths || []).length > 0 && (
                <div className="text-xs mt-1">Strengths: {match.strengths.join("; ")}</div>
              )}
              {ghRelevant.length > 0 && (<>
                <div className="rla-section-title" style={{ marginTop: 10 }}>GitHub evidence</div>
                {ghRelevant.map((r, i) => (
                  <div key={i} className="text-xs py-0.5">{r.project} {r.url && <a href={r.url} target="_blank" rel="noreferrer" className="underline">open ↗</a>}</div>
                ))}
              </>)}
            </Panel>
          </div>

          {/* RIGHT: output tabs */}
          <div className="rla-stack">
            <Panel title="Generated Output" sub={proposal || cover || summary ? "Editable — changes stay local until saved" : "Generate to fill the tabs"}
              action={<div className="rla-inline-actions">
                <button onClick={() => copy(outTab === "cover" ? cover : outTab === "summary" ? summary : outTab === "explanation" ? explanation : proposal)} className="rla-btn rla-btn-ghost rla-btn-sm">Copy</button>
                <button onClick={download} disabled={!(proposal || cover || summary)} className="rla-btn rla-btn-ghost rla-btn-sm">Download</button>
                <button onClick={doSave} disabled={busySave || busyGenerate} className="rla-btn rla-btn-primary rla-btn-sm">{busySave ? "Saving…" : "Save"}</button>
              </div>}>
              <div className="rla-chip-row">
                {TABS.map((t) => <Chip key={t.v} active={outTab === t.v} onClick={() => setOutTab(t.v)}>{t.label}</Chip>)}
              </div>
              {outTab === "sources" ? (
                <div>
                  {sources.length === 0 && <div className="text-xs" style={{ color: "var(--rla-text-faint)" }}>None yet — generate to see evidence.</div>}
                  {sources.map((s, i) => (
                    <div key={i} className="text-xs py-1" style={{ borderBottom: "1px solid var(--rla-border)" }}>
                      <div><b>{s.title}</b> <span style={{ color: "var(--rla-text-faint)" }}>({s.type})</span></div>
                      {s.reason && <div style={{ color: "var(--rla-text-secondary)" }}>{s.reason}</div>}
                      {s.url && <a href={s.url} target="_blank" rel="noreferrer" className="underline">Verified source ↗</a>}
                    </div>
                  ))}
                  <div className="rla-inline-actions" style={{ marginTop: 10 }}>
                    <button onClick={doGenerate} disabled={busyAnalyze || busyGenerate} className="rla-btn rla-btn-ghost rla-btn-sm">Regenerate</button>
                  </div>
                </div>
              ) : (
                <>
                  <textarea
                    value={outTab === "cover" ? cover : outTab === "summary" ? summary : outTab === "explanation" ? explanation : proposal}
                    onChange={(e) => outTab === "cover" ? setCover(e.target.value) : outTab === "summary" ? setSummary(e.target.value) : outTab === "explanation" ? setExplanation(e.target.value) : setProposal(e.target.value)}
                    rows={outTab === "summary" ? 3 : 12}
                    placeholder={`${TABS.find((t) => t.v === outTab)?.label} appears here — editable.`}
                    className="rla-textarea" aria-label={outTab} />
                  <div className="rla-inline-actions" style={{ marginTop: 10 }}>
                    <button onClick={() => doRefine("Make it shorter.", outTab === "cover" ? "cover_letter" : outTab === "summary" ? "summary" : outTab === "explanation" ? "explanation" : "proposal")} disabled={busyRefine !== null || busyGenerate} className="rla-btn rla-btn-ghost rla-btn-sm">{busyRefine ? "Refining…" : "Shorter"}</button>
                    <button onClick={() => doRefine("Make it more technical.", outTab === "cover" ? "cover_letter" : outTab)} disabled={busyRefine !== null || busyGenerate} className="rla-btn rla-btn-ghost rla-btn-sm">Technical</button>
                    <button onClick={() => doRefine("Make it more business-focused.", outTab === "cover" ? "cover_letter" : outTab)} disabled={busyRefine !== null || busyGenerate} className="rla-btn rla-btn-ghost rla-btn-sm">Business</button>
                    <button onClick={() => doRefine("Remove generic language; sound human.", outTab === "cover" ? "cover_letter" : outTab)} disabled={busyRefine !== null || busyGenerate} className="rla-btn rla-btn-ghost rla-btn-sm">De-AI</button>
                    <button onClick={() => refineProject(true)} disabled={busyRefine !== null || busyGenerate} className="rla-btn rla-btn-ghost rla-btn-sm">+ Project</button>
                    <button onClick={() => refineProject(false)} disabled={busyRefine !== null || busyGenerate} className="rla-btn rla-btn-ghost rla-btn-sm">− Project</button>
                  </div>
                  {relevant.length > 0 && <div style={{ marginTop: 8 }}><StatusPill status={match?.match_score >= 70 ? "ready" : "draft"} /></div>}
                </>
              )}
            </Panel>
          </div>
        </div>
      )}
    </div>
  );
}
