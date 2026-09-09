/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export default function Learning(){
  const [paths,setPaths]=useState<any[]>([]);
  const [active,setActive]=useState<any>(null);
  useEffect(()=>{
    const base=(import.meta.env.VITE_API_BASE as string|undefined) ?? "";
    fetch(`${base}/api/learning/paths`).then(r=>r.ok?r.json():[]).then(j=>setPaths(Array.isArray(j)?j:[])).catch(()=>{});
    fetch(`${base}/api/learning/active`).then(r=>r.ok?r.json():null).then(j=>{ if(j && j.active) setActive(j); }).catch(()=>{});
  },[]);
  return (
    <div className="rlz" style={{background:"var(--rlz-bg)", minHeight:"100vh"}}>
      <div className="rlz-page-bg"/><div className="rlz-bg-grid"/>
      <section style={{padding:"48px 0 20px"}}>
        <div className="rlz-container">
          <div className="rlz-section-tag"><i className="material-symbols-outlined">school</i> LEARNING</div>
          <h1 style={{fontFamily:"Sora, sans-serif", fontSize:"clamp(2rem,4.5vw,3.2rem)"}}>Continue where you left off</h1>
          <p style={{color:"var(--rlz-text-dim)", maxWidth:680, marginTop:8}}>A mentor-guided path — one day at a time, with prerequisites, examples and homework. You define Topic + Duration, the agent builds the rest.</p>
        </div>
      </section>
      <div className="rlz-container" style={{paddingBottom:40, display:"grid", gap:22}}>
        {active && active.path && (
          <section style={{background:"var(--rlz-surface-2)", border:"1px solid var(--rlz-border)", borderRadius:20, padding:24}}>
            <div style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
              <h2 style={{fontFamily:"Sora, sans-serif"}}>Active: {active.path.topic} — {active.path.duration} days</h2>
              <span className="rlz-chip">{active.progress || active.path.progress || 0}% · Day {active.path.current_day || 0}/{active.path.duration}</span>
            </div>
            <div style={{marginTop:12, height:8, background:"var(--rlz-bg-2)", borderRadius:8, overflow:"hidden"}}>
              <div style={{width:`${active.progress || 0}%`, height:"100%", background:"var(--rlz-grad-1)"}}/>
            </div>
            <Link to={`/learning/${active.path.slug}`} className="rlz-btn rlz-btn-primary" style={{marginTop:14, display:"inline-flex", textDecoration:"none"}}>Continue → Day {(active.path.current_day||0)+1}</Link>
          </section>
        )}
        <section>
          <h2 style={{fontFamily:"Sora, sans-serif"}}>Learning Paths</h2>
          <div style={{display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(280px,1fr))", gap:16, marginTop:12}}>
            {paths.map((p:any)=>(
              <Link key={p.slug} to={`/learning/${p.slug}`} style={{textDecoration:"none", color:"inherit", background:"var(--rlz-surface-2)", border:"1px solid var(--rlz-border)", borderRadius:16, padding:18, display:"block"}}>
                <div style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
                  <h3 style={{margin:0, fontFamily:"Sora, sans-serif"}}>{p.topic}</h3>
                  <span className="rlz-chip">{p.duration} days</span>
                </div>
                <p style={{color:"var(--rlz-text-dim)", fontSize:"0.9rem", marginTop:6}}>{p.goal || "Practical understanding"}</p>
                <div style={{marginTop:10, height:6, background:"var(--rlz-bg-2)", borderRadius:6, overflow:"hidden"}}><div style={{width:`${p.progress||0}%`, height:"100%", background:"var(--rlz-cyan)"}}/></div>
                <p style={{fontSize:"0.78rem", color:"var(--rla-text-faint)", marginTop:6}}>{p.progress||0}% · {p.status}</p>
              </Link>
            ))}
          </div>
          {paths.length===0 && <p style={{color:"var(--rla-text-faint)", marginTop:12}}>No published paths yet — check back after the 06:00 IST agent run.</p>}
        </section>
      </div>
    </div>
  );
}
