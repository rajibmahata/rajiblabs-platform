/* Shared language storage helpers (no components — see LanguageContext). */

export const STORE_KEY = "rlabs_lang";

export function readStoredLang(): string | null {
  try { return localStorage.getItem(STORE_KEY); } catch { return null; }
}

export function getUiLang(): string {
  return readStoredLang() || "en";
}

export function persistLang(code: string): void {
  try { localStorage.setItem(STORE_KEY, code); } catch { /* private mode */ }
  try { document.cookie = `${STORE_KEY}=${encodeURIComponent(code)};path=/;max-age=31536000`; } catch { /* ignore */ }
}
