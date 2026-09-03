import { useRef } from "react";
import { EXPERTISE } from "./data";

export default function RlzExpertise() {
  const gridRef = useRef<HTMLDivElement | null>(null);

  const onMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = (e.target as HTMLElement).closest(".rlz-bento-card") as HTMLElement | null;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    card.style.setProperty("--rlz-mx", `${e.clientX - rect.left}px`);
    card.style.setProperty("--rlz-my", `${e.clientY - rect.top}px`);
  };

  return (
    <section id="expertise" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag"><i className="material-symbols-outlined">auto_awesome</i> CORE_CAPABILITIES</div>
          <h2 className="rlz-section-title">Intelligence by <span className="rlz-grad-text">Design</span></h2>
          <p className="rlz-section-desc">Deep expertise across the full intelligent-systems stack — from enterprise backends to production AI.</p>
        </div>

        <div className="rlz-bento" ref={gridRef} onMouseMove={onMouseMove}>
          {EXPERTISE.map((c, i) => (
            <div className={`rlz-bento-card ${c.span} rlz-reveal${i % 3 === 1 ? " rlz-reveal-d1" : i % 3 === 2 ? " rlz-reveal-d2" : ""}`} key={c.title}>
              <div className={`rlz-bento-icon ${c.iconClass}`}><i className="material-symbols-outlined">{c.icon}</i></div>
              <h3>{c.title}</h3>
              <p>{c.desc}</p>
              <div className="rlz-chip-row">
                {c.chips.map((chip) => <span className="rlz-chip" key={chip}>{chip}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
