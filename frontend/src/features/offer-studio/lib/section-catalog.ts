/**
 * Slug → display metadata for every offer-studio section. Single source
 * of truth for labels and icons used by the nav rail, breadcrumb and
 * topbar.
 *
 * Kept client-safe (no backend call required) because offer-studio section
 * names are pure UI concerns — the backend stores data by ``SectionKey``
 * and the visible sections per offer are resolved dynamically by
 * ``resolvePresetSections`` + the archetype catalog. This module only
 * carries display metadata (``label`` + ``icon`` + ``kind``).
 *
 * Mirrors the brand-studio pattern at
 * ``features/brand-studio/lib/section-catalog.ts`` so both studios render
 * their FinderColumn with the same primitive.
 */

import {
  BookOpen,
  Calendar,
  CheckCircle2,
  FileText,
  Fingerprint,
  Flag,
  Gift,
  Heart,
  HelpCircle,
  Image,
  Images,
  Layers,
  MapPin,
  Megaphone,
  Monitor,
  Package,
  ShoppingCart,
  Sparkles,
  Star,
  Target,
  Users,
  Wrench,
} from "lucide-react";

import type { SectionKey } from "../api/archetype-catalog-api";

export interface OfferSectionMeta {
  slug: SectionKey;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  /** Whether the section edits a collection (testimonials, instructors, FAQ). */
  kind: "singleton" | "collection";
}

export const OFFER_SECTIONS: readonly OfferSectionMeta[] = [
  { slug: "identity", label: "Identidad", icon: Fingerprint, kind: "singleton" },
  { slug: "strategy", label: "Para quién es", icon: Target, kind: "singleton" },
  { slug: "psychology", label: "Psicología de compra", icon: Heart, kind: "singleton" },
  { slug: "promise", label: "Promesa", icon: Flag, kind: "singleton" },
  { slug: "program_details", label: "Detalles del programa", icon: Calendar, kind: "singleton" },
  { slug: "service_details", label: "Detalles del servicio", icon: Wrench, kind: "singleton" },
  { slug: "event_details", label: "Detalles del evento", icon: Calendar, kind: "singleton" },
  { slug: "product_details", label: "Detalles del producto", icon: Package, kind: "singleton" },
  {
    slug: "subscription_details",
    label: "Detalles de la suscripción",
    icon: Layers,
    kind: "singleton",
  },
  { slug: "platform_details", label: "Plataforma", icon: Monitor, kind: "singleton" },
  { slug: "location", label: "Ubicación", icon: MapPin, kind: "singleton" },
  { slug: "instructors", label: "Instructores", icon: Users, kind: "collection" },
  { slug: "value_stack", label: "Value stack", icon: Gift, kind: "singleton" },
  { slug: "pricing", label: "Pricing", icon: ShoppingCart, kind: "singleton" },
  { slug: "testimonials", label: "Testimonios", icon: Sparkles, kind: "collection" },
  { slug: "portfolio", label: "Portfolio", icon: Image, kind: "collection" },
  { slug: "faq", label: "FAQ", icon: HelpCircle, kind: "collection" },
  { slug: "gallery", label: "Galería", icon: Images, kind: "collection" },
  { slug: "resources", label: "Recursos", icon: FileText, kind: "singleton" },
  { slug: "closing", label: "Cierre", icon: Megaphone, kind: "singleton" },
  { slug: "knowledge", label: "Conocimiento", icon: BookOpen, kind: "singleton" },
] as const;

const BY_SLUG: Record<string, OfferSectionMeta> = Object.fromEntries(
  OFFER_SECTIONS.map((s) => [s.slug, s]),
);

/** Returns the section meta for a slug, or undefined for unknown slugs. */
export function getOfferSection(slug: string): OfferSectionMeta | undefined {
  return BY_SLUG[slug];
}

/** Returns the section label for breadcrumbs — falls back to the slug. */
export function getOfferSectionLabel(slug: string): string {
  return BY_SLUG[slug]?.label ?? slug;
}

/** Returns the section icon. CheckCircle2 as defensive fallback for unknown slugs. */
export function getOfferSectionIcon(slug: string) {
  return BY_SLUG[slug]?.icon ?? CheckCircle2;
}

/** True when the section is edited as a collection (landing + detail), not a singleton. */
export function isCollectionSection(slug: string): boolean {
  return BY_SLUG[slug]?.kind === "collection";
}
