/**
 * Centralized date formatting utilities.
 * All dates displayed in the UI pass through these functions,
 * which convert UTC to the tenant's timezone.
 *
 * Uses date-fns-tz (already installed) for timezone conversion.
 */

import { es } from "date-fns/locale";
import { formatInTimeZone } from "date-fns-tz";

/**
 * Format a date string in the tenant's timezone.
 * @param isoDate - ISO 8601 date string (UTC from backend)
 * @param timezone - IANA timezone (e.g., "America/Lima")
 * @param format - date-fns format string (default: "d MMM yyyy")
 */
export function formatTenantDate(isoDate: string, timezone: string, format?: string): string {
  return formatInTimeZone(new Date(isoDate), timezone, format ?? "d MMM yyyy", { locale: es });
}

/**
 * Format a date+time string in the tenant's timezone.
 */
export function formatTenantDateTime(isoDate: string, timezone: string): string {
  return formatInTimeZone(new Date(isoDate), timezone, "d MMM yyyy, HH:mm", { locale: es });
}

/**
 * Format only the time portion in the tenant's timezone.
 */
export function formatTenantTime(isoDate: string, timezone: string): string {
  return formatInTimeZone(new Date(isoDate), timezone, "HH:mm", { locale: es });
}
