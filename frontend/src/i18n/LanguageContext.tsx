import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { LanguageCtx, type UILanguage } from "./langContext";
import { persistLang, readStoredLang } from "./langStore";
import en from "./en.json";
import bn from "./bn.json";
import hi from "./hi.json";
import fr from "./fr.json";
import ja from "./ja.json";
import de from "./de.json";
import es from "./es.json";
import pt from "./pt.json";
import zhCN from "./zh-CN.json";
import ko from "./ko.json";
import it from "./it.json";
import ar from "./ar.json";

const BUNDLES: Record<string, Record<string, unknown>> = {
  en, bn, hi, fr, ja, de, es, pt, "zh-CN": zhCN, ko, it, ar,
};
const FALLBACK_LANGS: UILanguage[] = [
  { code: "en", name: "English", native_name: "English", direction: "ltr", is_default: true },
];

function detectBrowser(codes: string[]): string | null {
  const prefs: string[] = [];
  try {
    prefs.push(...(navigator.languages || []));
    if (navigator.language) prefs.push(navigator.language);
  } catch { /* private mode */ }
  const norm = (c: string) => c.trim().replace("_", "-");
  const exact = new Map(codes.map((c) => [c.toLowerCase(), c]));
  for (const p of prefs) {
    const hit = exact.get(norm(p).toLowerCase());
    if (hit) return hit;
  }
  for (const p of prefs) {
    const base = norm(p).split("-")[0].toLowerCase();
    const hit = codes.find((c) => c.split("-")[0].toLowerCase() === base);
    if (hit) return hit;
    const prefixed = codes.find((c) => c.toLowerCase().startsWith(base + "-"));
    if (prefixed) return prefixed;
  }
  return null;
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [languages, setLanguages] = useState<UILanguage[]>(FALLBACK_LANGS);
  const [lang, setLangState] = useState<string>(() => readStoredLang() || "en");

  // Enabled languages drive the selector; disabled ones vanish immediately.
  useEffect(() => {
    let alive = true;
    const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
    fetch(`${base}/api/public/languages`).then((r) => (r.ok ? r.json() : null)).then((list) => {
      if (!alive || !Array.isArray(list) || !list.length) return;
      const langs = list as UILanguage[];
      setLanguages(langs);
      const stored = readStoredLang();
      if (stored && langs.some((l) => l.code === stored)) {
        setLangState(stored);
      } else if (!stored) {
        // Browser detection ONLY with no saved preference.
        const detected = detectBrowser(langs.map((l) => l.code));
        setLangState(detected || langs.find((l) => l.is_default)?.code || "en");
      } else {
        // Saved preference points at a now-disabled language → default.
        setLangState(langs.find((l) => l.is_default)?.code || "en");
      }
    }).catch(() => {});
    return () => { alive = false; };
  }, []);

  // SEO + RTL: keep <html lang/dir> in sync, no reload needed.
  const dir: "ltr" | "rtl" = languages.find((l) => l.code === lang)?.direction === "rtl" ? "rtl" : "ltr";
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
  }, [lang, dir]);

  const setLang = useCallback((code: string) => {
    setLangState(code);
    persistLang(code);
  }, []);

  const t = useCallback((key: string, vars?: Record<string, string | number>) => {
    const bundle = BUNDLES[lang] || {};
    let s = typeof bundle[key] === "string" ? (bundle[key] as string) : undefined;
    if (s === undefined) {
      const fb = en as Record<string, unknown>;
      s = typeof fb[key] === "string" ? (fb[key] as string) : key;
    }
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, String(v));
    return s;
  }, [lang]);

  const tArr = useCallback((key: string): string[] => {
    const bundle = BUNDLES[lang] || {};
    const v = bundle[key];
    if (Array.isArray(v)) return v as string[];
    const fb = (en as Record<string, unknown>)[key];
    return Array.isArray(fb) ? (fb as string[]) : [];
  }, [lang]);

  const value = useMemo(() => ({ lang, dir, languages, setLang, t, tArr }),
    [lang, dir, languages, setLang, t, tArr]);
  return <LanguageCtx.Provider value={value}>{children}</LanguageCtx.Provider>;
}
