import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

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

export default function RlzLearning() {
  const [paths, setPaths] = useState<LearningPath[]>([]);
  const [active, setActive] = useState<{ active: boolean; path?: LearningPath; progress?: number } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
    Promise.all([
      fetch(`${base}/api/learning/paths`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
      fetch(`${base}/api/learning/active`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ]).then(([pathsRes, activeRes]) => {
      if (Array.isArray(pathsRes)) setPaths(pathsRes);
      if (activeRes && activeRes.active) setActive(activeRes);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <section id="learning" className="rlz-section">
        <div className="rlz-container">
          <div className="rlz-center">
            <p style={{ color: "var(--rlz-text-faint)" }}>Loading learning paths…</p>
          </div>
        </div>
      </section>
    );
  }

  if (paths.length === 0) return null;

  const LEVEL_COLORS: Record<string, string> = {
    beginner: "var(--rlz-green)",
    intermediate: "var(--rlz-violet)",
    advanced: "var(--rlz-amber)",
  };

  return (
    <section id="learning" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag">
            <i className="material-symbols-outlined">school</i> GUIDED_LEARNING
          </div>
          <h2 className="rlz-section-title">
            Learn <span className="rlz-grad-text">by Building</span>
          </h2>
          <p className="rlz-section-desc">
            Mentor-guided paths — one day at a time, with prerequisites, examples and homework. You define the topic, the agent builds the rest.
          </p>
        </div>

        {active && active.path && (
          <Link
            to={`/learning/${active.path.slug}`}
            className="rlz-learning-active-card rlz-reveal"
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <div className="rlz-learning-active-inner">
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                <span className="rlz-pulse-dot" />
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", color: "var(--rlz-green)", fontWeight: 600, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Continue Learning</span>
              </div>
              <h3 style={{ fontFamily: "'Sora', sans-serif", fontSize: "1.35rem", margin: "0 0 4px" }}>{active.path.topic}</h3>
              <p style={{ color: "var(--rlz-text-dim)", fontSize: "0.9rem", margin: 0 }}>Day {active.path.current_day || 0} of {active.path.duration} — {active.progress || active.path.progress || 0}% complete</p>
              <div className="rlz-learning-progress-track">
                <div className="rlz-learning-progress-fill" style={{ width: `${active.progress || active.path.progress || 0}%` }} />
              </div>
              <span className="rlz-btn rlz-btn-primary" style={{ marginTop: 14, display: "inline-flex", alignSelf: "flex-start" }}>
                Continue → Day {(active.path.current_day || 0) + 1} <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_forward</i>
              </span>
            </div>
          </Link>
        )}

        <div className="rlz-learning-grid">
          {paths.map((p, i) => (
            <Link
              key={p.slug}
              to={`/learning/${p.slug}`}
              className="rlz-learning-card rlz-reveal"
              style={{ textDecoration: "none", color: "inherit", transitionDelay: `${i * 0.06}s` }}
            >
              <div className="rlz-learning-card-top">
                <span className="rlz-chip" style={{ background: LEVEL_COLORS[p.level || ""] || "var(--rlz-violet-soft)", color: LEVEL_COLORS[p.level || ""] || "var(--rlz-violet)", border: "none", fontWeight: 600 }}>
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
          ))}
        </div>

        <div className="rlz-center" style={{ marginTop: 22 }}>
          <Link to="/learning" className="rlz-btn rlz-btn-ghost" style={{ textDecoration: "none", display: "inline-flex" }}>
            View all learning paths <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_forward</i>
          </Link>
        </div>
      </div>
    </section>
  );
}
