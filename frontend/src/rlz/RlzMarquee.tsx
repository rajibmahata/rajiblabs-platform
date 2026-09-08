import { MARQUEE_TECH } from "./data";

// Rendered twice in JSX (instead of innerHTML self-duplication) for the
// seamless -50% marquee loop — React-owned DOM only.
const LOOP = [...MARQUEE_TECH, ...MARQUEE_TECH];

export default function RlzMarquee() {
  return (
    <div className="rlz-marquee-section" aria-label="Technology stack">
      <div className="rlz-marquee">
        {LOOP.map((t, i) => (
          <span className="rlz-marquee-item" key={`${t.name}-${i}`} aria-hidden={i >= MARQUEE_TECH.length}>
            <i className="material-symbols-outlined">{t.icon}</i> {t.name}
          </span>
        ))}
      </div>
    </div>
  );
}
