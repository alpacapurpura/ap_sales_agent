// Offer assets hooks — CONTRACT.md §5.3
import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { assetsApi } from "../api/assets-api";

import type {
  AssetGeneratePayload,
  AssetListQuery,
  AssetListResponse,
  AssetResponse,
} from "../types/assets";

const assetsKey = (offerId: string, query?: AssetListQuery) =>
  ["offer", offerId, "assets", query ?? {}] as const;

/**
 *
 */
export function useAssets(offerId: string, query?: AssetListQuery) {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery<AssetListResponse, Error>({
    queryKey: assetsKey(offerId, query),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return assetsApi.list(offerId, query, token);
    },
    enabled: isLoaded && isSignedIn && !!offerId && offerId !== "undefined",
    staleTime: 30 * 1000,
  });
}

const invalidateAssets = (queryClient: ReturnType<typeof useQueryClient>, offerId: string) => {
  void queryClient.invalidateQueries({ queryKey: ["offer", offerId, "assets"] });
  void queryClient.invalidateQueries({ queryKey: ["offer", offerId, "counts"] });
};

/**
 *
 */
export function useUploadAsset(offerId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<AssetResponse, Error, File>({
    mutationFn: async (file) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return assetsApi.upload(offerId, file, token);
    },
    onSuccess: () => {
      invalidateAssets(queryClient, offerId);
      toast.success("Recurso subido correctamente");
    },
    onError: (err) => {
      toast.error(err.message || "Error al subir el recurso");
    },
  });
}

/**
 *
 */
export function useCreateAsset(offerId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<AssetResponse, Error, AssetGeneratePayload>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return assetsApi.generate(offerId, payload, token);
    },
    onSuccess: () => {
      invalidateAssets(queryClient, offerId);
      toast.success("Generación de recurso en cola");
    },
    onError: (err) => {
      toast.error(err.message || "Error al generar el recurso");
    },
  });
}

/**
 *
 */
export function useDeleteAsset(offerId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (assetId) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      await assetsApi.remove(offerId, assetId, token);
    },
    onSuccess: () => {
      invalidateAssets(queryClient, offerId);
      toast.success("Recurso eliminado");
    },
    onError: (err) => {
      toast.error(err.message || "Error al eliminar el recurso");
    },
  });
}
