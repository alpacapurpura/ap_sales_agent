import {
  AgendaPage,
  EquipoPage,
  GeneralPage,
  LlmKeysPage,
  PagosPage,
  PerfilNegocioPage,
  PerfilPage,
  WebhooksPage,
} from "./section-pages";

/**
 * Server-safe registry of settings section pages.
 *
 * This module intentionally has NO "use client" directive. The catch-all
 * Server Component dispatcher at
 * app/(main)/[tenantId]/(dashboard)/settings/[section]/page.tsx
 * needs to index the map (``section in SETTINGS_SECTION_MAP``) and pick a
 * component. When the map lives in a "use client" module its exports are
 * replaced with opaque client references on the server and the index lookup
 * silently returns false → notFound() fires → 404 for every real route.
 * Defining the map here keeps it a plain server-land object whose values
 * happen to be client components — Next renders them through the normal
 * client boundary.
 */
export const SETTINGS_SECTION_MAP = {
  general: GeneralPage,
  perfil: PerfilPage,
  equipo: EquipoPage,
  "perfil-negocio": PerfilNegocioPage,
  "llm-keys": LlmKeysPage,
  agenda: AgendaPage,
  pagos: PagosPage,
  webhooks: WebhooksPage,
} as const satisfies Readonly<Record<string, () => React.JSX.Element>>;

export type SettingsSectionSlug = keyof typeof SETTINGS_SECTION_MAP;
