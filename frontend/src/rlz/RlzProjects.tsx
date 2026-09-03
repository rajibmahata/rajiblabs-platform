import { PROJECTS, type Project } from "./data";

function ProjectLinks({ p }: { p: Project }) {
  return (
    <div className="rlz-project-links">
      {p.liveUrl ? (
        <a href={p.liveUrl} target="_blank" rel="noopener noreferrer" className="rlz-plink">
          <i className="material-symbols-outlined">open_in_new</i> Live Site
        </a>
      ) : null}
      {p.githubUrl ? (
        <a href={p.githubUrl} target="_blank" rel="noopener noreferrer" className="rlz-plink" aria-label={`View ${p.name} GitHub repository`}>
          <i className="material-symbols-outlined">code</i> GitHub
        </a>
      ) : null}
      {!p.liveUrl && !p.githubUrl ? (
        <span className="rlz-project-unavailable">GitHub repository unavailable</span>
      ) : null}
    </div>
  );
}

export default function RlzProjects() {
  return (
    <section id="projects" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag"><i className="material-symbols-outlined">rocket_launch</i> SHIPPED_SYSTEMS</div>
          <h2 className="rlz-section-title">Featured <span className="rlz-grad-text">Projects</span></h2>
          <p className="rlz-section-desc">Real products solving real problems — each one production-grade and built around intelligence.</p>
        </div>

        <div className="rlz-projects-grid">
          {PROJECTS.map((p, i) => (
            <div className={`rlz-project-card${p.featured ? " rlz-featured" : ""} rlz-reveal${i % 2 === 1 ? " rlz-reveal-d1" : ""}`} key={p.name}>
              <div className="rlz-project-media">
                <span className="rlz-project-num">{p.num}</span>
                {p.image ? (
                  <img src={p.image} alt={`${p.name} platform screenshot`} loading="lazy" />
                ) : (
                  <div className="rlz-media-fallback" role="img" aria-label={`${p.name} illustration`}>
                    <i className="material-symbols-outlined">{p.icon}</i>
                  </div>
                )}
              </div>
              <div className="rlz-project-body">
                <div className="rlz-chip-row" style={{ margin: "0 0 14px" }}>
                  {p.chips.map((c) => <span className="rlz-chip" key={c}>{c}</span>)}
                </div>
                <h3>{p.live ? <span className="rlz-live-dot" aria-label="Live" /> : null} {p.name}</h3>
                <p>{p.desc}</p>
                <ProjectLinks p={p} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
