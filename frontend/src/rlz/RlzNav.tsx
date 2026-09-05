import { useEffect, useState } from "react";
import { useLang } from "../i18n/langContext";
import LanguageSelector from "../i18n/LanguageSelector";

export default function RlzNav() {
  const { t } = useLang();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const LINKS = [
    { href: "#expertise", label: t("nav.expertise") },
    { href: "#architecture", label: t("nav.architecture") },
    { href: "#projects", label: t("nav.projects") },
    { href: "#experience", label: t("nav.experience") },
  ];

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav className={`rlz-nav${scrolled ? " rlz-scrolled" : ""}`} aria-label="Primary">
      <a href="#home" className="rlz-logo">
        <span className="rlz-logo-mark"><i className="material-symbols-outlined">memory</i></span>
        Rajib<span><em>Labs</em></span>
      </a>
      <ul className={`rlz-nav-links${open ? " rlz-open" : ""}`} id="rlzNavLinks">
        {LINKS.map((l) => (
          <li key={l.href}>
            <a href={l.href} onClick={() => setOpen(false)}>{l.label}</a>
          </li>
        ))}
        <li>
          <a href="#contact" className="rlz-nav-cta" onClick={() => setOpen(false)}>
            {t("nav.letsTalk")} <i className="material-symbols-outlined" style={{ fontSize: "0.85rem" }}>arrow_forward</i>
          </a>
        </li>
      </ul>
      <LanguageSelector />
      <button
        className="rlz-hamburger"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? t("nav.closeMenu") : t("nav.menu")}
        aria-expanded={open}
      >
        <i className="material-symbols-outlined">{open ? "close" : "menu"}</i>
      </button>
    </nav>
  );
}
