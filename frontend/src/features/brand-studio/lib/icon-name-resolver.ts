/**
 * Resolves Lucide React component names (strings from the backend brand
 * section catalog) to actual icon components. Mirrors
 * ``features/offer-studio/lib/icon-name-resolver.ts`` — kept per-feature
 * to respect FE boundary rules (brand-studio must not import from
 * offer-studio). Promote to a shared lib once a 3rd studio needs the
 * same resolver.
 */

import {
  FileText,
  Fingerprint,
  Flag,
  Headphones,
  Landmark,
  Layers,
  Megaphone,
  MessageCircle,
  Palette,
  Scale,
  ScrollText,
  Sparkles,
  Target,
  Users,
} from "lucide-react";

import type { LucideIcon } from "lucide-react";

export const BRAND_ICON_BY_NAME: Readonly<Record<string, LucideIcon>> = {
  FileText,
  Fingerprint,
  Flag,
  Headphones,
  Landmark,
  Layers,
  Megaphone,
  MessageCircle,
  Palette,
  Scale,
  ScrollText,
  Sparkles,
  Target,
  Users,
};

/**
 * Return the ``LucideIcon`` for a brand-catalog ``icon_name``. Falls back
 * to ``Sparkles`` when the name is unknown so a missing icon never
 * crashes the UI.
 */
export function resolveBrandIconByName(iconName: string | undefined): LucideIcon {
  if (!iconName) return Sparkles;
  return BRAND_ICON_BY_NAME[iconName] ?? Sparkles;
}
