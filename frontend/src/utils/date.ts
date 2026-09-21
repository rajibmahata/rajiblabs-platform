/**
 * Shared date validation and formatting utilities.
 * Prevents nonsensical dates like "July 2026" (future), "July 20226" (typo),
 * or any unparseable string from reaching the UI.
 */

/** Valid month names for period parsing (case-insensitive match). */
const MONTHS: Record<string, number> = {
  jan: 0, january: 0, feb: 1, february: 1, mar: 2, march: 2,
  apr: 3, april: 3, may: 4, jun: 5, june: 5,
  jul: 6, july: 6, aug: 7, august: 7, sep: 8, september: 8,
  oct: 9, october: 9, nov: 10, november: 10, dec: 11, december: 11,
};

/**
 * Check if a year value looks valid (4-digit, 1900–current year + 1).
 * Returns false for typos like "20226" or future years beyond next year.
 */
export function isValidYear(yearStr: string): boolean {
  const y = parseInt(yearStr, 10);
  if (isNaN(y)) return false;
  const now = new Date();
  const currentYear = now.getFullYear();
  // Allow current year and next year (for "Present" entries), but nothing beyond
  return y >= 1900 && y <= currentYear + 1 && String(y).length === 4;
}

/**
 * Parse a period string like "Aug 2019", "2019", "Aug 2019 – Present" etc.
 * Returns { valid, display } where display is the cleaned-up version.
 * Returns { valid: false } if the period contains invalid dates.
 */
export function validatePeriod(period: string): { valid: boolean; display: string } {
  if (!period || !period.trim()) return { valid: true, display: "" };

  const cleaned = period.trim();
  // Allow "PRESENT" / "present" / "Current" etc. — always valid as a suffix
  const presentPattern = /present|current|now/i;

  // Split on common separators: –, -, —, to, till, until
  const parts = cleaned.split(/\s*(?:–|—|-{2,}|\bto\b|\btill\b|\buntil\b)\s*/i);

  for (const part of parts) {
    const p = part.trim();
    if (!p || presentPattern.test(p)) continue;

    // Try to extract year (4 digits)
    const yearMatch = p.match(/\b(\d{4})\b/);
    if (!yearMatch) {
      // No year found — could be just "Present" which is fine
      if (!presentPattern.test(p)) return { valid: false, display: cleaned };
      continue;
    }

    const yearStr = yearMatch[1];
    if (!isValidYear(yearStr)) {
      return { valid: false, display: cleaned };
    }

    // Try to extract month
    const monthMatch = p.match(/\b([a-zA-Z]+)\b/);
    if (monthMatch) {
      const monthKey = monthMatch[1].toLowerCase();
      if (MONTHS[monthKey] === undefined && !presentPattern.test(monthKey)) {
        // Not a recognized month and not "present" — could be invalid
        // But don't reject it outright (could be a company name in the period)
      }
    }
  }

  return { valid: true, display: cleaned };
}

/**
 * Validate an ISO date string (YYYY-MM-DD or YYYY-MM-DDTHH:mm).
 * Returns true if parseable and within reasonable range.
 */
export function isValidISODate(value: string): boolean {
  if (!value || !value.trim()) return true; // empty is OK (optional field)
  const d = new Date(value);
  if (isNaN(d.getTime())) return false;
  const year = d.getFullYear();
  return year >= 1900 && year <= new Date().getFullYear() + 1;
}

/**
 * Safely format a date string for display.
 * Returns a formatted string or "—" if the date is invalid.
 */
export function safeFormatDate(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    const d = new Date(value);
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleDateString(undefined, {
      year: "numeric", month: "short", day: "numeric",
    });
  } catch {
    return "—";
  }
}

/**
 * Safely format a datetime string for display.
 * Returns a formatted string or "—" if the date is invalid.
 */
export function safeFormatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    const d = new Date(value);
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleString();
  } catch {
    return "—";
  }
}

/**
 * Get max date string for HTML date input (next year end).
 */
export function getMaxDateString(): string {
  const now = new Date();
  return `${now.getFullYear() + 1}-12-31`;
}

/**
 * Get min date string for HTML date input (1900-01-01).
 */
export function getMinDateString(): string {
  return "1900-01-01";
}
