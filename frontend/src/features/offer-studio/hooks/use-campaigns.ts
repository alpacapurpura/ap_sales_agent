// useOfferCampaigns — GET /offers/{id}/campaigns (cross-module read)
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { campaignsApi } from "../api/campaigns-api";

import type { OfferCampaignsQuery, OfferCampaignsResponse } from "../types/campaigns";

export function useOfferCampaigns(offerId: string, filters?: OfferCampaignsQuery) {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery<OfferCampaignsResponse, Error>({
    queryKey: ["offer", offerId, "campaigns", filters ?? {}],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return campaignsApi.list(offerId, filters, token);
    },
    enabled: isLoaded && isSignedIn && !!offerId && offerId !== "undefined",
    staleTime: 60 * 1000,
  });
}
