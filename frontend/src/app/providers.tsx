"use client";

import "../../sentry.client.config";
import { useUser } from "@clerk/nextjs";
import * as Sentry from "@sentry/nextjs";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from "react";

import { ThemeProvider } from "@/components/providers/theme-provider";
import DevelopmentTools from "@/components/shared/development-tools";
import { NavigationProvider, NavigationOverlay } from "@/components/shared/navigation";
import { Toaster } from "@/components/ui/sonner";
import { TenantLocaleProvider } from "@/features/tenant/context/tenant-locale-context";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000, // 5 min — data considered fresh
            gcTime: 10 * 60 * 1000, // 10 min — cache kept after unmount
            refetchOnWindowFocus: false, // Prevent cascade refetch on tab switch
            retry: 1, // Single retry on failure
          },
        },
      }),
  );
  const { user } = useUser();

  useEffect(() => {
    if (user?.publicMetadata?.tenant_id) {
      const tenantId = user.publicMetadata.tenant_id as string;
      localStorage.setItem("x-tenant-id", tenantId);
      Sentry.setTag("tenant_id", tenantId);
    }
    if (user) {
      Sentry.setUser({ id: user.id, email: user.primaryEmailAddress?.emailAddress });
    } else {
      Sentry.setUser(null);
    }
  }, [user]);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
        <NavigationProvider>
          <NavigationOverlay />
          <TenantLocaleProvider>{children}</TenantLocaleProvider>
        </NavigationProvider>
        <Toaster />
      </ThemeProvider>
      <DevelopmentTools />
    </QueryClientProvider>
  );
}
