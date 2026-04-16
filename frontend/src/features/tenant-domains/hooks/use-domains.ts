"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import * as api from "../api";

const QUERY_KEY = ["domains"] as const;

export function useDomains() {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return api.listDomains(token);
    },
    enabled: isLoaded && !!isSignedIn,
  });
}

export function useCreateDomain() {
  const { getToken } = useAuth();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async ({
      hostname,
      domainType,
    }: {
      hostname: string;
      domainType: "platform" | "custom";
    }) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return api.createDomain(token, hostname, domainType);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useDeleteDomain() {
  const { getToken } = useAuth();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return api.deleteDomain(token, id);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useSetPrimary() {
  const { getToken } = useAuth();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return api.setPrimary(token, id);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useVerifyDomain() {
  const { getToken } = useAuth();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return api.verifyDomain(token, id);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useGetDomainInstructions() {
  const { getToken } = useAuth();

  return useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return api.getDomainInstructions(token, id);
    },
  });
}
