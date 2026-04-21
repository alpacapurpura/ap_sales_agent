"use client";

import { AIKeysForm } from "@/features/settings/components/AiKeysForm";
import { GeneralSettingsForm } from "@/features/settings/components/GeneralSettingsForm";
import { PaymentSettingsView } from "@/features/settings/components/PaymentSettingsView";
import { PerfilNegocioSection } from "@/features/settings/components/PerfilNegocioSection";
import { ProfileView } from "@/features/settings/components/ProfileView";
import { SchedulingSettingsView } from "@/features/settings/components/SchedulingSettingsView";
import { SectionShell } from "@/features/settings/components/SectionShell";
import { TeamView } from "@/features/settings/components/TeamView";
import { WebhookView } from "@/features/settings/components/WebhookView";

/**
 * Factory page components for every settings section.
 *
 * Each export is a thin wrapper that provides the SectionShell (title +
 * description) and delegates rendering to the existing form/view component.
 *
 * The SETTINGS_SECTION_MAP in section-page-map.ts indexes these; that file
 * has NO "use client" so the server dispatcher can safely index the map.
 * These components are still client components — Next.js renders them through
 * the normal client boundary.
 */

/**
 *
 */
export function GeneralPage() {
  return (
    <SectionShell title="General" description="Configuración general del workspace.">
      <GeneralSettingsForm />
    </SectionShell>
  );
}

/**
 *
 */
export function PerfilPage() {
  return (
    <SectionShell title="Perfil" description="Tu cuenta personal dentro del workspace.">
      <ProfileView />
    </SectionShell>
  );
}

/**
 *
 */
export function EquipoPage() {
  return (
    <SectionShell title="Equipo" description="Miembros con acceso a este workspace.">
      <TeamView />
    </SectionShell>
  );
}

/**
 *
 */
export function PerfilNegocioPage() {
  return (
    <SectionShell
      title="Perfil de negocio"
      description="Define qué tipo de negocio manejas. Esto personaliza los tipos de oferta del wizard, las plantillas de landing y el contexto del agente de ventas."
    >
      <PerfilNegocioSection />
    </SectionShell>
  );
}

/**
 *
 */
export function LlmKeysPage() {
  return (
    <SectionShell title="LLM API Keys" description="Claves de API para los modelos de lenguaje.">
      <AIKeysForm />
    </SectionShell>
  );
}

/**
 *
 */
export function AgendaPage() {
  return (
    <SectionShell title="Agenda" description="Configuración del calendario y eventos.">
      <SchedulingSettingsView />
    </SectionShell>
  );
}

/**
 *
 */
export function PagosPage() {
  return (
    <SectionShell title="Pagos" description="Métodos de pago y configuración de cobros.">
      <PaymentSettingsView />
    </SectionShell>
  );
}

/**
 *
 */
export function WebhooksPage() {
  return (
    <SectionShell title="Webhooks" description="Configura los webhooks de integración.">
      <WebhookView />
    </SectionShell>
  );
}
