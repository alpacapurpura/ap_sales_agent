"use client"

import { Suspense } from "react"
import { useParams } from "next/navigation"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { NavLink } from "@/components/shared/navigation"
import { getProvider } from "@/features/connections/config/provider-registry"
import { OAuthCallbackHandler } from "@/features/connections/components/oauth-callback-handler"
import { useSearchParams } from "next/navigation"

function DetailContent() {
  const params = useParams()
  const searchParams = useSearchParams()
  const tenantId = params?.tenantId as string
  const providerId = params?.provider as string

  // OAuth callback detection (popup mode)
  const isPopupCallback =
    typeof window !== "undefined" &&
    !!window.opener &&
    !!(searchParams?.get("code") || searchParams?.get("error"))

  if (isPopupCallback) {
    return <OAuthCallbackHandler provider="auto" />
  }

  const provider = getProvider(providerId)

  if (!provider) {
    return (
      <div className="p-10">
        <p className="text-muted-foreground">Integración no encontrada.</p>
        <NavLink href={`/${tenantId}/connections`}>
          <Button variant="link" className="mt-2 px-0">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Volver a Conexiones
          </Button>
        </NavLink>
      </div>
    )
  }

  const ProviderComponent = provider.component

  return (
    <div className="space-y-6 p-6 md:p-10 pb-16">
      {/* Breadcrumb / back link */}
      <div className="flex items-center gap-4">
        <NavLink href={`/${tenantId}/connections`} loadingClassName="opacity-70">
          <Button variant="ghost" size="sm" className="gap-2 text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            Conexiones
          </Button>
        </NavLink>
        <span className="text-muted-foreground">/</span>
        <h2 className="text-lg font-semibold">{provider.name}</h2>
      </div>

      <div className="border-t" />

      {/* Provider-specific view */}
      <Suspense
        fallback={
          <div className="flex items-center justify-center py-16 text-muted-foreground">
            Cargando...
          </div>
        }
      >
        <ProviderComponent />
      </Suspense>
    </div>
  )
}

export function ConnectionDetailLayout() {
  return (
    <Suspense fallback={<div className="p-10 text-muted-foreground">Cargando...</div>}>
      <DetailContent />
    </Suspense>
  )
}
