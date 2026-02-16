'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { ThemeProvider } from '@/components/providers/theme-provider'
import DevelopmentTools from '@/components/shared/development-tools'
import { Toaster } from "@/components/ui/sonner"
import { useUser } from '@clerk/nextjs'

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient())
  const { user } = useUser()

  useEffect(() => {
    if (user?.publicMetadata?.tenant_id) {
      localStorage.setItem('x-tenant-id', user.publicMetadata.tenant_id as string)
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
        {children}
        <Toaster />
      </ThemeProvider>
      <DevelopmentTools />
    </QueryClientProvider>
  )
}
