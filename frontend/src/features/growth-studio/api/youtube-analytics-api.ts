import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type {
  YouTubeTopVideo,
  YouTubeTrafficSource,
  YouTubeDemographic,
  YouTubeCountry,
} from "../types/metrics";

const API_URL = config.api.baseUrl;

function buildUrl(path: string, params: Record<string, string | number | undefined>): string {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) qs.set(k, String(v));
  }
  const query = qs.toString();
  return `${API_URL}/api/v1/connections/youtube-analytics/${path}${query ? `?${query}` : ""}`;
}

/**
 *
 */
export async function getYoutubeTopVideosEnriched(
  token: string,
  startDate?: string,
  endDate?: string,
  maxResults?: number,
): Promise<YouTubeTopVideo[]> {
  const url = buildUrl("top-videos-enriched", {
    start_date: startDate,
    end_date: endDate,
    max_results: maxResults,
  });
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`YouTube Top Videos API returned ${res.status}`);
  const json = (await res.json()) as { data?: Record<string, unknown>[] };
  // Map snake_case response to camelCase interface
  return (json.data || []).map((v) => ({
    videoId: v.video_id as string,
    title: v.title as string,
    thumbnailUrl: v.thumbnail_url as string,
    duration: v.duration as string,
    publishedAt: v.published_at as string,
    views: v.views as number,
    likes: v.likes as number,
    watchTimeMinutes: v.watch_time_minutes as number,
    avgViewDuration: v.avg_view_duration as number,
  }));
}

/**
 *
 */
export async function getYoutubeTrafficSources(
  token: string,
  startDate?: string,
  endDate?: string,
): Promise<YouTubeTrafficSource[]> {
  const url = buildUrl("traffic-sources", { start_date: startDate, end_date: endDate });
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`YouTube Traffic Sources API returned ${res.status}`);
  const json = (await res.json()) as { data?: Record<string, unknown>[] };
  return (json.data || []).map((s) => ({
    insightTrafficSourceType: s.insightTrafficSourceType as string,
    views: s.views as number,
    estimatedMinutesWatched: s.estimatedMinutesWatched as number,
  }));
}

/**
 *
 */
export async function getYoutubeDemographics(
  token: string,
  startDate?: string,
  endDate?: string,
): Promise<YouTubeDemographic[]> {
  const url = buildUrl("demographics", { start_date: startDate, end_date: endDate });
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`YouTube Demographics API returned ${res.status}`);
  const json = (await res.json()) as { data?: Record<string, unknown>[] };
  return (json.data || []).map((d) => ({
    ageGroup: d.ageGroup as string,
    gender: d.gender as string,
    viewerPercentage: d.viewerPercentage as number,
  }));
}

/**
 *
 */
export async function getYoutubeCountries(
  token: string,
  startDate?: string,
  endDate?: string,
  maxResults?: number,
): Promise<YouTubeCountry[]> {
  const url = buildUrl("countries", {
    start_date: startDate,
    end_date: endDate,
    max_results: maxResults,
  });
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`YouTube Countries API returned ${res.status}`);
  const json = (await res.json()) as { data?: Record<string, unknown>[] };
  return (json.data || []).map((c) => ({
    country: c.country as string,
    views: c.views as number,
    estimatedMinutesWatched: c.estimatedMinutesWatched as number,
  }));
}
