import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

export function useOfferMetadata() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["offer-metadata"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return {};
      const res = await fetchClient("/products/metadata/hints", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch metadata");
      return res.json();
    },
    staleTime: 1000 * 60 * 60, // Cache for 1 hour
  });
}
