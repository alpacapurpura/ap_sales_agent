// useChangeOfferStatus — POST /offers/{id}/status
import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { statusApi } from "../api/status-api";

import type { ChangeOfferStatusPayload, OfferStatusResponse } from "../types/lifecycle";

interface UseChangeOfferStatusOptions {
  onSuccess?: (data: OfferStatusResponse) => void;
  onError?: (error: Error) => void;
}

export function useChangeOfferStatus(offerId: string, options?: UseChangeOfferStatusOptions) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<OfferStatusResponse, Error, ChangeOfferStatusPayload>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return statusApi.change(offerId, payload, token);
    },
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["offer", offerId] });
      void queryClient.invalidateQueries({
        queryKey: ["offer", offerId, "counts"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["offer", offerId, "landing-status"],
      });
      void queryClient.invalidateQueries({ queryKey: ["offers"] });
      void queryClient.invalidateQueries({ queryKey: ["offers", "archived"] });
      toast.success("Estado de la oferta actualizado");
      options?.onSuccess?.(data);
    },
    onError: (err) => {
      const message = err instanceof Error ? err.message : "Error al cambiar el estado";
      toast.error(message);
      options?.onError?.(err);
    },
  });
}
