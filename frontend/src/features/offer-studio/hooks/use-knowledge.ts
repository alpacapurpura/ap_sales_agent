// Offer knowledge sources hooks — CONTRACT.md §5.4
import { useAuth } from "@clerk/nextjs";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { toast } from "sonner";
import { knowledgeApi } from "../api/knowledge-api";
import type {
  KnowledgeListQuery,
  KnowledgeListResponse,
  KnowledgeSourceResponse,
  KnowledgeUrlIngestPayload,
} from "../types/knowledge";

const knowledgeKey = (offerId: string, query?: KnowledgeListQuery) =>
  ["offer", offerId, "knowledge", query ?? {}] as const;

export function useKnowledgeSources(
  offerId: string,
  query?: KnowledgeListQuery,
) {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery<KnowledgeListResponse, Error>({
    queryKey: knowledgeKey(offerId, query),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return knowledgeApi.list(offerId, query, token);
    },
    enabled: isLoaded && isSignedIn && !!offerId && offerId !== "undefined",
    staleTime: 30 * 1000,
  });
}

const invalidateKnowledge = (
  queryClient: ReturnType<typeof useQueryClient>,
  offerId: string,
) => {
  queryClient.invalidateQueries({ queryKey: ["offer", offerId, "knowledge"] });
  queryClient.invalidateQueries({ queryKey: ["offer", offerId, "counts"] });
};

export function useUploadKnowledge(offerId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<KnowledgeSourceResponse, Error, File>({
    mutationFn: async (file) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return knowledgeApi.upload(offerId, file, token);
    },
    onSuccess: () => {
      invalidateKnowledge(queryClient, offerId);
      toast.success("Archivo de conocimiento subido");
    },
    onError: (err) => {
      toast.error(err.message || "Error al subir el archivo");
    },
  });
}

export function useAddKnowledgeUrl(offerId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<KnowledgeSourceResponse, Error, KnowledgeUrlIngestPayload>(
    {
      mutationFn: async (payload) => {
        const token = await getToken();
        if (!token) throw new Error("No autenticado");
        return knowledgeApi.addUrl(offerId, payload, token);
      },
      onSuccess: () => {
        invalidateKnowledge(queryClient, offerId);
        toast.success("URL añadida a la base de conocimiento");
      },
      onError: (err) => {
        toast.error(err.message || "Error al registrar la URL");
      },
    },
  );
}

export function useDeleteKnowledge(offerId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (sourceId) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      await knowledgeApi.remove(offerId, sourceId, token);
    },
    onSuccess: () => {
      invalidateKnowledge(queryClient, offerId);
      toast.success("Fuente eliminada");
    },
    onError: (err) => {
      toast.error(err.message || "Error al eliminar la fuente");
    },
  });
}

export function useReindexKnowledge(offerId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<KnowledgeSourceResponse, Error, string>({
    mutationFn: async (sourceId) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return knowledgeApi.reindex(offerId, sourceId, token);
    },
    onSuccess: () => {
      invalidateKnowledge(queryClient, offerId);
      toast.success("Reindexación en cola");
    },
    onError: (err) => {
      toast.error(err.message || "Error al reindexar la fuente");
    },
  });
}
