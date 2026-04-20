import { useAuth } from "@clerk/nextjs";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { editionsApi } from "../api/editions-api";

import type {
  EditionClonePayload,
  EditionCloneResponse,
  LaunchEditionCreate,
  LaunchEditionUpdate,
} from "../types";

/**
 *
 */
export function useEditions(offerId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const queryKey = ["editions", offerId];

  const {
    data: editions = [],
    isLoading,
    error,
  } = useQuery({
    queryKey,
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.list(offerId, token);
    },
    enabled: !!offerId,
    staleTime: 2 * 60 * 1000,
  });

  const createMutation = useMutation({
    mutationFn: async (data: LaunchEditionCreate) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.create(offerId, data, token);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
      toast.success("Edición creada");
    },
    onError: () => toast.error("Error al crear edición"),
  });

  const updateMutation = useMutation({
    mutationFn: async ({ editionId, data }: { editionId: string; data: LaunchEditionUpdate }) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.update(offerId, editionId, data, token);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
      toast.success("Edición actualizada");
    },
    onError: () => toast.error("Error al actualizar edición"),
  });

  const deleteMutation = useMutation({
    mutationFn: async (editionId: string) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.delete(offerId, editionId, token);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
      toast.success("Edición eliminada");
    },
    onError: () => toast.error("Error al eliminar edición"),
  });

  const duplicateMutation = useMutation({
    mutationFn: async (editionId: string) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.duplicate(offerId, editionId, token);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
      toast.success("Edición duplicada");
    },
    onError: () => toast.error("Error al duplicar edición"),
  });

  const cloneMutation = useMutation<
    EditionCloneResponse,
    Error,
    { editionId: string; payload: EditionClonePayload }
  >({
    mutationFn: async ({ editionId, payload }) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.clone(offerId, editionId, payload, token);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
      // Assets for the new edition exist under a fresh cache key; invalidate
      // the whole edition/assets tree so the gallery reflects the clone.
      void queryClient.invalidateQueries({ queryKey: ["offer", offerId] });
      toast.success("Edición clonada");
    },
    onError: (err) => toast.error(err.message || "Error al clonar edición"),
  });

  return {
    editions,
    loading: isLoading,
    error: error ? error.message : null,
    createEdition: createMutation.mutateAsync,
    updateEdition: updateMutation.mutateAsync,
    deleteEdition: deleteMutation.mutateAsync,
    duplicateEdition: duplicateMutation.mutateAsync,
    cloneEdition: cloneMutation.mutateAsync,
    saving:
      createMutation.isPending ||
      updateMutation.isPending ||
      deleteMutation.isPending ||
      duplicateMutation.isPending ||
      cloneMutation.isPending,
  };
}
