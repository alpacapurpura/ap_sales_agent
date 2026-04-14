import { fetchClient } from "@/lib/http-client";
import { config } from "@/lib/config";
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
  const json = await res.json();
  // Map snake_case response to camelCase interface
  return (json.data || []).map((v: Record<string, unknown>) => ({
    videoId: v.video_id,
    title: v.title,
    thumbnailUrl: v.thumbnail_url,
    duration: v.duration,
    publishedAt: v.published_at,
    views: v.views,
    likes: v.likes,
    watchTimeMinutes: v.watch_time_minutes,
    avgViewDuration: v.avg_view_duration,
  }));
}

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
  const json = await res.json();
  return (json.data || []).map((s: Record<string, unknown>) => ({
    insightTrafficSourceType: s.insightTrafficSourceType,
    views: s.views,
    estimatedMinutesWatched: s.estimatedMinutesWatched,
  }));
}

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
  const json = await res.json();
  return (json.data || []).map((d: Record<string, unknown>) => ({
    ageGroup: d.ageGroup,
    gender: d.gender,
    viewerPercentage: d.viewerPercentage,
  }));
}

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
  const json = await res.json();
  return (json.data || []).map((c: Record<string, unknown>) => ({
    country: c.country,
    views: c.views,
    estimatedMinutesWatched: c.estimatedMinutesWatched,
  }));
}
