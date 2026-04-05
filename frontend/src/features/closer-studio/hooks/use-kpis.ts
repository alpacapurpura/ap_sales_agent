"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { fetchKPIs } from "../api";

export function useKPIs() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["closer-studio", "kpis"],
    queryFn: async () => {
      const token = (await getToken()) ?? "";
      return fetchKPIs(token);
    },
    refetchInterval: 30_000,
    staleTime: 15_000,
  });
}
