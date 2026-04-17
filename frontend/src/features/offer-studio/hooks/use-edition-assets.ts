// Edition-scoped asset hooks — Phase 3
// Thin wrapper around ``useAssets`` that injects ``edition_id`` so the
// component tree never has to know the filter key. Callers in the edition
// detail shell pass the active edition id; offer-level pages keep using
// ``useAssets`` directly.
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { assetsApi } from "../api/assets-api";

import type { AssetListQuery, AssetListResponse } from "../types/assets";

const editionAssetsKey = (offerId: string, editionId: string, query?: AssetListQuery) =>
  ["offer", offerId, "edition", editionId, "assets", query ?? {}] as const;

/**
 * List assets scoped to a specific edition.
 *
 * Backend semantics: returns assets where ``edition_id = editionId`` OR
 * ``shared_across_editions = true``. Enabled only once both ids are known
 * so the query key doesn't churn during auth hydration.
 */
export function useEditionAssets(
  offerId: string,
  editionId: string | null | undefined,
  query?: Omit<AssetListQuery, "edition_id">,
) {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery<AssetListResponse, Error>({
    queryKey: editionAssetsKey(offerId, editionId ?? "unknown", query),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return assetsApi.list(
        offerId,
        { ...(query ?? {}), edition_id: editionId ?? undefined },
        token,
      );
    },
    enabled: isLoaded && isSignedIn && !!offerId && !!editionId,
    staleTime: 30 * 1000,
  });
}
