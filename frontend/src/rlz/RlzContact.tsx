import { siteConfig } from "../config/site";
import { useLang } from "../i18n/langContext";

export default function RlzContact() {
  const { t } = useLang();
  return (
    <section className="rlz-cta-section rlz-section" id="contact" style={{ paddingTop: 40 }}>
      <div className="rlz-cta-card rlz-reveal">
        <div className="rlz-section-tag"><i className="material-symbols-outlined">satellite_alt</i> {t("contact.tag")}</div>
        <h2>{t("contact.titleA")}<br /><span className="rlz-grad-text">{t("contact.titleB")}</span></h2>
        <p>{t("contact.lede")}</p>

        <div className="rlz-contact-grid">
          <a href={siteConfig.callLink} className="rlz-contact-tile">
            <span className="rlz-ct-icon rlz-icon-violet"><i className="material-symbols-outlined">call</i></span>
            <h4>{t("contact.call")}</h4><p>{siteConfig.contact.phone}</p>
          </a>
          <a href={siteConfig.whatsappLink} target="_blank" rel="noopener noreferrer" className="rlz-contact-tile">
            <span className="rlz-ct-icon rlz-icon-green"><i className="material-symbols-outlined">chat</i></span>
            <h4>{t("contact.whatsapp")}</h4><p>{t("contact.instantChat")}</p>
          </a>
          <a href={siteConfig.emailLink} className="rlz-contact-tile">
            <span className="rlz-ct-icon rlz-icon-cyan"><i className="material-symbols-outlined">mail</i></span>
            <h4>{t("contact.email")}</h4><p>{siteConfig.contact.email}</p>
          </a>
          <a href="/Rajib-Mahata-Resume-2026.pdf" download className="rlz-contact-tile">
            <span className="rlz-ct-icon rlz-icon-fuchsia"><i className="material-symbols-outlined">download</i></span>
            <h4>{t("contact.resume")}</h4><p>{t("contact.downloadPdf")}</p>
          </a>
        </div>
      </div>
    </section>
  );
}
