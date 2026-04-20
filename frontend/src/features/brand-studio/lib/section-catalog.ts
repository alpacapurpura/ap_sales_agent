/**
 * Slug → display metadata for every brand-studio section. Single source of
 * truth for labels and icons used by the nav rail, breadcrumb and topbar.
 *
 * Keeping this here (client-safe) rather than on the backend because the
 * brand-studio section names are pure UI concerns — the backend stores the
 * data by key, not by label.
 */

import {
  FileText,
  Fingerprint,
  Flag,
  Headphones,
  Landmark,
  Layers,
  Megaphone,
  Palette,
  ScrollText,
  Sparkles,
  Target,
  Users,
} from "lucide-react";

export interface BrandSectionMeta {
  slug: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  /** Whether this section edits a collection (buyer personas, team, etc.). */
  kind: "singleton" | "collection";
}

export const BRAND_SECTIONS: readonly BrandSectionMeta[] = [
  { slug: "publico", label: "Buyer personas", icon: Sparkles, kind: "collection" },
  { slug: "identity", label: "Identidad", icon: Fingerprint, kind: "singleton" },
  { slug: "positioning", label: "Posicionamiento", icon: Target, kind: "singleton" },
  { slug: "narrative", label: "Narrativa", icon: ScrollText, kind: "singleton" },
  { slug: "methodology", label: "Metodología", icon: Flag, kind: "singleton" },
  { slug: "story", label: "Historia", icon: FileText, kind: "singleton" },
  { slug: "team", label: "Equipo", icon: Users, kind: "collection" },
  { slug: "authority", label: "Autoridad", icon: Landmark, kind: "collection" },
  { slug: "testimonials", label: "Testimonios", icon: Headphones, kind: "collection" },
  { slug: "visuals", label: "Visuales", icon: Palette, kind: "singleton" },
  { slug: "communication-assets", label: "Assets", icon: Layers, kind: "singleton" },
  { slug: "contact", label: "Contacto", icon: Megaphone, kind: "singleton" },
] as const;

const BY_SLUG: Record<string, BrandSectionMeta> = Object.fromEntries(
  BRAND_SECTIONS.map((s) => [s.slug, s]),
);

/** Returns the section meta for a slug, or undefined for unknown slugs. */
export function getBrandSection(slug: string): BrandSectionMeta | undefined {
  return BY_SLUG[slug];
}

/** Returns the section label for breadcrumbs — falls back to the slug. */
export function getBrandSectionLabel(slug: string): string {
  return BY_SLUG[slug]?.label ?? slug;
}
