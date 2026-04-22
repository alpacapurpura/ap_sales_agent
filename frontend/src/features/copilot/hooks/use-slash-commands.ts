"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { listSlashCommands } from "../api/commands-api";

/**
 * Query hook for available slash commands.
 * staleTime: 5min — slash commands change rarely.
 */
export function useSlashCommands() {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery({
    queryKey: ["copilot", "slash-commands"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return listSlashCommands(token);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: isLoaded && isSignedIn === true,
  });
}
