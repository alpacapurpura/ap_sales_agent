"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import {
  placementApi,
  type Placement,
  type PlacementCreateDTO,
  type PlacementUpdateDTO,
  type SourceTable,
} from "@/lib/api/placement";

const NO_AUTH_TOKEN_ERROR = "No auth token";

/**
 * List placements for a given source row (testimonial/authority/team) + mutations.
 */
export function usePlacements(params: {
  sourceTable: SourceTable;
  sourceId: string | null | undefined;
}) {
  const { sourceTable, sourceId } = params;
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const routeParams = useParams<{ tenantId: string }>();
  const tenantId = routeParams?.tenantId ?? "";
  const queryKey = ["placements", tenantId, sourceTable, sourceId] as const;

  const { data, isLoading, error } = useQuery<Placement[]>({
    queryKey,
    enabled: Boolean(sourceId),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !sourceId) return [];
      return placementApi.listBySource(token, sourceTable, sourceId);
    },
    retry: (failureCount, err: Error) => {
      if (err.message.includes("401") || err.message.includes("404")) return false;
      return failureCount < 2;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (dto: PlacementCreateDTO) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return placementApi.create(token, dto);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const patchMutation = useMutation({
    mutationFn: async ({ id, data: patchData }: { id: string; data: PlacementUpdateDTO }) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return placementApi.patch(token, id, patchData);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return placementApi.delete(token, id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  return {
    placements: data ?? [],
    isLoading,
    error,
    create: createMutation.mutateAsync,
    patch: patchMutation.mutateAsync,
    remove: deleteMutation.mutateAsync,
    isCreating: createMutation.isPending,
  };
}
