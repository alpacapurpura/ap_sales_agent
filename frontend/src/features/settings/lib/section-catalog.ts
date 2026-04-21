/**
 * Slug → display metadata for every settings section. Single source of truth
 * for labels, icons, and groups used by the nav rail, breadcrumb and router.
 *
 * Spanish rule 11: all labels are español latinoamericano neutro — no voseo.
 */
import {
  Building2,
  CalendarClock,
  CreditCard,
  Key,
  Settings as SettingsIcon,
  User,
  Users,
  Webhook,
} from "lucide-react";

export type SettingsGroup = "principal" | "ventas" | "desarrolladores";

export interface SettingsSectionMeta {
  slug: string;
  label: string;
  group: SettingsGroup;
  icon: React.ComponentType<{ className?: string }>;
}

export const SETTINGS_GROUP_LABELS: Record<SettingsGroup, string> = {
  principal: "Principal",
  ventas: "Ventas",
  desarrolladores: "Desarrolladores",
};

export const SETTINGS_SECTIONS: readonly SettingsSectionMeta[] = [
  { slug: "general", label: "General", group: "principal", icon: SettingsIcon },
  { slug: "perfil", label: "Perfil", group: "principal", icon: User },
  { slug: "equipo", label: "Equipo", group: "principal", icon: Users },
  { slug: "perfil-negocio", label: "Perfil de negocio", group: "principal", icon: Building2 },
  { slug: "llm-keys", label: "LLM API Keys", group: "principal", icon: Key },
  { slug: "agenda", label: "Agenda", group: "ventas", icon: CalendarClock },
  { slug: "pagos", label: "Pagos", group: "ventas", icon: CreditCard },
  { slug: "webhooks", label: "Webhooks", group: "desarrolladores", icon: Webhook },
] as const;

export const SETTINGS_DEFAULT_SECTION = "general" as const;

const BY_SLUG: Record<string, SettingsSectionMeta> = Object.fromEntries(
  SETTINGS_SECTIONS.map((s) => [s.slug, s]),
);

/** Returns the section meta for a slug, or undefined for unknown slugs. */
export function getSettingsSection(slug: string): SettingsSectionMeta | undefined {
  return BY_SLUG[slug];
}

/** Returns the section label for breadcrumbs — falls back to the slug. */
export function getSettingsSectionLabel(slug: string): string {
  return BY_SLUG[slug]?.label ?? slug;
}
