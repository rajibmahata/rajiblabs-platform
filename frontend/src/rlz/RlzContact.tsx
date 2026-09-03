import { siteConfig } from "../config/site";

export default function RlzContact() {
  return (
    <section className="rlz-cta-section rlz-section" id="contact" style={{ paddingTop: 40 }}>
      <div className="rlz-cta-card rlz-reveal">
        <div className="rlz-section-tag"><i className="material-symbols-outlined">satellite_alt</i> OPEN_CHANNEL</div>
        <h2>Let&apos;s Build Something<br /><span className="rlz-grad-text">Intelligent Together</span></h2>
        <p>Have a system to architect, an AI product to ship, or a legacy platform to modernize? Let&apos;s talk.</p>

        <div className="rlz-contact-grid">
          <a href={siteConfig.callLink} className="rlz-contact-tile">
            <span className="rlz-ct-icon rlz-icon-violet"><i className="material-symbols-outlined">call</i></span>
            <h4>Call</h4><p>{siteConfig.contact.phone}</p>
          </a>
          <a href={siteConfig.whatsappLink} target="_blank" rel="noopener noreferrer" className="rlz-contact-tile">
            <span className="rlz-ct-icon rlz-icon-green"><i className="material-symbols-outlined">chat</i></span>
            <h4>WhatsApp</h4><p>Instant chat</p>
          </a>
          <a href={siteConfig.emailLink} className="rlz-contact-tile">
            <span className="rlz-ct-icon rlz-icon-cyan"><i className="material-symbols-outlined">mail</i></span>
            <h4>Email</h4><p>{siteConfig.contact.email}</p>
          </a>
          <a href="/Rajib-Mahata-Resume-2026.pdf" download className="rlz-contact-tile">
            <span className="rlz-ct-icon rlz-icon-fuchsia"><i className="material-symbols-outlined">download</i></span>
            <h4>Resume</h4><p>Download PDF</p>
          </a>
        </div>
      </div>
    </section>
  );
}
