/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

export default function AgentsManage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [slug, setSlug] = useState("rajiblabs-concierge");
  const [doc, setDoc] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [convos, setConvos] = useState<any[]>([]);
  const [testMsg, setTestMsg] = useState("What projects has Rajib completed?");
  const [testRes, setTestRes] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<any>({});
  const [policy, setPolicy] = useState<Record<string, any>>({});
  const [creating, setCreating] = useState({ slug: "", name: "", agent_type: "support" });

  const load = async (s = slug) => {
    try {
      const list = await api.get<any[]>("/api/admin/agents");
      setAgents(Array.isArray(list) ? list : []);
      const d = await api.get<any>(`/api/admin/agents/${s}`);
      setDoc(d); setForm(d);
      setPolicy(d.knowledge_policy || {});
      try { setStats(await api.get(`/api/admin/agents/${s}/stats`)); } catch { /* no turns yet */ }
      try { setConvos(await api.get<any[]>(`/api/admin/agents/${s}/conversations?limit=20`)); } catch { /* none */ }
    } catch (e: any) { toast("Load failed", String(e.message || e).slice(0, 120)); }
  };
  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps, react-hooks/set-state-in-effect -- initial mount fetch

  const pick = (s: string) => { setSlug(s); setTestRes(null); load(s); };
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));

  const save = async () => {
    setBusy(true);
    try {
      const d = await api.put<any>(`/api/admin/agents/${slug}`, { ...form, knowledge_policy: policy });
      setDoc(d); setForm(d); setPolicy(d.knowledge_policy || {});
      load(slug); toast("Agent saved", d.name);
    } catch (e: any) { toast("Save failed", String(e.message || e).slice(0, 160)); } finally { setBusy(false); }
  };
  const toggle = async (k: "enabled" | "public_enabled") => {
    try { const d = await api.put<any>(`/api/admin/agents/${slug}`, { [k]: !form[k] }); setDoc(d); setForm(d); load(slug); }
    catch (e: any) { toast("Update failed", String(e.message || e).slice(0, 120)); }
  };
  const runTest = async () => {
    if (!testMsg.trim()) return;
    setBusy(true);
    try { setTestRes(await api.post<any>(`/api/admin/agents/${slug}/test`, { message: testMsg.trim() })); }
    catch (e: any) { toast("Test failed", String(e.message || e).slice(0, 160)); } finally { setBusy(false); }
  };
  const create = async () => {
    if (!creating.slug.trim() || !creating.name.trim()) { toast("Validation", "Slug + name are required."); return; }
    try { await api.post("/api/admin/agents", creating); setCreating({ slug: "", name: "", agent_type: "support" }); load(slug); toast("Agent created", creating.slug); }
    catch (e: any) { toast("Create failed", String(e.message || e).slice(0, 160)); }
  };
  const toggleTool = (t: string) => {
    const cur: string[] = form.allowed_tools || [];
    set("allowed_tools", cur.includes(t) ? cur.filter(x => x !== t) : [...cur, t]);
  };
  const setPol = (src: string, k: string, v: any) => setPolicy((p) => ({ ...p, [src]: { ...(p[src] || {}), [k]: v } }));

  const sources: string[] = doc?.known_sources || Object.keys(policy);
  return (
    <div>
      <PageHead title="AI Agents" desc="One shared knowledge base; per-agent tools, guardrails and behavior. The concierge serves the public homepage chat."
        actions={<button onClick={save} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-check" /> {busy ? "Saving…" : "Save Agent"}</button>} />
      <div className="rla-chip-row" style={{ marginBottom: 16 }}>
        {agents.map(a => (
          <button key={a.slug} onClick={() => pick(a.slug)} className={`rla-chip${slug === a.slug ? " active" : ""}`}>
            {a.name}{a.enabled === false ? " (off)" : ""}
          </button>
        ))}
      </div>

      {doc && (<>
        <Panel title={doc.name} sub={`${doc.slug} · ${doc.agent_type} · ${doc.description || ""}`}
          action={<div className="rla-inline-actions">
            <button onClick={() => toggle("enabled")} className="rla-btn rla-btn-ghost rla-btn-sm">{form.enabled === false ? "Enable" : "Disable"}</button>
            <button onClick={() => toggle("public_enabled")} className="rla-btn rla-btn-ghost rla-btn-sm">{form.public_enabled === false ? "Make public" : "Make private"}</button>
          </div>}>
          <div className="rla-form-grid">
            <Field label="Name"><input value={form.name || ""} onChange={e => set("name", e.target.value)} className="rla-input" /></Field>
            <Field label="Description" span><input value={form.description || ""} onChange={e => set("description", e.target.value)} className="rla-input" /></Field>
            <Field label="System instructions" span><textarea value={form.system_prompt || ""} onChange={e => set("system_prompt", e.target.value)} rows={5} className="rla-textarea" /></Field>
            <Field label="Response style" span><input value={form.response_style || ""} onChange={e => set("response_style", e.target.value)} className="rla-input" /></Field>
            <Field label="Hallucination policy"><input value={form.hallucination_policy || ""} onChange={e => set("hallucination_policy", e.target.value)} className="rla-input" /></Field>
            <Field label="Guardrail policy"><input value={form.guardrail_policy || ""} onChange={e => set("guardrail_policy", e.target.value)} className="rla-input" /></Field>
            <Field label="Response policy"><input value={form.response_policy || ""} onChange={e => set("response_policy", e.target.value)} className="rla-input" /></Field>
            <Field label="Fallback message" span><textarea value={form.fallback_message || ""} onChange={e => set("fallback_message", e.target.value)} rows={2} className="rla-textarea" /></Field>
            <Field label="Lead capture"><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.lead_capture_enabled !== false} onChange={e => set("lead_capture_enabled", e.target.checked)} /> enabled</label></Field>
            <Field label="Lead fields (comma separated)"><input value={(form.lead_fields || []).join(", ")} onChange={e => set("lead_fields", e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean))} className="rla-input" /></Field>
          </div>
          <h4 className="rla-h4">Allowed tools</h4>
          <div className="rla-chip-row">
            {(doc.public_tools || []).map((t: string) => (
              <label key={t} className={`rla-chip${(form.allowed_tools || []).includes(t) ? " active" : ""}`} style={{ cursor: "pointer" }}>
                <input type="checkbox" checked={(form.allowed_tools || []).includes(t)} onChange={() => toggleTool(t)} style={{ marginRight: 6 }} />{t}
              </label>
            ))}
          </div>
          <h4 className="rla-h4">Knowledge sources & guardrails</h4>
          <div className="rla-table-wrap"><table className="rla-table">
            <thead><tr><th>Source</th><th>Public AI</th><th>Priority</th></tr></thead>
            <tbody>{sources.map(s => (
              <tr key={s}>
                <td><span className="rla-code">{s}</span></td>
                <td><input type="checkbox" checked={policy[s]?.public_allowed !== false} onChange={e => setPol(s, "public_allowed", e.target.checked)} aria-label={`${s} public`} /></td>
                <td><input type="number" min={1} max={9} value={policy[s]?.priority ?? 5} onChange={e => setPol(s, "priority", Number(e.target.value))} className="rla-input" style={{ width: 70 }} aria-label={`${s} priority`} /></td>
              </tr>
            ))}</tbody>
          </table></div>
        </Panel>
        <div style={{ height: 16 }} />

        <Panel title="Test console" sub="Dry-run — nothing is stored">
          <div className="rla-inline-actions">
            <input value={testMsg} onChange={e => setTestMsg(e.target.value)} onKeyDown={e => e.key === "Enter" && void runTest()} placeholder="Ask something…" className="rla-input" style={{ flex: 1 }} />
            <button onClick={runTest} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">Run test</button>
          </div>
          {testRes && <div className="text-sm mt-3">
            <p>{testRes.reply}</p>
            <p className="text-xs mt-1" style={{ color: "var(--rla-text-faint)" }}>intent: {testRes.intent} · tools: {(testRes.tools_called || []).join(", ") || "—"}{testRes.used_llm ? " · LLM" : " · tool-only"}</p>
            {(testRes.sources || []).length > 0 && <p className="text-xs">sources: {testRes.sources.map((s: any) => s.title).join(" · ")}</p>}
          </div>}
        </Panel>
        <div style={{ height: 16 }} />

        <Panel title="Usage & statistics" sub="Turns, tools, conversions, errors, latency, models">
          {stats ? <div className="text-sm">
            <p>Assistant turns: <b>{stats.assistant_turns}</b> · Conversations: <b>{stats.conversations}</b> · Leads converted: <b>{stats.leads_converted}</b> · p50 latency: <b>{stats.latency_ms_p50 ?? "—"} ms</b></p>
            <p className="mt-1">Tools: {Object.entries(stats.tool_usage || {}).map(([t, n]) => `${t}×${n}`).join(" · ") || "—"}</p>
            <p className="mt-1">Models: {Object.entries(stats.models || {}).map(([m, n]) => `${m}×${n}`).join(" · ") || "—"}</p>
            {(stats.errors_recent || []).length > 0 && <p className="mt-1 rla-danger-text">Recent errors: {stats.errors_recent.map((e: any) => e.message).join(" | ").slice(0, 200)}</p>}
          </div> : <Empty>No turns recorded yet.</Empty>}
        </Panel>
        <div style={{ height: 16 }} />

        <Panel title="Conversations" sub="Recent sessions with this agent">
          <div className="rla-table-wrap"><table className="rla-table">
            <thead><tr><th>Session</th><th>Turns</th><th>Intents</th><th>Last</th></tr></thead>
            <tbody>{convos.map(c => (
              <tr key={c.session_token}>
                <td><span className="rla-code">{String(c.session_token).slice(0, 12)}…</span>{c.lead_id && <span className="rla-code" style={{ marginLeft: 6 }}>lead ✓</span>}</td>
                <td>{c.turns}</td>
                <td className="text-xs">{(c.intents || []).join(", ")}</td>
                <td className="text-xs">{c.last_at ? new Date(c.last_at).toLocaleString() : "—"}</td>
              </tr>
            ))}</tbody>
          </table>
          {convos.length === 0 && <Empty>No conversations yet.</Empty>}
          </div>
        </Panel>
        <div style={{ height: 16 }} />
      </>)}

      <Panel title="Create future agent" sub="Proposal, recruiter, marketing, research, support — shared knowledge base, own permissions">
        <div className="rla-form-grid">
          <Field label="Slug"><input value={creating.slug} onChange={e => setCreating({ ...creating, slug: e.target.value })} placeholder="proposal-agent" className="rla-input" /></Field>
          <Field label="Name"><input value={creating.name} onChange={e => setCreating({ ...creating, name: e.target.value })} placeholder="Proposal Agent" className="rla-input" /></Field>
          <Field label="Type"><select value={creating.agent_type} onChange={e => setCreating({ ...creating, agent_type: e.target.value })} className="rla-select">
            {["concierge", "proposal", "recruiter", "marketing", "research", "support"].map(t => <option key={t} value={t}>{t}</option>)}
          </select></Field>
        </div>
        <div style={{ marginTop: 12 }}><button onClick={create} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-plus" /> Create Agent</button></div>
      </Panel>
    </div>
  );
}
