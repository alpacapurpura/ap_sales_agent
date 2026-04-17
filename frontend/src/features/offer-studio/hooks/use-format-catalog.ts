"use client";

import { useQuery } from "@tanstack/react-query";

import {
  formatCatalogApi,
  type FormatCatalogResponse,
  type FormatMetadata,
  type FormatCatalogParams,
} from "../api/format-catalog-api";

/**
 * Fetches the format catalog, optionally pre-filtered server-side by archetype
 * and/or business types. The server sorts by best-matching suitability score
 * descending when business types are provided.
 *
 * Each combination of params is cached independently — changing business types
 * triggers a new fetch but once cached the result is reused.
 */
export function useFormatCatalog(params: FormatCatalogParams = {}) {
  const businessTypesKey = params.businessTypes ? [...params.businessTypes].sort().join(",") : "";
  const queryKey = [
    "offer",
    "formats",
    "catalog",
    params.archetype ?? "",
    businessTypesKey,
  ] as const;

  return useQuery<FormatCatalogResponse>({
    queryKey,
    queryFn: () => formatCatalogApi.fetch(params),
    staleTime: 60 * 60 * 1000,
    gcTime: 24 * 60 * 60 * 1000,
  });
}

/** Find a single format by its stable ``format_id``. */
export function useFormatMetadata(formatId: string | undefined): FormatMetadata | undefined {
  const { data } = useFormatCatalog();
  if (!data || !formatId) return undefined;
  return data.formats.find((f) => f.format_id === formatId);
}
