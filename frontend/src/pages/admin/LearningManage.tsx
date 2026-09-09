/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";

export default function LearningManage(){
  const [paths,setPaths]=useState<any[]>([]);
  const [activePath,setActivePath]=useState<any>(null);
  const [blocks,setBlocks]=useState<any[]>([]);
  const [topics,setTopics]=useState<string[]>([]);
  const [tab,setTab]=useState<"paths"|"active"|"topics"|"blocks">("paths");
  const [busy,setBusy]=useState(false);
  const [form,setForm]=useState<any>({topic:"", duration:7, goal:"", level:"beginner"});
  const [selected,setSelected]=useState<string>("");

  const loadPaths=()=> api.get<any[]>("/api/admin/learning/paths").then(d=>setPaths(Array.isArray(d)?d:[])).catch(()=>{});
  const loadTopics=()=> api.get<any>("/api/learning/topics").then((d:any)=> setTopics(Array.isArray(d)?d: Array.isArray(d.topics)?d.topics:[])).catch(()=>{});
  const loadActive=()=> api.get<any>("/api/learning/active").then(d=>{
    if(d && d.active) setActivePath(d.path);
    else setActivePath(null);
  }).catch(()=>{});
  const loadBlocks=(slug:string)=>{
    if(!slug) return;
    api.get<any[]>(`/api/admin/learning/paths/${slug}/blocks`).then(setBlocks).catch(()=>{});
  };

  useEffect(()=>{ loadPaths(); loadTopics(); loadActive(); },[]);
  useEffect(()=>{ if(selected) loadBlocks(selected); },[selected]);

  const createPath=async()=>{
    if(!form.topic.trim()){ toast("Validation","Topic required"); return;}
    if(!(form.duration>=1 && form.duration<=60)){ toast("Validation","Duration 1-60"); return;}
    setBusy(true);
    try{
      const r=await api.post<any>("/api/admin/learning/paths", {topic: form.topic.trim(), duration: Number(form.duration), goal: form.goal, level: form.level});
      toast("Created","Learning path created — agent will build roadmap");
      setForm({topic:"", duration:7, goal:"", level:"beginner"});
      loadPaths();
      setSelected(r.slug || r.slug);
    }catch(e:any){ toast("Create failed", String(e.message||e).slice(0,200)); } finally{ setBusy(false); }
  };

  const runAgent=async()=>{
    setBusy(true);
    try{
      await api.post<any>("/api/admin/learning/paths/any/run", {}).catch(async ()=>{
        // fallback to generic run via admin domains run? Use learning agent run endpoint if exists
        return await api.post<any>("/api/admin/learning/agent/runs", {});
      });
      toast("Agent", "Run triggered");
    }catch(e:any){ toast("Run failed", String(e.message||e).slice(0,200)); } finally{ setBusy(false); }
  };

  const updateStatus=async(slug:string, status:string)=>{
    try{ await api.patch(`/api/admin/learning/paths/${slug}`, {status}); toast("Updated", status); loadPaths(); }catch(e:any){ toast("Failed", String(e.message||e).slice(0,160)); }
  };

  return (
    <div>
      <PageHead title="Learning" desc="Define Topic + Duration — agent builds roadmap, daily blocks, RAG and validation. 06:00 IST autonomous."
        actions={<button onClick={runAgent} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm"><i className="fas fa-robot" /> Run Learning Agent</button>} />
      <div className="rla-chip-row" style={{marginBottom:12}}>
        {(["paths","active","topics","blocks"] as const).map(t=><button key={t} onClick={()=>setTab(t)} className={`rla-chip${tab===t?" active":""}`}>{t}</button>)}
      </div>

      {tab==="paths" && (
        <>
          <Panel title="Create Learning Path" sub="Only Topic + Duration + optional Goal/Level — agent does the rest">
            <div className="rla-form-grid">
              <Field label="Topic"><input value={form.topic} onChange={e=>setForm({...form, topic:e.target.value})} className="rla-input" placeholder="e.g. C#, .NET, ASP.NET Core" /></Field>
              <Field label="Duration (days)"><input type="number" min={1} max={60} value={form.duration} onChange={e=>setForm({...form, duration:e.target.value})} className="rla-input" /></Field>
              <Field label="Goal (optional)"><input value={form.goal} onChange={e=>setForm({...form, goal:e.target.value})} className="rla-input" placeholder="e.g. Build a practical project" /></Field>
              <Field label="Level"><select value={form.level} onChange={e=>setForm({...form, level:e.target.value})} className="rla-select"><option value="beginner">beginner</option><option value="intermediate">intermediate</option><option value="advanced">advanced</option></select></Field>
            </div>
            <div style={{marginTop:12}}><button onClick={createPath} disabled={busy} className="rla-btn rla-btn-primary rla-btn-sm">Create Path</button></div>
          </Panel>
          <div style={{height:12}}/>
          <Panel title="Learning Paths" sub={`${paths.length} paths`}>
            <div className="rla-table-wrap"><table className="rla-table">
              <thead><tr><th>Topic</th><th>Duration</th><th>Status</th><th>Progress</th><th>Updated</th><th></th></tr></thead>
              <tbody>{paths.map((p:any)=>(
                <tr key={p.slug}>
                  <td><b>{p.topic}</b><div className="text-xs" style={{color:"var(--rla-text-faint)"}}>{p.slug} · {p.level}</div></td>
                  <td>{p.duration} days</td>
                  <td><StatusPill status={p.status} /></td>
                  <td>{p.progress ?? 0}%</td>
                  <td className="text-xs">{p.updated_at? new Date(p.updated_at).toLocaleDateString() : "—"}</td>
                  <td>
                    <button onClick={()=>setSelected(p.slug)} className="rla-mini-btn" title="View blocks"><i className="fas fa-eye" /></button>
                    <select value={p.status} onChange={e=>updateStatus(p.slug, e.target.value)} className="rla-select" style={{fontSize:"0.75rem", padding:"2px 6px", marginLeft:6}}>
                      <option value="planned">planned</option><option value="active">active</option><option value="paused">paused</option><option value="completed">completed</option><option value="archived">archived</option>
                    </select>
                  </td>
                </tr>))}
              </tbody>
            </table>{paths.length===0 && <Empty>No learning paths — create one above.</Empty>}</div>
            {selected && (
              <div style={{marginTop:16}}>
                <h4>Roadmap — {selected}</h4>
                <div className="rla-stack">
                  {blocks.map((b:any)=>(
                    <div key={b.day_number} className="rla-list-card text-sm" style={{borderLeft: b.status==="published"?"3px solid var(--rla-violet)":"1px solid var(--rla-border)"}}>
                      <div><b>Day {b.day_number}: {b.title || b.topic}</b> <StatusPill status={b.status} /></div>
                      <div className="text-xs" style={{color:"var(--rla-text-faint)"}}>{b.learning_objective || b.topic}</div>
                      {b.validation_issues?.length ? <div className="text-xs text-red-600">Needs review: {b.validation_issues.join("; ")}</div> : null}
                    </div>
                  ))}
                  {blocks.length===0 && <Empty>No blocks yet — agent will generate on next 06:00 run or Run Now.</Empty>}
                </div>
              </div>
            )}
          </Panel>
        </>
      )}

      {tab==="active" && (
        <Panel title="Active Learning" sub="Current day, progress, next lesson">
          {!activePath ? <Empty>No active path.</Empty> : (
            <div>
              <h3>{activePath.topic} — {activePath.duration} days</h3>
              <p className="text-sm" style={{color:"var(--rla-text-faint)"}}>Progress: {activePath.progress || 0}% · Current day: {activePath.current_day || 0}</p>
              <div className="rla-stack" style={{marginTop:12}}>
                {blocks.filter(b=>b.status==="published").map((b:any)=>(
                  <div key={b.day_number} className="rla-list-card">
                    <b>Day {b.day_number}: {b.title}</b> <StatusPill status={b.status} />
                    <div className="text-xs" style={{color:"var(--rla-text-faint)"}}>{b.learning_objective}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Panel>
      )}

      {tab==="topics" && (
        <Panel title="Topics" sub="Distinct learning topics">
          <div style={{display:"flex", flexWrap:"wrap", gap:8}}>{topics.map(t=><span key={t} className="rla-chip">{t}</span>)}</div>
          {topics.length===0 && <Empty>No topics yet.</Empty>}
        </Panel>
      )}

      {tab==="blocks" && (
        <Panel title="Daily Blocks" sub="Select a path to view blocks">
          <div className="rla-form-grid">
            <Field label="Path slug"><input value={selected} onChange={e=>setSelected(e.target.value)} placeholder="e.g. c-sharp" className="rla-input" /></Field>
            <Field label=""><button onClick={()=>loadBlocks(selected)} className="rla-btn rla-btn-ghost rla-btn-sm">Load</button></Field>
          </div>
          <div className="rla-stack" style={{marginTop:12}}>
            {blocks.map((b:any)=>(
              <div key={b.day_number} className="rla-list-card">
                <b>Day {b.day_number}: {b.title}</b> <StatusPill status={b.status} />
                <div className="text-xs" style={{color:"var(--rla-text-faint)"}}>v{b.version} · {b.content_hash?.slice(0,8) || "no hash"} · {b.generated_at? new Date(b.generated_at).toLocaleString():"not generated"}</div>
              </div>
            ))}
            {blocks.length===0 && <Empty>Select a path and load.</Empty>}
          </div>
        </Panel>
      )}
    </div>
  );
}
