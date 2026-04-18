/**
 * Resolves Lucide React component names (strings from the backend catalogs)
 * to actual icon components. The catalogs only ship ``icon_name`` as a
 * PascalCase string; the frontend imports the specific components it needs
 * and exposes a typed lookup to keep tree-shaking working.
 *
 * Adding a new icon used by a catalog entry: import it below and add it
 * to the map. The ``resolveIconByName`` function falls back to ``Sparkles``
 * when the name is unknown so a missing icon never crashes the UI.
 */

import {
  Award,
  BadgeCheck,
  BookMarked,
  BookOpen,
  Box,
  Brain,
  Briefcase,
  Building2,
  CalendarCheck,
  CalendarClock,
  CalendarDays,
  Cloud,
  Cog,
  Compass,
  CreditCard,
  Crown,
  Database,
  DollarSign,
  FileStack,
  Fingerprint,
  Gem,
  Gift,
  GraduationCap,
  Hammer,
  HeartPulse,
  Image as ImageIcon,
  Infinity as InfinityIcon,
  Library,
  Lightbulb,
  Mic,
  Monitor,
  Mountain,
  Package,
  PackageOpen,
  Presentation,
  Rocket,
  Route,
  Scale,
  Settings,
  ShoppingBag,
  Sparkles,
  Star,
  Stethoscope,
  Store,
  Target,
  Tent,
  Terminal,
  TrendingUp,
  UserCheck,
  Users,
  Video,
  Wrench,
  Zap,
  CheckCircle,
} from "lucide-react";

import type { LucideIcon } from "lucide-react";

export const ICON_BY_NAME: Readonly<Record<string, LucideIcon>> = {
  Award,
  BadgeCheck,
  BookMarked,
  BookOpen,
  Box,
  Brain,
  Briefcase,
  Building2,
  CalendarCheck,
  CalendarClock,
  CalendarDays,
  CheckCircle,
  Cloud,
  Cog,
  Compass,
  CreditCard,
  Crown,
  Database,
  DollarSign,
  FileStack,
  Fingerprint,
  Gem,
  Gift,
  GraduationCap,
  Hammer,
  HeartPulse,
  Image: ImageIcon,
  Infinity: InfinityIcon,
  Library,
  Lightbulb,
  Mic,
  Monitor,
  Mountain,
  Package,
  PackageOpen,
  Presentation,
  Rocket,
  Route,
  Scale,
  Settings,
  ShoppingBag,
  Sparkles,
  Star,
  Stethoscope,
  Store,
  Target,
  Tent,
  Terminal,
  TrendingUp,
  UserCheck,
  Users,
  Video,
  Wrench,
  Zap,
};

/**
 * Return the ``LucideIcon`` for a catalog ``icon_name``. Falls back to
 * ``Sparkles`` if the name isn't in the registered map — better than
 * crashing on an unrecognised value.
 */
export function resolveIconByName(iconName: string | undefined): LucideIcon {
  if (!iconName) return Sparkles;
  return ICON_BY_NAME[iconName] ?? Sparkles;
}
