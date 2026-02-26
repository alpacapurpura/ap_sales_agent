"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { settingsApi, SystemUserProfile } from "@/lib/api/settings";

export function useUserProfile() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  
  // Read tenant ID to invalidate cache on switch
  // This is safe because useQuery handles the key change
  const tenantId = typeof window !== 'undefined' ? localStorage.getItem('x-tenant-id') : null;

  return useQuery<SystemUserProfile>({
    queryKey: ["user-profile", tenantId], // Include tenantId in key to force refresh on switch
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return settingsApi.getProfile(token);
    },
    enabled: isLoaded && isSignedIn,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
