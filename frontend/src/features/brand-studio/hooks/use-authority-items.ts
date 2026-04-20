"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import {
  authorityApi,
  type AuthorityItem,
  type AuthorityCreateDTO,
  type AuthorityUpdateDTO,
} from "@/lib/api/authority-item";

const NO_AUTH_TOKEN_ERROR = "No auth token";

/**
 * Tenant-scoped list of authority items + CRUD mutations.
 */
export function useAuthorityItems() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";
  const queryKey = ["authority_items", tenantId] as const;

  const { data, isLoading, error } = useQuery<AuthorityItem[]>({
    queryKey,
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return authorityApi.list(token);
    },
    retry: (failureCount, err: Error) => {
      if (err.message.includes("401") || err.message.includes("404")) return false;
      return failureCount < 2;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (dto: AuthorityCreateDTO) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return authorityApi.create(token, dto);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const patchMutation = useMutation({
    mutationFn: async ({ id, data: patchData }: { id: string; data: AuthorityUpdateDTO }) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return authorityApi.patch(token, id, patchData);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return authorityApi.delete(token, id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const cloneMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return authorityApi.clone(token, id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  return {
    authorityItems: data ?? [],
    isLoading,
    error,
    create: createMutation.mutateAsync,
    patch: patchMutation.mutateAsync,
    remove: deleteMutation.mutateAsync,
    clone: cloneMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isPatching: patchMutation.isPending,
  };
}
