import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { enrollmentsApi } from "../api/enrollments-api";

import type { EnrollmentFilters } from "../types/enrollment";

/** List enrollments filtered by any combination of params. */
export function useEnrollments(filters: EnrollmentFilters = {}) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["enrollments", filters],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return enrollmentsApi.list(filters, token);
    },
    staleTime: 60 * 1000,
  });
}

/** Return the most recent enrollment linked to a conversation (or null). */
export function useActiveEnrollmentForConversation(conversationId: string | null | undefined) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["enrollment", "by-conversation", conversationId],
    queryFn: async () => {
      if (!conversationId) return null;
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return enrollmentsApi.getByConversation(conversationId, token);
    },
    enabled: Boolean(conversationId),
    staleTime: 30 * 1000,
  });
}
