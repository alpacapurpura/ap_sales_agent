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
  BookOpen,
  Box,
  Brain,
  Briefcase,
  Building2,
  CalendarClock,
  CalendarDays,
  Cloud,
  Compass,
  Crown,
  Gem,
  GraduationCap,
  Hammer,
  Infinity as InfinityIcon,
  Library,
  Lightbulb,
  Mic,
  Monitor,
  Mountain,
  Package,
  Presentation,
  Rocket,
  Settings,
  Sparkles,
  Tent,
  TrendingUp,
  UserCheck,
  Users,
  Video,
  Wrench,
  Zap,
} from "lucide-react";

import type { LucideIcon } from "lucide-react";

export const ICON_BY_NAME: Readonly<Record<string, LucideIcon>> = {
  Award,
  BookOpen,
  Box,
  Brain,
  Briefcase,
  Building2,
  CalendarClock,
  CalendarDays,
  Cloud,
  Compass,
  Crown,
  Gem,
  GraduationCap,
  Hammer,
  Infinity: InfinityIcon,
  Library,
  Lightbulb,
  Mic,
  Monitor,
  Mountain,
  Package,
  Presentation,
  Rocket,
  Settings,
  Sparkles,
  Tent,
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
