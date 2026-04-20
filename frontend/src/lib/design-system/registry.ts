/**
 * Component Registry — Single source of truth for all frontend components.
 *
 * Machine-readable catalog used by:
 * 1. Playground page (/playground/design-system) for visual browsing
 * 2. Claude (AI) before generating any new component — check what exists first
 * 3. Audit tooling to detect duplications and inconsistencies
 *
 * Last audited: 2026-03-18
 *
 * Split into partial registries for maintainability:
 * - registry-primitives.ts  → Shadcn UI + Shared components
 * - registry-sales.ts       → Sales feature components
 * - registry-growth.ts      → Growth Studio components
 * - registry-features.ts    → Brand, Connections, Offer, Audit, Admin
 */

import { REGISTRY_OTHER_FEATURES } from "./registry-features";
import { REGISTRY_GROWTH } from "./registry-growth";
import { REGISTRY_PRIMITIVES } from "./registry-primitives";
import { REGISTRY_SALES } from "./registry-sales";

import type { ComponentEntry, DesignToken } from "./types";

// ---------------------------------------------------------------------------
// COMPONENT REGISTRY (assembled from partial registries)
// ---------------------------------------------------------------------------

export const COMPONENT_REGISTRY: ComponentEntry[] = [
  ...REGISTRY_PRIMITIVES,
  ...REGISTRY_SALES,
  ...REGISTRY_GROWTH,
  ...REGISTRY_OTHER_FEATURES,
];

// ---------------------------------------------------------------------------
// DESIGN TOKENS
// ---------------------------------------------------------------------------

export const DESIGN_TOKENS: DesignToken[] = [
  // --- Colors (from globals.css CSS variables) ---
  {
    category: "color",
    name: "Background",
    cssVar: "--background",
    tailwindClass: "bg-background",
    value: "hsl(0 0% 100%)",
  },
  {
    category: "color",
    name: "Foreground",
    cssVar: "--foreground",
    tailwindClass: "text-foreground",
    value: "hsl(222.2 84% 4.9%)",
  },
  {
    category: "color",
    name: "Primary",
    cssVar: "--primary",
    tailwindClass: "bg-primary",
    value: "hsl(222.2 47.4% 11.2%)",
  },
  {
    category: "color",
    name: "Primary Foreground",
    cssVar: "--primary-foreground",
    tailwindClass: "text-primary-foreground",
    value: "hsl(210 40% 98%)",
  },
  {
    category: "color",
    name: "Secondary",
    cssVar: "--secondary",
    tailwindClass: "bg-secondary",
    value: "hsl(210 40% 96.1%)",
  },
  {
    category: "color",
    name: "Secondary Foreground",
    cssVar: "--secondary-foreground",
    tailwindClass: "text-secondary-foreground",
    value: "hsl(222.2 47.4% 11.2%)",
  },
  {
    category: "color",
    name: "Muted",
    cssVar: "--muted",
    tailwindClass: "bg-muted",
    value: "hsl(210 40% 96.1%)",
  },
  {
    category: "color",
    name: "Muted Foreground",
    cssVar: "--muted-foreground",
    tailwindClass: "text-muted-foreground",
    value: "hsl(215.4 16.3% 46.9%)",
  },
  {
    category: "color",
    name: "Accent",
    cssVar: "--accent",
    tailwindClass: "bg-accent",
    value: "hsl(210 40% 96.1%)",
  },
  {
    category: "color",
    name: "Accent Foreground",
    cssVar: "--accent-foreground",
    tailwindClass: "text-accent-foreground",
    value: "hsl(222.2 47.4% 11.2%)",
  },
  {
    category: "color",
    name: "Destructive",
    cssVar: "--destructive",
    tailwindClass: "bg-destructive",
    value: "hsl(0 84.2% 60.2%)",
  },
  {
    category: "color",
    name: "Destructive Foreground",
    cssVar: "--destructive-foreground",
    tailwindClass: "text-destructive-foreground",
    value: "hsl(210 40% 98%)",
  },
  {
    category: "color",
    name: "Card",
    cssVar: "--card",
    tailwindClass: "bg-card",
    value: "hsl(0 0% 100%)",
  },
  {
    category: "color",
    name: "Card Foreground",
    cssVar: "--card-foreground",
    tailwindClass: "text-card-foreground",
    value: "hsl(222.2 84% 4.9%)",
  },
  {
    category: "color",
    name: "Popover",
    cssVar: "--popover",
    tailwindClass: "bg-popover",
    value: "hsl(0 0% 100%)",
  },
  {
    category: "color",
    name: "Popover Foreground",
    cssVar: "--popover-foreground",
    tailwindClass: "text-popover-foreground",
    value: "hsl(222.2 84% 4.9%)",
  },
  {
    category: "color",
    name: "Border",
    cssVar: "--border",
    tailwindClass: "border-border",
    value: "hsl(214.3 31.8% 91.4%)",
  },
  {
    category: "color",
    name: "Input",
    cssVar: "--input",
    tailwindClass: "border-input",
    value: "hsl(214.3 31.8% 91.4%)",
  },
  {
    category: "color",
    name: "Ring",
    cssVar: "--ring",
    tailwindClass: "ring-ring",
    value: "hsl(222.2 84% 4.9%)",
  },

  // --- Typography ---
  { category: "typography", name: "Text XS", tailwindClass: "text-xs", value: "0.75rem / 1rem" },
  {
    category: "typography",
    name: "Text SM",
    tailwindClass: "text-sm",
    value: "0.875rem / 1.25rem",
  },
  { category: "typography", name: "Text Base", tailwindClass: "text-base", value: "1rem / 1.5rem" },
  {
    category: "typography",
    name: "Text LG",
    tailwindClass: "text-lg",
    value: "1.125rem / 1.75rem",
  },
  { category: "typography", name: "Text XL", tailwindClass: "text-xl", value: "1.25rem / 1.75rem" },
  { category: "typography", name: "Text 2XL", tailwindClass: "text-2xl", value: "1.5rem / 2rem" },
  {
    category: "typography",
    name: "Text 3XL",
    tailwindClass: "text-3xl",
    value: "1.875rem / 2.25rem",
  },
  { category: "typography", name: "Font Normal", tailwindClass: "font-normal", value: "400" },
  { category: "typography", name: "Font Medium", tailwindClass: "font-medium", value: "500" },
  { category: "typography", name: "Font Semibold", tailwindClass: "font-semibold", value: "600" },
  { category: "typography", name: "Font Bold", tailwindClass: "font-bold", value: "700" },

  // --- Spacing ---
  { category: "spacing", name: "Space 1", tailwindClass: "p-1", value: "0.25rem (4px)" },
  { category: "spacing", name: "Space 2", tailwindClass: "p-2", value: "0.5rem (8px)" },
  { category: "spacing", name: "Space 3", tailwindClass: "p-3", value: "0.75rem (12px)" },
  { category: "spacing", name: "Space 4", tailwindClass: "p-4", value: "1rem (16px)" },
  { category: "spacing", name: "Space 6", tailwindClass: "p-6", value: "1.5rem (24px)" },
  { category: "spacing", name: "Space 8", tailwindClass: "p-8", value: "2rem (32px)" },
  { category: "spacing", name: "Space 12", tailwindClass: "p-12", value: "3rem (48px)" },
  { category: "spacing", name: "Space 16", tailwindClass: "p-16", value: "4rem (64px)" },

  // --- Border Radius ---
  {
    category: "radius",
    name: "Radius SM",
    cssVar: "--radius-sm",
    tailwindClass: "rounded-sm",
    value: "calc(var(--radius) - 4px)",
  },
  {
    category: "radius",
    name: "Radius MD",
    cssVar: "--radius-md",
    tailwindClass: "rounded-md",
    value: "calc(var(--radius) - 2px)",
  },
  {
    category: "radius",
    name: "Radius LG",
    cssVar: "--radius-lg",
    tailwindClass: "rounded-lg",
    value: "var(--radius) = 0.5rem",
  },
  { category: "radius", name: "Radius Full", tailwindClass: "rounded-full", value: "9999px" },

  // --- Shadows ---
  {
    category: "shadow",
    name: "Shadow SM",
    tailwindClass: "shadow-sm",
    value: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  },
  {
    category: "shadow",
    name: "Shadow",
    tailwindClass: "shadow",
    value: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
  },
  {
    category: "shadow",
    name: "Shadow MD",
    tailwindClass: "shadow-md",
    value: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
  },
  {
    category: "shadow",
    name: "Shadow LG",
    tailwindClass: "shadow-lg",
    value: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
  },
];

// ---------------------------------------------------------------------------
// HELPER FUNCTIONS
// ---------------------------------------------------------------------------

/** Get all components at a specific atomic level */
export function getByLevel(level: ComponentEntry["atomicLevel"]): ComponentEntry[] {
  return COMPONENT_REGISTRY.filter((c) => c.atomicLevel === level);
}

/** Get all components from a specific source */
export function getBySource(source: ComponentEntry["source"]): ComponentEntry[] {
  return COMPONENT_REGISTRY.filter((c) => c.source === source);
}

/** Get all components with issues */
export function getWithIssues(): ComponentEntry[] {
  return COMPONENT_REGISTRY.filter((c) => c.issues && c.issues.length > 0);
}

/** Get components for a specific feature slice */
export function getByFeature(featureSlice: string): ComponentEntry[] {
  return COMPONENT_REGISTRY.filter((c) => c.featureSlice === featureSlice);
}

/** Get tokens by category */
export function getTokensByCategory(category: DesignToken["category"]): DesignToken[] {
  return DESIGN_TOKENS.filter((t) => t.category === category);
}

/** Registry stats */
export function getStats() {
  const atoms = getByLevel("atom").length;
  const molecules = getByLevel("molecule").length;
  const organisms = getByLevel("organism").length;
  const withIssues = getWithIssues().length;
  return {
    total: COMPONENT_REGISTRY.length,
    atoms,
    molecules,
    organisms,
    withIssues,
    bySource: {
      shadcn: getBySource("shadcn").length,
      shared: getBySource("shared").length,
      feature: getBySource("feature").length,
    },
  };
}
