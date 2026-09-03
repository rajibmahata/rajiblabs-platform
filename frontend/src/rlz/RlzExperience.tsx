import { EXPERIENCE } from "./data";

const DELAYS = ["", " rlz-reveal-d1", " rlz-reveal-d2"];

export default function RlzExperience() {
  return (
    <section id="experience" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag"><i className="material-symbols-outlined">route</i> CAREER_PATH</div>
          <h2 className="rlz-section-title">Professional <span className="rlz-grad-text">Experience</span></h2>
          <p className="rlz-section-desc">Twelve years of building, scaling and leading enterprise software systems.</p>
        </div>

        <div className="rlz-xp-list">
          {EXPERIENCE.map((x, i) => (
            <div className={`rlz-xp-item rlz-reveal${DELAYS[i % DELAYS.length]}`} key={x.title}>
              <div className="rlz-xp-date">{x.date}</div>
              <div>
                <h3>{x.title}</h3>
                <div className="rlz-xp-org">{x.org}</div>
                <p>{x.desc}</p>
                <div className="rlz-xp-tags">
                  {x.tags.map((t) => <span className="rlz-chip" key={t}>{t}</span>)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
