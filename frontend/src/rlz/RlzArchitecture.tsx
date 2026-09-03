import { Fragment } from "react";
import { ARCH_LAYERS } from "./data";

export default function RlzArchitecture() {
  return (
    <section id="architecture" className="rlz-section" style={{ paddingTop: 0 }}>
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag"><i className="material-symbols-outlined">account_tree</i> SYSTEM_DESIGN</div>
          <h2 className="rlz-section-title">How I <span className="rlz-grad-text">Architect</span> Intelligent Systems</h2>
          <p className="rlz-section-desc">A layered, AI-native reference architecture — every layer independently scalable, observable and secure.</p>
        </div>

        <div className="rlz-arch-flow rlz-reveal rlz-reveal-d1">
          <div className="rlz-arch-layers">
            {ARCH_LAYERS.map((layer, i) => (
              <Fragment key={layer.title}>
                {i > 0 && <div className="rlz-flow-connector" aria-hidden="true" />}
                <div className="rlz-arch-node">
                  <div className={`rlz-node-icon ${layer.iconClass}`}><i className="material-symbols-outlined">{layer.icon}</i></div>
                  <div><h4>{layer.title}</h4><p>{layer.desc}</p></div>
                  <span className="rlz-node-tag">{layer.tag}</span>
                </div>
              </Fragment>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
