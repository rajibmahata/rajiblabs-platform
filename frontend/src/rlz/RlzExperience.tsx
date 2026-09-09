import { useEffect, useState } from "react";
import { EXPERIENCE, type Xp } from "./data";

const DELAYS = ["", " rlz-reveal-d1", " rlz-reveal-d2"];

type CareerEntry = {
  company?: string; role?: string; period?: string; client?: string;
  description?: string; achievements?: string[]; tech_stack?: string[]; technologies?: string[];
};

function mapCareer(career: CareerEntry[]): Xp[] {
  return career.map((c) => ({
    date: c.period || "",
    title: c.role || "",
    org: [c.company, c.client].filter(Boolean).join(" · "),
    desc: c.description || (c.achievements || [])[0] || "",
    tags: (c.tech_stack || c.technologies || []).slice(0, 4),
  }));
}

export default function RlzExperience() {
  const [items, setItems] = useState<Xp[]>(EXPERIENCE);

  useEffect(() => {
    fetch("/api/profile")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        const career: CareerEntry[] = Array.isArray(d?.career) ? d.career : [];
        if (career.length) setItems(mapCareer(career));
      })
      .catch(() => {});
  }, []);

  return (
    <section id="experience" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag"><i className="material-symbols-outlined">route</i> CAREER_PATH</div>
          <h2 className="rlz-section-title">Professional <span className="rlz-grad-text">Experience</span></h2>
          <p className="rlz-section-desc">Twelve years of building, scaling and leading enterprise software systems.</p>
        </div>

        <div className="rlz-xp-list">
          {items.map((x, i) => (
            <div className={`rlz-xp-item rlz-reveal${DELAYS[i % DELAYS.length]}`} key={`${x.title}-${i}`}>
              <div className="rlz-xp-date">{x.date}</div>
              <div>
                <h3>{x.title}</h3>
                <div className="rlz-xp-org">{x.org}</div>
                <p>{x.desc}</p>
                {!!x.tags.length && (
                  <div className="rlz-xp-tags">
                    {x.tags.map((t) => <span className="rlz-chip" key={t}>{t}</span>)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
