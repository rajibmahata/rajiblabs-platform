import { useEffect, useRef } from "react";
import { MARQUEE_TECH } from "./data";

export default function RlzMarquee() {
  const trackRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Duplicate content once for a seamless -50% loop (guard StrictMode double-run).
    const track = trackRef.current;
    if (track && !track.dataset.doubled) {
      track.dataset.doubled = "1";
      track.innerHTML += track.innerHTML;
    }
  }, []);

  return (
    <div className="rlz-marquee-section" aria-label="Technology stack">
      <div className="rlz-marquee" ref={trackRef}>
        {MARQUEE_TECH.map((t) => (
          <span className="rlz-marquee-item" key={t.name}>
            <i className="material-symbols-outlined">{t.icon}</i> {t.name}
          </span>
        ))}
      </div>
    </div>
  );
}
