"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { settingsApi, SystemUserProfile } from "@/lib/api/settings";

export function useUserProfile() {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery<SystemUserProfile>({
    queryKey: ["user-profile"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return settingsApi.getProfile(token);
    },
    enabled: isLoaded && isSignedIn,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
