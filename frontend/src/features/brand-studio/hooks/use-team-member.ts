"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { teamMemberApi, type TeamMember } from "@/lib/api/team-member";

/**
 * Single-team-member query keyed by (tenant_id, member_id).
 */
export function useTeamMember(memberId: string | null | undefined) {
  const { getToken } = useAuth();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";

  return useQuery<TeamMember | null>({
    queryKey: ["team_member", tenantId, memberId],
    enabled: Boolean(memberId),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !memberId) return null;
      return teamMemberApi.get(token, memberId);
    },
    retry: (failureCount, err: Error) => {
      if (err.message.includes("401") || err.message.includes("404")) return false;
      return failureCount < 2;
    },
  });
}
