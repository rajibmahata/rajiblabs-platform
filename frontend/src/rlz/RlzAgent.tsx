import { useLang } from "../i18n/langContext";
import { OPEN_CHAT_EVENT } from "../components/ChatWidget";

function openChat(message?: string) {
  window.dispatchEvent(new CustomEvent(OPEN_CHAT_EVENT, { detail: { message } }));
}

export default function RlzAgent() {
  const { t, tArr } = useLang();
  const starters = tArr("agent.starters").slice(0, 5);
  return (
    <section className="rlz-cta-section rlz-section" id="live-agent" style={{ paddingTop: 40 }}>
      <div className="rlz-cta-card rlz-reveal">
        <div className="rlz-section-tag">
          <span className="rlz-live-dot" aria-hidden="true" />
          {t("agent.eyebrow")}
        </div>
        <h2>
          {t("agent.titleA")}
          <br />
          <span className="rlz-grad-text">{t("agent.titleB")}</span>
        </h2>
        <p>{t("agent.lede")}</p>
        <div className="rlz-agent-actions">
          <button className="rlz-btn rlz-btn-primary" onClick={() => openChat()}>
            <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>forum</i>
            {t("agent.cta")}
          </button>
        </div>
        {starters.length > 0 && (
          <div className="rlz-chip-row rlz-agent-starters" aria-label={t("agent.cta")}>
            {starters.map((q) => (
              <button key={q} className="rlz-chip" onClick={() => openChat(q)}>
                {q}
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
