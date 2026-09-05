import { useEffect, useRef, useState } from "react";
import { useLang } from "./langContext";

/** Top-right public language selector — enabled languages only, no reload. */
export default function LanguageSelector() {
  const { lang, languages, setLang, t } = useLang();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);
  const current = languages.find((l) => l.code === lang) || languages[0];

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  if (!languages.length) return null;
  return (
    <div className="rlz-lang" ref={ref}>
      <button
        className="rlz-lang-btn" onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox" aria-expanded={open}
        aria-label={t("nav.language")} title={t("nav.language")}
      >
        <i className="material-symbols-outlined">translate</i>
        <span className="rlz-lang-current">{current?.native_name || current?.code}</span>
        <i className="material-symbols-outlined rlz-lang-caret">expand_more</i>
      </button>
      {open && (
        <ul className="rlz-lang-drop" role="listbox" aria-label={t("nav.language")}>
          {languages.map((l) => (
            <li key={l.code}>
              <button
                role="option" aria-selected={l.code === lang}
                className={`rlz-lang-opt${l.code === lang ? " active" : ""}`}
                onClick={() => { setLang(l.code); setOpen(false); }}
              >
                <span>{l.native_name}</span>
                <span className="rlz-lang-name">{l.name}</span>
                {l.code === lang && <i className="material-symbols-outlined">check</i>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
