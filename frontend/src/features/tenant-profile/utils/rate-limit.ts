/**
 * Rate-limit display helpers for the tenant-profile feature.
 * CONTRACT §6.1 — utils/rate-limit.ts
 */

/**
 * Formats an ISO-8601 timestamp as a human-readable date in the given locale.
 *
 * Example output (es-AR): "15 de mayo de 2026"
 *
 * @param iso  ISO-8601 string (from ``next_allowed_change_at``)
 * @param locale  BCP 47 locale tag. Defaults to "es".
 */
export function formatNextAllowed(iso: string, locale = "es"): string {
  try {
    const date = new Date(iso);
    if (isNaN(date.getTime())) return iso;
    return new Intl.DateTimeFormat(locale, {
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(date);
  } catch {
    return iso;
  }
}
