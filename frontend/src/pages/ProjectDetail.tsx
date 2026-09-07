import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import Markdown from "../components/Markdown";

type DetailKind = "portfolio" | "product";

type ProjectDetailData = {
  id?: string;
  title?: string;
  name?: string;
  slug: string;
  shortDescription?: string;
  short_description?: string;
  description?: string;
  full_description?: string;
  purpose?: string;
  problem?: string;
  solution?: string;
  targetUsers?: string[];
  target_users?: string[];
  functionalDetails?: string;
  functional_details?: string;
  features?: string[];
  workflow?: string;
  role?: string;
  architecture?: string;
  businessValue?: string;
  business_value?: string;
  challenges?: string;
  category?: string;
  techStack?: string[];
  technologies?: string[];
  tech_stack?: string[];
  tags?: string[];
  featuredImage?: string | null;
  featured_image?: string | null;
  logoUrl?: string | null;
  gallery?: string[];
  screenshots?: string[];
  liveUrl?: string | null;
  live_url?: string | null;
  gitHubUrl?: string | null;
  github_url?: string | null;
  demoUrl?: string | null;
  demo_url?: string | null;
  productUrl?: string | null;
  product_url?: string | null;
  docsUrl?: string | null;
  docs_url?: string | null;
  ctaText?: string | null;
  cta_text?: string | null;
  ctaUrl?: string | null;
  cta_url?: string | null;
  videoUrl?: string | null;
  video_url?: string | null;
  videoEmbedUrl?: string | null;
  featured?: boolean;
  status?: string;
  seoTitle?: string;
  seo_title?: string;
  seoDescription?: string;
  seo_description?: string;
  seoImage?: string;
  seo_image?: string;
  displayOrder?: number;
  display_order?: number;
};

function getTitle(d: ProjectDetailData) {
  return d.title || d.name || d.slug;
}
function getShort(d: ProjectDetailData) {
  return d.shortDescription || d.short_description || d.purpose || "";
}
function getDesc(d: ProjectDetailData) {
  return d.description || d.full_description || "";
}
function getTech(d: ProjectDetailData) {
  return d.techStack || d.technologies || d.tech_stack || [];
}
function getTags(d: ProjectDetailData) {
  return d.tags || [];
}
function getGh(d: ProjectDetailData) {
  return d.gitHubUrl || d.github_url || null;
}
function getLive(d: ProjectDetailData) {
  return d.liveUrl || d.live_url || d.demoUrl || d.demo_url || null;
}
function getFeaturedImg(d: ProjectDetailData) {
  return d.featuredImage || d.featured_image || d.logoUrl || null;
}
function getGallery(d: ProjectDetailData) {
  return d.gallery || d.screenshots || [];
}
function getWorkflowSteps(workflow?: string): string[] {
  if (!workflow) return [];
  // split by newline or → or numbered steps
  const parts = workflow.split(/\n|→|→|—|–/).map((s) => s.trim()).filter(Boolean);
  if (parts.length <= 1) {
    // try split by numbered list 1. 2.
    const numbered = workflow.split(/\d+\.\s/).map((s) => s.trim()).filter(Boolean);
    if (numbered.length > 1) return numbered;
  }
  return parts;
}

export default function ProjectDetail({ kind }: { kind: DetailKind }) {
  const { slug = "" } = useParams<{ slug: string }>();
  const [data, setData] = useState<ProjectDetailData | null>(null);
  const [related, setRelated] = useState<ProjectDetailData[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setNotFound(false);
    (async () => {
      const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
      const tryUrls =
        kind === "portfolio"
          ? [`${base}/api/portfolio/${slug}`, `${base}/api/public/projects/${slug}`]
          : [`${base}/api/products/${slug}`, `${base}/api/public/projects/${slug}`];
      let found: ProjectDetailData | null = null;
      for (const u of tryUrls) {
        try {
          const r = await fetch(u);
          if (r.ok) {
            const j = (await r.json()) as ProjectDetailData;
            // normalize: if it returns {items: []} skip
            if ((j as unknown as { slug?: string }).slug || (j as unknown as { title?: string }).title) {
              found = j;
              break;
            }
          }
        } catch {}
      }
      if (!alive) return;
      if (!found) {
        setNotFound(true);
        setLoading(false);
        return;
      }
      setData(found);
      setLoading(false);

      // SEO
      const title = getTitle(found);
      const seoTitle = found.seoTitle || found.seo_title || `${title} | RajibLabs`;
      const seoDesc = found.seoDescription || found.seo_description || found.shortDescription || found.short_description || (found.description || "").slice(0, 160);
      const ogImg = found.seoImage || found.seo_image || found.featuredImage || found.featured_image || "";
      document.title = seoTitle;
      // meta description
      let md = document.querySelector('meta[name="description"]');
      if (!md) {
        md = document.createElement("meta");
        md.setAttribute("name", "description");
        document.head.appendChild(md);
      }
      md.setAttribute("content", seoDesc || "");
      // og image
      let og = document.querySelector('meta[property="og:image"]');
      if (!og) {
        og = document.createElement("meta");
        og.setAttribute("property", "og:image");
        document.head.appendChild(og);
      }
      if (ogImg) og.setAttribute("content", ogImg);
      // canonical
      let link = document.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
      if (!link) {
        link = document.createElement("link");
        link.rel = "canonical";
        document.head.appendChild(link);
      }
      link.href = `https://rajiblabs.com/${kind === "portfolio" ? "portfolio" : "products"}/${found.slug}`;

      // fetch related (2-4)
      try {
        const relBase = kind === "portfolio" ? `${base}/api/portfolio` : `${base}/api/products`;
        const r = await fetch(relBase);
        if (r.ok) {
          const list = (await r.json()) as ProjectDetailData[];
          const arr = Array.isArray(list) ? list : [];
          const filtered = arr.filter((x) => x.slug !== found!.slug).slice(0, 4);
          // if portfolio, also try to enrich with products for variety
          if (filtered.length < 2 && kind === "portfolio") {
            try {
              const rr = await fetch(`${base}/api/products`);
              if (rr.ok) {
                const prod = (await rr.json()) as ProjectDetailData[];
                const pArr = Array.isArray(prod) ? prod : [];
                for (const p of pArr) {
                  if (filtered.length >= 4) break;
                  if (p.slug !== found!.slug) filtered.push(p);
                }
              }
            } catch {}
          }
          if (alive) setRelated(filtered);
        }
      } catch {}
    })();
    return () => {
      alive = false;
    };
  }, [slug, kind]);

  if (loading) {
    return (
      <div className="rlz" style={{ background: "var(--rlz-bg)", minHeight: "100vh", padding: "120px 24px" }}>
        <div className="rlz-container" style={{ maxWidth: 1200 }}>
          <div style={{ height: 18, width: 120, background: "var(--rlz-bg-2)", borderRadius: 8, marginBottom: 16 }} />
          <div style={{ height: 36, width: "60%", background: "var(--rlz-bg-2)", borderRadius: 12, marginBottom: 12 }} />
          <div style={{ height: 14, width: "80%", background: "var(--rlz-bg-2)", borderRadius: 8 }} />
        </div>
      </div>
    );
  }
  if (notFound || !data) {
    return (
      <div className="rlz" style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "var(--rlz-bg)", padding: 40 }}>
        <div style={{ textAlign: "center" }}>
          <p style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.85rem", color: "var(--rlz-text-faint)" }}>404 — Not Found</p>
          <h1 style={{ fontFamily: "Sora, sans-serif", fontSize: "2rem", marginTop: 8 }}>Project not found</h1>
          <p style={{ color: "var(--rlz-text-dim)", marginTop: 8 }}>The project “{slug}” does not exist or is not published.</p>
          <Link to="/" className="rlz-btn rlz-btn-primary" style={{ marginTop: 20, display: "inline-flex" }}>
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  const d = data;
  const title = getTitle(d);
  const shortDesc = getShort(d);
  const desc = getDesc(d);
  const purpose = d.purpose || "";
  const problem = d.problem || "";
  const solution = d.solution || "";
  const targetUsers = d.targetUsers || d.target_users || [];
  const functionalDetails = d.functionalDetails || d.functional_details || "";
  const features = d.features || [];
  const workflow = d.workflow || "";
  const workflowSteps = getWorkflowSteps(workflow);
  const role = d.role || "";
  const architecture = d.architecture || "";
  const businessValue = d.businessValue || d.business_value || "";
  const challenges = d.challenges || "";
  const techs = getTech(d);
  const tags = getTags(d);
  const gh = getGh(d);
  const live = getLive(d);
  const heroImg = getFeaturedImg(d);
  const gallery = getGallery(d).filter((g) => g !== heroImg);
  const videoEmbed = d.videoEmbedUrl || (d.videoUrl || d.video_url ? (d.videoUrl || d.video_url)!.replace("youtu.be/", "www.youtube.com/embed/").split("?")[0].replace("watch?v=", "embed/") : null);
  const docs = d.docsUrl || d.docs_url || null;
  const category = d.category || (kind === "product" ? "Product" : "Portfolio");
  const displayPurpose = purpose || shortDesc;

  return (
    <div className="rlz" style={{ background: "var(--rlz-bg)", minHeight: "100vh" }}>
      {/* subtle grid + orbs */}
      <div className="rlz-page-bg" />
      <div className="rlz-bg-grid" />
      <div className="rlz-orb rlz-orb-1" style={{ opacity: 0.35 }} />
      <div className="rlz-orb rlz-orb-2" style={{ opacity: 0.3 }} />

      {/* Header nav simple */}
      <nav style={{ position: "sticky", top: 0, zIndex: 50, backdropFilter: "blur(14px)", background: "rgba(247,248,252,0.75)", borderBottom: "1px solid var(--rlz-border)" }}>
        <div className="rlz-container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 24px" }}>
          <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", color: "var(--rlz-text)", fontFamily: "Sora, sans-serif", fontWeight: 700 }}>
            <span style={{ width: 32, height: 32, borderRadius: 9, background: "var(--rlz-grad-1)", display: "grid", placeItems: "center", color: "#fff" }}>R</span>
            Rajib<span style={{ fontWeight: 400, color: "var(--rlz-text-faint)" }}>Labs</span>
          </Link>
          <Link to="/#projects" style={{ fontSize: "0.9rem", color: "var(--rlz-text-dim)", textDecoration: "none" }}>← All Projects</Link>
        </div>
      </nav>

      {/* HERO */}
      <section style={{ padding: "48px 0 32px" }}>
        <div className="rlz-container">
          <div style={{ maxWidth: 900 }}>
            <div className="rlz-section-tag" style={{ marginBottom: 16 }}>
              <i className="material-symbols-outlined">layers</i> {category.toUpperCase()} {d.featured ? "· FEATURED" : ""} {d.status ? `· ${d.status.toUpperCase()}` : ""}
            </div>
            <h1 style={{ fontFamily: "Sora, sans-serif", fontSize: "clamp(2rem, 4.5vw, 3.4rem)", lineHeight: 1.1, letterSpacing: "-0.02em", margin: 0 }}>{title}</h1>
            {displayPurpose && <p style={{ marginTop: 16, fontSize: "1.25rem", color: "var(--rlz-text)", fontWeight: 600, lineHeight: 1.4 }}>{displayPurpose}</p>}
            {shortDesc && shortDesc !== displayPurpose && <p style={{ marginTop: 12, fontSize: "1.05rem", color: "var(--rlz-text-dim)", lineHeight: 1.6 }}>{shortDesc}</p>}
            {(purpose && purpose !== displayPurpose && purpose !== shortDesc) && <p style={{ marginTop: 10, color: "var(--rlz-text-dim)" }}>{purpose}</p>}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 22 }}>
              {live && (
                <a href={live} target="_blank" rel="noopener noreferrer" className="rlz-btn rlz-btn-primary" style={{ textDecoration: "none" }}>
                  <i className="material-symbols-outlined">open_in_new</i> Live Website
                </a>
              )}
              {gh && (
                <a href={gh} target="_blank" rel="noopener noreferrer" className="rlz-btn rlz-btn-ghost" style={{ textDecoration: "none" }}>
                  <i className="material-symbols-outlined">code</i> GitHub Repository
                </a>
              )}
              {docs && (
                <a href={docs} target="_blank" rel="noopener noreferrer" className="rlz-btn rlz-btn-ghost" style={{ textDecoration: "none" }}>
                  <i className="material-symbols-outlined">description</i> Documentation
                </a>
              )}
              {!live && !gh && <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.8rem", color: "var(--rlz-text-faint)", alignSelf: "center" }}>Links unavailable — private / in development</span>}
            </div>
            {!!tags.length && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 18 }}>
                {tags.map((t) => (
                  <span key={t} style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.75rem", padding: "6px 10px", borderRadius: 100, background: "var(--rlz-bg-2)", border: "1px solid var(--rlz-border)", color: "var(--rlz-text-faint)" }}>
                    #{t}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* hero media */}
          {heroImg && (
            <div style={{ marginTop: 32, borderRadius: 20, overflow: "hidden", border: "1px solid var(--rlz-border)", boxShadow: "var(--rlz-shadow-lg)", background: "var(--rlz-surface-2)" }}>
              <img src={heroImg} alt={`${title} cover`} loading="eager" decoding="async" style={{ width: "100%", maxHeight: 520, objectFit: "cover", display: "block" }} />
            </div>
          )}
          {!!gallery.length && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12, marginTop: 14 }}>
              {gallery.slice(0, 6).map((g) => (
                <a key={g} href={g} target="_blank" rel="noopener noreferrer" style={{ borderRadius: 14, overflow: "hidden", border: "1px solid var(--rlz-border)", display: "block", background: "var(--rlz-surface-2)" }}>
                  <img src={g} alt={`${title} gallery`} loading="lazy" decoding="async" style={{ width: "100%", height: 140, objectFit: "cover", display: "block" }} />
                </a>
              ))}
            </div>
          )}
          {videoEmbed && (
            <div style={{ marginTop: 28, borderRadius: 20, overflow: "hidden", border: "1px solid var(--rlz-border)", background: "#0d1024", aspectRatio: "16/9", position: "relative" }}>
              <iframe src={videoEmbed} title={`${title} demo`} loading="lazy" allowFullScreen style={{ position: "absolute", inset: 0, width: "100%", height: "100%", border: 0 }} />
            </div>
          )}
        </div>
      </section>

      {/* CONTENT GRID */}
      <div className="rlz-container" style={{ paddingBottom: 60 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 28, alignItems: "start" }}>
          {/* Main column */}
          <div style={{ display: "grid", gap: 22 }}>
            {/* Overview / Description */}
            {desc && (
              <section style={{ background: "var(--rlz-surface-2)", border: "1px solid var(--rlz-border)", borderRadius: 20, padding: 28, boxShadow: "var(--rlz-shadow-sm)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                  <span style={{ width: 36, height: 36, borderRadius: 10, background: "var(--rlz-violet-soft)", display: "grid", placeItems: "center", color: "var(--rlz-violet)" }}>
                    <i className="material-symbols-outlined">info</i>
                  </span>
                  <h2 style={{ fontFamily: "Sora, sans-serif", fontSize: "1.25rem", margin: 0 }}>Overview</h2>
                </div>
                <div style={{ color: "var(--rlz-text-dim)", lineHeight: 1.7, fontSize: "0.98rem" }}>
                  <Markdown text={desc} />
                </div>
              </section>
            )}

            {/* Problem / Solution bento */}
            {(problem || solution) && (
              <div style={{ display: "grid", gridTemplateColumns: problem && solution ? "1fr 1fr" : "1fr", gap: 16 }}>
                {problem && (
                  <section style={{ background: "linear-gradient(135deg, rgba(124,58,237,0.08), rgba(255,255,255,0.9))", border: "1px solid var(--rlz-border)", borderRadius: 20, padding: 24 }}>
                    <h3 style={{ fontFamily: "Sora, sans-serif", fontSize: "1.05rem", display: "flex", alignItems: "center", gap: 8 }}>
                      <i className="material-symbols-outlined" style={{ color: "var(--rlz-fuchsia)" }}>report_problem</i> The Problem
                    </h3>
                    <p style={{ marginTop: 10, color: "var(--rlz-text-dim)", lineHeight: 1.6, fontSize: "0.95rem" }}>{problem}</p>
                    {!!targetUsers.length && (
                      <div style={{ marginTop: 14, display: "flex", flexWrap: "wrap", gap: 6 }}>
                        {targetUsers.map((u) => (
                          <span key={u} style={{ fontSize: "0.75rem", padding: "5px 10px", borderRadius: 100, background: "var(--rlz-bg-2)", border: "1px solid var(--rlz-border)", color: "var(--rlz-text-faint)" }}>
                            {u}
                          </span>
                        ))}
                      </div>
                    )}
                  </section>
                )}
                {solution && (
                  <section style={{ background: "linear-gradient(135deg, rgba(6,182,212,0.08), rgba(255,255,255,0.9))", border: "1px solid var(--rlz-border)", borderRadius: 20, padding: 24 }}>
                    <h3 style={{ fontFamily: "Sora, sans-serif", fontSize: "1.05rem", display: "flex", alignItems: "center", gap: 8 }}>
                      <i className="material-symbols-outlined" style={{ color: "var(--rlz-cyan)" }}>lightbulb</i> The Solution
                    </h3>
                    <p style={{ marginTop: 10, color: "var(--rlz-text-dim)", lineHeight: 1.6, fontSize: "0.95rem" }}>{solution}</p>
                  </section>
                )}
              </div>
            )}

            {/* Functional Details */}
            {functionalDetails && (
              <section style={{ background: "var(--rlz-surface-2)", border: "1px solid var(--rlz-border)", borderRadius: 20, padding: 28 }}>
                <h2 style={{ fontFamily: "Sora, sans-serif", fontSize: "1.2rem", display: "flex", alignItems: "center", gap: 10 }}>
                  <i className="material-symbols-outlined" style={{ color: "var(--rlz-violet)" }}>lists</i> Functional Details
                </h2>
                <div style={{ marginTop: 14, color: "var(--rlz-text-dim)", lineHeight: 1.7 }}>
                  <Markdown text={functionalDetails} />
                </div>
              </section>
            )}

            {/* Key Features bento */}
            {!!features.length && (
              <section>
                <h2 style={{ fontFamily: "Sora, sans-serif", fontSize: "1.2rem", marginBottom: 14 }}>Key Functionality</h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 14 }}>
                  {features.map((f, idx) => (
                    <div key={f} style={{ background: "var(--rlz-surface-2)", border: "1px solid var(--rlz-border)", borderRadius: 16, padding: 18, display: "flex", gap: 12, alignItems: "start" }}>
                      <span style={{ width: 32, height: 32, borderRadius: 10, background: "var(--rlz-violet-soft)", color: "var(--rlz-violet)", display: "grid", placeItems: "center", flexShrink: 0, fontFamily: "JetBrains Mono, monospace", fontSize: "0.8rem", fontWeight: 700 }}>
                        {String(idx + 1).padStart(2, "0")}
                      </span>
                      <p style={{ margin: 0, fontSize: "0.92rem", color: "var(--rlz-text)", lineHeight: 1.5 }}>{f}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Workflow */}
            {(workflow || workflowSteps.length > 0) && (
              <section style={{ background: "var(--rlz-surface)", border: "1px solid var(--rlz-border)", borderRadius: 20, padding: 28, backdropFilter: "blur(10px)" }}>
                <h2 style={{ fontFamily: "Sora, sans-serif", fontSize: "1.2rem", display: "flex", alignItems: "center", gap: 10 }}>
                  <i className="material-symbols-outlined" style={{ color: "var(--rlz-cyan)" }}>account_tree</i> How It Works
                </h2>
                {workflowSteps.length > 1 ? (
                  <div style={{ marginTop: 18, display: "grid", gap: 0 }}>
                    {workflowSteps.map((step, i) => (
                      <div key={step + i} style={{ display: "flex", gap: 14, alignItems: "start" }}>
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                          <span style={{ width: 28, height: 28, borderRadius: 999, background: "var(--rlz-grad-1)", color: "#fff", display: "grid", placeItems: "center", fontSize: "0.75rem", fontWeight: 700 }}>{i + 1}</span>
                          {i < workflowSteps.length - 1 && <span style={{ width: 2, height: 24, background: "linear-gradient(to bottom, var(--rlz-violet), var(--rlz-cyan-bright))", opacity: 0.5, marginTop: 4 }} />}
                        </div>
                        <p style={{ margin: 0, padding: "4px 0 18px", color: "var(--rlz-text-dim)", fontSize: "0.95rem" }}>{step}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ marginTop: 14, color: "var(--rlz-text-dim)", lineHeight: 1.7 }}>
                    <Markdown text={workflow} />
                  </div>
                )}
              </section>
            )}

            {/* Architecture */}
            {architecture && (
              <section style={{ background: "var(--rlz-surface-2)", border: "1px solid var(--rlz-border)", borderRadius: 20, padding: 28 }}>
                <h2 style={{ fontFamily: "Sora, sans-serif", fontSize: "1.2rem" }}>Architecture Overview</h2>
                <p style={{ marginTop: 10, color: "var(--rlz-text-dim)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{architecture}</p>
              </section>
            )}
          </div>

          {/* Sidebar */}
          <aside style={{ display: "grid", gap: 16, position: "sticky", top: 80 }}>
            {/* Tech stack */}
            {!!techs.length && (
              <section style={{ background: "var(--rlz-surface-2)", border: "1px solid var(--rlz-border)", borderRadius: 20, padding: 20 }}>
                <h3 style={{ fontFamily: "Sora, sans-serif", fontSize: "1rem", display: "flex", alignItems: "center", gap: 8 }}>
                  <i className="material-symbols-outlined" style={{ color: "var(--rlz-violet)" }}>code</i> Technology
                </h3>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12 }}>
                  {techs.map((t) => (
                    <span key={t} style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.75rem", padding: "6px 12px", borderRadius: 100, background: "var(--rlz-violet-soft)", border: "1px solid rgba(124,58,237,0.15)", color: "var(--rlz-violet)" }}>
                      {t}
                    </span>
                  ))}
                </div>
                {architecture && <p style={{ marginTop: 12, fontSize: "0.85rem", color: "var(--rlz-text-faint)", lineHeight: 1.5 }}>{architecture.slice(0, 140)}</p>}
              </section>
            )}

            {/* Role */}
            {role && (
              <section style={{ background: "var(--rlz-surface)", border: "1px solid var(--rlz-border)", borderRadius: 20, padding: 20 }}>
                <h3 style={{ fontFamily: "Sora, sans-serif", fontSize: "1rem", display: "flex", alignItems: "center", gap: 8 }}>
                  <i className="material-symbols-outlined" style={{ color: "var(--rlz-amber)" }}>person</i> Rajib&apos;s Role
                </h3>
                <p style={{ marginTop: 10, color: "var(--rlz-text-dim)", fontSize: "0.92rem", lineHeight: 1.6 }}>{role}</p>
              </section>
            )}

            {/* Outcome / Value */}
            {businessValue && (
              <section style={{ background: "linear-gradient(135deg, rgba(124,58,237,0.08), #fff)", border: "1px solid var(--rlz-border)", borderRadius: 20, padding: 20 }}>
                <h3 style={{ fontFamily: "Sora, sans-serif", fontSize: "1rem", display: "flex", alignItems: "center", gap: 8 }}>
                  <i className="material-symbols-outlined" style={{ color: "var(--rlz-green)" }}>trending_up</i> Outcome / Value
                </h3>
                <p style={{ marginTop: 10, color: "var(--rlz-text)", fontSize: "0.92rem", lineHeight: 1.6 }}>{businessValue}</p>
                {challenges && <p style={{ marginTop: 12, color: "var(--rlz-text-faint)", fontSize: "0.85rem", lineHeight: 1.6, borderTop: "1px dashed var(--rlz-border)", paddingTop: 12 }}><b>Challenges:</b> {challenges}</p>}
              </section>
            )}

            {/* Links */}
            <section style={{ background: "var(--rlz-surface-2)", border: "1px solid var(--rlz-border)", borderRadius: 20, padding: 20 }}>
              <h3 style={{ fontFamily: "Sora, sans-serif", fontSize: "1rem" }}>Links</h3>
              <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
                {live && (
                  <a href={live} target="_blank" rel="noopener noreferrer" style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderRadius: 12, background: "var(--rlz-grad-1)", color: "#fff", textDecoration: "none", fontWeight: 600, fontSize: "0.9rem" }}>
                    <i className="material-symbols-outlined">language</i> Live Website <i className="material-symbols-outlined" style={{ marginLeft: "auto" }}>open_in_new</i>
                  </a>
                )}
                {gh && (
                  <a href={gh} target="_blank" rel="noopener noreferrer" style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderRadius: 12, background: "var(--rlz-bg)", border: "1px solid var(--rlz-border)", color: "var(--rlz-text)", textDecoration: "none", fontWeight: 600, fontSize: "0.9rem" }}>
                    <i className="material-symbols-outlined">code</i> GitHub Repository <i className="material-symbols-outlined" style={{ marginLeft: "auto" }}>open_in_new</i>
                  </a>
                )}
                {docs && (
                  <a href={docs} target="_blank" rel="noopener noreferrer" style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderRadius: 12, background: "var(--rlz-surface)", border: "1px solid var(--rlz-border)", color: "var(--rlz-text-dim)", textDecoration: "none", fontSize: "0.9rem" }}>
                    <i className="material-symbols-outlined">description</i> Documentation
                  </a>
                )}
                {d.productUrl || d.product_url ? (
                  <a href={(d.productUrl || d.product_url)!} target="_blank" rel="noopener noreferrer" style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderRadius: 12, background: "var(--rlz-surface)", border: "1px solid var(--rlz-border)", color: "var(--rlz-text-dim)", textDecoration: "none", fontSize: "0.9rem" }}>
                    <i className="material-symbols-outlined">shopping_bag</i> Product Page
                  </a>
                ) : null}
                {!live && !gh && <p style={{ fontSize: "0.85rem", color: "var(--rlz-text-faint)" }}>Links will appear when verified URLs are available.</p>}
              </div>
            </section>

            {/* Quick facts */}
            <section style={{ background: "var(--rlz-bg)", border: "1px dashed var(--rlz-border)", borderRadius: 16, padding: 16 }}>
              <div style={{ display: "grid", gap: 8, fontSize: "0.85rem", color: "var(--rlz-text-dim)" }}>
                {category && <div style={{ display: "flex", justifyContent: "space-between" }}><span>Category</span><b style={{ color: "var(--rlz-text)" }}>{category}</b></div>}
                {d.status && <div style={{ display: "flex", justifyContent: "space-between" }}><span>Status</span><b style={{ textTransform: "capitalize", color: d.status === "published" ? "var(--rlz-green)" : "var(--rlz-text)" }}>{d.status}</b></div>}
                {!!tags.length && <div><span style={{ display: "block", marginBottom: 6 }}>Tags</span><div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>{tags.map((t) => <span key={t} style={{ fontSize: "0.7rem", padding: "4px 8px", borderRadius: 100, background: "#fff", border: "1px solid var(--rlz-border)" }}>{t}</span>)}</div></div>}
              </div>
            </section>
          </aside>
        </div>

        {/* Related */}
        {!!related.length && (
          <section style={{ marginTop: 48 }}>
            <h2 style={{ fontFamily: "Sora, sans-serif", fontSize: "1.4rem" }}>Related Projects</h2>
            <p style={{ color: "var(--rlz-text-faint)", fontSize: "0.9rem", marginTop: 6 }}>More work from RajibLabs — same stack, different problems.</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 16, marginTop: 18 }}>
              {related.map((r) => {
                const rt = (r as ProjectDetailData).title || (r as ProjectDetailData).name || r.slug;
                const rImg = (r as ProjectDetailData).featuredImage || (r as ProjectDetailData).featured_image || null;
                const rDesc = (r as ProjectDetailData).shortDescription || (r as ProjectDetailData).short_description || "";
                const rHref = (r as ProjectDetailData).category && (r as unknown as { category: string }).category === "product" ? `/products/${r.slug}` : `/portfolio/${r.slug}`;
                return (
                  <Link key={r.slug} to={rHref} style={{ textDecoration: "none", color: "inherit", background: "var(--rlz-surface-2)", border: "1px solid var(--rlz-border)", borderRadius: 16, overflow: "hidden", display: "block" }}>
                    <div style={{ height: 140, overflow: "hidden", background: "var(--rlz-bg)" }}>
                      {rImg ? <img src={rImg} alt={rt} loading="lazy" style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : <div style={{ height: "100%", display: "grid", placeItems: "center", color: "var(--rlz-violet)", opacity: 0.4 }}><i className="material-symbols-outlined" style={{ fontSize: "2rem" }}>deployed_code</i></div>}
                    </div>
                    <div style={{ padding: 16 }}>
                      <h3 style={{ fontFamily: "Sora, sans-serif", fontSize: "1rem", margin: 0 }}>{rt}</h3>
                      <p style={{ margin: "6px 0 0", color: "var(--rlz-text-dim)", fontSize: "0.85rem", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{rDesc || "View case study"}</p>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 6, marginTop: 10, fontSize: "0.85rem", fontWeight: 600, color: "var(--rlz-violet)" }}>
                        View <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_forward</i>
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </section>
        )}

        <div style={{ textAlign: "center", marginTop: 48 }}>
          <Link to="/#contact" className="rlz-btn rlz-btn-primary" style={{ textDecoration: "none" }}>
            Discuss your project <i className="material-symbols-outlined">arrow_forward</i>
          </Link>
        </div>
      </div>

      <style>{`
        @media (max-width: 960px) {
          .rlz-container > div[style*="gridTemplateColumns: 1fr 340px"] { grid-template-columns: 1fr !important; }
          aside[style*="position: sticky"] { position: static !important; }
        }
      `}</style>
    </div>
  );
}
