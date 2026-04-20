import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchOfferMetadata } from "../api/offer-metadata-api";

/**
 *
 */
export function useOfferMetadata() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["offer-metadata"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return {};
      return fetchOfferMetadata(token);
    },
    staleTime: 1000 * 60 * 60, // Cache for 1 hour
  });
}
