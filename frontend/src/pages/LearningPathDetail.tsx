import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import Markdown from "../components/Markdown";

export default function LearningPathDetail(){
  const {slug=""} = useParams<{slug:string}>();
  const [path,setPath]=useState<any>(null);
  const [blocks,setBlocks]=useState<any[]>([]);
  const [activeDay,setActiveDay]=useState<number>(1);
  const [progress,setProgress]=useState<any>(null);
  useEffect(()=>{
    const base=(import.meta.env.VITE_API_BASE as string|undefined) ?? "";
    fetch(`${base}/api/learning/paths/${slug}`).then(r=>r.ok?r.json():null).then(setPath).catch(()=>{});
    fetch(`${base}/api/learning/paths/${slug}/blocks`).then(r=>r.ok?r.json():[]).then((j:any)=>{
      const arr=Array.isArray(j)?j:[];
      setBlocks(arr);
      const firstPublished=arr.find((b:any)=>b.status==="published");
      if(firstPublished) setActiveDay(firstPublished.day_number);
      else if(arr[0]) setActiveDay(arr[0].day_number);
    }).catch(()=>{});
  },[slug]);
  const markProgress=async(day:number, done:boolean)=>{
    const base=(import.meta.env.VITE_API_BASE as string|undefined) ?? "";
    const r=await fetch(`${base}/api/learning/paths/${slug}/progress`, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({day, exercise_done: done})});
    const j=await r.json().catch(()=>null);
    if(j) setProgress(j);
  };
  if(!path) return <div className="rlz" style={{minHeight:"60vh", padding:80}}><div className="rlz-container">Loading…</div></div>;
  const block=blocks.find((b:any)=>b.day_number===activeDay);
  return (
    <div className="rlz" style={{background:"var(--rlz-bg)", minHeight:"100vh"}}>
      <div className="rlz-page-bg"/><div className="rlz-bg-grid"/>
      <section style={{padding:"32px 0 12px"}}>
        <div className="rlz-container">
          <Link to="/learning" style={{fontSize:"0.85rem", color:"var(--rlz-text-dim)", textDecoration:"none"}}>← All Learning</Link>
          <h1 style={{fontFamily:"Sora, sans-serif", fontSize:"clamp(1.8rem,4vw,2.6rem)", marginTop:8}}>{path.topic} — {path.duration} days</h1>
          <p style={{color:"var(--rlz-text-dim)", maxWidth:720}}>{path.goal || "Mentor-guided progression"}</p>
          <div style={{marginTop:10, display:"flex", gap:8, alignItems:"center"}}>
            <div style={{flex:1, height:8, background:"var(--rlz-bg-2)", borderRadius:8, overflow:"hidden", maxWidth:400}}><div style={{width:`${path.progress||0}%`, height:"100%", background:"var(--rlz-grad-1)"}}/></div>
            <span className="rlz-chip">{path.progress||0}%</span>
          </div>
          <div style={{marginTop:12, display:"flex", gap:8, flexWrap:"wrap"}}>
            {blocks.map((b:any)=>(
              <button key={b.day_number} onClick={()=>setActiveDay(b.day_number)} className="rlz-chip" style={{background: activeDay===b.day_number? "var(--rlz-violet)":"var(--rlz-bg-2)", color: activeDay===b.day_number? "#fff": "var(--rlz-text-faint)", border: b.status==="published"?"1px solid var(--rlz-violet)":"1px solid var(--rlz-border)"}}>
                Day {b.day_number} {b.status==="published"?"· ✓": b.status==="needs_review"?"· !" :""}
              </button>
            ))}
          </div>
        </div>
      </section>
      <div className="rlz-container" style={{paddingBottom:40, display:"grid", gap:18}}>
        {!block ? <p style={{color:"var(--rla-text-faint)"}}>No published lesson for this day yet — agent generates daily at 06:00 IST.</p> : (
          <article style={{background:"#fff", border:"1px solid var(--rlz-border)", borderRadius:20, padding:24}}>
            <div className="rlz-section-tag" style={{marginBottom:8}}><i className="material-symbols-outlined">auto_stories</i> Day {block.day_number} — {block.topic || block.title}</div>
            <h2 style={{fontFamily:"Sora, sans-serif"}}>Today's Lesson — {block.topic || block.title}</h2>

            <section style={{marginTop:16, background:"var(--rlz-bg-2)", borderRadius:12, padding:16}}>
              <h3>What you'll learn</h3>
              <p style={{color:"var(--rlz-text-dim)"}}>{block.learning_objective}</p>
              <h4 style={{marginTop:12}}>Why this matters</h4>
              <p style={{color:"var(--rlz-text-dim)"}}>{block.why_matters}</p>
            </section>

            <section style={{marginTop:16}}>
              <h3>Let's understand it</h3>
              <div style={{color:"var(--rlz-text-dim)", lineHeight:1.7}}><Markdown text={block.concept_explanation || ""} /></div>
              {!!block.step_by_step?.length && <ol style={{marginLeft:18, marginTop:10}}>{block.step_by_step.map((s:string)=><li key={s} style={{color:"var(--rlz-text-dim)"}}>{s}</li>)}</ol>}
            </section>

            {!!block.examples?.length && (
              <section style={{marginTop:16}}>
                <h3>Example</h3>
                {block.examples.map((ex:any, i:number)=>(
                  <div key={i} style={{background:"#0d1024", color:"#c3c9e8", borderRadius:12, padding:16, marginTop:10, fontFamily:"JetBrains Mono, monospace", fontSize:"0.85rem"}}>
                    <div style={{color:"#a78bfa", marginBottom:6}}>{ex.title}</div>
                    <pre style={{whiteSpace:"pre-wrap", margin:0}}>{ex.code}</pre>
                    <div style={{color:"#6b7194", marginTop:8, fontFamily:"Inter, sans-serif"}}>{ex.explanation}</div>
                    {ex.expected_output && <div style={{marginTop:6, color:"#6ee7b7"}}>▶ {ex.expected_output}</div>}
                  </div>
                ))}
              </section>
            )}

            <section style={{marginTop:16, background:"var(--rlz-violet-soft)", borderRadius:12, padding:16}}>
              <h3>Try it yourself</h3>
              <p style={{color:"var(--rlz-text-dim)"}}>{block.exercise}</p>
              <button onClick={()=>markProgress(block.day_number, true)} className="rlz-btn rlz-btn-primary" style={{marginTop:10}}>Mark exercise done</button>
              {progress && <span style={{marginLeft:8, fontSize:"0.85rem", color:"var(--rlz-green)"}}>Progress {progress.progress}%</span>}
            </section>

            <section style={{marginTop:16, display:"grid", gap:12}}>
              <div style={{background:"var(--rlz-bg-2)", borderRadius:12, padding:14}}><h4>Homework</h4><p style={{color:"var(--rlz-text-dim)"}}>{block.homework || "—"}</p></div>
              <div style={{background:"var(--rlz-bg-2)", borderRadius:12, padding:14}}><h4>Challenge</h4><p style={{color:"var(--rlz-text-dim)"}}>{block.challenge || "—"}</p></div>
              <div style={{background:"var(--rlz-bg-2)", borderRadius:12, padding:14}}><h4>Quick review</h4><ul style={{marginLeft:18}}>{(block.quick_review||[]).map((q:string)=><li key={q} style={{color:"var(--rlz-text-dim)"}}>{q}</li>)}</ul></div>
              <div style={{background:"var(--rlz-bg-2)", borderRadius:12, padding:14}}><h4>Questions — check yourself</h4><ul style={{marginLeft:18}}>{(block.questions||[]).map((q:string)=><li key={q} style={{color:"var(--rlz-text-dim)"}}>{q}</li>)}</ul></div>
            </section>

            <section style={{marginTop:16, borderTop:"1px dashed var(--rlz-border)", paddingTop:12}}>
              <p style={{color:"var(--rla-text-faint)", fontSize:"0.85rem"}}>Before Day {block.day_number+1}: make sure you can {block.learning_objective?.toLowerCase() || "explain what you learned"}. {block.next_preview || ""}</p>
            </section>
          </article>
        )}
      </div>
    </div>
  );
}
