import { siteConfig } from "../config/site";
import { useLang } from "../i18n/langContext";

export default function RlzFooter() {
  const { t } = useLang();
  return (
    <footer className="rlz-footer">
      <div className="rlz-container rlz-footer-inner">
        <a href="#home" className="rlz-logo" style={{ fontSize: "1.05rem" }}>
          <span className="rlz-logo-mark" style={{ width: 30, height: 30, fontSize: "0.8rem" }}>
            <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>memory</i>
          </span>
          Rajib<span><em>Labs</em></span>
        </a>
        <p>{t("footer.rights", { year: new Date().getFullYear() })}</p>
        <div className="rlz-footer-social">
          <a href={siteConfig.social.github} target="_blank" rel="noopener noreferrer" aria-label="GitHub">
            <i className="material-symbols-outlined">code</i>
          </a>
          <a href={siteConfig.social.linkedin} target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
            <i className="material-symbols-outlined">work</i>
          </a>
          <a href={siteConfig.emailLink} aria-label="Email">
            <i className="material-symbols-outlined">mail</i>
          </a>
        </div>
      </div>
    </footer>
  );
}
