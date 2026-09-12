import { Link } from "react-router-dom";

/**
 * Lightweight header for standalone pages (Learning, etc.).
 * Reuses .rlz-nav styling from RlzNav for visual consistency.
 * Shows: Logo/Home + optional breadcrumb trail.
 */
export default function RlzHeader({ crumbs }: { crumbs?: { label: string; to?: string }[] }) {
  return (
    <header className="rlz-nav rlz-scrolled" style={{ position: "sticky", top: 0, zIndex: 1000 }}>
      <Link to="/" className="rlz-logo">
        <span className="rlz-logo-mark"><i className="material-symbols-outlined">memory</i></span>
        Rajib<span><em>Labs</em></span>
      </Link>
      {crumbs && crumbs.length > 0 && (
        <nav style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.88rem" }}>
          {crumbs.map((c, i) => (
            <span key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ color: "var(--rlz-text-faint)" }}>/</span>
              {c.to ? (
                <Link to={c.to} style={{ color: "var(--rlz-text-dim)", textDecoration: "none", fontWeight: 500, padding: "4px 8px", borderRadius: 6, transition: "color 0.2s" }}>
                  {c.label}
                </Link>
              ) : (
                <span style={{ color: "var(--rlz-text)", fontWeight: 600 }}>{c.label}</span>
              )}
            </span>
          ))}
        </nav>
      )}
    </header>
  );
}
