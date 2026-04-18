import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface ConnectionStatusItem {
  readonly channel_type: string;
  readonly is_connected: boolean;
}

export interface ConnectionsStatusResponse {
  readonly connections: readonly ConnectionStatusItem[];
}

/**
 * Thin wrapper over ``/api/v1/connections/status``. Returns every channel
 * the tenant has ever connected — the hook filters payment providers
 * client-side against the static ``PROVIDER_CATALOG``.
 *
 * When the backend ships a dedicated ``/connections/payment-providers``
 * endpoint (tracked in catalogs-consolidation Phase 12 gap), this
 * wrapper swaps to it without touching the hook signature.
 */
export const paymentProvidersApi = {
  fetchConnectionsStatus: async (): Promise<ConnectionsStatusResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/status`);
    if (!res.ok) throw new Error("Failed to fetch connections status");
    return res.json() as Promise<ConnectionsStatusResponse>;
  },
};
