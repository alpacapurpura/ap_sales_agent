/**
 * Brand Studio — Section Configuration
 *
 * Single source of truth for the 6-section Brand Studio layout.
 * Defines navigation structure, icons, routes, and health validation
 * mappings for each section.
 *
 * Adding a new section:
 *  1. Add entry to BRAND_SECTIONS
 *  2. Create view component in components/views/
 *  3. Create route page in app/(main)/[tenantId]/(dashboard)/brand-studio/<slug>/page.tsx
 *  4. Add to sidebar navItems in app-sidebar.tsx
 */

import {
  Building2,
  Target,
  Users,
  Award,
  Contact,
  Crosshair,
  BookOpen,
  Trophy,
  Compass,
  MessageSquare,
  Palette,
  Image as ImageIcon,
  UserSearch,
  Lightbulb,
  LayoutGrid,
  Theater,
  type LucideIcon,
} from "lucide-react";
import type { BrandSettings } from "../types";
import type { EditMode } from "../types/edit-mode";
import type { StatusResult } from "../utils/brand-validation";
import {
  validateIdentity,
  validateStory,
  validatePositioning,
  validateTeam,
  validateAuthority,
  validateContact,
  validateNarrative,
  validateStrategy,
  validateAvatars,
  validateVisuals,
  validateCommunicationAssets,
} from "../utils/brand-validation";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type BrandSectionId = "esencia" | "estrategia" | "publico" | "identidad-creativa";

export interface SectionNavItemConfig {
  /** Unique key within the section */
  id: string;
  /** Display label */
  label: string;
  /** Lucide icon component */
  icon: LucideIcon;
  /** DOM id to scroll to */
  scrollTo: string;
  /** Validation functions that determine this item's health */
  validators: ((settings: BrandSettings) => StatusResult)[];
}

export interface BrandSectionConfig {
  id: BrandSectionId;
  label: string;
  subtitle: string;
  icon: LucideIcon;
  /** Route slug under /brand-studio/ */
  slug: string;
  /** Nav rail items for in-page navigation */
  navItems: SectionNavItemConfig[];
}

// ---------------------------------------------------------------------------
// Validator Adapters
// (Wrap existing validators to accept full BrandSettings for uniform API)
// ---------------------------------------------------------------------------

const vIdentity = (s: BrandSettings) => validateIdentity(s.identity ?? {});
const vStory = (s: BrandSettings) => validateStory(s.story ?? {});
const vPositioning = (s: BrandSettings) => validatePositioning(s.positioning);
const vTeam = (s: BrandSettings) => validateTeam(s.team ?? []);
const vAuthority = (s: BrandSettings) => validateAuthority(s.authority_vault ?? []);
const vContact = (s: BrandSettings) => validateContact(s.contact ?? {});
const vNarrative = (s: BrandSettings) => validateNarrative(s.narrative);
const vStrategy = (s: BrandSettings) => validateStrategy(s.strategy ?? { methodology_pillars: [] });
const vAvatars = (s: BrandSettings) => validateAvatars(s.visuals ?? {});
const vVisuals = (s: BrandSettings) => validateVisuals(s.visuals ?? {});
const vCommAssets = (s: BrandSettings) => validateCommunicationAssets(s.communication_assets);

// ---------------------------------------------------------------------------
// Section Definitions
// ---------------------------------------------------------------------------

export const BRAND_SECTIONS: Record<BrandSectionId, BrandSectionConfig> = {
  esencia: {
    id: "esencia",
    label: "Esencia",
    subtitle: "Tu ADN — quien eres",
    icon: Building2,
    slug: "esencia",
    navItems: [
      {
        id: "origin",
        label: "Origen",
        icon: BookOpen,
        scrollTo: "story",
        validators: [vIdentity, vStory],
      },
      {
        id: "personality",
        label: "Personalidad",
        icon: Target,
        scrollTo: "values-essence",
        validators: [vPositioning],
      },
      {
        id: "voice-personality",
        label: "Voz & Personalidad",
        icon: Theater,
        scrollTo: "voice-personality",
        validators: [],
      },
      { id: "team", label: "Equipo", icon: Users, scrollTo: "team", validators: [vTeam] },
      {
        id: "credibility",
        label: "Credibilidad",
        icon: Award,
        scrollTo: "authority",
        validators: [vAuthority],
      },
      {
        id: "contact",
        label: "Contacto",
        icon: Contact,
        scrollTo: "contact",
        validators: [vContact],
      },
    ],
  },

  estrategia: {
    id: "estrategia",
    label: "Estrategia",
    subtitle: "Tu plan de juego",
    icon: Crosshair,
    slug: "estrategia",
    navItems: [
      {
        id: "positioning",
        label: "Posicionamiento",
        icon: Trophy,
        scrollTo: "positioning",
        validators: [vPositioning],
      },
      {
        id: "market",
        label: "Mercado",
        icon: Crosshair,
        scrollTo: "market",
        validators: [vPositioning],
      },
      {
        id: "storybrand",
        label: "StoryBrand",
        icon: BookOpen,
        scrollTo: "storybrand",
        validators: [vNarrative],
      },
      {
        id: "methodology",
        label: "Metodologia",
        icon: Compass,
        scrollTo: "methodology",
        validators: [vStrategy],
      },
    ],
  },

  publico: {
    id: "publico",
    label: "Público",
    subtitle: "Tus clientes ideales",
    icon: UserSearch,
    slug: "publico",
    navItems: [
      {
        id: "avatars",
        label: "Buyer Personas",
        icon: UserSearch,
        scrollTo: "avatars",
        validators: [vAvatars],
      },
    ],
  },

  "identidad-creativa": {
    id: "identidad-creativa",
    label: "Identidad Creativa",
    subtitle: "Tu imagen, voz y mensajes",
    icon: Palette,
    slug: "identidad-creativa",
    navItems: [
      {
        id: "gallery",
        label: "Galeria de Marca",
        icon: LayoutGrid,
        scrollTo: "gallery",
        validators: [vVisuals],
      },
      {
        id: "design-system",
        label: "Sistema de Diseno",
        icon: Palette,
        scrollTo: "visuals",
        validators: [vVisuals],
      },
      { id: "logos", label: "Logos", icon: ImageIcon, scrollTo: "logos", validators: [vVisuals] },
      {
        id: "concepts",
        label: "Conceptos Creativos",
        icon: Lightbulb,
        scrollTo: "creative-concepts",
        validators: [vCommAssets],
      },
      {
        id: "funnel-assets",
        label: "Assets por Funnel",
        icon: LayoutGrid,
        scrollTo: "funnel-assets",
        validators: [vCommAssets],
      },
    ],
  },
};

// ---------------------------------------------------------------------------
// Edit Mode Metadata (for EditSheetManager headers)
// ---------------------------------------------------------------------------

export const EDIT_MODE_META: Record<EditMode, { title: string; desc: string }> = {
  none: { title: "Editar", desc: "Realiza cambios en tu marca." },
  identity: { title: "Identidad Corporativa", desc: "Edita los datos fundamentales de tu marca." },
  voice: { title: "Voz & Comunicacion", desc: "Configura el tono y estilo de comunicacion." },
  legal: { title: "Datos Legales", desc: "Informacion fiscal y legal." },
  authority: { title: "Autoridad & Prensa", desc: "Gestiona premios y apariciones en medios." },
  team: { title: "Equipo", desc: "Gestiona los miembros clave de la marca." },
  testimonials: {
    title: "Testimonios",
    desc: "Gestiona la prueba social y opiniones de clientes.",
  },
  avatars: { title: "Avatares", desc: "Personaliza los avatares para diferentes canales." },
  contact: { title: "Contacto", desc: "Informacion publica de contacto." },
  visuals: { title: "Identidad Visual", desc: "Colores, tipografia y estilo." },
  "visuals-wizard": { title: "Wizard Visual", desc: "Extrae tu identidad visual automaticamente." },
  logos: { title: "Kit de Logos", desc: "Gestiona las variantes de tu logo." },
  story: { title: "Historia de Origen", desc: "El relato fundacional de tu marca." },
  methodology: { title: "Metodologia", desc: "Tus pilares y metodos unicos." },
  positioning: {
    title: "Posicionamiento",
    desc: "Entorno competitivo, insight y beneficios (Brand Love Key).",
  },
  "values-essence": {
    title: "Valores & Esencia",
    desc: "Valores, personalidad, RTBs y esencia de marca.",
  },
  storybrand: { title: "Narrativa StoryBrand", desc: "El viaje del heroe de tu marca." },
  "communication-assets": {
    title: "Activos de Comunicacion",
    desc: "Conceptos creativos y piezas por etapa de funnel.",
  },
  "personality-profile": {
    title: "Voz & Personalidad",
    desc: "Configura cómo habla y se expresa tu agente de ventas.",
  },
};

/** Ordered list of sections for sidebar rendering */
export const BRAND_SECTION_ORDER: BrandSectionId[] = [
  "esencia",
  "estrategia",
  "publico",
  "identidad-creativa",
];

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

/**
 * Compute health for a single nav item by aggregating its validators.
 */
export function computeNavItemHealth(
  item: SectionNavItemConfig,
  settings: BrandSettings,
): { score: number; status: "complete" | "partial" | "empty"; missingFields: string[] } {
  const results = item.validators.map((v) => v(settings));
  if (results.length === 0) return { score: 0, status: "empty", missingFields: [] };

  const score = Math.round(results.reduce((a, r) => a + r.score, 0) / results.length);
  const allComplete = results.every((r) => r.status === "complete");
  const allEmpty = results.every((r) => r.status === "empty");
  const status = allComplete
    ? ("complete" as const)
    : allEmpty
      ? ("empty" as const)
      : ("partial" as const);
  const missingFields = results.flatMap((r) => r.missingFields);

  return { score, status, missingFields };
}

/**
 * Build the full nav item array with computed health for a section.
 */
export function buildSectionNavItems(sectionId: BrandSectionId, settings: BrandSettings) {
  const section = BRAND_SECTIONS[sectionId];
  return section.navItems.map((item) => ({
    ...item,
    ...computeNavItemHealth(item, settings),
  }));
}
