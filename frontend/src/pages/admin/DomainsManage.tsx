/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

export default function DomainsManage(){
  const [tab,setTab]=useState<"domains"|"sources"|"health">("domains");
  const [domains,setDomains]=useState<any[]>([]);
  const [sources,setSources]=useState<any[]>([]);
  const [health,setHealth]=useState<any>(null);
  const [q,setQ]=useState("");
  const [status,setStatus]=useState("");
  const [busy,setBusy]=useState(false);
  const [srcForm,setSrcForm]=useState<any>({type:"linkedin", url:"https://www.linkedin.com/in/rajib-mahata", enabled:true, public_source:true, linkedin_text:""});
  const loadDomains=()=>{
    const p=new URLSearchParams();
    if(status) p.set("status",status);
    if(q.trim()) p.set("q",q.trim());
    api.get<any[]>(`/api/admin/domains?${p.toString()}`).then(d=>setDomains(Array.isArray(d)?d:[])).catch(()=>{});
  };
  const loadSources=()=> api.get<any[]>("/api/admin/domains/sources/list").then(setSources).catch(()=>{});
  const loadHealth=()=> api.get<any>("/api/admin/domains/health/overview").then(setHealth).catch(()=>{});
  useEffect(()=>{ loadDomains(); },[status]);
  useEffect(()=>{ const t=setTimeout(loadDomains,400); return ()=>clearTimeout(t);},[q]);
  useEffect(()=>{ loadSources(); loadHealth(); },[]);
  const runNow=async()=>{
    setBusy(true);
    try{ const r=await api.post<any>("/api/admin/domains/run", {}); toast("Run complete", `${r.domains?.length||0} domains`); loadDomains(); loadHealth(); }
    catch(e:any){ toast("Run failed", String(e.message||e).slice(0,160)); } finally{ setBusy(false);}
  };
  const saveSource=async()=>{
    if(!srcForm.type.trim()){ toast("Validation","Type required"); return;}
    if(srcForm.type==="linkedin" && srcForm.url.includes("/feed")){ toast("Validation","Use https://www.linkedin.com/in/... not /feed"); return;}
    setBusy(true);
    try{ await api.post("/api/admin/domains/sources", srcForm); toast("Saved","Source upserted"); loadSources(); }
    catch(e:any){ toast("Save failed", String(e.message||e).slice(0,200)); } finally{ setBusy(false);}
  };
  const validateUrls=async()=>{
    setBusy(true);
    try{ const r=await api.post<any>("/api/admin/domains/sources/validate", {}); toast("Validated", `${r.checks?.length||0} URLs checked`); }
    catch(e:any){ toast("Validate failed", String(e.message||e).slice(0,160)); } finally{ setBusy(false);}
  };
  const toggleFeatured=async(d:any)=>{
    try{ await api.patch(`/api/admin/domains/${d.slug}`, {featured: !d.featured}); loadDomains(); }catch(e:any){ toast("Update failed", String(e.message||e).slice(0,120)); }
  };
  return (
    <div>
      <PageHead title="Profile Intelligence — Domains" desc="Professional domains discovered from verified sources. Autonomous, audit-logged, RAG-indexed."
        actions={<><button onClick={runNow} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-rotate" /> Run Now</button>
        <button onClick={validateUrls} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm">Validate URLs</button></>} />
      <div className="rla-chip-row" style={{marginBottom:12}}>
        {(["domains","sources","health"] as const).map(t=><button key={t} onClick={()=>setTab(t)} className={`rla-chip${tab===t?" active":""}`}>{t}</button>)}
      </div>
      {tab==="domains" && (
        <>
          <div className="rla-filter-grid" style={{marginBottom:12}}>
            <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search domain, slug, description…" className="rla-input" />
            <select value={status} onChange={e=>setStatus(e.target.value)} className="rla-select"><option value="">all statuses</option><option value="active">active</option><option value="inactive">inactive</option></select>
            <button onClick={loadDomains} className="rla-btn rla-btn-ghost rla-btn-sm">Refresh</button>
          </div>
          <Panel title="Domains" sub={`${domains.length} domains · confidence threshold from Profile Agent policy (default 50)`}>
            <div className="rla-table-wrap"><table className="rla-table">
              <thead><tr><th>Domain</th><th>Confidence</th><th>Evidence</th><th>Projects</th><th>Portfolio</th><th>GitHub</th><th>Status</th><th>Updated</th><th></th></tr></thead>
              <tbody>{domains.map((d:any)=>(
                <tr key={d.slug}>
                  <td><b>{d.name}</b><div className="text-xs" style={{color:"var(--rla-text-faint)"}}>{d.slug}</div></td>
                  <td><span className="rla-chip" style={{background: d.confidence_score>=75?"var(--rla-violet-soft)":"var(--rla-bg-2)"}}>{d.confidence_score}% · {d.confidence_label}</span></td>
                  <td className="text-xs">{d.evidence_count}</td>
                  <td className="text-xs">{(d.projects||[]).slice(0,2).join(", ") || "—"}</td>
                  <td className="text-xs">{(d.portfolio_items||[]).slice(0,2).join(", ") || "—"}</td>
                  <td className="text-xs">{(d.github_repositories||[]).slice(0,2).join(", ") || "—"}</td>
                  <td><StatusPill status={d.status} /></td>
                  <td className="text-xs">{d.last_verified_at? new Date(d.last_verified_at).toLocaleDateString() : "—"}</td>
                  <td><button onClick={()=>toggleFeatured(d)} className="rla-mini-btn" title="Toggle featured">{d.featured?"★":"☆"}</button></td>
                </tr>))}
              </tbody>
            </table>{domains.length===0 && <Empty>No domains yet — click Run Now.</Empty>}</div>
          </Panel>
        </>
      )}
      {tab==="sources" && (
        <Panel title="Professional Sources" sub="LinkedIn, portfolio, GitHub — where domains come from.">
          <div className="rla-form-grid">
            <Field label="Type"><input value={srcForm.type} onChange={e=>setSrcForm({...srcForm, type:e.target.value})} className="rla-input" placeholder="linkedin" /></Field>
            <Field label="URL" span><input value={srcForm.url} onChange={e=>setSrcForm({...srcForm, url:e.target.value})} className="rla-input" placeholder="https://www.linkedin.com/in/..." /></Field>
            <Field label="LinkedIn text (manual import, 6k max)" span><textarea value={srcForm.linkedin_text||""} onChange={e=>setSrcForm({...srcForm, linkedin_text:e.target.value})} rows={4} className="rla-textarea" placeholder="Paste publicly approved headline/about/experience text — never passwords or cookies" /></Field>
            <Field label="Enabled"><label className="flex items-center gap-2"><input type="checkbox" checked={!!srcForm.enabled} onChange={e=>setSrcForm({...srcForm, enabled:e.target.checked})} /> Enabled</label></Field>
            <Field label="Public source"><label className="flex items-center gap-2"><input type="checkbox" checked={!!srcForm.public_source} onChange={e=>setSrcForm({...srcForm, public_source:e.target.checked})} /> Public</label></Field>
          </div>
          <div style={{marginTop:12}}><button onClick={saveSource} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">Save Source</button></div>
          <div style={{marginTop:16}}><h4>Existing sources</h4>{sources.map((s:any)=><div key={s.type} className="rla-list-card text-sm"><b>{s.type}</b> — {s.url || "—"} · {s.status} · {s.enabled?"enabled":"disabled"}<div className="text-xs" style={{color:"var(--rla-text-faint)"}}>Last checked: {s.last_checked_at? new Date(s.last_checked_at).toLocaleString():"never"}</div></div>)}{sources.length===0 && <Empty>No sources configured.</Empty>}</div>
        </Panel>
      )}
      {tab==="health" && health && (
        <Panel title="Health Overview" sub="Evidence, stale, weak domains">
          <div className="rla-kpi-grid" style={{gridTemplateColumns:"repeat(4,1fr)"}}>
            <div className="rla-panel"><h3>Total</h3><p>{health.total}</p></div>
            <div className="rla-panel"><h3>Active</h3><p>{health.active}</p></div>
            <div className="rla-panel"><h3>Weak (&lt;50)</h3><p>{health.weak}</p></div>
            <div className="rla-panel"><h3>Stale (&gt;30d)</h3><p>{health.stale}</p></div>
          </div>
          <p className="text-xs mt-2" style={{color:"var(--rla-text-faint)"}}>Sources: {health.sources} · Threshold from ai_agents rajiblabs-profile policy.domain_publish_threshold</p>
        </Panel>
      )}
    </div>
  );
}
