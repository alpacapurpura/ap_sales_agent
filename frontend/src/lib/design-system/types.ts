/**
 * Design System Registry Types
 *
 * Machine-readable schema for the component registry.
 * Used by: Playground page, Claude (AI component generation), audit tooling.
 */

export type AtomicLevel = "token" | "atom" | "molecule" | "organism";

export interface ComponentEntry {
  /** Display name, e.g. "Button" */
  name: string;
  /** Atomic Design classification */
  atomicLevel: AtomicLevel;
  /** Path relative to frontend/src */
  filePath: string;
  /** Origin of the component */
  source: "shadcn" | "shared" | "feature";
  /** Feature slice name (only for source === 'feature') */
  featureSlice?: string;
  /** CVA variant names if applicable */
  variants?: string[];
  /** Key exported prop names */
  props?: string[];
  /** One-line purpose */
  description: string;
  /** Audit issues found */
  issues?: string[];
}

export interface DesignToken {
  category: "color" | "typography" | "spacing" | "radius" | "shadow";
  name: string;
  cssVar?: string;
  tailwindClass: string;
  value: string;
  /** Dark mode HSL value (color tokens only) */
  darkValue?: string;
}
