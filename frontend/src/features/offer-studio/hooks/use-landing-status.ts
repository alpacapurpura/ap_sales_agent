// useLandingStatus — GET /offers/{id}/landing/status with derived UI state.
import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { toast } from "sonner";

import { landingApi } from "../api/landing-api";

import type {
  LandingGenerateResponse,
  LandingPublishResponse,
  LandingStatusResponse,
  LandingUnpublishResponse,
} from "../types/landing-status";

const COMPLETION_THRESHOLD = 90;

/**
 * UI state derived from the landing status response:
 * - `disabled`          → offer completion below 90%, cannot generate yet.
 * - `ready-to-generate` → offer is ready but no landing has been generated.
 * - `in-sync`           → landing generated and matches the latest offer version.
 * - `outdated`          → landing generated but offer changed since then.
 */
export type LandingUiState = "disabled" | "ready-to-generate" | "in-sync" | "outdated";

/**
 *
 */
export function deriveLandingUiState(status: LandingStatusResponse): LandingUiState {
  if (!status.is_generated) {
    if (status.completion_percentage < COMPLETION_THRESHOLD) {
      return "disabled";
    }
    return "ready-to-generate";
  }
  if (status.is_outdated) {
    return "outdated";
  }
  return "in-sync";
}

/**
 *
 */
export function useLandingStatus(offerId: string) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const queryClient = useQueryClient();

  const query = useQuery<LandingStatusResponse, Error>({
    queryKey: ["offer", offerId, "landing-status"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return landingApi.getStatus(offerId, token);
    },
    enabled: isLoaded && isSignedIn && !!offerId && offerId !== "undefined",
    staleTime: 30 * 1000,
  });

  const uiState: LandingUiState | null = useMemo(
    () => (query.data ? deriveLandingUiState(query.data) : null),
    [query.data],
  );

  const invalidate = () => {
    void queryClient.invalidateQueries({
      queryKey: ["offer", offerId, "landing-status"],
    });
  };

  const generateMutation = useMutation<LandingGenerateResponse, Error, void>({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return landingApi.generate(offerId, token);
    },
    onSuccess: () => {
      invalidate();
      toast.success("Generación de landing en cola");
    },
    onError: (err) => {
      toast.error(err.message || "Error al generar la landing");
    },
  });

  const regenerateMutation = useMutation<LandingGenerateResponse, Error, void>({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return landingApi.regenerate(offerId, token);
    },
    onSuccess: () => {
      invalidate();
      toast.success("Regeneración de landing en cola");
    },
    onError: (err) => {
      toast.error(err.message || "Error al regenerar la landing");
    },
  });

  const publishMutation = useMutation<LandingPublishResponse, Error, void>({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return landingApi.publish(offerId, token);
    },
    onSuccess: () => {
      invalidate();
      toast.success("Landing publicada");
    },
    onError: (err) => {
      toast.error(err.message || "Error al publicar la landing");
    },
  });

  const unpublishMutation = useMutation<LandingUnpublishResponse, Error, void>({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return landingApi.unpublish(offerId, token);
    },
    onSuccess: () => {
      invalidate();
      toast.success("Landing despublicada");
    },
    onError: (err) => {
      toast.error(err.message || "Error al despublicar la landing");
    },
  });

  return {
    ...query,
    uiState,
    generate: generateMutation,
    regenerate: regenerateMutation,
    publish: publishMutation,
    unpublish: unpublishMutation,
  };
}
