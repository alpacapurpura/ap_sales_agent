'use client';

import "../../sentry.client.config";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { ThemeProvider } from '@/components/providers/theme-provider'
import { NavigationProvider, NavigationOverlay } from '@/components/shared/navigation'
import DevelopmentTools from '@/components/shared/development-tools'
import { Toaster } from "@/components/ui/sonner"
import { useUser } from '@clerk/nextjs'
import * as Sentry from "@sentry/nextjs"

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient())
  const { user } = useUser()

  useEffect(() => {
    if (user?.publicMetadata?.tenant_id) {
      const tenantId = user.publicMetadata.tenant_id as string
      localStorage.setItem('x-tenant-id', tenantId)
      Sentry.setTag("tenant_id", tenantId)
    }
    if (user) {
      Sentry.setUser({ id: user.id, email: user.primaryEmailAddress?.emailAddress })
    } else {
      Sentry.setUser(null)
    }
  }, [user])

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <NavigationProvider>
          <NavigationOverlay />
          {children}
        </NavigationProvider>
        <Toaster />
      </ThemeProvider>
      <DevelopmentTools />
    </QueryClientProvider>
  )
}
