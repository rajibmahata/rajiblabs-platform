import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import RlzHeader from "../rlz/RlzHeader";
import "../rlz/rlz.css";

type LearningPath = {
  slug: string;
  topic: string;
  duration: number;
  goal?: string;
  level?: string;
  progress?: number;
  status: string;
  current_day?: number;
  roadmap?: { day: number; title: string; objective: string }[];
};

type ActiveData = {
  active: boolean;
  path?: LearningPath;
  progress?: number;
};

export default function Learning() {
  const [paths, setPaths] = useState<LearningPath[]>([]);
  const [active, setActive] = useState<ActiveData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
    Promise.all([
      fetch(`${base}/api/learning/paths`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
      fetch(`${base}/api/learning/active`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ])
      .then(([pathsRes, activeRes]) => {
        setPaths(Array.isArray(pathsRes) ? pathsRes : []);
        if (activeRes && activeRes.active) setActive(activeRes);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, []);

  const LEVEL_COLORS: Record<string, { bg: string; fg: string }> = {
    beginner: { bg: "rgba(16,185,129,0.1)", fg: "var(--rlz-green)" },
    intermediate: { bg: "var(--rlz-violet-soft)", fg: "var(--rlz-violet)" },
    advanced: { bg: "rgba(217,119,6,0.1)", fg: "var(--rlz-amber)" },
  };

  return (
    <div className="rlz" style={{ background: "var(--rlz-bg)", minHeight: "100vh" }}>
      <div className="rlz-page-bg" />
      <div className="rlz-bg-grid" />

      <RlzHeader crumbs={[{ label: "Home", to: "/" }, { label: "Learning" }]} />

      {/* Hero */}
      <section className="rlz-ld-hero">
        <div className="rlz-container">
          <div className="rlz-section-tag">
            <i className="material-symbols-outlined">school</i> LEARNING
          </div>
          <h1 style={{ fontFamily: "'Sora', sans-serif", fontSize: "clamp(2rem, 4.5vw, 3.2rem)", letterSpacing: "-0.02em" }}>
            Guided Learning Paths
          </h1>
          <p style={{ color: "var(--rlz-text-dim)", maxWidth: 680, marginTop: 8, fontSize: "1.05rem" }}>
            Mentor-guided progression — one day at a time, with prerequisites, examples and homework. You define Topic + Duration, the agent builds the rest.
          </p>
        </div>
      </section>

      {/* Active path banner */}
      <div className="rlz-container" style={{ paddingBottom: 40, display: "grid", gap: 22 }}>
        {active && active.path && (
          <Link
            to={`/learning/${active.path.slug}`}
            className="rlz-learning-active-card"
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <div className="rlz-learning-active-inner">
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                <span className="rlz-pulse-dot" />
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", color: "var(--rlz-green)", fontWeight: 600, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Continue Learning</span>
              </div>
              <h3 style={{ fontFamily: "'Sora', sans-serif", fontSize: "1.35rem", margin: "0 0 4px" }}>{active.path.topic}</h3>
              <p style={{ color: "var(--rlz-text-dim)", fontSize: "0.9rem", margin: 0 }}>
                Day {active.path.current_day || 0} of {active.path.duration} — {active.progress || active.path.progress || 0}% complete
              </p>
              <div className="rlz-learning-progress-track" style={{ maxWidth: 400, marginTop: 10 }}>
                <div className="rlz-learning-progress-fill" style={{ width: `${active.progress || active.path.progress || 0}%` }} />
              </div>
              <span className="rlz-btn rlz-btn-primary" style={{ marginTop: 14, display: "inline-flex", alignSelf: "flex-start" }}>
                Continue → Day {(active.path.current_day || 0) + 1} <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_forward</i>
              </span>
            </div>
          </Link>
        )}

        {/* Paths grid */}
        <section>
          <h2 style={{ fontFamily: "'Sora', sans-serif", fontSize: "1.4rem" }}>Available Learning Paths</h2>

          {loading && (
            <div className="rlz-learning-grid" style={{ marginTop: 14 }}>
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="rlz-learning-card" style={{ opacity: 0.5, pointerEvents: "none" }}>
                  <div className="rlz-learning-card-top">
                    <span className="rlz-chip" style={{ width: 70, height: 22, borderRadius: 100 }} />
                    <span className="rlz-chip" style={{ width: 80, height: 22, borderRadius: 100 }} />
                  </div>
                  <div style={{ marginTop: 14, height: 20, width: "70%", background: "var(--rlz-bg-2)", borderRadius: 8 }} />
                  <div style={{ marginTop: 8, height: 14, width: "100%", background: "var(--rlz-bg-2)", borderRadius: 6 }} />
                  <div style={{ marginTop: 6, height: 14, width: "80%", background: "var(--rlz-bg-2)", borderRadius: 6 }} />
                </div>
              ))}
            </div>
          )}

          {error && (
            <div style={{ padding: 20, background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 14, marginTop: 12 }}>
              <p style={{ color: "#dc2626", fontSize: "0.9rem", margin: 0 }}>Unable to load learning paths. Please try again later.</p>
            </div>
          )}

          {!loading && !error && paths.length === 0 && (
            <div className="rlz-ld-empty" style={{ marginTop: 12 }}>
              <i className="material-symbols-outlined">school</i>
              <p>No published paths yet — check back after the agent run at 06:30 IST.</p>
            </div>
          )}

          {!loading && !error && paths.length > 0 && (
            <div className="rlz-learning-grid">
              {paths.map((p, i) => {
                const lc = LEVEL_COLORS[p.level || ""] || LEVEL_COLORS.beginner;
                return (
                  <Link
                    key={p.slug}
                    to={`/learning/${p.slug}`}
                    className="rlz-learning-card rlz-reveal"
                    style={{ textDecoration: "none", color: "inherit", transitionDelay: `${i * 0.06}s` }}
                  >
                    <div className="rlz-learning-card-top">
                      <span className="rlz-chip" style={{ background: lc.bg, color: lc.fg, border: "none", fontWeight: 600 }}>
                        {p.level || "Beginner"}
                      </span>
                      <span className="rlz-chip" style={{ background: "var(--rlz-bg-2)", border: "1px solid var(--rlz-border)" }}>
                        <i className="material-symbols-outlined" style={{ fontSize: "0.85rem", marginRight: 2 }}>schedule</i>
                        {p.duration} Days
                      </span>
                    </div>

                    <h3 style={{ fontFamily: "'Sora', sans-serif", fontSize: "1.2rem", margin: "14px 0 6px" }}>{p.topic}</h3>
                    <p style={{ color: "var(--rlz-text-dim)", fontSize: "0.88rem", margin: 0, lineHeight: 1.55 }}>
                      {p.goal || "Practical understanding through daily mentor-guided lessons."}
                    </p>

                    {p.roadmap && p.roadmap.length > 0 && (
                      <div className="rlz-learning-roadmap-preview">
                        {p.roadmap.slice(0, 3).map((r) => (
                          <div key={r.day} className="rlz-learning-roadmap-item">
                            <span className="rlz-learning-roadmap-day">Day {r.day}</span>
                            <span className="rlz-learning-roadmap-title">{r.title}</span>
                          </div>
                        ))}
                        {p.roadmap.length > 3 && (
                          <div className="rlz-learning-roadmap-more">+{p.roadmap.length - 3} more days</div>
                        )}
                      </div>
                    )}

                    <div className="rlz-learning-card-footer">
                      <div className="rlz-learning-progress-track" style={{ flex: 1 }}>
                        <div className="rlz-learning-progress-fill" style={{ width: `${p.progress || 0}%` }} />
                      </div>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", color: "var(--rlz-text-faint)", whiteSpace: "nowrap" }}>
                        {p.progress || 0}%
                      </span>
                    </div>

                    <div className="rlz-learning-cta">
                      Start Learning <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_forward</i>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
