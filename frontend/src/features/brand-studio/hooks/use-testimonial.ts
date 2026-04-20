"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { testimonialApi, type Testimonial } from "@/lib/api/testimonial";

/**
 * Single-testimonial query keyed by (tenant_id, testimonial_id).
 */
export function useTestimonial(testimonialId: string | null | undefined) {
  const { getToken } = useAuth();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";

  return useQuery<Testimonial | null>({
    queryKey: ["testimonial", tenantId, testimonialId],
    enabled: Boolean(testimonialId),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !testimonialId) return null;
      return testimonialApi.get(token, testimonialId);
    },
    retry: (failureCount, err: Error) => {
      if (err.message.includes("401") || err.message.includes("404")) return false;
      return failureCount < 2;
    },
  });
}
