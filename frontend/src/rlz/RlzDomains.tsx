import { useEffect, useState } from "react";

type Domain = {
  id: string; name: string; slug: string;
  short_description: string; detailed_description: string;
  business_problems: string[]; solutions_delivered: string[]; capabilities: string[];
  technologies: string[]; projects: string[]; products: string[]; portfolio_items: string[];
  github_repositories: string[]; experience_evidence: string[];
  confidence_score: number; confidence_label: string; status: string; featured: boolean;
};

export default function RlzDomains() {
  const [domains, setDomains] = useState<Domain[] | null>(null);
  useEffect(() => {
    const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
    fetch(`${base}/api/domains`).then(r => r.ok ? r.json() : []).then(j => {
      if (Array.isArray(j)) setDomains(j);
      else setDomains([]);
    }).catch(()=>setDomains([]));
  }, []);
  if (!domains || domains.length===0) return null;
  return (
    <section id="domains" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag"><i className="material-symbols-outlined">hub</i> DOMAINS & INDUSTRY EXPERIENCE</div>
          <h2 className="rlz-section-title">Domains <span className="rlz-grad-text">Rajib has worked in</span></h2>
          <p className="rlz-section-desc">Verified business domains — each backed by projects, live portfolio and GitHub evidence, not keywords.</p>
        </div>
        <div className="rlz-bento" style={{marginTop:40}}>
          {domains.map((d)=> (
            <a key={d.slug} href={`/domains/${d.slug}`} className="rlz-bento-card rlz-b-6" style={{textDecoration:"none", color:"inherit", cursor:"pointer"}}>
              <div style={{display:"flex", justifyContent:"space-between", alignItems:"start", gap:12}}>
                <h3 style={{margin:0}}>{d.name}</h3>
                <span className="rlz-chip" style={{background: d.confidence_score>=75? "var(--rlz-violet-soft)": "var(--rlz-bg-2)", color: d.confidence_score>=75? "var(--rlz-violet)": "var(--rlz-text-faint)"}}>{d.confidence_score}% · {d.confidence_label}</span>
              </div>
              <p style={{marginTop:8, color:"var(--rlz-text-dim)", fontSize:"0.93rem"}}>{d.short_description}</p>
              {!!d.business_problems.length && <div style={{marginTop:12}}><b style={{fontSize:"0.78rem", color:"var(--rlz-text-faint)"}}>Business problems solved:</b><ul style={{margin:"6px 0 0 18px", fontSize:"0.86rem", color:"var(--rlz-text-dim)"}}>{d.business_problems.slice(0,2).map(x=><li key={x}>{x}</li>)}</ul></div>}
              {!!d.capabilities.length && <div style={{marginTop:10, display:"flex", flexWrap:"wrap", gap:6}}>{d.capabilities.slice(0,3).map(c=><span key={c} className="rlz-chip">{c}</span>)}</div>}
              {!!d.projects.length && <div style={{marginTop:10, fontSize:"0.8rem", color:"var(--rlz-text-faint)"}}>Projects: {d.projects.slice(0,2).join(", ")}</div>}
              {!!d.technologies.length && <div style={{marginTop:8}}><span style={{fontSize:"0.75rem", color:"var(--rlz-text-faint)"}}>Tech:</span><div className="rlz-chip-row" style={{marginTop:6}}>{d.technologies.slice(0,4).map(t=><span key={t} className="rlz-chip">{t}</span>)}</div></div>}
              <div style={{marginTop:12, display:"flex", gap:14, fontSize:"0.78rem", color:"var(--rlz-text-faint)"}}>
                <span>{d.portfolio_items.length} live sites</span><span>{d.github_repositories.length} repos</span><span>{d.experience_evidence.length} experience</span>
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
