"use client";

import { useQuery } from "@tanstack/react-query";

import {
  currencyCatalogApi,
  type CurrencyCatalogResponse,
  type CurrencyMetadata,
} from "@/lib/api/currency-catalog-api";

const QUERY_KEY = ["shared", "currencies", "catalog"] as const;

/**
 * Fetches the curated currency catalog (see
 * ``backend/src/shared/domain/currency_catalog.py``). Drives every
 * currency picker in the app — wizard pricing step, settings, etc.
 *
 * Cached for 1 hour since the catalog is domain metadata that only
 * changes on deploy.
 */
export function useCurrencyCatalog() {
  return useQuery<CurrencyCatalogResponse>({
    queryKey: QUERY_KEY,
    queryFn: currencyCatalogApi.fetch,
    staleTime: 60 * 60 * 1000,
    gcTime: 24 * 60 * 60 * 1000,
  });
}

/** Return the metadata for a specific ``code`` or ``undefined`` while loading. */
export function useCurrencyMetadata(code: string | undefined): CurrencyMetadata | undefined {
  const { data } = useCurrencyCatalog();
  if (!data || !code) return undefined;
  return data.currencies.find((c) => c.code === code);
}
