import { createContext, useContext } from "react";

export interface UILanguage {
  code: string; name: string; native_name: string; direction: string; is_default?: boolean;
}

export interface LangCtx {
  lang: string;
  dir: "ltr" | "rtl";
  languages: UILanguage[];
  setLang: (code: string) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  tArr: (key: string) => string[];
}

const FALLBACK = {
  lang: "en", dir: "ltr" as const, languages: [],
  setLang: () => {}, t: (k: string) => k, tArr: () => [],
};

export const LanguageCtx = createContext<LangCtx>(FALLBACK);

export function useLang(): LangCtx {
  return useContext(LanguageCtx);
}
