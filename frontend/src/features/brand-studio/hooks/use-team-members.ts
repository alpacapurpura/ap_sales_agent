"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import {
  teamMemberApi,
  type TeamMember,
  type TeamMemberCreateDTO,
  type TeamMemberUpdateDTO,
} from "@/lib/api/team-member";

const NO_AUTH_TOKEN_ERROR = "No auth token";

/**
 * Tenant-scoped list of team members + CRUD mutations.
 */
export function useTeamMembers() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";
  const queryKey = ["team_members", tenantId] as const;

  const { data, isLoading, error } = useQuery<TeamMember[]>({
    queryKey,
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return teamMemberApi.list(token);
    },
    retry: (failureCount, err: Error) => {
      if (err.message.includes("401") || err.message.includes("404")) return false;
      return failureCount < 2;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (dto: TeamMemberCreateDTO) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return teamMemberApi.create(token, dto);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const patchMutation = useMutation({
    mutationFn: async ({ id, data: patchData }: { id: string; data: TeamMemberUpdateDTO }) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return teamMemberApi.patch(token, id, patchData);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return teamMemberApi.delete(token, id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const cloneMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return teamMemberApi.clone(token, id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  return {
    teamMembers: data ?? [],
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
