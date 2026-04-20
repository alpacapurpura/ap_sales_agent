"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import {
  placementApi,
  type ResolvedSocialProof,
  type SurfaceType,
} from "@/lib/api/placement";

/**
 * Resolve every visible social-proof item for a surface (offer, landing,
 * email sequence, sales_agent_kb) — including brand-homepage fallbacks
 * when ``includeBrand`` is true.
 */
export function useSocialProofForSurface(params: {
  surfaceType: SurfaceType;
  surfaceRefId?: string | null;
  includeBrand?: boolean;
  enabled?: boolean;
}) {
  const { surfaceType, surfaceRefId, includeBrand = false, enabled = true } = params;
  const { getToken } = useAuth();
  const routeParams = useParams<{ tenantId: string }>();
  const tenantId = routeParams?.tenantId ?? "";

  return useQuery<ResolvedSocialProof>({
    queryKey: [
      "social_proof_for_surface",
      tenantId,
      surfaceType,
      surfaceRefId ?? null,
      includeBrand,
    ],
    enabled,
    queryFn: async () => {
      const token = await getToken();
      if (!token) return { testimonials: [], authority_items: [], team_members: [] };
      return placementApi.forSurface(token, { surfaceType, surfaceRefId, includeBrand });
    },
    retry: (failureCount, err: Error) => {
      if (err.message.includes("401") || err.message.includes("404")) return false;
      return failureCount < 2;
    },
  });
}
