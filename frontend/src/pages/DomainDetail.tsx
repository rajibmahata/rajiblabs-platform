import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import Markdown from "../components/Markdown";

type Domain = {
  id:string; name:string; slug:string; short_description:string; detailed_description:string;
  business_problems:string[]; solutions_delivered:string[]; capabilities:string[];
  technologies:string[]; projects:string[]; products:string[]; portfolio_items:string[];
  github_repositories:string[]; experience_evidence:string[]; confidence_score:number; confidence_label:string;
  seo:{title:string; description:string; keywords:string[]};
  _related_portfolio?: any[];
};

export default function DomainDetail(){
  const {slug=""}=useParams<{slug:string}>();
  const [d,setD]=useState<Domain|null>(null);
  const [notFound,setNF]=useState(false);
  useEffect(()=>{
    const base=(import.meta.env.VITE_API_BASE as string|undefined) ?? "";
    fetch(`${base}/api/domains/${slug}`).then(r=>{ if(!r.ok) throw 0; return r.json();}).then(j=>setD(j)).catch(()=>setNF(true));
  },[slug]);
  useEffect(()=>{
    if(d){
      document.title=d.seo?.title || `${d.name} | RajibLabs Domains`;
      let md=document.querySelector('meta[name="description"]');
      if(!md){ md=document.createElement("meta"); md.setAttribute("name","description"); document.head.appendChild(md);}
      md.setAttribute("content", d.seo?.description || d.short_description || "");
    }
  },[d]);
  if(notFound) return <div className="rlz" style={{minHeight:"60vh", display:"grid", placeItems:"center", padding:40}}><div style={{textAlign:"center"}}><h2>Domain not found</h2><Link to="/">Back to home</Link></div></div>;
  if(!d) return <div className="rlz" style={{minHeight:"60vh", padding:80}}><div className="rlz-container">Loading domain…</div></div>;
  return (
    <div className="rlz" style={{background:"var(--rlz-bg)", minHeight:"100vh"}}>
      <div className="rlz-page-bg"/><div className="rlz-bg-grid"/>
      <section style={{padding:"48px 0 20px"}}>
        <div className="rlz-container">
          <Link to="/#domains" style={{fontSize:"0.85rem", color:"var(--rlz-text-dim)", textDecoration:"none"}}>← All Domains</Link>
          <div className="rlz-section-tag" style={{marginTop:16}}><i className="material-symbols-outlined">verified</i> {d.confidence_score}% · {d.confidence_label}</div>
          <h1 style={{fontFamily:"Sora, sans-serif", fontSize:"clamp(2rem,4.5vw,3.2rem)", margin:"8px 0 0"}}>{d.name}</h1>
          <p style={{marginTop:12, fontSize:"1.15rem", color:"var(--rlz-text-dim)", maxWidth:720}}>{d.short_description}</p>
          <div style={{marginTop:14, display:"flex", flexWrap:"wrap", gap:8}}>{d.technologies.slice(0,6).map(t=><span key={t} className="rlz-chip">{t}</span>)}</div>
        </div>
      </section>

      <div className="rlz-container" style={{paddingBottom:60, display:"grid", gap:22}}>
        {/* Overview */}
        <section style={{background:"var(--rlz-surface-2)", border:"1px solid var(--rlz-border)", borderRadius:20, padding:28}}>
          <h2 style={{fontFamily:"Sora, sans-serif"}}>Domain Overview</h2>
          <div style={{marginTop:10, color:"var(--rlz-text-dim)", lineHeight:1.7}}><Markdown text={d.detailed_description || d.short_description} /></div>
        </section>

        <section style={{background:"var(--rlz-surface)", border:"1px solid var(--rlz-border)", borderRadius:20, padding:28}}>
          <h2>What Rajib Worked On</h2>
          <p style={{color:"var(--rlz-text-dim)"}}>Verified work spanning {d.projects.length+d.portfolio_items.length} portfolio items and {d.github_repositories.length} repositories.</p>
          {!!d.business_problems.length && <><h3 style={{marginTop:16}}>Business Problems</h3><ul style={{marginLeft:18}}>{d.business_problems.map(x=><li key={x} style={{color:"var(--rlz-text-dim)"}}>{x}</li>)}</ul></>}
          {!!d.solutions_delivered.length && <><h3 style={{marginTop:16}}>Solutions Delivered</h3><ul style={{marginLeft:18}}>{d.solutions_delivered.map(x=><li key={x} style={{color:"var(--rlz-text-dim)"}}>{x}</li>)}</ul></>}
          {!!d.capabilities.length && <><h3 style={{marginTop:16}}>Capabilities</h3><div style={{display:"flex", flexWrap:"wrap", gap:8, marginTop:8}}>{d.capabilities.map(c=><span key={c} className="rlz-chip">{c}</span>)}</div></>}
        </section>

        {!!d.projects.length && <section style={{background:"var(--rlz-surface-2)", border:"1px solid var(--rlz-border)", borderRadius:20, padding:28}}><h2>Relevant Projects</h2><div style={{display:"flex", flexWrap:"wrap", gap:8, marginTop:10}}>{d.projects.map(p=><a key={p} href={`/portfolio/${p}`} className="rlz-chip" style={{textDecoration:"none"}}>{p}</a>)}</div></section>}
        {!!d.products.length && <section style={{background:"var(--rlz-surface-2)", border:"1px solid var(--rlz-border)", borderRadius:20, padding:28}}><h2>Products</h2><div style={{display:"flex", flexWrap:"wrap", gap:8, marginTop:10}}>{d.products.map(p=><span key={p} className="rlz-chip">{p}</span>)}</div></section>}
        {!!d.portfolio_items.length && <section style={{background:"var(--rlz-surface-2)", border:"1px solid var(--rlz-border)", borderRadius:20, padding:28}}><h2>Live Portfolio</h2>{(d as any)._related_portfolio?.length ? <div style={{display:"grid", gap:12, marginTop:10}}>{(d as any)._related_portfolio.map((p:any)=><a key={p.slug} href={p.live_url||`/portfolio/${p.slug}`} target="_blank" rel="noopener noreferrer" style={{display:"flex", justifyContent:"space-between", padding:"12px 16px", border:"1px solid var(--rlz-border)", borderRadius:12, textDecoration:"none", color:"var(--rlz-text)"}}><span>{p.title}</span><span style={{color:"var(--rlz-violet)"}}>{p.live_url? "Live →" : "Details →"}</span></a>)}</div> : <div style={{display:"flex", flexWrap:"wrap", gap:8, marginTop:10}}>{d.portfolio_items.map(p=><span key={p} className="rlz-chip">{p}</span>)}</div>}</section>}

        <section style={{background:"var(--rlz-surface-2)", border:"1px solid var(--rlz-border)", borderRadius:20, padding:28}}><h2>Technology Used</h2><div style={{display:"flex", flexWrap:"wrap", gap:8, marginTop:10}}>{d.technologies.map(t=><span key={t} className="rlz-chip">{t}</span>)}</div>{d.technologies.some(t=>/openai|gpt|rag|agent/i.test(t)) && <p style={{marginTop:12, color:"var(--rlz-text-dim)"}}>AI/automation: {d.technologies.filter(t=>/openai|gpt|rag|agent|ai/i.test(t)).join(", ")}</p>}</section>

        {!!d.experience_evidence.length && <section style={{background:"var(--rlz-surface)", border:"1px solid var(--rlz-border)", borderRadius:20, padding:28}}><h2>Professional Experience</h2><ul style={{marginLeft:18, color:"var(--rlz-text-dim)"}}>{d.experience_evidence.map(e=><li key={e}>{e}</li>)}</ul></section>}

        {!!d.github_repositories.length && <section style={{background:"var(--rlz-surface-2)", border:"1px solid var(--rlz-border)", borderRadius:20, padding:28}}><h2>GitHub Evidence</h2><div style={{display:"flex", flexWrap:"wrap", gap:8, marginTop:10}}>{d.github_repositories.map(r=><a key={r} href={`https://github.com/${r}`} target="_blank" rel="noopener noreferrer" className="rlz-chip" style={{textDecoration:"none"}}>{r}</a>)}</div></section>}

        <section style={{background:"var(--rlz-bg)", border:"1px dashed var(--rlz-border)", borderRadius:16, padding:16}}><h3>Related Domains</h3><p style={{color:"var(--rlz-text-faint)", fontSize:"0.9rem"}}><Link to="/#domains">Back to all domains</Link> — knowledge graph: Domain ↔ Project ↔ Portfolio ↔ Product ↔ GitHub ↔ Experience ↔ Knowledge Document</p></section>
      </div>
    </div>
  );
}
