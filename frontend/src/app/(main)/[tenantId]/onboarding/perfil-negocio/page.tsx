import { Sparkles } from "lucide-react";

import { BusinessTypesOnboardingClient } from "./BusinessTypesOnboardingClient";

interface OnboardingPerfilNegocioPageProps {
  params: { tenantId: string };
  searchParams: { returnTo?: string };
}

/**
 * Full-screen onboarding gate for declaring business_types.
 *
 * No sidebar, no header — tenant must complete this before accessing
 * the dashboard.
 *
 * SERVER COMPONENT: catalog fetch happens server-side.
 * Client interactivity is delegated to BusinessTypesOnboardingClient.
 *
 * CONTRACT §6.3 — onboarding/perfil-negocio/page.tsx
 */
export default function OnboardingPerfilNegocioPage({
  params,
  searchParams,
}: OnboardingPerfilNegocioPageProps) {
  const returnTo = searchParams.returnTo ?? `/${params.tenantId}/overview`;

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/30 flex items-center justify-center p-6">
      <div className="w-full max-w-5xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-primary/10 mb-2">
            <Sparkles className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            ¿Qué tipo de negocio manejás?
          </h1>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            Esto personaliza tus plantillas de ofertas, landings y el agente de ventas para que se
            adapten exactamente a lo que vendés.
          </p>
          <p className="text-sm text-muted-foreground">
            Elegí entre 1 y 2 categorías. Podés cambiarlo después desde la configuración.
          </p>
        </div>

        {/* Interactive selector + CTA (client component) */}
        <BusinessTypesOnboardingClient tenantId={params.tenantId} returnTo={returnTo} />
      </div>
    </div>
  );
}
