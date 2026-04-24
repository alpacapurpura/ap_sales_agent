"use client";

import { useParams } from "next/navigation";

import { CommunicationStyleView } from "@/features/brand-studio/components/communication-style/CommunicationStyleView";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";

/**
 * Estilo Comunicacional page. Respaldada por la tabla
 * `personality_profiles`, no por `BrandSettings` JSONB — por eso no usa
 * el `SectionPage` genérico ni el factory de brand.
 *
 * Lee el campo legacy `voice_tone` de `BrandSettings.identity` para
 * ofrecer la migration card one-time a tenants con texto existente. El
 * flag `voice_tone_migration_dismissed` lo persiste `MigrationCard` en
 * localStorage — pasamos `false` y dejamos que el componente chequee al
 * montar.
 */
export function EstiloPage() {
  const params = useParams<{ tenantId: string }>();
  const { tenantId } = params;
  const hook = useBrandSettings();
  const voiceToneLegacy = hook.settings?.identity?.voice_tone ?? null;

  return (
    <CommunicationStyleView
      tenantId={tenantId}
      voiceToneLegacy={voiceToneLegacy}
      voiceToneMigrationDismissed={false}
    />
  );
}
