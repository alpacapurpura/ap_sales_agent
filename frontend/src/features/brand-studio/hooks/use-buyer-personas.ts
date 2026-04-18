"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import {
  buyerPersonaApi,
  type BuyerPersona,
  type BuyerPersonaCreateDTO,
  type BuyerPersonaSectionUpdateDTO,
} from "@/lib/api/buyer-persona";

const NO_AUTH_TOKEN_ERROR = "No auth token";

/**
 *
 */
export function useBuyerPersonas() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";
  const queryKey = ["buyer_personas", tenantId] as const;

  const { data, isLoading, error } = useQuery<BuyerPersona[]>({
    queryKey: queryKey,
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return buyerPersonaApi.list(token);
    },
    retry: (failureCount, err: Error) => {
      if (err.message.includes("401") || err.message.includes("404")) return false;
      return failureCount < 2;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (dto: BuyerPersonaCreateDTO) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return buyerPersonaApi.create(token, dto);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKey });
    },
  });

  const patchMutation = useMutation({
    mutationFn: async ({
      id,
      data: patchData,
    }: {
      id: string;
      data: BuyerPersonaSectionUpdateDTO;
    }) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return buyerPersonaApi.patch(token, id, patchData);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKey });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return buyerPersonaApi.delete(token, id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKey });
    },
  });

  return {
    personas: data ?? [],
    isLoading,
    error,
    create: createMutation.mutateAsync,
    patch: patchMutation.mutateAsync,
    remove: deleteMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isPatching: patchMutation.isPending,
  };
}
