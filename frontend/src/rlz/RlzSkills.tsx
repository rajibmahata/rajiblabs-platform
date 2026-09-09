import { useEffect, useState } from "react";

type Skill = {
  id: string;
  name: string;
  slug: string;
  category: string;
  display_order: number;
  status: string;
};

export default function RlzSkills() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/public/skills")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        if (Array.isArray(data)) setSkills(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <section id="skills" className="rlz-section">
        <div className="rlz-container">
          <div className="rlz-center">
            <p style={{ color: "var(--rlz-text-faint)" }}>Loading skills…</p>
          </div>
        </div>
      </section>
    );
  }

  if (skills.length === 0) return null;

  // Group by category, preserve display_order within category
  const grouped = skills.reduce((acc: Record<string, Skill[]>, s) => {
    const cat = s.category || "Other";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(s);
    return acc;
  }, {});

  // Sort categories by first appearance order (display_order of first skill)
  const sortedCats = Object.entries(grouped).sort((a, b) => {
    const aOrder = Math.min(...a[1].map((s) => s.display_order));
    const bOrder = Math.min(...b[1].map((s) => s.display_order));
    return aOrder - bOrder;
  });

  return (
    <section id="skills" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag">
            <i className="material-symbols-outlined">code</i> TECHNICAL ARSENAL
          </div>
          <h2 className="rlz-section-title">
            Skills <span className="rlz-grad-text">in Production</span>
          </h2>
          <p className="rlz-section-desc">
            Every skill backed by shipped code — projects, GitHub, and resume evidence. No keywords, no invention.
          </p>
        </div>

        <div style={{ marginTop: 40, display: "grid", gap: 24 }}>
          {sortedCats.map(([category, list]) => (
            <div
              key={category}
              className="rlz-bento-card"
              style={{ padding: 28, gridColumn: "span 12" } as React.CSSProperties}
            >
              <h3 style={{ fontSize: "1.05rem", marginBottom: 4, color: "var(--rlz-text)" }}>{category}</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--rlz-text-faint)", marginBottom: 14 }}>
                {list.length} {list.length === 1 ? "skill" : "skills"} · evidence-backed
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {list.map((s) => (
                  <span
                    key={s.id}
                    className="rlz-chip"
                    title={`${s.name} — ${s.category}`}
                    style={{ fontSize: "0.85rem", padding: "6px 14px" }}
                  >
                    {s.name}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
