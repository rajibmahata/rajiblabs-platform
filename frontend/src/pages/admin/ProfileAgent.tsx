/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

export default function ProfileAgent() {
  const [cfg, setCfg] = useState<any>(null);
  const [dash, setDash] = useState<any>(null);
  const [runs, setRuns] = useState<any[]>([]);
  const [props, setProps] = useState<any[]>([]);
  const [filter, setFilter] = useState("pending");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const [c, d, r, p] = await Promise.all([
        api.get<any>("/api/admin/profile-agent/config"),
        api.get<any>("/api/admin/profile-agent/dashboard"),
        api.get<any[]>("/api/admin/profile-agent/runs"),
        api.get<any[]>(`/api/admin/profile-agent/proposals?status=${filter}`),
      ]);
      setCfg(c); setDash(d); setRuns(Array.isArray(r)?r:[]); setProps(Array.isArray(p)?p:[]);
    } catch (e:any) { toast("Load failed", String(e.message||e).slice(0,120)); }
  };
  useEffect(()=>{ load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(()=>{ api.get<any[]>(`/api/admin/profile-agent/proposals?status=${filter}`).then(setProps).catch(()=>{}); }, [filter]);

  const saveCfg = async () => {
    setBusy(true);
    try{
      const updated = await api.put<any>("/api/admin/profile-agent/config", {enabled: cfg.enabled, policy: cfg.policy, allowed_tools: cfg.allowed_tools});
      setCfg(updated); toast("Saved","Agent config updated");
    }catch(e:any){ toast("Save failed", String(e.message||e).slice(0,120)); } finally{ setBusy(false); }
  };
  const runNow = async () => {
    setBusy(true);
    try{
      const r = await api.post<any>("/api/admin/profile-agent/run", {});
      toast("Run complete", `Proposed ${r.proposed} Applied ${r.applied}`);
      load();
    }catch(e:any){ toast("Run failed", String(e.message||e).slice(0,120)); } finally{ setBusy(false); }
  };
  const decide = async (id:string, action:"approve"|"reject") => {
    try{
      await api.post(`/api/admin/profile-agent/proposals/${id}/${action}`, {});
      toast(action==="approve"?"Approved":"Rejected","Proposal updated");
      load();
    }catch(e:any){ toast("Action failed", String(e.message||e).slice(0,120)); }
  };

  if (!cfg || !dash) return <div className="p-4">Loading Profile Agent…</div>;

  return (
    <div>
      <PageHead title="Profile Intelligence Agent" desc="Persistent agent keeping profile, GitHub, portfolio and knowledge synchronized."
        actions={<><button onClick={runNow} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm"><i className={`fas fa-play${busy?" fa-spin":""}`} /> Run Now</button>
          <button onClick={saveCfg} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm">Save Config</button></>} />

      {/* Config */}
      <Panel title="Agent Configuration" sub="Safe defaults require approval for public content">
        <div className="rla-form-grid">
          <Field label="Enabled"><label className="flex items-center gap-2"><input type="checkbox" checked={!!cfg.enabled} onChange={e=>setCfg({...cfg, enabled:e.target.checked})} /> Enabled</label></Field>
          <Field label="Run frequency"><input value={cfg.policy?.run_frequency||"daily"} onChange={e=>setCfg({...cfg, policy:{...cfg.policy, run_frequency:e.target.value}})} className="rla-input" /></Field>
          <Field label="GitHub sync"><label className="flex items-center gap-2"><input type="checkbox" checked={!!cfg.policy?.github_sync} onChange={e=>setCfg({...cfg, policy:{...cfg.policy, github_sync:e.target.checked}})} /> Enabled</label></Field>
          <Field label="Auto-create drafts"><label className="flex items-center gap-2"><input type="checkbox" checked={!!cfg.policy?.auto_create_drafts} onChange={e=>setCfg({...cfg, policy:{...cfg.policy, auto_create_drafts:e.target.checked}})} /> On</label></Field>
          <Field label="Auto-update metadata"><label className="flex items-center gap-2"><input type="checkbox" checked={!!cfg.policy?.auto_update_metadata} onChange={e=>setCfg({...cfg, policy:{...cfg.policy, auto_update_metadata:e.target.checked}})} /> On</label></Field>
          <Field label="Auto-translation"><label className="flex items-center gap-2"><input type="checkbox" checked={!!cfg.policy?.auto_translation} onChange={e=>setCfg({...cfg, policy:{...cfg.policy, auto_translation:e.target.checked}})} /> On</label></Field>
          <Field label="Auto-publish"><label className="flex items-center gap-2"><input type="checkbox" checked={!!cfg.policy?.auto_publish} onChange={e=>setCfg({...cfg, policy:{...cfg.policy, auto_publish:e.target.checked}})} /> Allow (requires approval by default)</label></Field>
        </div>
      </Panel>
      <div style={{height:16}} />

      {/* Dashboard */}
      <div className="rla-kpi-grid" style={{gridTemplateColumns:"repeat(4,1fr)"}}>
        <div className="rla-panel"><div className="rla-panel-head"><div><h3>Profile</h3><p>{dash.profile_completeness}% complete</p></div><StatusPill status={dash.resume_status} /></div>
          <div className="rla-panel-body text-xs">Resume: {dash.resume_status} · Health warnings: {dash.health?.warnings?.length||0}</div></div>
        <div className="rla-panel"><div className="rla-panel-head"><div><h3>GitHub</h3><p>{dash.github_sync?.repos||0} repos</p></div></div>
          <div className="rla-panel-body text-xs">Last sync: {dash.github_sync?.last_synced ? new Date(dash.github_sync.last_synced).toLocaleString() : "never"}</div></div>
        <div className="rla-panel"><div className="rla-panel-head"><div><h3>Content</h3><p>{dash.portfolio} portfolio · {dash.products} products</p></div></div>
          <div className="rla-panel-body text-xs">Knowledge docs: {dash.knowledge} · Pending: {dash.pending_approvals}</div></div>
        <div className="rla-panel"><div className="rla-panel-head"><div><h3>Agent</h3><p>Next: {dash.next_run}</p></div><StatusPill status={dash.agent?.enabled?"active":"disabled"} /></div>
          <div className="rla-panel-body text-xs">Last run: {dash.last_run? new Date(dash.last_run.started_at).toLocaleString():"never"} · Proposed {dash.last_run?.proposed||0}</div></div>
      </div>
      <div style={{height:16}} />

      {/* Health */}
      <Panel title="Health Report" sub="Configuration and content completeness">
        {dash.health?.errors?.length>0 && <div className="text-sm text-red-600">Errors: {dash.health.errors.join("; ")}</div>}
        {dash.health?.warnings?.length>0 && <div className="text-sm" style={{color:"var(--rla-amber)"}}>Warnings: {dash.health.warnings.join("; ")}</div>}
        {dash.health?.healthy?.length>0 && <div className="text-sm text-green-600">{dash.health.healthy[0]}</div>}
        <div className="text-xs mt-2" style={{color:"var(--rla-text-faint)"}}>Actions: {(dash.health?.actions||[]).join("; ") || "None"}</div>
      </Panel>
      <div style={{height:16}} />

      {/* Activity */}
      <Panel title="Pending Approvals" sub={`${props.length} proposals`}>
        <div className="rla-chip-row">
          {["pending","approved","rejected","applied"].map(s=>(
            <button key={s} onClick={()=>setFilter(s)} className={`rla-chip${filter===s?" active":""}`}>{s}</button>
          ))}
        </div>
        <div className="rla-stack" style={{marginTop:12}}>
          {props.map((p:any)=>(
            <div key={p.id} className="rla-list-card text-sm">
              <div><b>{p.target_collection}.{p.field}</b> — {p.reason} <span className="rla-code">{p.confidence}</span></div>
              <div className="text-xs">Before: {JSON.stringify(p.before)?.slice(0,120)} → After: {JSON.stringify(p.after)?.slice(0,120)}</div>
              <div className="text-xs" style={{color:"var(--rla-text-faint)"}}>Source: {p.source?.type}:{p.source?.id} · {new Date(p.created_at).toLocaleString()} · <StatusPill status={p.status} /></div>
              {p.status==="pending" && <div className="rla-inline-actions" style={{marginTop:8}}>
                <button onClick={()=>decide(p.id,"approve")} className="rla-btn rla-btn-primary rla-btn-sm">Approve</button>
                <button onClick={()=>decide(p.id,"reject")} className="rla-btn rla-btn-ghost rla-btn-sm">Reject</button>
              </div>}
            </div>
          ))}
          {props.length===0 && <Empty>No proposals in {filter}.</Empty>}
        </div>
      </Panel>
      <div style={{height:16}} />
      <Panel title="Recent Runs" sub="Execution history">
        <div className="rla-stack">
          {runs.map((r:any)=>(
            <div key={r.id} className="rla-list-card text-sm">
              <div>{new Date(r.started_at).toLocaleString()} — {r.status} · Proposed {r.proposed} Applied {r.applied} · <span className="rla-code">{r.triggered_by}</span></div>
              <div className="text-xs" style={{color:"var(--rla-text-faint)"}}>Sources: {(r.sources_inspected||[]).join(", ")} · Health warnings: {r.health?.warnings?.length||0}</div>
              {r.errors?.length>0 && <div className="text-xs text-red-600">{r.errors.join("; ")}</div>}
            </div>
          ))}
          {runs.length===0 && <Empty>No runs yet — click Run Now.</Empty>}
        </div>
      </Panel>
    </div>
  );
}
