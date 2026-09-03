import { DEMOS } from "./data";

export default function RlzDemos() {
  return (
    <section id="demos" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag"><i className="material-symbols-outlined">play_circle</i> WATCH_IT_WORK</div>
          <h2 className="rlz-section-title">Live Product <span className="rlz-grad-text">Demos</span></h2>
          <p className="rlz-section-desc">Full walkthroughs of ARIA and DocuSign Hub in action — see the systems, not just the slides.</p>
        </div>

        <div className="rlz-demo-grid">
          {DEMOS.map((d, i) => (
            <div className={`rlz-demo-card rlz-reveal${i === 1 ? " rlz-reveal-d1" : ""}`} key={d.title}>
              <div className="rlz-video-wrap">
                <iframe
                  src={`https://www.youtube.com/embed/${d.videoId}`}
                  title={d.title}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  loading="lazy"
                />
              </div>
              <div className="rlz-demo-body">
                <h3>{d.title}</h3>
                <p>{d.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
