/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Empty, Field, PageHead, Panel, StatusPill } from "../../components/admin/ui";
import { toast } from "../../components/admin/toast";
import { useAsyncActions } from "../../components/admin/async";
import { InlineLoader } from "../../components/admin/ui";

function DetailSection({ icon, title, children, tone }: { icon: string; title: string; children: React.ReactNode; tone?: string }) {
  if (!children) return null;
  return (
    <div style={{ marginTop: 18 }}>
      <h4 style={{ fontSize: "0.85rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8, color: "var(--rla-text)", marginBottom: 6 }}>
        <i className={`fas ${icon}`} style={{ color: tone || "var(--rla-violet)", fontSize: "0.85rem" }} /> {title}
      </h4>
      <div className="text-sm" style={{ color: "var(--rla-text-dim)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{children}</div>
    </div>
  );
}

function CodeBlock({ ex }: { ex: any }) {
  if (!ex?.code) return null;
  return (
    <div style={{ marginTop: 10, border: "1px solid var(--rla-border)", borderRadius: 10, overflow: "hidden" }}>
      <div style={{ padding: "8px 12px", background: "var(--rla-violet-soft)", borderBottom: "1px solid var(--rla-border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--rla-violet)" }}>{ex.title || "Example"}</span>
        <span className="rla-code" style={{ fontSize: "0.7rem" }}>{ex.code.split("\n").length} lines</span>
      </div>
      <pre style={{ margin: 0, padding: 14, background: "#0f1220", color: "#e6e8f2", fontSize: "0.82rem", overflowX: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{ex.code}</pre>
      {ex.explanation && <div style={{ padding: "10px 14px", background: "#fff", borderTop: "1px solid var(--rla-border)", fontSize: "0.82rem", color: "var(--rla-text-dim)" }}><b style={{ color: "var(--rla-text)" }}>How it works:</b> {ex.explanation}</div>}
      {ex.expected_output && <div style={{ padding: "8px 14px", background: "var(--rla-green-soft)", borderTop: "1px solid #c4ead9", fontFamily: "monospace", fontSize: "0.78rem", color: "var(--rla-green)" }}>▶ {ex.expected_output}</div>}
    </div>
  );
}

export default function LearningManage(){
  const [paths,setPaths]=useState<any[]>([]);
  const [activePath,setActivePath]=useState<any>(null);
  const [blocks,setBlocks]=useState<any[]>([]);
  const [topics,setTopics]=useState<string[]>([]);
  const [tab,setTab]=useState<"paths"|"active"|"topics"|"blocks">("paths");
  const { run, isLoading } = useAsyncActions();
  const busy = isLoading("create") || isLoading("run-agent");
  const [form,setForm]=useState<any>({topic:"", duration:7, goal:"", level:"beginner"});
  const [selected,setSelected]=useState<string>("");
  const [detailBlock,setDetailBlock]=useState<any>(null);
  const [showDetail,setShowDetail]=useState(false);

  const loadPaths=()=> api.get<any[]>("/api/admin/learning/paths").then(d=>setPaths(Array.isArray(d)?d:[])).catch(()=>{});
  const loadTopics=()=> api.get<any>("/api/learning/topics").then((d:any)=> setTopics(Array.isArray(d)?d: Array.isArray(d.topics)?d.topics:[])).catch(()=>{});
  const loadActive=()=> api.get<any>("/api/learning/active").then(d=>{
    if(d && d.active) setActivePath(d.path);
    else setActivePath(null);
  }).catch(()=>{});
  const loadBlocks=(slug:string)=>{
    if(!slug) return;
    api.get<any[]>(`/api/admin/learning/paths/${slug}/blocks`).then(d=> setBlocks(Array.isArray(d)?d:[])).catch(()=>{});
  };

  useEffect(()=>{ loadPaths(); loadTopics(); loadActive(); },[]);
  useEffect(()=>{ if(selected) loadBlocks(selected); },[selected]);

  const openBlock = (b:any) => {
    setDetailBlock(b);
    setShowDetail(true);
  };

  const createPath=()=>{
    if(!form.topic.trim()){ toast("Validation","Topic required"); return;}
    if(!(form.duration>=1 && form.duration<=60)){ toast("Validation","Duration 1-60"); return;}
    run("create", async () => {
      const r=await api.post<any>("/api/admin/learning/paths", {topic: form.topic.trim(), duration: Number(form.duration), goal: form.goal, level: form.level});
      setForm({topic:"", duration:7, goal:"", level:"beginner"});
      loadPaths();
      setSelected(r.slug || r.slug);
    }, { successTitle: "Created", successMsg: "Learning path created — agent will build roadmap", errorTitle: "Create failed" });
  };

  const runAgent=()=> run("run-agent", async () => {
      const slug = selected || "any";
      try { await api.post<any>(`/api/admin/learning/paths/${slug}/run`, {}); } catch { await api.post<any>(`/api/admin/learning/run`, {}); }
      setTimeout(()=> { loadBlocks(selected); loadPaths(); }, 2500);
    }, { successTitle: "Agent triggered", successMsg: "Check blocks in a few seconds", errorTitle: "Run failed" });

  const runSingleDay = (slug: string, day: number) => {
    run(`run-day-${day}`, async () => {
      await api.post<any>(`/api/admin/learning/paths/${slug}/run`, {});
      setTimeout(()=> loadBlocks(slug), 3000);
    }, { successTitle: "Agent", successMsg: `Regenerating Day ${day}...`, errorTitle: "Run failed" });
  };

  const updateStatus=async(slug:string, status:string)=>{
    try{ await api.patch(`/api/admin/learning/paths/${slug}`, {status}); toast("Updated", status); loadPaths(); }catch(e:any){ toast("Failed", String(e.message||e).slice(0,160)); }
  };

  return (
    <div>
      <PageHead title="Learning" desc="Define Topic + Duration — agent builds roadmap, daily blocks, RAG and validation. 06:30 IST autonomous."
        actions={<button onClick={runAgent} disabled={isLoading("run-agent")} className="rla-btn rla-btn-primary rla-btn-sm" aria-busy={isLoading("run-agent")}><i className={`fas fa-robot ${isLoading("run-agent") ? "fa-spin" : ""}`} /> {isLoading("run-agent") ? "Running..." : "Run Learning Agent"}</button>} />
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
            <div style={{marginTop:12}}><button onClick={createPath} disabled={isLoading("create")} className="rla-btn rla-btn-primary rla-btn-sm" aria-busy={isLoading("create")}>{isLoading("create") ? <InlineLoader text="Creating..." /> : "Create Path"}</button></div>
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
                    <button onClick={()=>setSelected(p.slug)} className={`rla-mini-btn ${selected===p.slug ? "active" : ""}`} title="View blocks"><i className="fas fa-eye" /></button>
                    <select value={p.status} onChange={e=>updateStatus(p.slug, e.target.value)} className="rla-select" style={{fontSize:"0.75rem", padding:"2px 6px", marginLeft:6}}>
                      <option value="planned">planned</option><option value="active">active</option><option value="paused">paused</option><option value="completed">completed</option><option value="archived">archived</option>
                    </select>
                  </td>
                </tr>))}
              </tbody>
            </table>{paths.length===0 && <Empty>No learning paths — create one above.</Empty>}</div>
            {isLoading("run-agent") && <div style={{marginBottom:12}}><InlineLoader text="Running Learning Agent — generating daily blocks..." /></div>}
      {selected && (
              <div style={{marginTop:16}}>
                <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8}}>
                  <h4 style={{margin:0}}>Roadmap — {selected}</h4>
                  <span className="text-xs" style={{color:"var(--rla-text-faint)"}}>{blocks.length} days · click a day to inspect full lesson</span>
                </div>
                <div className="rla-stack">
                  {blocks.map((b:any)=>(
                    <div key={b.day_number} onClick={()=>openBlock(b)} className="rla-list-card text-sm" style={{borderLeft: b.status==="published"?"3px solid var(--rla-violet)": b.status==="needs_review"?"3px solid var(--rla-amber)":"1px solid var(--rla-border)", cursor:"pointer", transition:"all 0.15s"}}>
                      <div style={{display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:8}}>
                        <div style={{flex:1}}>
                          <div style={{display:"flex", gap:8, alignItems:"center", flexWrap:"wrap"}}>
                            <b>Day {b.day_number}: {b.title || b.topic}</b> <StatusPill status={b.status} />
                            {b.version && <span className="rla-code" style={{fontSize:"0.7rem"}}>v{b.version}</span>}
                          </div>
                          <div className="text-xs" style={{color:"var(--rla-text-faint)", marginTop:4, display:"-webkit-box", WebkitLineClamp:2, WebkitBoxOrient:"vertical", overflow:"hidden"}}>{b.learning_objective || b.topic}</div>
                          <div className="text-xs" style={{color:"var(--rla-text-faint)", marginTop:4}}>
                            {b.generated_at ? `Generated ${new Date(b.generated_at).toLocaleString()}` : "Not generated"} {b.validated_at ? `· Validated ${new Date(b.validated_at).toLocaleDateString()}` : ""}
                            {b.content_hash ? ` · ${b.content_hash.slice(0,8)}` : ""}
                          </div>
                        </div>
                        <div style={{display:"flex", gap:6, flexShrink:0}}>
                          <button onClick={(e)=>{e.stopPropagation(); openBlock(b);}} className="rla-btn rla-btn-ghost rla-btn-sm" style={{padding:"4px 10px", fontSize:"0.75rem"}}><i className="fas fa-book-open" /> Open</button>
                          {b.status==="needs_review" && <span className="rla-pill warn" style={{fontSize:"0.65rem"}}>NEEDS REVIEW</span>}
                        </div>
                      </div>
                      {b.validation_issues?.length ? <div className="text-xs" style={{color:"var(--rla-red)", marginTop:6, background:"var(--rla-red-soft)", padding:"6px 10px", borderRadius:8}}>⚠ {b.validation_issues.join("; ")}</div> : null}
                      {(b.real_world_example || b.simple_explanation) && (
                        <div className="text-xs" style={{color:"var(--rla-text-dim)", marginTop:6, borderLeft:"2px solid var(--rla-border)", paddingLeft:8, display:"-webkit-box", WebkitLineClamp:2, WebkitBoxOrient:"vertical", overflow:"hidden"}}>
                          {b.real_world_example || b.simple_explanation}
                        </div>
                      )}
                    </div>
                  ))}
                  {blocks.length===0 && <Empty>No blocks yet — agent will generate on next 06:30 run or Run Now.</Empty>}
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
                  <div key={b.day_number} onClick={()=>openBlock(b)} className="rla-list-card" style={{cursor:"pointer"}}>
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
              <div key={b.day_number} onClick={()=>openBlock(b)} className="rla-list-card" style={{cursor:"pointer"}}>
                <div style={{display:"flex", justifyContent:"space-between"}}>
                  <b>Day {b.day_number}: {b.title}</b> <StatusPill status={b.status} />
                </div>
                <div className="text-xs" style={{color:"var(--rla-text-faint)"}}>v{b.version} · {b.content_hash?.slice(0,8) || "no hash"} · {b.generated_at? new Date(b.generated_at).toLocaleString():"not generated"}</div>
                <div className="text-xs" style={{color:"var(--rla-violet)", marginTop:4}}>Click to view full lesson →</div>
              </div>
            ))}
            {blocks.length===0 && <Empty>Select a path and load.</Empty>}
          </div>
        </Panel>
      )}

      {/* Lesson Detail Drawer / Modal */}
      {showDetail && detailBlock && (
        <div className="rla-modal-overlay" onClick={()=>setShowDetail(false)} style={{zIndex:9999, overflowY:"auto", padding:"20px 0"}}>
          <div className="rla-modal rla-modal-wide" onClick={e=>e.stopPropagation()} role="dialog" aria-label="Lesson detail" style={{maxWidth:760, width:"92%", maxHeight:"90vh", overflowY:"auto", margin:"20px auto"}}>
            <div className="rla-modal-head" style={{position:"sticky", top:0, background:"#fff", zIndex:2, borderBottom:"1px solid var(--rla-border)", padding:"16px 20px"}}>
              <div>
                <div style={{display:"flex", gap:8, alignItems:"center", flexWrap:"wrap"}}>
                  <span className="rla-code" style={{fontSize:"0.7rem", background:"var(--rla-violet-soft)", color:"var(--rla-violet)", padding:"4px 8px", borderRadius:6}}>DAY {detailBlock.day_number}</span>
                  <StatusPill status={detailBlock.status} />
                  {detailBlock.validation_issues?.length ? <span className="rla-pill err">NEEDS REVIEW</span> : detailBlock.status==="published" ? <span className="rla-pill ok">VALIDATED</span> : null}
                </div>
                <h3 style={{margin:"8px 0 4px", fontSize:"1.15rem", lineHeight:1.3}}>{detailBlock.title || detailBlock.topic}</h3>
                <div className="text-xs" style={{color:"var(--rla-text-faint)"}}>
                  v{detailBlock.version} · {detailBlock.content_hash?.slice(0,12) || "no hash"} · {detailBlock.generated_at ? `Generated ${new Date(detailBlock.generated_at).toLocaleString()}` : "Not generated"}
                  {detailBlock.validated_at ? ` · Validated ${new Date(detailBlock.validated_at).toLocaleString()}` : ""}
                </div>
              </div>
              <button onClick={()=>setShowDetail(false)} className="rla-mini-btn" style={{flexShrink:0}}><i className="fas fa-times" /></button>
            </div>

            <div style={{padding:"0 20px 20px"}}>
              {detailBlock.validation_issues?.length ? (
                <div style={{marginTop:12, padding:"10px 14px", background:"var(--rla-amber-soft)", border:"1px solid #f0d9a8", borderRadius:10, fontSize:"0.82rem", color:"#7a5a12"}}>
                  <b><i className="fas fa-exclamation-triangle" /> Validation:</b> {detailBlock.validation_issues.join("; ")}
                </div>
              ) : null}

              <DetailSection icon="fa-bullseye" title="What you will learn" tone="var(--rla-violet)">{detailBlock.learning_objective}</DetailSection>
              <DetailSection icon="fa-heart" title="Why this matters">{detailBlock.why_matters}</DetailSection>
              <DetailSection icon="fa-globe" title="Real-world example">{detailBlock.real_world_example}</DetailSection>
              <DetailSection icon="fa-comments" title="Simple explanation">{detailBlock.simple_explanation || detailBlock.concept_explanation}</DetailSection>
              {detailBlock.concept_explanation && detailBlock.simple_explanation && detailBlock.concept_explanation !== detailBlock.simple_explanation && (
                <DetailSection icon="fa-lightbulb" title="Deeper concept">{detailBlock.concept_explanation}</DetailSection>
              )}
              {detailBlock.practical_example && <DetailSection icon="fa-briefcase" title="Practical example">{detailBlock.practical_example}</DetailSection>}

              {!!detailBlock.step_by_step?.length && (
                <div style={{marginTop:18}}>
                  <h4 style={{fontSize:"0.85rem", fontWeight:700, display:"flex", gap:8, alignItems:"center"}}><i className="fas fa-list-ol" style={{color:"var(--rla-cyan)"}} /> Step-by-step</h4>
                  <ol style={{margin:"8px 0 0 18px", padding:0}}>
                    {detailBlock.step_by_step.map((s:string,i:number)=>(
                      <li key={i} style={{fontSize:"0.85rem", color:"var(--rla-text-dim)", marginBottom:6, lineHeight:1.6}}><span style={{fontWeight:600, color:"var(--rla-text)"}}>{i+1}.</span> {s}</li>
                    ))}
                  </ol>
                </div>
              )}

              {!!detailBlock.examples?.length && (
                <div style={{marginTop:18}}>
                  <h4 style={{fontSize:"0.85rem", fontWeight:700, display:"flex", gap:8, alignItems:"center"}}><i className="fas fa-code" style={{color:"var(--rla-violet)"}} /> Code example{detailBlock.examples.length>1 ? "s" : ""}</h4>
                  {detailBlock.examples.map((ex:any,i:number)=> <CodeBlock key={i} ex={ex} />)}
                </div>
              )}

              <DetailSection icon="fa-mouse-pointer" title="Try it yourself">{detailBlock.try_it_yourself}</DetailSection>

              {!!detailBlock.common_mistakes?.length && (
                <div style={{marginTop:18}}>
                  <h4 style={{fontSize:"0.85rem", fontWeight:700, display:"flex", gap:8, alignItems:"center", color:"var(--rla-amber)"}}><i className="fas fa-exclamation-circle" /> Common mistakes</h4>
                  <ul style={{margin:"8px 0 0 18px", padding:0}}>
                    {detailBlock.common_mistakes.map((m:string,i:number)=>(
                      <li key={i} style={{fontSize:"0.82rem", color:"var(--rla-text-dim)", marginBottom:4, lineHeight:1.6}}>{m}</li>
                    ))}
                  </ul>
                </div>
              )}

              <DetailSection icon="fa-dumbbell" title="Exercise">{detailBlock.exercise}</DetailSection>
              <DetailSection icon="fa-home" title="Homework">{detailBlock.homework}</DetailSection>
              {detailBlock.challenge && <DetailSection icon="fa-trophy" title="Challenge (optional)" tone="var(--rla-amber)">{detailBlock.challenge}</DetailSection>}

              {!!detailBlock.quick_review?.length && (
                <div style={{marginTop:18}}>
                  <h4 style={{fontSize:"0.85rem", fontWeight:700, display:"flex", gap:8, alignItems:"center"}}><i className="fas fa-undo" style={{color:"var(--rla-green)"}} /> Quick recap</h4>
                  <ul style={{margin:"8px 0 0 18px", padding:0}}>
                    {detailBlock.quick_review.map((q:string,i:number)=><li key={i} style={{fontSize:"0.82rem", color:"var(--rla-text-dim)", marginBottom:4}}>{q}</li>)}
                  </ul>
                </div>
              )}

              {!!detailBlock.what_you_can_do_now?.length && (
                <div style={{marginTop:18}}>
                  <h4 style={{fontSize:"0.85rem", fontWeight:700, display:"flex", gap:8, alignItems:"center", color:"var(--rla-green)"}}><i className="fas fa-check-double" /> What you can do now</h4>
                  <ul style={{margin:"8px 0 0 18px", padding:0}}>
                    {detailBlock.what_you_can_do_now.map((w:string,i:number)=><li key={i} style={{fontSize:"0.82rem", color:"var(--rla-text-dim)", marginBottom:4}}>{w}</li>)}
                  </ul>
                </div>
              )}

              {!!detailBlock.questions?.length && (
                <div style={{marginTop:18}}>
                  <h4 style={{fontSize:"0.85rem", fontWeight:700, display:"flex", gap:8, alignItems:"center"}}><i className="fas fa-question-circle" style={{color:"var(--rla-cyan)"}} /> Check yourself</h4>
                  <ul style={{margin:"8px 0 0 18px", padding:0}}>
                    {detailBlock.questions.map((q:string,i:number)=><li key={i} style={{fontSize:"0.82rem", color:"var(--rla-text-dim)", marginBottom:4}}>{q}</li>)}
                  </ul>
                </div>
              )}

              <DetailSection icon="fa-forward" title="Next up">{detailBlock.next_preview}</DetailSection>

              <div style={{marginTop:20, padding:"12px 14px", background:"var(--rla-bg)", border:"1px solid var(--rla-border)", borderRadius:10, display:"flex", justifyContent:"space-between", alignItems:"center", flexWrap:"wrap", gap:8}}>
                <span className="text-xs" style={{color:"var(--rla-text-faint)"}}>Status: <StatusPill status={detailBlock.status} /> · v{detailBlock.version} · {detailBlock.generated_at ? new Date(detailBlock.generated_at).toLocaleString() : "not generated"}</span>
                <div style={{display:"flex", gap:8}}>
                  <button onClick={()=>{ setShowDetail(false); runSingleDay(selected, detailBlock.day_number); }} disabled={busy} className="rla-btn rla-btn-ghost rla-btn-sm"><i className="fas fa-sync" /> Regenerate</button>
                  <button onClick={()=>setShowDetail(false)} className="rla-btn rla-btn-primary rla-btn-sm">Close</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
