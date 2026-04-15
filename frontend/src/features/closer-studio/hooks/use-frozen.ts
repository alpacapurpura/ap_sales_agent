"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchFrozen } from "../api";

export function useFrozen() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["closer-studio", "frozen"],
    queryFn: async () => {
      const token = (await getToken()) ?? "";
      return fetchFrozen(token);
    },
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}
