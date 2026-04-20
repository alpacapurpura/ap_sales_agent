"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import {
  testimonialApi,
  type Testimonial,
  type TestimonialCreateDTO,
  type TestimonialUpdateDTO,
} from "@/lib/api/testimonial";

const NO_AUTH_TOKEN_ERROR = "No auth token";

/**
 * Tenant-scoped list of testimonials + CRUD mutations.
 */
export function useTestimonials() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";
  const queryKey = ["testimonials", tenantId] as const;

  const { data, isLoading, error } = useQuery<Testimonial[]>({
    queryKey,
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return testimonialApi.list(token);
    },
    retry: (failureCount, err: Error) => {
      if (err.message.includes("401") || err.message.includes("404")) return false;
      return failureCount < 2;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (dto: TestimonialCreateDTO) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return testimonialApi.create(token, dto);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const patchMutation = useMutation({
    mutationFn: async ({ id, data: patchData }: { id: string; data: TestimonialUpdateDTO }) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return testimonialApi.patch(token, id, patchData);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return testimonialApi.delete(token, id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const cloneMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error(NO_AUTH_TOKEN_ERROR);
      return testimonialApi.clone(token, id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  return {
    testimonials: data ?? [],
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
