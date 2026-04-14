import { formatTenantDate, formatTenantTime } from "@/lib/format-date";

/**
 * Return a human-readable relative time string like "hace 3m", "hace 2h", "hace 1d".
 * Falls back to a formatted date for dates older than 7 days, using the tenant timezone.
 */
export function formatDistanceToNow(dateStr: string, timezone = "UTC"): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);

  if (diffMin < 1) return "ahora";
  if (diffMin < 60) return `hace ${diffMin}m`;

  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `hace ${diffHours}h`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `hace ${diffDays}d`;

  return formatTenantDate(dateStr, timezone, "d MMM");
}

/**
 * Format a datetime for message timestamps in the tenant's timezone.
 */
export function formatMessageTime(dateStr: string | null, timezone = "UTC"): string {
  if (!dateStr) return "";
  return formatTenantTime(dateStr, timezone);
}
