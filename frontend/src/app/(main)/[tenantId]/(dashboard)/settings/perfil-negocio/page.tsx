import { fetchTenantProfileServer } from "@/features/tenant-profile/api/tenant-profile-server";

import { PerfilNegocioSettingsClient } from "./PerfilNegocioSettingsClient";

interface PerfilNegocioPageProps {
  params: Promise<{ tenantId: string }>;
}

/**
 * Settings sub-section for managing business_types.
 *
 * SERVER COMPONENT: loads current profile server-side to seed the form.
 * Client interactivity is delegated to PerfilNegocioSettingsClient.
 *
 * CONTRACT §6.3 — settings/perfil-negocio/page.tsx
 */
export default async function PerfilNegocioPage({ params }: PerfilNegocioPageProps) {
  const { tenantId } = await params;
  const profile = await fetchTenantProfileServer(tenantId);

  return (
    <div className="space-y-6 p-6 max-w-3xl">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Perfil de negocio</h1>
        <p className="text-muted-foreground">
          Definí qué tipo de negocio manejás. Esto personaliza los tipos de oferta del wizard,
          plantillas de landing y el contexto del agente de ventas.
        </p>
      </div>

      <PerfilNegocioSettingsClient initialProfile={profile} />
    </div>
  );
}
