// useOfferCounts — GET /offers/{id}/counts
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { countsApi } from "../api/counts-api";
import type { OfferCountsResponse } from "../types/counts";

export function useOfferCounts(offerId: string) {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery<OfferCountsResponse, Error>({
    queryKey: ["offer", offerId, "counts"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return countsApi.get(offerId, token);
    },
    enabled: isLoaded && isSignedIn && !!offerId && offerId !== "undefined",
    staleTime: 30 * 1000,
  });
}
