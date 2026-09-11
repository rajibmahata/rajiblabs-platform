import { useEffect, useState } from "react";

type Product = {
  slug: string;
  name: string;
  category?: string;
  short_description?: string;
  shortDescription?: string;
  description?: string;
  technologies?: string[];
  techStack?: string[];
  features?: string[];
  live_url?: string | null;
  liveUrl?: string | null;
  github_url?: string | null;
  gitHubUrl?: string | null;
  display_order?: number;
  displayOrder?: number;
  featured?: boolean;
  status?: string;
  published?: boolean;
};

type UnifiedProduct = {
  slug: string;
  name: string;
  desc: string;
  category: string;
  tech: string[];
  features: string[];
  liveUrl: string | null;
  githubUrl: string | null;
  displayOrder: number;
  featured: boolean;
};

function mapProduct(p: Product): UnifiedProduct {
  const name = p.name || p.slug;
  const short = p.short_description || p.shortDescription || p.description || "";
  const tech = (p.technologies || p.techStack || []).slice(0, 4);
  return {
    slug: p.slug,
    name,
    desc: short,
    category: p.category || "Product",
    tech,
    features: (p.features || []).slice(0, 3),
    liveUrl: p.live_url || p.liveUrl || null,
    githubUrl: p.github_url || p.gitHubUrl || null,
    displayOrder: p.display_order ?? p.displayOrder ?? 0,
    featured: !!p.featured,
  };
}

export default function RlzProducts() {
  const [products, setProducts] = useState<UnifiedProduct[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
        // Public product grid: prefer /api/public/products (projects.category==product), fallback to /api/products (legacy)
        const [pubRes, legacyRes] = await Promise.all([
          fetch(`${base}/api/public/products`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
          fetch(`${base}/api/products`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
        ]);
        const pub = Array.isArray(pubRes) ? (pubRes as Product[]) : [];
        const leg = Array.isArray(legacyRes) ? (legacyRes as Product[]) : [];
        // Merge, dedupe by slug, prefer public (projects) over legacy
        const seen = new Map<string, UnifiedProduct>();
        for (const p of pub) {
          const m = mapProduct(p);
          if (!seen.has(m.slug)) seen.set(m.slug, m);
        }
        for (const p of leg) {
          const m = mapProduct(p);
          if (!seen.has(m.slug)) seen.set(m.slug, m);
        }
        const merged = Array.from(seen.values());
        // Only published products, sort by displayOrder
        const filtered = merged.filter((p) => p.slug);
        filtered.sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
        if (alive) {
          if (filtered.length > 0) setProducts(filtered);
          else setProducts([]);
        }
      } catch {
        if (alive) setProducts([]);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  // Empty-state only when genuinely no active products
  if (!loading && products && products.length === 0) {
    return (
      <section id="products" className="rlz-section">
        <div className="rlz-container">
          <div className="rlz-center">
            <div className="rlz-section-tag">
              <i className="material-symbols-outlined">inventory_2</i> PRODUCTS
            </div>
            <h2 className="rlz-section-title">
              Products <span className="rlz-grad-text">Built</span>
            </h2>
            <p className="rlz-section-desc">No products published yet — check back soon.</p>
          </div>
        </div>
      </section>
    );
  }

  const toShow = products && products.length > 0 ? products : null;
  if (!toShow) return null;

  return (
    <section id="products" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag">
            <i className="material-symbols-outlined">inventory_2</i> PRODUCTS
          </div>
          <h2 className="rlz-section-title">
            Products <span className="rlz-grad-text">Built</span>
          </h2>
          <p className="rlz-section-desc">
            Five products — from pest-control operations to AI knowledge and the RajibLabs platform itself — each live or linked with verified sources.
          </p>
        </div>

        <div className="rlz-projects-grid" style={{ marginTop: 28 }}>
          {loading && !products ? (
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="rlz-project-card" style={{ opacity: 0.6 }}>
                <div className="rlz-project-media" style={{ background: "var(--rlz-bg)" }}>
                  <div className="rlz-media-fallback" style={{ minHeight: 180 }}>
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
            toShow.slice(0, 5).map((p, i) => {
              const href = `/products/${p.slug}`;
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
                    <span className="rlz-project-num">
                      {num} / {p.category.toUpperCase()}
                    </span>
                    <div className="rlz-media-fallback" role="img" aria-label={`${p.name} illustration`}>
                      <i className="material-symbols-outlined">deployed_code</i>
                    </div>
                  </div>
                  <div className="rlz-project-body">
                    <div className="rlz-chip-row" style={{ margin: "0 0 10px" }}>
                      {p.featured && <span className="rlz-chip" style={{ background: "var(--rla-violet)", color: "#fff" }}>Featured</span>}
                      <span className="rlz-chip" style={{ background: p.liveUrl ? "rgba(16,185,129,0.12)" : "var(--rlz-bg-2)", border: "1px solid var(--rlz-border)", color: p.liveUrl ? "var(--rlz-green)" : undefined }}>
                        {p.liveUrl ? "● Live" : "Published"}
                      </span>
                      <span className="rlz-chip" style={{ background: "var(--rlz-bg-2)", border: "1px solid var(--rlz-border)" }}>{p.category}</span>
                      {p.tech.slice(0, 2).map((c) => (
                        <span className="rlz-chip" key={c}>
                          {c}
                        </span>
                      ))}
                    </div>
                    <h3>{p.name}</h3>
                    <p style={{ display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden", minHeight: 44 }}>{p.desc}</p>
                    {!!p.features.length && (
                      <ul style={{ margin: "10px 0 0", padding: 0, listStyle: "none", display: "grid", gap: 6 }}>
                        {p.features.slice(0, 2).map((f) => (
                          <li key={f} style={{ display: "flex", gap: 8, fontSize: "0.82rem", color: "var(--rlz-text-dim)" }}>
                            <i className="material-symbols-outlined" style={{ fontSize: "1rem", color: "var(--rla-violet)" }}>check_circle</i>
                            <span style={{ display: "-webkit-box", WebkitLineClamp: 1, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{f}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 16, gap: 12 }}>
                      <a
                        href={href}
                        onClick={(e) => e.stopPropagation()}
                        className="rlz-plink"
                        style={{ fontWeight: 700, color: "var(--rla-violet)", textDecoration: "none" }}
                      >
                        View Product <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_forward</i>
                      </a>
                      <span style={{ display: "flex", gap: 8 }}>
                        {p.liveUrl && (
                          <a href={p.liveUrl} target="_blank" rel="noopener noreferrer" className="rlz-plink" onClick={(e) => e.stopPropagation()}>
                            <i className="material-symbols-outlined">open_in_new</i> Live
                          </a>
                        )}
                        {p.githubUrl && (
                          <a href={p.githubUrl} target="_blank" rel="noopener noreferrer" className="rlz-plink" onClick={(e) => e.stopPropagation()}>
                            <i className="material-symbols-outlined">code</i> Code
                          </a>
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </section>
  );
}
