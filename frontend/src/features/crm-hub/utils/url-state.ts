import { contactFilterParamsSchema, type ContactFilterParams } from "../types";

/**
 * Clamps an integer from a raw search param string.
 * Returns `defaultVal` when the string is absent or not a valid integer.
 */
export function clampInt(
  raw: string | string[] | undefined,
  min: number,
  max: number,
  defaultVal: number,
): number {
  if (raw === undefined || Array.isArray(raw)) return defaultVal;
  const n = parseInt(raw, 10);
  if (isNaN(n)) return defaultVal;
  return Math.min(Math.max(n, min), max);
}

/**
 * Parses URL search params into ContactFilterParams.
 * Comma-separated lists (e.g. lifecycle_stage_in=mql,sql) are split.
 */
export function parseFiltersFromSearchParams(
  params: Record<string, string | string[] | undefined>,
): ContactFilterParams {
  const raw: Record<string, unknown> = {};

  const str = (key: string): string | undefined => {
    const v = params[key];
    if (!v || Array.isArray(v)) return undefined;
    return v || undefined;
  };

  const listStr = (key: string): string[] | undefined => {
    const v = params[key];
    if (!v) return undefined;
    const joined = Array.isArray(v) ? v.join(",") : v;
    const parts = joined.split(",").filter(Boolean);
    return parts.length > 0 ? parts : undefined;
  };

  const boolParam = (key: string): boolean | undefined => {
    const v = str(key);
    if (v === "true") return true;
    if (v === "false") return false;
    return undefined;
  };

  const numParam = (key: string): number | undefined => {
    const v = str(key);
    if (v === undefined) return undefined;
    const n = parseInt(v, 10);
    return isNaN(n) ? undefined : n;
  };

  raw.lifecycle_stage_in = listStr("lifecycle_stage_in");
  raw.score_min = numParam("score_min");
  raw.score_max = numParam("score_max");
  raw.source_in = listStr("source_in");
  raw.has_email = boolParam("has_email");
  raw.has_phone = boolParam("has_phone");
  raw.has_telegram_id = boolParam("has_telegram_id");
  raw.has_whatsapp_id = boolParam("has_whatsapp_id");
  raw.has_instagram_id = boolParam("has_instagram_id");
  raw.has_tiktok_id = boolParam("has_tiktok_id");
  raw.created_after = str("created_after");
  raw.created_before = str("created_before");
  raw.last_activity_after = str("last_activity_after");
  raw.last_activity_before = str("last_activity_before");
  raw.is_inactive = boolParam("is_inactive");
  raw.has_campaign_engagement = boolParam("has_campaign_engagement");
  raw.country_in = listStr("country_in");
  raw.q = str("q");

  // Strip undefined values before parsing
  for (const key of Object.keys(raw)) {
    if (raw[key] === undefined) delete raw[key];
  }

  const result = contactFilterParamsSchema.safeParse(raw);
  return result.success ? result.data : {};
}

/**
 * Serializes ContactFilterParams + pagination to URLSearchParams.
 * Lists are encoded as comma-separated strings.
 */
export function filtersToSearchParams(
  filters: ContactFilterParams,
  pagination: { limit: number; offset: number },
): URLSearchParams {
  const sp = new URLSearchParams();

  if (pagination.limit !== 50) sp.set("limit", String(pagination.limit));
  if (pagination.offset !== 0) sp.set("offset", String(pagination.offset));

  for (const [k, v] of Object.entries(filters)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) {
      if (v.length > 0) sp.set(k, v.join(","));
    } else {
      sp.set(k, String(v));
    }
  }

  return sp;
}
