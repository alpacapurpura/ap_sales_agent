import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import {
  getYoutubeTopVideosEnriched,
  getYoutubeTrafficSources,
  getYoutubeDemographics,
  getYoutubeCountries,
} from "../api/youtube-analytics-api";

import type {
  YouTubeTopVideo,
  YouTubeTrafficSource,
  YouTubeDemographic,
  YouTubeCountry,
} from "../types/metrics";

/**
 *
 */
export function useYoutubeTopVideos(enabled = false) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;

  return useQuery<YouTubeTopVideo[]>({
    queryKey: ["youtube-top-videos", tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return getYoutubeTopVideosEnriched(token);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 *
 */
export function useYoutubeTrafficSources(enabled = false) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;

  return useQuery<YouTubeTrafficSource[]>({
    queryKey: ["youtube-traffic-sources", tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return getYoutubeTrafficSources(token);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 *
 */
export function useYoutubeDemographics(enabled = false) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;

  return useQuery<YouTubeDemographic[]>({
    queryKey: ["youtube-demographics", tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return getYoutubeDemographics(token);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 *
 */
export function useYoutubeCountries(enabled = false) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;

  return useQuery<YouTubeCountry[]>({
    queryKey: ["youtube-countries", tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return getYoutubeCountries(token);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}
