import { useEffect, useState } from "react";
import { PROJECTS, type Project } from "./data";

type CmsPortfolio = {
  id: string;
  title: string;
  slug: string;
  shortDescription: string;
  description: string;
  purpose: string;
  problem: string;
  solution: string;
  targetUsers: string[];
  functionalDetails: string;
  features: string[];
  workflow: string;
  role: string;
  architecture: string;
  businessValue: string;
  challenges: string;
  category: string;
  techStack: string[];
  tags: string[];
  featuredImage: string | null;
  gallery: string[];
  liveUrl: string | null;
  gitHubUrl: string | null;
  videoUrl: string | null;
  videoEmbedUrl: string | null;
  displayOrder: number;
  featured: boolean;
  status: string;
};

type UnifiedProject = {
  slug: string;
  name: string;
  purpose: string;
  shortDesc: string;
  desc: string;
  category: string;
  tech: string[];
  features: string[];
  role: string;
  businessValue: string;
  image: string | null;
  icon: string;
  liveUrl: string | null;
  githubUrl: string | null;
  featured: boolean;
  displayOrder: number;
  kind: "portfolio" | "product";
  problem?: string;
  solution?: string;
  targetUsers?: string[];
};

function ProjectLinks({ p }: { p: UnifiedProject }) {
  const hasLive = !!p.liveUrl;
  const hasGh = !!p.githubUrl;
  return (
    <div className="rlz-project-links" style={{ gap: 12 }}>
      {hasLive && (
        <a href={p.liveUrl!} target="_blank" rel="noopener noreferrer" className="rlz-plink" onClick={(e) => e.stopPropagation()}>
          <i className="material-symbols-outlined">open_in_new</i> Live
        </a>
      )}
      {hasGh && (
        <a href={p.githubUrl!} target="_blank" rel="noopener noreferrer" className="rlz-plink" aria-label={`View ${p.name} GitHub`} onClick={(e) => e.stopPropagation()}>
          <i className="material-symbols-outlined">code</i> GitHub
        </a>
      )}
      {!hasLive && !hasGh && <span className="rlz-project-unavailable">Links unavailable</span>}
    </div>
  );
}

function mapFallback(p: Project, idx: number): UnifiedProject {
  return {
    slug: p.name.toLowerCase().replace(/\s+/g, "-"),
    name: p.name,
    purpose: p.desc.split("—")[0]?.trim() || p.desc.slice(0, 80),
    shortDesc: p.desc,
    desc: p.desc,
    category: p.chips[0] || "Project",
    tech: p.chips,
    features: [],
    role: "",
    businessValue: "",
    image: p.image || null,
    icon: p.icon,
    liveUrl: p.liveUrl ?? null,
    githubUrl: p.githubUrl ?? null,
    featured: !!p.featured,
    displayOrder: idx,
    kind: "portfolio",
  };
}

function mapCms(p: CmsPortfolio, kind: "portfolio" | "product"): UnifiedProject {
  const name = p.title;
  const purpose = p.purpose || p.shortDescription || p.description.slice(0, 120) || "";
  return {
    slug: p.slug,
    name,
    purpose,
    shortDesc: p.shortDescription || purpose,
    desc: p.description || p.shortDescription || "",
    category: p.category || (kind === "product" ? "Product" : "Project"),
    tech: (p.techStack || []).slice(0, 5),
    features: (p.features || []).slice(0, 3),
    role: p.role || "",
    businessValue: p.businessValue || "",
    image: p.featuredImage || (p.gallery && p.gallery[0]) || null,
    icon: "deployed_code",
    liveUrl: p.liveUrl || null,
    githubUrl: p.gitHubUrl || null,
    featured: !!p.featured,
    displayOrder: p.displayOrder ?? 0,
    kind,
    problem: p.problem,
    solution: p.solution,
    targetUsers: p.targetUsers,
  };
}

export default function RlzProjects() {
  const [cmsProjects, setCmsProjects] = useState<UnifiedProject[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
        const [portRes, prodRes, pubRes] = await Promise.all([
          fetch(`${base}/api/portfolio`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
          fetch(`${base}/api/products`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
          fetch(`${base}/api/public/projects`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
        ]);
        const port = Array.isArray(portRes) ? portRes as CmsPortfolio[] : [];
        const prod = Array.isArray(prodRes) ? prodRes as CmsPortfolio[] : [];
        const pub = Array.isArray(pubRes) ? (pubRes as unknown as CmsPortfolio[]) : [];
        // legacy pub projects already include enriched fields (purpose, tech etc) — map via same logic
        const legacy: CmsPortfolio[] = pub;
        const mappedPort = port.map((p) => mapCms(p, "portfolio"));
        const mappedProd = prod.map((p) => {
          // products have name field not title, normalize
          const anyP = p as unknown as { name?: string; title?: string; slug: string };
          const norm = { ...p, title: (anyP.name || anyP.title || p.title) } as CmsPortfolio;
          return mapCms(norm, "product");
        });
        const mappedLegacy = legacy.map((p: unknown) => {
          const d = p as {
            slug: string; title?: string; name?: string;
            short_description?: string; shortDescription?: string;
            full_description?: string; description?: string;
            purpose?: string; problem?: string; solution?: string;
            target_users?: string[]; functional_details?: string; workflow?: string;
            business_value?: string; businessValue?: string;
            role?: string; architecture?: string; challenges?: string;
            category?: string; features?: string[];
            techStack?: string[]; technologies?: string[]; tech_stack?: string[];
            featured_image?: string; featuredImage?: string; gallery?: string[]; screenshots?: string[];
            live_url?: string; liveUrl?: string; github_url?: string; gitHubUrl?: string;
            display_order?: number; displayOrder?: number; featured?: boolean; status?: string
          };
          const cat = (d.category || "").toLowerCase();
          const kind: "portfolio" | "product" = cat === "product" ? "product" : "portfolio";
          return {
            slug: d.slug,
            name: (d.title || d.name || d.slug) as string,
            purpose: d.purpose || d.short_description || d.shortDescription || (d.description || "").slice(0, 120),
            shortDesc: d.short_description || d.shortDescription || d.purpose || "",
            desc: d.full_description || d.description || "",
            category: d.category || (kind === "product" ? "Product" : "Project"),
            tech: (d.techStack || d.technologies || d.tech_stack || []).slice(0, 5),
            features: (d.features || []).slice(0, 3),
            role: d.role || "",
            businessValue: d.business_value || d.businessValue || "",
            image: d.featured_image || d.featuredImage || (d.gallery && d.gallery[0]) || (d.screenshots && d.screenshots[0]) || null,
            icon: "deployed_code",
            liveUrl: d.live_url || d.liveUrl || null,
            githubUrl: d.github_url || d.gitHubUrl || null,
            featured: !!d.featured,
            displayOrder: d.display_order ?? d.displayOrder ?? 0,
            kind,
          } as UnifiedProject;
        });
        const all = [...mappedPort, ...mappedProd, ...mappedLegacy];
        // dedupe by slug
        const seen = new Map<string, UnifiedProject>();
        for (const p of all) {
          if (!seen.has(p.slug)) seen.set(p.slug, p);
        }
        const merged = Array.from(seen.values());
        // sort featured first then displayOrder
        merged.sort((a, b) => {
          if (a.featured && !b.featured) return -1;
          if (!a.featured && b.featured) return 1;
          return (a.displayOrder || 0) - (b.displayOrder || 0);
        });
        // if nothing, keep null to show fallback
        if (alive) {
          if (merged.length > 0) setCmsProjects(merged);
          else setCmsProjects(null);
        }
      } catch {
        if (alive) setCmsProjects(null);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const projectsToShow: UnifiedProject[] =
    cmsProjects && cmsProjects.length > 0
      ? cmsProjects
      : PROJECTS.map(mapFallback);

  return (
    <section id="projects" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag">
            <i className="material-symbols-outlined">rocket_launch</i> SHIPPED_SYSTEMS
          </div>
          <h2 className="rlz-section-title">
            Featured <span className="rlz-grad-text">Projects</span>
          </h2>
          <p className="rlz-section-desc">
            Real products solving real problems — each one production-grade and built around intelligence. Click any project for the full case study.
          </p>
        </div>

        <div className="rlz-projects-grid">
          {loading && !cmsProjects ? (
            // skeleton
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="rlz-project-card rlz-reveal" style={{ opacity: 0.6 }}>
                <div className="rlz-project-media" style={{ background: "var(--rlz-bg)" }}>
                  <div className="rlz-media-fallback" style={{ minHeight: 240 }}>
                    <i className="material-symbols-outlined">hourglass_empty</i>
                  </div>
                </div>
                <div className="rlz-project-body">
                  <div className="rlz-chip-row" style={{ height: 18 }} />
                  <h3 style={{ background: "var(--rlz-bg-2)", height: 20, width: "70%", borderRadius: 8 }} />
                  <p style={{ background: "var(--rlz-bg-2)", height: 14, borderRadius: 6 }} />
                </div>
              </div>
            ))
          ) : (
            projectsToShow.map((p, i) => {
              const href = p.kind === "product" ? `/products/${p.slug}` : `/portfolio/${p.slug}`;
              const num = String(i + 1).padStart(2, "0");
              return (
                <div
                  key={p.slug}
                  role="link"
                  tabIndex={0}
                  onClick={() => (window.location.href = href)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") window.location.href = href;
                  }}
                  className={`rlz-project-card${p.featured ? " rlz-featured" : ""} rlz-reveal${i % 2 === 1 ? " rlz-reveal-d1" : ""}`}
                  style={{ textDecoration: "none", color: "inherit", cursor: "pointer" }}
                >
                  <div className="rlz-project-media">
                    <span className="rlz-project-num">{num} / {p.category.toUpperCase()}</span>
                    {p.image ? (
                      <img src={p.image} alt={`${p.name} screenshot`} loading="lazy" decoding="async" />
                    ) : (
                      <div className="rlz-media-fallback" role="img" aria-label={`${p.name} illustration`}>
                        <i className="material-symbols-outlined">{p.icon}</i>
                      </div>
                    )}
                  </div>
                  <div className="rlz-project-body">
                    <div className="rlz-chip-row" style={{ margin: "0 0 10px" }}>
                      {p.featured && <span className="rlz-chip" style={{ background: "var(--rlz-violet)", color: "#fff" }}>Featured</span>}
                      <span className="rlz-chip" style={{ background: "var(--rlz-bg-2)", border: "1px solid var(--rlz-border)" }}>{p.category}</span>
                      {p.tech.slice(0, 3).map((c) => (
                        <span className="rlz-chip" key={c}>{c}</span>
                      ))}
                    </div>
                    <h3>
                      {p.liveUrl ? <span className="rlz-live-dot" aria-label="Live" /> : null} {p.name}
                    </h3>
                    {p.purpose && (
                      <p style={{ fontWeight: 600, color: "var(--rlz-text)", fontSize: "0.9rem", marginBottom: 8 }}>{p.purpose}</p>
                    )}
                    <p style={{ display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden", minHeight: 44 }}>
                      {p.shortDesc || p.desc.slice(0, 140)}
                    </p>
                    {!!p.features.length && (
                      <ul style={{ margin: "12px 0 0", padding: 0, listStyle: "none", display: "grid", gap: 6 }}>
                        {p.features.map((f) => (
                          <li key={f} style={{ display: "flex", gap: 8, fontSize: "0.82rem", color: "var(--rlz-text-dim)" }}>
                            <i className="material-symbols-outlined" style={{ fontSize: "1rem", color: "var(--rlz-violet)" }}>check_circle</i>
                            <span style={{ display: "-webkit-box", WebkitLineClamp: 1, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{f}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 18, gap: 12 }}>
                      <a
                        href={href}
                        onClick={(e) => e.stopPropagation()}
                        className="rlz-plink"
                        style={{ fontWeight: 700, color: "var(--rlz-violet)", textDecoration: "none" }}
                      >
                        View Case Study <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_forward</i>
                      </a>
                      <span onClick={(e) => e.stopPropagation()} style={{ display: "flex", gap: 10 }}>
                        <ProjectLinks p={p} />
                      </span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
        {cmsProjects && cmsProjects.length === 0 && (
          <p className="rlz-section-desc" style={{ marginTop: 20, textAlign: "center" }}>
            No published projects yet — add one in <a href="/admin/portfolio">Admin → Portfolio</a>.
          </p>
        )}
      </div>
    </section>
  );
}
