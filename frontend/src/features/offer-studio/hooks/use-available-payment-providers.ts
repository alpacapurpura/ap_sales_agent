"use client";

import { useMemo } from "react";

import { useQuery } from "@tanstack/react-query";

import {
  paymentProvidersApi,
  type ConnectionsStatusResponse,
} from "../api/payment-providers-api";

/**
 * Payment provider known to the system. Mirror of the ``PaymentProvider``
 * StrEnum in ``backend/src/modules/sales_agent/domain/enrollment.py``.
 *
 * ``manual`` covers operators who mark a sale as paid manually (cash,
 * offline wire transfer) — it doesn't trigger a webhook but surfaces in
 * reports all the same.
 */
export type PaymentProviderKey = "stripe" | "mercadopago" | "culqi" | "paypal" | "manual";

export interface AvailablePaymentProvider {
  readonly key: PaymentProviderKey;
  readonly display_name: string;
  readonly is_connected: boolean;
  readonly country_fit: readonly string[];
}

/**
 * Static catalog + geo fit matrix. When the backend exposes a dedicated
 * ``/api/v1/connections/payment-providers/enabled`` endpoint (gap tracked
 * in catalogs-consolidation Phase 12), the hook drops this catalog in
 * favour of the server response.
 */
const PROVIDER_CATALOG: readonly AvailablePaymentProvider[] = [
  {
    key: "mercadopago",
    display_name: "Mercado Pago",
    is_connected: false,
    country_fit: ["AR", "BR", "CL", "CO", "MX", "PE", "UY"],
  },
  {
    key: "culqi",
    display_name: "Culqi",
    is_connected: false,
    country_fit: ["PE"],
  },
  {
    key: "stripe",
    display_name: "Stripe",
    is_connected: false,
    country_fit: ["MX", "BR", "CL", "GLOBAL"],
  },
  {
    key: "paypal",
    display_name: "PayPal",
    is_connected: false,
    country_fit: ["GLOBAL"],
  },
  {
    key: "manual",
    display_name: "Pago manual (transferencia, efectivo)",
    is_connected: true,
    country_fit: ["GLOBAL"],
  },
];

const QUERY_KEY = ["connections", "status"] as const;

/**
 * Returns the list of payment providers with ``is_connected`` flipped
 * true for those whose channel appears active in
 * ``/api/v1/connections/status``.
 *
 * Consumer: the ``payment-provider-picker`` custom action referenced
 * from ``pricing.schema.ts``.
 */
export function useAvailablePaymentProviders() {
  const { data, isLoading, error } = useQuery<ConnectionsStatusResponse>({
    queryKey: QUERY_KEY,
    queryFn: paymentProvidersApi.fetchConnectionsStatus,
    staleTime: 5 * 60 * 1000,
  });

  const providers = useMemo<readonly AvailablePaymentProvider[]>(() => {
    if (!data) return PROVIDER_CATALOG;
    const connected = new Set(
      data.connections.filter((c) => c.is_connected).map((c) => c.channel_type),
    );
    return PROVIDER_CATALOG.map((p) => ({
      ...p,
      is_connected: p.key === "manual" ? true : connected.has(p.key),
    }));
  }, [data]);

  return {
    providers,
    isLoading,
    error,
    /** True when at least one non-manual provider is connected. */
    hasAutomatedProvider: providers.some((p) => p.key !== "manual" && p.is_connected),
  };
}
